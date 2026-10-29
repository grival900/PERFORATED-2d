"""Player, enemies, projectiles and pickups."""
import math
import random

import settings as S


def _len(x, y):
    return math.hypot(x, y)


def _angle_to_dir(a):
    """Facing angle (0 = up, clockwise positive) to a unit vector."""
    return math.sin(a), -math.cos(a)


def _dir_to_angle(dx, dy):
    return math.atan2(dx, -dy)


def _turn(cur, target, rate):
    d = (target - cur + math.pi) % math.tau - math.pi
    return cur + d * min(1.0, rate)


class Player:
    def __init__(self, carry=None):
        self.x, self.y = S.PLAYER_START
        self.vx = self.vy = 0.0
        self.r = S.PLAYER_RADIUS
        self.hp = self.max_hp = S.PLAYER_MAX_HP
        self.invuln = 0.0
        self.facing = 0.0
        # dash
        self.dash_t = 0.0
        self.dash_dx = self.dash_dy = 0.0
        self.dash_hit = set()
        self.charges = self.charge_cap = S.DASH_CHARGES
        self.recharge = S.DASH_RECHARGE
        self.recharge_t = 0.0
        # weapon stats shared by every weapon (raised by box-point upgrades)
        self.weapons = {}                 # id -> Weapon, filled in by the game
        self.dmg_mult = 1.0
        self.rate_mult = 1.0              # multiplies every cooldown (lower is faster)
        self.bonus = 0                    # extra projectiles / orbs / jumps / mines
        self.pierce_bonus = 0
        self.area = 1.0
        self.speed = S.PLAYER_SPEED
        self.ghost_t = 0.0
        if carry:
            self.dmg_mult, self.rate_mult = carry["dmg_mult"], carry["rate_mult"]
            self.bonus, self.pierce_bonus, self.area = carry["bonus"], carry["pierce_bonus"], carry["area"]
            self.speed = carry["speed"]
            self.hp = self.max_hp = carry["max_hp"]
            self.charges = self.charge_cap = carry["charge_cap"]
            self.recharge = carry["recharge"]

    def snapshot(self):
        """Everything Level 1 gave the hero that carries over to the next level."""
        return dict(weapons=list(self.weapons), dmg_mult=self.dmg_mult, rate_mult=self.rate_mult, bonus=self.bonus,
                    pierce_bonus=self.pierce_bonus, area=self.area, speed=self.speed, max_hp=self.max_hp,
                    charge_cap=self.charge_cap, recharge=self.recharge)

    @property
    def dashing(self):
        return self.dash_t > 0

    def try_dash(self, move_x, move_y):
        if self.charges < 1 or self.dash_t > 0:
            return False
        if _len(move_x, move_y) > 0.1:
            n = _len(move_x, move_y)
            self.dash_dx, self.dash_dy = move_x / n, move_y / n
        else:
            self.dash_dx, self.dash_dy = _angle_to_dir(self.facing)
        self.charges -= 1
        self.dash_t = S.DASH_TIME
        self.invuln = max(self.invuln, S.DASH_IFRAMES)
        self.dash_hit = set()
        return True

    def update(self, dt, move, level, target):
        mx, my = move
        n = _len(mx, my)
        if n > 1.0:
            mx, my = mx / n, my / n
            n = 1.0
        # recharge dash charges one at a time
        if self.charges < self.charge_cap:
            self.recharge_t += dt
            if self.recharge_t >= self.recharge:
                self.recharge_t = 0.0
                self.charges += 1
        else:
            self.recharge_t = 0.0
        self.invuln = max(0.0, self.invuln - dt)

        if self.dash_t > 0:
            self.dash_t -= dt
            self.vx, self.vy = self.dash_dx * S.DASH_SPEED, self.dash_dy * S.DASH_SPEED
            if self.dash_t <= 0:                       # carry some momentum out of the dash
                self.vx, self.vy = self.dash_dx * self.speed * 1.25, self.dash_dy * self.speed * 1.25
        else:
            tx, ty = mx * self.speed, my * self.speed
            dvx, dvy = tx - self.vx, ty - self.vy
            dist = _len(dvx, dvy)
            step = (S.PLAYER_ACCEL if n > 0.05 else S.PLAYER_FRICTION) * dt
            if dist <= step or dist < 1e-6:
                self.vx, self.vy = tx, ty
            else:
                self.vx += dvx / dist * step
                self.vy += dvy / dist * step

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y, hit = level.collide(self.x, self.y, self.r)
        if hit and self.dash_t > 0:
            self.dash_t = 0.0

        # facing: towards the target, else the direction of travel
        if target is not None:
            self.facing = _turn(self.facing, _dir_to_angle(target.x - self.x, target.y - self.y), 18 * dt)
        elif _len(self.vx, self.vy) > 30:
            self.facing = _turn(self.facing, _dir_to_angle(self.vx, self.vy), 10 * dt)

    def hurt(self):
        self.hp -= 1
        self.invuln = S.INVULN_TIME


