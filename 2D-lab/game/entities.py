"""Player, enemies and projectiles."""
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
    def __init__(self):
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
        # weapon
        self.shots = 1
        self.cooldown = S.SHOT_COOLDOWN
        self.damage = S.SHOT_DAMAGE
        self.pierce = S.SHOT_PIERCE
        self.speed = S.PLAYER_SPEED
        self.shot_cd = 0.3
        self.ghost_t = 0.0

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
        self.shot_cd = max(0.0, self.shot_cd - dt)

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
        self.cd = random.uniform(0.6, 1.8)    # lancer: time to next throw; elite: time to next charge
        self.windup = 0.0
        self.charge_t = 0.0
        self.cdx = self.cdy = 0.0
        self.spawn_t = 0.35                   # fade/scale in
        self.detour = None                    # (dx, dy, time left): slide along an obstacle

    def hit(self, dmg, dx, dy, force=220.0):
        self.hp -= dmg
        self.flash = 0.12
        n = _len(dx, dy) or 1.0
        self.kx += dx / n * force * self.knock
        self.ky += dy / n * force * self.knock

    def update(self, dt, player, level, game):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.spawn_t = max(0.0, self.spawn_t - dt)
        dx, dy = player.x - self.x, player.y - self.y
        dist = _len(dx, dy) or 1.0
        ux, uy = dx / dist, dy / dist
        mx = my = 0.0
        sp = self.speed * game.enemy_speed_mult

        if self.kind == "sentinel":
            mx, my = ux * sp, uy * sp
        elif self.kind == "skirmisher":
            wob = math.sin(self.t * 4.2) * 0.55         # weaves left/right on the way in
            mx, my = (ux - uy * wob) * sp, (uy + ux * wob) * sp
        elif self.kind == "lancer":
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
                    game.spawn_spear(self.x, self.y, self.cdx, self.cdy)
            elif self.cd <= 0 and dist < 560:
                self.windup = S.SPEAR_WINDUP
                self.cd = S.SPEAR_COOLDOWN * random.uniform(0.9, 1.2)
                self.cdx, self.cdy = ux, uy
            if self.windup > 0:                          # keep aiming while winding up
                self.cdx, self.cdy = ux, uy
        elif self.kind == "elite":
            if self.charge_t > 0:
                self.charge_t -= dt
                mx, my = self.cdx * S.ELITE_CHARGE_SPEED, self.cdy * S.ELITE_CHARGE_SPEED
            elif self.windup > 0:
                self.windup -= dt
                mx = my = 0.0
                if self.windup <= 0:
                    self.charge_t = S.ELITE_CHARGE_TIME
                    game.assets.play("slam")
            else:
                mx, my = ux * sp, uy * sp
                self.cd -= dt
                if self.cd <= 0 and dist < 700:
                    self.windup = S.ELITE_WINDUP
                    self.cd = S.ELITE_CHARGE_COOLDOWN
                    self.cdx, self.cdy = ux, uy
            if self.windup > 0:
                self.cdx, self.cdy = ux, uy

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
        if self.kind in ("lancer", "elite") and self.windup > 0:
            self.face = _turn(self.face, _dir_to_angle(self.cdx, self.cdy), 10 * dt)
        else:
            self.face = _turn(self.face, _dir_to_angle(ux, uy), 8 * dt)


class Shot:
    """The hero's piercing needle."""
    __slots__ = ("x", "y", "vx", "vy", "life", "dmg", "pierce", "hit")

    def __init__(self, x, y, vx, vy, dmg, pierce):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = S.SHOT_LIFE
        self.dmg = dmg
        self.pierce = pierce
        self.hit = set()


class Spear:
    """Light spear thrown by lancers."""
    __slots__ = ("x", "y", "vx", "vy", "life")

    def __init__(self, x, y, ux, uy):
        self.x, self.y = x + ux * 30, y + uy * 30
        self.vx, self.vy = ux * S.SPEAR_SPEED, uy * S.SPEAR_SPEED
        self.life = S.SPEAR_LIFE


class HeartPickup:
    def __init__(self, x, y, respawns=True):
        self.x, self.y = x, y
        self.alive = True
        self.timer = 0.0
        self.respawns = respawns