class Enemy:
    _next_id = 0

    def __init__(self, kind, x, y, hp_scale=1.0):
        st = S.ENEMIES[kind]
        self.kind = kind
        self.id = Enemy._next_id
        Enemy._next_id += 1
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.kx = self.ky = 0.0               # knock-back velocity
        self.hp = self.max_hp = st["hp"] * hp_scale
        self.r = st["r"]
        self.speed = st["speed"] * random.uniform(0.92, 1.08)
        self.pts = st["pts"]
        self.sprite = st["sprite"]
        self.shadow = st["shadow"]
        self.knock = st["knock"]
        self.flash = 0.0
        self.face = random.uniform(0, math.tau)
        self.t = random.uniform(0, 6.0)
        self.cd = random.uniform(0.6, 1.8)    # lancer: time to next throw; elite/skirmisher: time to next charge
        self.windup = 0.0
        self.windup_max = 1.0
        self.charge_t = 0.0
        self.cdx = self.cdy = 0.0
        self.spawn_t = 0.35                   # fade/scale in
        self.detour = None                    # (dx, dy, time left): slide along an obstacle
        self.flank = random.choice((-1, 1)) * random.uniform(0.25, 0.85)   # swing wide so groups surround
        self.nova_i = 0
        self.charm_t = 0.0                    # charmer: time left dragging the hero in
        self.burst = 0                        # banker: coin spears still to fire
        self.burst_t = 0.0

    def hit(self, dmg, dx, dy, force=220.0):
        self.hp -= dmg
        self.flash = 0.12
        n = _len(dx, dy) or 1.0
        self.kx += dx / n * force * self.knock
        self.ky += dy / n * force * self.knock

    def steer(self, player, dist, ux, uy, lead):
        """Direction to run in: optionally aimed at where the hero is heading, bent sideways while far away."""
        if lead:
            t = min(0.6, dist / max(self.speed, 1.0) * 0.5)
            dx, dy = player.x + player.vx * t - self.x, player.y + player.vy * t - self.y
            d = _len(dx, dy) or 1.0
            if (dx * ux + dy * uy) / d > 0.5:          # only lead when it still points at the hero
                ux, uy = dx / d, dy / d
        a = self.flank * min(1.0, max(0.0, (dist - 140.0) / 450.0))
        c, s = math.cos(a), math.sin(a)
        return ux * c - uy * s, ux * s + uy * c

    def update(self, dt, player, level, game):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.spawn_t = max(0.0, self.spawn_t - dt)
        dx, dy = player.x - self.x, player.y - self.y
        dist = _len(dx, dy) or 1.0
        ux, uy = dx / dist, dy / dist
        mx = my = 0.0
        sp = self.speed * game.enemy_speed_mult
        kind = self.kind

        if kind in ("sentinel", "swarmer"):
            sx, sy = self.steer(player, dist, ux, uy, True)
            mx, my = sx * sp, sy * sp
        elif kind == "bulwark":
            if self.hp < self.max_hp * S.BULWARK_ENRAGE:
                sp *= 1.5
            sx, sy = self.steer(player, dist, ux, uy, False)
            mx, my = sx * sp, sy * sp
        elif kind == "skirmisher":
            if self.charge_t > 0:                        # lunge
                self.charge_t -= dt
                mx, my = self.cdx * S.LUNGE_SPEED, self.cdy * S.LUNGE_SPEED
            elif self.windup > 0:                        # telegraph, aim until the last instant
                self.windup -= dt
                if self.windup > 0.08:
                    self.cdx, self.cdy = ux, uy
                if self.windup <= 0:
                    self.charge_t = S.LUNGE_TIME
            else:
                wob = math.sin(self.t * 4.2) * 0.55      # weaves left/right on the way in
                sx, sy = self.steer(player, dist, ux, uy, False)
                mx, my = (sx - sy * wob) * sp, (sy + sx * wob) * sp
                self.cd -= dt
                if self.cd <= 0 and dist < S.LUNGE_RANGE:
                    self.windup = self.windup_max = S.LUNGE_WINDUP
                    self.cd = S.LUNGE_COOLDOWN * random.uniform(0.8, 1.3)
                    self.cdx, self.cdy = ux, uy
        elif kind == "lancer":
            want = 340.0
            if dist > want + 40:
                mx, my = ux * sp, uy * sp
            elif dist < want - 80:
                mx, my = -ux * sp * 0.7, -uy * sp * 0.7
            else:
                mx, my = -uy * sp * 0.45, ux * sp * 0.45  # circle the player
            self.cd -= dt
            if self.windup > 0:
                self.windup -= dt
                mx, my = mx * 0.2, my * 0.2
                if self.windup <= 0:
                    fan = 3 if game.stage >= game.cfg.fan_stage else 1
                    for i in range(fan):
                        a = (i - (fan - 1) / 2) * 0.27
                        c, s = math.cos(a), math.sin(a)
                        game.spawn_spear(self.x, self.y, self.cdx * c - self.cdy * s, self.cdx * s + self.cdy * c)
            elif self.cd <= 0 and dist < 560:
                self.windup = self.windup_max = S.SPEAR_WINDUP
                self.cd = S.SPEAR_COOLDOWN * random.uniform(0.9, 1.2) * (0.85 if game.stage >= game.cfg.fan_stage else 1.0)
                self.cdx, self.cdy = ux, uy
            if self.windup > 0:                          # keep aiming while winding up
                self.cdx, self.cdy = ux, uy
        elif kind == "bomber":
            if self.windup > 0:                          # fuse lit: it stops and swells, then blows
                self.windup -= dt
                mx, my = ux * sp * 0.15, uy * sp * 0.15
                if self.windup <= 0:
                    game.bomber_explode(self)
            else:
                sx, sy = self.steer(player, dist, ux, uy, True)
                mx, my = sx * sp, sy * sp
                if dist < S.BOMBER_RANGE and self.spawn_t <= 0:
                    self.windup = self.windup_max = S.BOMBER_FUSE
        elif kind == "banker":
            want = 400.0
            if dist > want + 50:
                mx, my = ux * sp, uy * sp
            elif dist < want - 90:
                mx, my = -ux * sp * 0.8, -uy * sp * 0.8
            else:
                mx, my = -uy * sp * 0.55, ux * sp * 0.55
            self.cd -= dt
            if self.windup > 0:
                self.windup -= dt
                mx, my = mx * 0.2, my * 0.2
                self.cdx, self.cdy = ux, uy
                if self.windup <= 0:
                    self.burst, self.burst_t = S.BANKER_BURST, 0.0
            elif self.burst > 0:                         # a burst of coin spears, each aimed where you are now
                mx, my = mx * 0.2, my * 0.2
                self.burst_t -= dt
                if self.burst_t <= 0:
                    self.burst -= 1
                    self.burst_t = S.BANKER_GAP
                    game.spawn_spear(self.x, self.y, ux, uy)
            elif self.cd <= 0 and dist < 620:
                self.windup = self.windup_max = 0.4
                self.cd = 2.8 * random.uniform(0.85, 1.2)
                self.cdx, self.cdy = ux, uy
        elif kind == "cupid":
            want = 470.0
            if dist > want + 50:
                mx, my = ux * sp, uy * sp
            elif dist < want - 100:
                mx, my = -ux * sp * 0.8, -uy * sp * 0.8
            else:
                mx, my = -uy * sp * 0.6, ux * sp * 0.6
            self.cd -= dt
            if self.windup > 0:
                self.windup -= dt
                mx, my = mx * 0.2, my * 0.2
                self.cdx, self.cdy = ux, uy
                if self.windup <= 0:                     # a volley of slow homing hearts
                    n = S.CUPID_HEARTS
                    for i in range(n):
                        a = (i - (n - 1) / 2) * 0.7
                        c, s = math.cos(a), math.sin(a)
                        game.spawn_spear(self.x, self.y, ux * c - uy * s, ux * s + uy * c, homing=True)
            elif self.cd <= 0 and dist < 680:
                self.windup = self.windup_max = 0.5
                self.cd = 3.2 * random.uniform(0.85, 1.2)
                self.cdx, self.cdy = ux, uy
        elif kind == "charmer":
            want = 430.0
            if dist > want + 50:
                mx, my = ux * sp, uy * sp
            elif dist < want - 100:
                mx, my = -ux * sp * 0.8, -uy * sp * 0.8
            else:
                mx, my = -uy * sp * 0.5, ux * sp * 0.5
            if self.charm_t > 0:                         # dragging the hero in; a dash breaks free
                self.charm_t -= dt
                mx, my = mx * 0.2, my * 0.2
                game.charm_pull(self, dt)
            elif self.windup > 0:
                self.windup -= dt
                mx, my = mx * 0.2, my * 0.2
                if self.windup <= 0:
                    self.charm_t = S.CHARM_TIME
            else:
                self.cd -= dt
                if self.cd <= 0 and dist < S.CHARM_RANGE and self.spawn_t <= 0:
                    self.windup = self.windup_max = S.CHARM_WINDUP
                    self.cd = S.CHARM_COOLDOWN * random.uniform(0.85, 1.2)
        elif kind == "elite":
            if self.charge_t > 0:
                self.charge_t -= dt
                mx, my = self.cdx * S.ELITE_CHARGE_SPEED, self.cdy * S.ELITE_CHARGE_SPEED
            elif self.windup > 0:
                self.windup -= dt
                mx = my = 0.0
                if self.windup <= 0:
                    self.charge_t = S.ELITE_CHARGE_TIME
                    game.assets.play("slam")
            elif self.nova_i < len(game.cfg.nova_marks) and self.hp <= self.max_hp * game.cfg.nova_marks[self.nova_i]:
                self.nova_i += 1                         # at set health marks: a ring of light spears
                n = game.cfg.nova_spears
                for i in range(n):
                    a = i * math.tau / n + self.t
                    game.spawn_spear(self.x, self.y, math.cos(a), math.sin(a))
                game.assets.play("elite")
            else:
                mx, my = ux * sp, uy * sp
                self.cd -= dt
                if self.cd <= 0 and dist < 700:
                    self.windup = self.windup_max = S.ELITE_WINDUP
                    self.cd = S.ELITE_CHARGE_COOLDOWN * (0.8 if game.stage >= game.cfg.elite_rage_stage else 1.0)
                    self.cdx, self.cdy = ux, uy
            if self.windup > 0:
                self.cdx, self.cdy = ux, uy

        if kind in S.MELEE_KINDS and self.charge_t <= 0:
            back = mx * ux + my * uy
            if back < 0:
                mx, my = mx - back * ux, my - back * uy

        if self.detour is not None:
            ddx, ddy, left = self.detour
            left -= dt
            self.detour = (ddx, ddy, left) if left > 0 else None
            mx, my = mx * 0.35 + ddx * sp * 0.9, my * 0.35 + ddy * sp * 0.9
        # knock-back decays quickly
        self.kx *= max(0.0, 1.0 - 9.0 * dt)
        self.ky *= max(0.0, 1.0 - 9.0 * dt)
        self.vx, self.vy = mx + self.kx, my + self.ky
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y, _ = level.collide(self.x, self.y, self.r, through_gate=False)
        if level.last_normal is not None and self.charge_t <= 0:
            nx, ny = level.last_normal
            tx, ty = -ny, nx
            side = tx * ux + ty * uy
            if abs(side) < 0.15:
                side = 1.0 if self.id % 2 == 0 else -1.0
            sgn = 1.0 if side > 0 else -1.0
            self.detour = (tx * sgn, ty * sgn, 0.7)
        if kind in ("lancer", "elite", "skirmisher", "banker", "cupid") and self.windup > 0:
            self.face = _turn(self.face, _dir_to_angle(self.cdx, self.cdy), 10 * dt)
        else:
            self.face = _turn(self.face, _dir_to_angle(ux, uy), 8 * dt)


class Shot:
    """A hero projectile: needle, scatter pellet or homing seeker."""
    __slots__ = ("x", "y", "vx", "vy", "life", "dmg", "pierce", "hit", "kind", "r", "speed")

    def __init__(self, x, y, vx, vy, dmg, pierce, kind="needle", life=S.SHOT_LIFE, r=9):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = life
        self.dmg = dmg
        self.pierce = pierce
        self.hit = set()
        self.kind = kind
        self.r = r
        self.speed = math.hypot(vx, vy)


class Spear:
    """Light spear thrown by lancers."""
    __slots__ = ("x", "y", "vx", "vy", "life", "homing")

    def __init__(self, x, y, ux, uy, homing=False):
        self.x, self.y = x + ux * 30, y + uy * 30
        sp = S.HEART_SPEED if homing else S.SPEAR_SPEED
        self.vx, self.vy = ux * sp, uy * sp
        self.life = S.HEART_LIFE if homing else S.SPEAR_LIFE
        self.homing = homing                  # a cupid's heart: slow, curves after the hero


class HeartPickup:
    def __init__(self, x, y, respawns=True):
        self.x, self.y = x, y
        self.alive = True
        self.timer = 0.0
        self.respawns = respawns


class Box:
    """A breakable crate: walk (or dash) over it and it bursts into box points."""
    __slots__ = ("x", "y", "gilded", "t")
    r = 26

    def __init__(self, x, y, gilded=False):
        self.x, self.y, self.gilded = x, y, gilded
        self.t = random.uniform(0, 6.0)


class Gem:
    """A box-point gem. It lies where it fell, then flies to the hero when close."""
    __slots__ = ("x", "y", "vx", "vy", "val", "life", "age", "t")

    def __init__(self, x, y, val):
        a = random.uniform(0, math.tau)
        sp = random.uniform(120, 300)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * sp, math.sin(a) * sp
        self.val = val
        self.life = S.GEM_LIFE
        self.age = 0.0
        self.t = random.uniform(0, 6.0)


class Mine:
    __slots__ = ("x", "y", "age", "life", "dmg", "radius")

    def __init__(self, x, y, dmg, radius):
        self.x, self.y = x, y
        self.age = 0.0
        self.life = S.MINE_LIFE
        self.dmg = dmg
        self.radius = radius


class Chakram:
    """Thrown out, then recalled to the hero; pierces everything on the way."""
    __slots__ = ("x", "y", "dx", "dy", "dist", "going", "traveled", "hit", "spin", "dmg", "life")

    def __init__(self, x, y, dx, dy, dist, dmg):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.dist = dist
        self.going = True
        self.traveled = 0.0
        self.hit = set()
        self.spin = 0.0
        self.dmg = dmg
        self.life = 4.0


class Hazard:
    """A telegraphed ground blast: a growing circle, then damage to anyone still inside."""
    __slots__ = ("x", "y", "r", "t", "dur", "style")

    def __init__(self, x, y, r, dur, style):
        self.x, self.y, self.r, self.dur, self.style = x, y, r, dur, style
        self.t = 0.0


class Boss(Enemy):
    """A level boss: keeps its distance and cycles through themed attacks, faster once below half health."""

    def __init__(self, x, y, spec):
        super().__init__("elite", x, y, 1.0)
        self.kind = "boss"
        self.spec = spec
        self.hp = self.max_hp = float(spec["hp"])
        self.r = spec["r"]
        self.sprite = "guardian_boss"
        self.shadow = 150
        self.knock = 0.0
        self.pts = 0
        self.speed = spec["speed"]
        self.spawn_t = 1.0
        self.act = None               # current attack
        self.act_t = 0.0
        self.rest = 2.4
        self.last = None
        self.tele = 0.0               # 0..1 progress of the current wind-up (for drawing)
        self.aim = (0.0, 1.0)
        self.fired = 0
        self.side = random.choice((-1, 1))
        self.spin = random.uniform(0, math.tau)

    @property
    def enraged(self):
        return self.hp < self.max_hp * 0.5

    def begin(self):
        moves = [m for m in self.spec["moves"] if m != self.last]
        self.act = self.last = random.choice(moves)
        self.act_t, self.fired, self.tele = 0.0, 0, 0.0

    def end(self):
        self.act = None
        self.tele = 0.0
        self.rest = 0.9 if self.enraged else 1.6

    def update(self, dt, player, level, game):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.spawn_t = max(0.0, self.spawn_t - dt)
        dx, dy = player.x - self.x, player.y - self.y
        dist = _len(dx, dy) or 1.0
        ux, uy = dx / dist, dy / dist
        sp = self.speed * (1.3 if self.enraged else 1.0)
        mx = my = 0.0
        if self.act is None:
            if dist > 430:
                mx, my = ux * sp, uy * sp
            elif dist < 280:
                mx, my = -ux * sp * 0.7, -uy * sp * 0.7
            else:
                mx, my = -uy * sp * 0.5 * self.side, ux * sp * 0.5 * self.side
            self.rest -= dt
            if self.rest <= 0 and self.spawn_t <= 0:
                self.begin()
        else:
            mx, my = self.run(dt, player, game, ux, uy)
        self.x += mx * dt
        self.y += my * dt
        self.x, self.y, _ = level.collide(self.x, self.y, self.r, through_gate=False)
        want = self.aim if self.act in ("fan", "charge") else (ux, uy)
        self.face = _turn(self.face, _dir_to_angle(*want), 6 * dt)

    # ---- the attacks ------------------------------------------------------------------------
    def ring(self, game, offset):
        sp = self.spec
        n = sp["ring_n"] if not sp["ring_homing"] else (7 if not self.enraged else 10)
        if self.enraged and not sp["ring_homing"]:
            n = int(n * 1.5)
        for i in range(n):
            a = offset + i * math.tau / n
            game.spawn_spear(self.x, self.y, math.cos(a), math.sin(a), homing=sp["ring_homing"])
        game.fx.ring(self.x, self.y, sp["color"], 260, 0.5, 8)

    def run(self, dt, p, game, ux, uy):
        a, t, enr, spec = self.act, self.act_t + dt, self.enraged, self.spec
        self.act_t = t
        mx = my = 0.0
        if a == "ring":
            W = 0.9
            self.tele = min(1.0, t / W)
            if t >= W and self.fired == 0:
                self.fired = 1
                self.ring(game, 0.0)
            if t >= W + 0.55 and self.fired == 1:
                self.fired = 2
                self.ring(game, math.pi / 9)
            if t >= W + 0.9:
                self.end()
        elif a == "fan":
            W, nv = 0.6, (4 if enr else 3)
            self.tele = min(1.0, t / W)
            if t < W - 0.15:
                self.aim = (ux, uy)
            if self.fired < nv and t >= W + self.fired * 0.4:
                self.fired += 1
                base = math.atan2(uy, ux)
                n = 7 if enr else 5
                for i in range(n):
                    ang = base + (i - (n - 1) / 2) * 0.2
                    game.spawn_spear(self.x, self.y, math.cos(ang), math.sin(ang))
            if self.fired >= nv and t > W + nv * 0.4:
                self.end()
        elif a == "zones":
            W = 0.5
            self.tele = min(1.0, t / W)
            if t >= W and self.fired == 0:
                self.fired = 1
                n = 6 if enr else 4
                game.spawn_hazard(p.x + p.vx * 0.5, p.y + p.vy * 0.5, 115, 1.1, spec["zone"])
                for _ in range(n - 1):
                    ang, rad = random.uniform(0, math.tau), random.uniform(120, 320)
                    game.spawn_hazard(p.x + math.cos(ang) * rad, p.y + math.sin(ang) * rad, 115, 1.1, spec["zone"])
            if t >= W + 0.5:
                self.end()
        elif a == "charge":
            W = 0.8
            self.tele = min(1.0, t / W)
            if t < W - 0.2:
                self.aim = (ux, uy)
            elif W <= t < W + 0.6:
                mx, my = self.aim[0] * 640.0, self.aim[1] * 640.0
            if t >= W + 0.6 and self.fired == 0:
                self.fired = 1
                game.spawn_hazard(self.x, self.y, 240, 0.3, spec["zone"])
                game.shake = max(game.shake, 0.5)
            if t >= W + 0.95:
                self.end()
        elif a == "summon":
            W = 1.0
            self.tele = min(1.0, t / W)
            if t >= W and self.fired == 0:
                self.fired = 1
                for kind, n in spec["summon"]:
                    for _ in range(n):
                        ang = random.uniform(0, math.tau)
                        game.spawn_enemy(kind, self.x + math.cos(ang) * 130, self.y + math.sin(ang) * 130)
                game.fx.ring(self.x, self.y, spec["color"], 300, 0.6, 10)
                game.assets.play("elite")
            if t >= W + 0.6:
                self.end()
        elif a == "spiral":
            W, total = 0.5, (34 if enr else 26)
            self.tele = min(1.0, t / W)
            while self.fired < total and t >= W + self.fired * 0.1:
                ang = self.spin + self.fired * 0.45
                for k in range(2 if enr else 1):
                    game.spawn_spear(self.x, self.y, math.cos(ang + k * math.pi), math.sin(ang + k * math.pi))
                self.fired += 1
            if self.fired >= total:
                self.end()
        elif a == "charm":
            W = 0.8
            self.tele = min(1.0, t / W)
            if t >= W and self.fired == 0:
                self.fired = 1
                self.charm_t = 1.7
            if self.fired == 1:
                self.charm_t -= dt
                game.charm_pull(self, dt)
                if self.charm_t <= 0:
                    self.end()
        return mx, my
