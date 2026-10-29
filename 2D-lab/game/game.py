"""PERFORATED, Level 1 (Pride): game state, simulation and rendering."""
import math
import random

import pygame

import settings as S
import strings
import weapons as W
from assets import Assets
from entities import Boss, Box, Enemy, Gem, Hazard, HeartPickup, Player, Shot, Spear
from fx import Particles
from level import Level
from strings import t, tl
from ui import UI

UPGRADE_IDS = ["multi", "rate", "pierce", "power", "area", "dash", "speed", "heart"]
HAZARD_COLORS = {"light": (255, 225, 120), "gold": (255, 205, 60), "rose": (255, 90, 160)}
AREA_WEAPONS = ("halo", "pulse", "arc", "mine", "chakram")


class Lighting:
    """Low-resolution additive light map, multiplied over the frame."""

    def __init__(self, assets, w, h, scale=4):
        self.a, self.w, self.h, self.s = assets, w, h, scale
        self.ambient = (62, 68, 98)
        self.lm = pygame.Surface((w // scale, h // scale))

    def render(self, screen, cam, lights):
        lm, s = self.lm, self.s
        lm.fill(self.ambient)
        lw, lh = lm.get_size()
        for x, y, r, col in lights:
            sx, sy, rr = (x - cam[0]) / s, (y - cam[1]) / s, max(3, int(r / s / 3) * 3)
            if sx < -rr or sx > lw + rr or sy < -rr or sy > lh + rr:
                continue
            g = self.a.glow(rr, col)
            lm.blit(g, (sx - rr, sy - rr), special_flags=pygame.BLEND_RGB_ADD)
        big = pygame.transform.smoothscale(lm, (self.w, self.h))
        screen.blit(big, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.assets = Assets()
        self.assets.load_images()
        self.assets.load_sounds()
        self.assets.prewarm()
        self.levels = {}                 # baked levels, built the first time they are played
        self.level_no = 1
        self.cfg = S.LEVELS[1]
        self.theme = S.THEMES[1]
        self.carry = None                # what the hero brings into this level
        self.level_carry = None
        self.level = self.get_level(1)
        self.fx = Particles(self.assets)
        self.ui = UI(self.assets)
        self.light = Lighting(self.assets, S.SCREEN_W, S.SCREEN_H)
        self._shadow = {}
        self.clock = 0.0                 # real time, runs in every state
        self.state = "title"
        self.cam = [0.0, 0.0]
        self.reset()
        self.state = "title"
        self.cam = [S.PLAYER_START[0] - S.SCREEN_W / 2, S.PLAYER_START[1] - S.SCREEN_H / 2 - 120]

    # ------------------------------------------------------------------ run control
    def get_level(self, n):
        if n not in self.levels:
            lvl = Level(self.assets, n)
            lvl.bake()
            self.levels[n] = lvl
        return self.levels[n]

    def begin_level(self, n, carry=None):
        """Start level n. `carry` is what the hero keeps from the levels before (None = a fresh hero)."""
        self.level_no, self.cfg, self.theme = n, S.LEVELS[n], S.THEMES[n]
        self.carry = self.level_carry = carry
        if self.assets.theme is not self.theme:
            self.assets.set_theme(self.theme)
        self.level = self.get_level(n)
        self.light.ambient = self.theme["ambient"]
        self.reset()
        self.assets.start_music()
        self.show_banner(tl("subtitle", n) if n > 1 else t("stage").format(n=1) + ": " + tl("stage_desc", n)[1])

    def reset(self):
        random.seed()
        Enemy._next_id = 0
        self.level.gate_open = False
        self.player = Player(self.carry)
        names = self.carry["weapons"] if self.carry else ["needle"]
        self.player.weapons = {w: W.WEAPONS[w]() for w in names}
        self.enemies, self.shots, self.spears = [], [], []
        self.mines, self.chakrams, self.bolts, self.waves = [], [], [], []
        self.hazards = []                # telegraphed ground blasts (boss)
        self.boss_due = False            # the final wave has begun and the boss has not arrived yet
        self.hold_exit = False           # the bar is full but the boss still lives
        self.grid = {}
        self.pickups = [HeartPickup(x, y) for x, y in S.HEART_SPOTS]
        self.fx.items.clear()
        self.time = 0.0
        self.kills = 0
        self.pride = 0.0
        self.pride_shown = 0.0
        self.bar_pulse = 0.0
        self.stage = 1
        self.banner_t = 0.0
        self.banner_text = ""
        self.spawn_t = 2.2
        self.recycle_t = 1.0
        self.elites = 0
        self.pending_elites = 0
        self.elite_t = 0.0
        # box points ("offerings") are separate from Pride points
        self.boxes, self.gems = [], []
        self.box_pts = 0               # progress towards the next stat upgrade
        self.box_total = 0
        self.box_upgrades = 0
        self.box_timer = S.BOX_RESPAWN
        self.box_pulse = 0.0
        self.gem_acc = 0
        self.gem_acc_t = 0.0
        self.populate_boxes()
        self.queue = []                # menus waiting to open: "weapon" / "stat"
        self.choice_kind = "stat"
        self.upgrade_choices = []
        self.upgrade_sel = 0
        self.exit_open = False
        self.over = False
        self.dying_t = 0.0
        self.shake = 0.0
        self.red_flash = 0.0
        self.enemy_speed_mult = self.cfg.stage_speed[1] * self.cfg.speed_mult
        self.ghost_t = 0.0
        self.cam = [S.PLAYER_START[0] - S.SCREEN_W / 2, S.PLAYER_START[1] - S.SCREEN_H / 2]
        self.state = "play"

    def start(self):
        """A fresh run from Level 1."""
        self.begin_level(1)

    def restart_level(self):
        """Retry the current level with the loadout the hero walked in with."""
        self.begin_level(self.level_no, self.level_carry)

    def next_level(self):
        self.begin_level(self.level_no + 1, self.player.snapshot())

    @property
    def final_level(self):
        return self.level_no >= S.NUM_LEVELS

    def show_banner(self, text):
        self.banner_text = text
        self.banner_t = 2.8

    # ------------------------------------------------------------------ input
    def handle_key(self, key):
        """Menu/keyboard events. Returns 'quit' to leave the game."""
        st = self.state
        K = pygame
        if key == K.K_m:
            self.assets.toggle_music()
            return None
        if st == "title":
            if key in (K.K_RETURN, K.K_KP_ENTER, K.K_SPACE):
                self.start()
            elif key == K.K_l:
                strings.toggle()
            elif key == K.K_F2:                      # jump to Level 2 with a sample loadout
                self.begin_level(2, dict(S.DEMO_CARRY))
            elif key == K.K_F3:                      # ... or to Level 3 with a late-game one
                self.begin_level(3, dict(S.DEMO_CARRY_LATE))
            elif key == K.K_ESCAPE:
                return "quit"
        elif st == "play":
            if key in (K.K_ESCAPE, K.K_p):
                self.state = "pause"
                pygame.mixer.music.pause() if self.assets.audio_ok else None
            elif key in (K.K_LSHIFT, K.K_RSHIFT, K.K_SPACE):
                self.try_dash(self._last_move)
        elif st == "pause":
            if key in (K.K_ESCAPE, K.K_p):
                self.state = "play"
                pygame.mixer.music.unpause() if self.assets.audio_ok else None
            elif key == K.K_r:
                self.restart_level()
            elif key == K.K_q:
                return "quit"
        elif st == "upgrade":
            n = max(1, len(self.upgrade_choices))
            if key in (K.K_1, K.K_2, K.K_3):
                self.pick_upgrade(key - K.K_1)
            elif key in (K.K_LEFT, K.K_a):
                self.upgrade_sel = (self.upgrade_sel - 1) % n
            elif key in (K.K_RIGHT, K.K_d):
                self.upgrade_sel = (self.upgrade_sel + 1) % n
            elif key in (K.K_RETURN, K.K_KP_ENTER, K.K_SPACE):
                self.pick_upgrade(self.upgrade_sel)
        elif st in ("over", "win"):
            if key in (K.K_RETURN, K.K_KP_ENTER):
                if st == "over":
                    self.restart_level()
                elif self.final_level:
                    self.start()
                else:
                    self.next_level()
            elif key == K.K_ESCAPE:
                return "quit"
        return None

    def handle_mouse(self, pos, click):
        if self.state != "upgrade":
            return
        for i, r in enumerate(self.ui.upgrade_rects(len(self.upgrade_choices))):
            if r.collidepoint(pos):
                self.upgrade_sel = i
                if click:
                    self.pick_upgrade(i)

    _last_move = (0.0, 0.0)

    # ------------------------------------------------------------------ simulation
    def update(self, dt, move):
        """Advance the game by dt seconds. `move` is the (x, y) movement input."""
        dt = min(dt, 1 / 30)
        self.clock += dt
        self._last_move = move
        self.red_flash = max(0.0, self.red_flash - dt)
        if self.state == "title":
            self.fx.update(dt)
            return
        if self.state in ("pause", "upgrade"):
            return
        if self.state == "dying":
            self.dying_t -= dt
            self.fx.update(dt)
            self.shake = max(0.0, self.shake - dt * 2)
            if self.dying_t <= 0:
                self.state = "over"
                self.over = True
                self.assets.play("over")
            return
        if self.state in ("over", "win"):
            self.fx.update(dt)
            return

        p = self.player
        self.time += dt
        self.banner_t = max(0.0, self.banner_t - dt)
        self.bar_pulse = max(0.0, self.bar_pulse - dt)
        self.box_pulse = max(0.0, self.box_pulse - dt)
        self.shake = max(0.0, self.shake - dt * 2.4)
        self.pride_shown += (self.pride - self.pride_shown) * min(1.0, dt * 6)

        target = self.nearest_enemy(p.x, p.y, S.SHOT_RANGE)
        p.update(dt, move, self.level, target)
        if p.dashing:
            self.ghost_t -= dt
            if self.ghost_t <= 0:
                self.ghost_t = 0.03
                self.fx.afterimage(p.x, p.y, self.assets.rotated("hero", p.facing))
            self.dash_hits()
        for w in list(p.weapons.values()):
            w.update(self, dt)
        W.update_waves(self, dt)
        W.update_mines(self, dt)
        W.update_chakrams(self, dt)
        W.update_bolts(self, dt)
        self.update_hazards(dt)
        self.enemies = [e for e in self.enemies if e.hp > 0]

        self.update_director(dt)
        for e in self.enemies:
            e.update(dt, p, self.level, self)
        self.grid = self.build_grid()
        self.separate_enemies(dt)
        self.update_shots(dt)
        self.update_spears(dt)
        self.contact_damage()
        self.update_pickups(dt)
        self.update_boxes(dt)
        self.fx.update(dt)
        self.check_progress()
        self.update_camera(dt)

        if self.exit_open and p.y < 8 and S.GATE_X0 < p.x < S.GATE_X1:
            self.state = "win"
            self.over = True
            self.assets.play("win")
            self.fx.diamonds(p.x, p.y, 40, 500, 1.4)
            self.fx.ring(p.x, p.y, (255, 232, 150), 300, 0.9, 6)

    # ---- combat -------------------------------------------------------------
    def nearest_enemy(self, x, y, max_d):
        best, bd = None, max_d * max_d
        for e in self.enemies:
            if e.spawn_t > 0 or e.hp <= 0:
                continue
            d = (e.x - x) ** 2 + (e.y - y) ** 2
            if d < bd:
                best, bd = e, d
        return best

    def enemies_near(self, x, y, r):
        """Live guardians whose body overlaps the circle (x, y, r), via the spatial grid."""
        reach = r + 42
        out = []
        for gx in range(int((x - reach) // 80), int((x + reach) // 80) + 1):
            for gy in range(int((y - reach) // 80), int((y + reach) // 80) + 1):
                for e in self.grid.get((gx, gy), ()):
                    if e.hp > 0 and (e.x - x) ** 2 + (e.y - y) ** 2 < (r + e.r) ** 2:
                        out.append(e)
        return out

    def try_dash(self, move):
        p = self.player
        if p.try_dash(*move):
            self.assets.play("dash")
            self.fx.ring(p.x, p.y, (90, 240, 225), 70, 0.25, 3)

    def build_grid(self):
        grid = {}
        for e in self.enemies:
            grid.setdefault((int(e.x // 80), int(e.y // 80)), []).append(e)
        return grid

    def update_shots(self, dt):
        grid = self.grid
        keep = []
        for s in self.shots:
            s.life -= dt
            if s.kind == "seeker":
                W.steer_seeker(self, s, dt)
            s.x += s.vx * dt
            s.y += s.vy * dt
            dead = s.life <= 0
            if not dead and self.level.shot_blocked(s.x, s.y):
                dead = True
                self.fx.burst(s.x, s.y, (90, 240, 225), 4, 120, 0.25, 5)
            if not dead:
                cx, cy = int(s.x // 80), int(s.y // 80)
                for gx in (cx - 1, cx, cx + 1):
                    for gy in (cy - 1, cy, cy + 1):
                        for e in grid.get((gx, gy), ()):
                            if e.id in s.hit or e.hp <= 0 or e.spawn_t > 0.2:
                                continue
                            if (e.x - s.x) ** 2 + (e.y - s.y) ** 2 < (e.r + s.r) ** 2:
                                s.hit.add(e.id)
                                self.damage_enemy(e, s.dmg, s.vx, s.vy)
                                s.pierce -= 1
                                if s.pierce < 0:
                                    dead = True
                                break
                        if dead:
                            break
                    if dead:
                        break
            if not dead:
                keep.append(s)
        self.shots = keep
        self.enemies = [e for e in self.enemies if e.hp > 0]

    def damage_enemy(self, e, dmg, dx, dy, force=220.0):
        if e.hp <= 0:
            return
        e.hit(dmg, dx, dy, force)
        self.fx.burst(e.x, e.y, (230, 255, 252), 5, 200, 0.25, 6)
        self.assets.play("hit", 0.04)
        if e.hp <= 0:
            self.kill_enemy(e)

    def kill_enemy(self, e, award=True):
        big = e.kind in ("elite", "bulwark")
        self.fx.diamonds(e.x, e.y, 14 if e.kind == "elite" else 7, 320)
        self.fx.burst(e.x, e.y, (255, 240, 190), 12 if big else 7, 260, 0.5, 9)
        self.fx.ring(e.x, e.y, (255, 236, 170), 150 if e.kind == "elite" else 70, 0.35, 3)
        if award:
            self.kills += 1
            self.assets.play("kill", 0.04)
            if not self.exit_open and e.pts:    # the bar is full: guardians stay, but are worth nothing
                self.fx.text(e.x, e.y - 20, f"+{e.pts}", (255, 232, 150), 34 if e.kind == "elite" else 22)
                self.add_pride(e.pts)
            if e.kind == "boss":
                self.fx.diamonds(e.x, e.y, 40, 600, 1.4)
                self.fx.ring(e.x, e.y, e.spec["color"], 420, 0.9, 12)
                self.shake = max(self.shake, 1.0)
                self.assets.play("slam")
                for dx, dy in ((-60, 0), (60, 0)):
                    self.pickups.append(HeartPickup(e.x + dx, e.y + dy, respawns=False))
                self.spears.clear()
            if e.kind == "elite":
                self.pickups.append(HeartPickup(e.x, e.y, respawns=False))
                self.shake = max(self.shake, 0.6)
                self.assets.play("slam")
        e.hp = 0
        if e.kind == "boss" and self.hold_exit:
            self.try_open_exit()

    def dash_hits(self):
        p = self.player
        for e in self.enemies:
            if e.hp > 0 and e.id not in p.dash_hit and (e.x - p.x) ** 2 + (e.y - p.y) ** 2 < (e.r + 34) ** 2:
                p.dash_hit.add(e.id)
                self.damage_enemy(e, S.DASH_DAMAGE * p.dmg_mult, p.dash_dx, p.dash_dy)
                self.fx.ring(e.x, e.y, (90, 240, 225), 60, 0.2, 3)
        self.enemies = [e for e in self.enemies if e.hp > 0]

    def bomber_explode(self, e):
        """A bomber's fuse ran out: blast radius BOMBER_BLAST, hurts the hero if still inside it."""
        p = self.player
        self.fx.burst(e.x, e.y, (255, 150, 60), 26, 460, 0.55, 12)
        self.fx.burst(e.x, e.y, (255, 240, 170), 10, 300, 0.4, 9)
        self.fx.ring(e.x, e.y, (255, 120, 60), S.BOMBER_BLAST, 0.35, 8)
        self.assets.play("mine", 0.05)
        self.shake = max(self.shake, 0.35)
        if p.invuln <= 0 and math.hypot(p.x - e.x, p.y - e.y) < S.BOMBER_BLAST + p.r * 0.5:
            self.hurt_player(p.x - e.x, p.y - e.y)
        e.hp = 0

    def spawn_hazard(self, x, y, r, dur, style):
        x = min(S.ARENA - 40, max(40, x))
        y = min(S.ARENA - 40, max(40, y))
        self.hazards.append(Hazard(x, y, r, dur, style))

    def update_hazards(self, dt):
        p = self.player
        keep = []
        for h in self.hazards:
            h.t += dt
            if h.t < h.dur:
                keep.append(h)
                continue
            col = HAZARD_COLORS[h.style]                # the blast, themed by the sin
            self.fx.ring(h.x, h.y, col, h.r * 1.2, 0.4, 9)
            if h.style == "light":
                self.fx.diamonds(h.x, h.y, 10, 380, 0.7)
                self.fx.burst(h.x, h.y, (255, 245, 200), 14, 360, 0.5, 10)
            elif h.style == "gold":
                self.fx.diamonds(h.x, h.y, 14, 420, 0.8)
                self.fx.burst(h.x, h.y, (255, 200, 40), 18, 340, 0.55, 10)
            else:
                self.fx.burst(h.x, h.y, (255, 90, 160), 20, 340, 0.6, 11)
                self.fx.burst(h.x, h.y, (255, 200, 225), 8, 240, 0.5, 8)
            self.assets.play("mine", 0.05)
            self.shake = max(self.shake, 0.15)
            if p.invuln <= 0 and math.hypot(p.x - h.x, p.y - h.y) < h.r + p.r * 0.4:
                self.hurt_player(p.x - h.x, p.y - h.y)
        self.hazards = keep

    def spawn_spear(self, x, y, ux, uy, homing=False):
        self.spears.append(Spear(x, y, ux, uy, homing))
        self.assets.play("seeker" if homing else "spear", 0.08)

    def charm_pull(self, e, dt):
        """A charmer's spell: the hero is dragged towards her unless dashing."""
        p = self.player
        if p.dashing:
            e.charm_t = 0.0
            return
        dx, dy = e.x - p.x, e.y - p.y
        d = math.hypot(dx, dy)
        if d > 80:
            p.x += dx / d * S.CHARM_PULL * dt
            p.y += dy / d * S.CHARM_PULL * dt
            p.x, p.y, _ = self.level.collide(p.x, p.y, p.r)

    def update_spears(self, dt):
        p = self.player
        keep = []
        for sp in self.spears:
            sp.life -= dt
            if sp.homing:                              # a cupid's heart bends towards the hero
                want = math.atan2(p.y - sp.y, p.x - sp.x)
                cur = math.atan2(sp.vy, sp.vx)
                d = (want - cur + math.pi) % math.tau - math.pi
                cur += max(-S.HEART_TURN * dt, min(S.HEART_TURN * dt, d))
                sp.vx, sp.vy = math.cos(cur) * S.HEART_SPEED, math.sin(cur) * S.HEART_SPEED
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            if sp.life <= 0 or self.level.shot_blocked(sp.x, sp.y):
                continue
            if (sp.x - p.x) ** 2 + (sp.y - p.y) ** 2 < (p.r + 10) ** 2 and p.invuln <= 0:
                self.hurt_player(sp.vx, sp.vy)
                continue
            keep.append(sp)
        self.spears = keep

    def contact_damage(self):
        p = self.player
        if p.invuln > 0:
            return
        for e in self.enemies:
            if e.spawn_t > 0:
                continue
            reach = e.r + p.r - 4
            if (e.x - p.x) ** 2 + (e.y - p.y) ** 2 < reach * reach:
                self.hurt_player(p.x - e.x, p.y - e.y)
                return

    def hurt_player(self, dx, dy):
        p = self.player
        p.hurt()
        n = math.hypot(dx, dy) or 1.0
        p.vx, p.vy = dx / n * 520, dy / n * 520
        self.shake = max(self.shake, 0.5)
        self.red_flash = 0.3
        self.fx.burst(p.x, p.y, (255, 90, 110), 12, 300, 0.5, 8)
        self.assets.play("hurt")
        if p.hp <= 0:
            self.state = "dying"
            self.dying_t = 1.1
            self.fx.diamonds(p.x, p.y, 24, 420, 1.0)
            self.fx.ring(p.x, p.y, (255, 120, 140), 200, 0.8, 5)
            self.enemies.clear()
            self.spears.clear()
            self.shots.clear()
            self.hazards.clear()
            self.mines.clear()
            self.chakrams.clear()
            self.bolts.clear()
            self.waves.clear()

    def separate_enemies(self, dt):
        grid = self.grid
        p = self.player
        for e in self.enemies:
            cx, cy = int(e.x // 80), int(e.y // 80)
            for gx in (cx - 1, cx, cx + 1):
                for gy in (cy - 1, cy, cy + 1):
                    for o in grid.get((gx, gy), ()):
                        if o.id <= e.id:
                            continue
                        dx, dy = o.x - e.x, o.y - e.y
                        d2 = dx * dx + dy * dy
                        rr = (e.r + o.r) * 0.85
                        if 1e-6 < d2 < rr * rr:
                            d = math.sqrt(d2)
                            push = (rr - d) * 0.5
                            ux, uy = dx / d, dy / d
                            if e.kind not in ("elite", "boss"):
                                e.x -= ux * push
                                e.y -= uy * push
                            if o.kind not in ("elite", "boss"):
                                o.x += ux * push
                                o.y += uy * push
            dx, dy = e.x - p.x, e.y - p.y
            d2 = dx * dx + dy * dy
            rr = (e.r + p.r) * 0.55
            if 1e-6 < d2 < rr * rr:
                d = math.sqrt(d2)
                e.x += dx / d * (rr - d)
                e.y += dy / d * (rr - d)

    # ---- progression: Pride bar -> waves -> weapons -------------------------------------
    def add_pride(self, pts):
        if self.exit_open:
            return
        cfg = self.cfg
        self.pride = min(cfg.pride_max, self.pride + pts)
        self.bar_pulse = 0.25
        new_stage = 1 + sum(1 for m in cfg.stage_at_pts if self.pride >= m)
        while self.stage < new_stage:
            self.stage += 1
            self.enemy_speed_mult = cfg.stage_speed[self.stage] * cfg.speed_mult
            self.pending_elites += cfg.elites.get(self.stage, 0)
            self.queue.append("weapon")               # every wave unlocks a weapon (a free upgrade once all are owned)
            if self.stage == cfg.num_stages and cfg.boss:
                self.boss_due = True                  # the final wave brings the level boss
            self.show_banner(t("stage").format(n=self.stage) + ": " + tl("stage_desc", self.level_no)[self.stage])
        if self.pride >= cfg.pride_max:
            self.try_open_exit()

    def boss_alive(self):
        return any(e.kind == "boss" and e.hp > 0 for e in self.enemies)

    def try_open_exit(self):
        """The gate opens when the bar is full AND the boss (if the level has one) is dead."""
        if self.exit_open:
            return
        if self.boss_due or self.boss_alive():
            self.hold_exit = True
            return
        self.hold_exit = False
        self.open_exit()

    def open_exit(self):
        """The bar is full: the gate opens. The guardians that are out there stay."""
        self.exit_open = True
        self.level.gate_open = True
        self.assets.play("gate")
        self.shake = max(self.shake, 0.7)

    def bar_frac(self, pts):
        """Fill of the HUD bar: every wave gets an equal slice, whatever its point cost."""
        edges, n = self.cfg.bar_edges, self.cfg.num_stages
        for i in range(n):
            if pts <= edges[i + 1]:
                return (i + (pts - edges[i]) / (edges[i + 1] - edges[i])) / n
        return 1.0

    # ---- progression: box points -> stat upgrades ----------------------------------------
    def add_box_points(self, v):
        self.box_pts += v
        self.box_total += v
        self.box_pulse = 0.25
        while self.box_pts >= S.upgrade_cost(self.box_upgrades):
            self.box_pts -= S.upgrade_cost(self.box_upgrades)
            self.box_upgrades += 1
            self.queue.append("stat")

    def check_progress(self):
        if self.state == "play" and self.queue:
            self.open_menu(self.queue.pop(0))

    def open_menu(self, kind):
        p = self.player
        if kind == "weapon":
            pool = [w for w in W.UNLOCKABLE if w not in p.weapons]
        else:
            has_area = any(w in p.weapons for w in AREA_WEAPONS)
            pool = [u for u in UPGRADE_IDS
                    if not (u == "multi" and p.bonus >= S.STAT_BONUS_CAP)
                    and not (u == "rate" and p.rate_mult <= S.STAT_RATE_FLOOR + 1e-6)
                    and not (u == "pierce" and p.pierce_bonus >= S.STAT_PIERCE_CAP)
                    and not (u == "area" and not has_area)
                    and not (u == "dash" and p.charge_cap >= S.DASH_CHARGES_CAP)
                    and not (u == "heart" and p.max_hp >= S.PLAYER_HP_CAP)]
        if not pool and kind == "weapon":                 # every weapon owned: the wave gives a free upgrade instead
            return self.open_menu("stat")
        if not pool:
            return
        self.choice_kind = kind
        self.upgrade_choices = random.sample(pool, min(3, len(pool)))
        self.upgrade_sel = 0
        self.state = "upgrade"
        self.assets.play("upgrade_open")

    def pick_upgrade(self, idx):
        if idx >= len(self.upgrade_choices):
            return
        uid = self.upgrade_choices[idx]
        p = self.player
        if self.choice_kind == "weapon":
            p.weapons[uid] = W.WEAPONS[uid]()
            self.assets.play("weapon")
            self.show_banner(t("weapon_new") + ": " + t("weapons")[uid][0])
        else:
            if uid == "multi":
                p.bonus = min(S.STAT_BONUS_CAP, p.bonus + 1)
            elif uid == "rate":
                p.rate_mult = max(S.STAT_RATE_FLOOR, p.rate_mult * S.STAT_RATE_STEP)
            elif uid == "pierce":
                p.pierce_bonus = min(S.STAT_PIERCE_CAP, p.pierce_bonus + 1)
            elif uid == "power":
                p.dmg_mult += S.STAT_DAMAGE_STEP
            elif uid == "area":
                p.area += S.STAT_AREA_STEP
            elif uid == "dash":
                p.charge_cap = min(S.DASH_CHARGES_CAP, p.charge_cap + 1)
                p.charges = min(p.charge_cap, p.charges + 1)
                p.recharge *= 0.9
            elif uid == "speed":
                p.speed *= 1.10
            elif uid == "heart":
                p.max_hp = min(S.PLAYER_HP_CAP, p.max_hp + 1)
                p.hp = min(p.max_hp, p.hp + 1)
            self.assets.play("upgrade_pick")
        self.state = "play"
        self.fx.ring(p.x, p.y, (255, 232, 150), 160, 0.5, 4)
        self.fx.diamonds(p.x, p.y, 12, 260)

    def update_pickups(self, dt):
        p = self.player
        keep = []
        for h in self.pickups:
            if not h.alive:
                h.timer -= dt
                if h.respawns and h.timer <= 0:
                    h.alive = True
                if h.respawns or h.alive:
                    keep.append(h)
                continue
            if p.hp < p.max_hp and (h.x - p.x) ** 2 + (h.y - p.y) ** 2 < (p.r + 26) ** 2:
                p.hp += 1
                h.alive = False
                h.timer = S.HEART_RESPAWN
                self.assets.play("heart")
                self.fx.burst(h.x, h.y, (255, 110, 130), 12, 260, 0.5, 8)
                self.fx.text(h.x, h.y - 26, "+1", (255, 130, 150), 26)
                if not h.respawns:
                    continue
            keep.append(h)
        self.pickups = keep

    # ---- boxes and gems -------------------------------------------------------------------
    def box_spot(self, min_player_dist=0.0):
        p = self.player
        for _ in range(40):
            x, y = random.uniform(140, S.ARENA - 140), random.uniform(140, S.ARENA - 140)
            if not self.level.is_free(x, y, 34):
                continue
            if min_player_dist and (x - p.x) ** 2 + (y - p.y) ** 2 < min_player_dist ** 2:
                continue
            if any((b.x - x) ** 2 + (b.y - y) ** 2 < 85 ** 2 for b in self.boxes):
                continue
            return x, y
        return None

    def add_box(self, x, y):
        self.boxes.append(Box(x, y, random.random() < S.BOX_GILDED_CHANCE))

    def populate_boxes(self):
        sx, sy = S.PLAYER_START
        for i in range(4):                      # a few right by the start so the idea is obvious
            for _ in range(20):
                a = -math.pi / 2 + (i - 1.5) * 0.7
                d = random.uniform(230, 330)
                x, y = sx + math.cos(a) * d, sy + math.sin(a) * d
                if self.level.is_free(x, y, 34) and not any((b.x - x) ** 2 + (b.y - y) ** 2 < 85 ** 2 for b in self.boxes):
                    self.boxes.append(Box(x, y, False))
                    break
        tries = 0
        while len(self.boxes) < S.BOX_START and tries < 400:      # clusters of 3-6 across the map
            tries += 1
            c = self.box_spot()
            if c is None:
                continue
            for _ in range(random.randint(3, 6)):
                for _ in range(10):
                    a, d = random.uniform(0, math.tau), random.uniform(60, 190)
                    x, y = c[0] + math.cos(a) * d, c[1] + math.sin(a) * d
                    if self.level.is_free(x, y, 34) and not any((b.x - x) ** 2 + (b.y - y) ** 2 < 85 ** 2 for b in self.boxes):
                        self.add_box(x, y)
                        break

    def break_box(self, b):
        vals = S.BOX_GILDED_GEMS if b.gilded else S.BOX_CRATE_GEMS
        for v in vals:
            self.gems.append(Gem(b.x, b.y, v))
        col = (255, 220, 120) if b.gilded else (200, 192, 232)
        self.fx.burst(b.x, b.y, col, 14, 300, 0.55, 9)
        self.fx.burst(b.x, b.y, self.theme["gem"], 6, 220, 0.4, 7)
        self.fx.ring(b.x, b.y, (200, 255, 240), 80, 0.3, 3)
        self.fx.text(b.x, b.y - 24, f"+{sum(vals)}", self.theme["gem"], 20)
        self.assets.play("box", 0.03)
        self.shake = max(self.shake, 0.06)

    def update_boxes(self, dt):
        p = self.player
        reach = Box.r + p.r
        alive = []
        for b in self.boxes:
            if (b.x - p.x) ** 2 + (b.y - p.y) ** 2 < reach * reach:
                self.break_box(b)
            else:
                alive.append(b)
        self.boxes = alive
        # restock, always out of view
        self.box_timer -= dt
        if self.box_timer <= 0:
            self.box_timer = S.BOX_RESPAWN
            if len(self.boxes) < S.BOX_TARGET:
                spot = self.box_spot(S.BOX_RESPAWN_MIN_DIST)
                if spot:
                    self.add_box(*spot)
        # gems: scatter, then fly to the hero
        keep = []
        for gm in self.gems:
            gm.age += dt
            gm.life -= dt
            if gm.life <= 0:
                continue
            dx, dy = p.x - gm.x, p.y - gm.y
            d = math.hypot(dx, dy) or 1.0
            if gm.age > 0.3 and d < S.GEM_MAGNET:
                spd = 420 + (1 - d / S.GEM_MAGNET) * (S.GEM_SPEED - 420)
                k = min(1.0, 12 * dt)
                gm.vx += (dx / d * spd - gm.vx) * k
                gm.vy += (dy / d * spd - gm.vy) * k
            else:
                f = max(0.0, 1.0 - 5.0 * dt)
                gm.vx *= f
                gm.vy *= f
            gm.x += gm.vx * dt
            gm.y += gm.vy * dt
            gm.x = min(S.ARENA - 20, max(20, gm.x))
            gm.y = min(S.ARENA - 20, max(20, gm.y))
            if d < p.r + 16 and gm.age > 0.15:
                self.add_box_points(gm.val)
                self.gem_acc += gm.val
                self.gem_acc_t = 0.35
                self.assets.play("gem", 0.05)
                self.fx.burst(p.x, p.y, self.theme["gem"], 3, 140, 0.25, 4)
                continue
            keep.append(gm)
        self.gems = keep[-400:]
        if self.gem_acc:
            self.gem_acc_t -= dt
            if self.gem_acc_t <= 0:
                self.fx.text(p.x, p.y - 38, f"+{self.gem_acc}", self.theme["gem"], 20)
                self.gem_acc = 0

    # ---- spawning ------------------------------------------------------------------
    def spawn_center(self, ang=None):
        """A point on a ring just outside the screen, in a free spot of the arena."""
        p = self.player
        for _ in range(14):
            a = ang if ang is not None else random.uniform(0, math.tau)
            d = random.uniform(*S.SPAWN_DIST)
            x = min(S.ARENA - 40, max(40, p.x + math.cos(a) * d))
            y = min(S.ARENA - 40, max(40, p.y + math.sin(a) * d))
            if math.hypot(x - p.x, y - p.y) >= S.MIN_SPAWN_DISTANCE and self.level.is_free(x, y, 30):
                return x, y
            ang = None
        pts = [pt for pt in S.SPAWN_POINTS if math.hypot(pt[0] - p.x, pt[1] - p.y) > S.MIN_SPAWN_DISTANCE]
        return random.choice(pts or S.SPAWN_POINTS)

    def spawn_enemy(self, kind, x, y):
        scale = self.cfg.stage_hp[self.stage] * self.cfg.hp_mult
        if kind == "elite":
            scale = (1.0 + 0.15 * max(0, self.stage - 4)) * self.cfg.elite_hp_mult
        x, y, _ = self.level.collide(x, y, S.ENEMIES[kind]["r"], through_gate=False)
        self.enemies.append(Enemy(kind, x, y, scale))

    def recycle_far(self):
        """Guardians left far behind jump back to the edge of the action so the alive cap is not wasted."""
        p = self.player
        lim = S.RECYCLE_DISTANCE ** 2
        for e in self.enemies:
            if (e.x - p.x) ** 2 + (e.y - p.y) ** 2 > lim and e.charge_t <= 0 and e.kind != "boss":
                e.x, e.y = self.spawn_center()
                e.spawn_t = 0.35

    def update_director(self, dt):
        if self.exit_open and not S.SPAWN_AFTER_EXIT:
            return
        st = self.cfg.stages[self.stage]
        self.recycle_t -= dt
        if self.recycle_t <= 0:
            self.recycle_t = 0.5
            self.recycle_far()
        if self.pending_elites > 0:                       # elites arrive one at a time when a wave begins
            self.elite_t -= dt
            if self.elite_t <= 0:
                self.pending_elites -= 1
                self.elite_t = 2.0
                self.elites += 1
                x, y = self.spawn_center()
                self.spawn_enemy("elite", x, y)
                self.assets.play("elite")
                self.fx.ring(x, y, (255, 220, 120), 220, 0.8, 6)
        if self.boss_due:                                   # the level boss arrives with the final wave
            self.boss_due = False
            x, y = self.spawn_center()
            self.enemies.append(Boss(x, y, self.cfg.boss))
            self.assets.play("elite")
            self.fx.ring(x, y, self.cfg.boss["color"], 320, 1.0, 10)
            self.shake = max(self.shake, 0.6)
            self.show_banner(t("boss_banner") + ": " + tl("boss_name", self.level_no))
        self.spawn_t -= dt
        if self.spawn_t > 0:
            return
        self.spawn_t = st["interval"] * random.uniform(0.85, 1.15)
        cap = min(st["cap"], S.MAX_ENEMIES) * (S.BOSS_CAP_FACTOR if self.boss_alive() else 1.0)
        room = int(cap) - len(self.enemies)
        if room <= 0:
            return
        if random.random() < st["swarm"]:                  # a pack of fast swarmers
            n = min(room, random.randint(*self.cfg.swarm_pack))
            kinds = ["swarmer"] * n
            spread = 95
        else:
            n = min(room, random.randint(*st["group"]))
            ks, ws = zip(*st["weights"].items())
            kinds = random.choices(ks, ws, k=n)
            lancers = sum(1 for e in self.enemies if e.kind in S.RANGED_KINDS)
            charmers = sum(1 for e in self.enemies if e.kind == "charmer")
            for i, k in enumerate(kinds):                  # never a storm of spears: extras become sentinels
                if k in S.RANGED_KINDS:
                    if lancers >= self.cfg.lancer_cap:
                        kinds[i] = "sentinel"
                    else:
                        lancers += 1
                elif k == "charmer":
                    if charmers >= S.CHARMER_CAP:
                        kinds[i] = "skirmisher"
                    else:
                        charmers += 1
            spread = 70
        centers = [self.spawn_center()]
        if st["pincer"] and n >= 4:                         # half the group comes from the opposite side
            p = self.player
            a = math.atan2(centers[0][1] - p.y, centers[0][0] - p.x) + math.pi + random.uniform(-0.5, 0.5)
            centers.append(self.spawn_center(a))
        for i, kind in enumerate(kinds):
            cx, cy = centers[i % len(centers)]
            ang = random.uniform(0, math.tau)
            rad = random.uniform(0, spread)
            self.spawn_enemy(kind, min(S.ARENA - 30, max(30, cx + math.cos(ang) * rad)),
                             min(S.ARENA - 30, max(30, cy + math.sin(ang) * rad)))

    def update_camera(self, dt):
        p = self.player
        tx = p.x + p.vx * 0.12 - S.SCREEN_W / 2
        ty = p.y + p.vy * 0.12 - S.SCREEN_H / 2
        tx = max(-S.WALL, min(S.ARENA + S.WALL - S.SCREEN_W, tx))
        ty = max(-S.WALL, min(S.ARENA + S.WALL - S.SCREEN_H, ty))
        k = 1 - math.exp(-9 * dt)
        self.cam[0] += (tx - self.cam[0]) * k
        self.cam[1] += (ty - self.cam[1]) * k

    # ------------------------------------------------------------------ drawing
    def shadow(self, w):
        w = int(w)
        s = self._shadow.get(w)
        if s is None:
            s = pygame.Surface((w, int(w * 0.55)), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 8, 90), s.get_rect())
            pygame.draw.ellipse(s, (0, 0, 8, 70), s.get_rect().inflate(-w * 0.3, -w * 0.18))
            self._shadow[w] = s
        return s

    def view_cam(self):
        if self.shake > 0:
            a = 10 * min(1.0, self.shake)
            return (self.cam[0] + random.uniform(-a, a), self.cam[1] + random.uniform(-a, a))
        return (self.cam[0], self.cam[1])

    def on_screen(self, x, y, pad, cam):
        return -pad < x - cam[0] < S.SCREEN_W + pad and -pad < y - cam[1] < S.SCREEN_H + pad

    def draw(self, screen):
        a = self.assets
        cam = self.view_cam()
        W_, H = S.SCREEN_W, S.SCREEN_H
        t_now = self.clock
        lvl = self.level
        lvl.draw_floor(screen, cam)
        lvl.draw_gate(screen, cam)

        # heart pickups
        for h in self.pickups:
            if h.alive:
                sx, sy = h.x - cam[0], h.y - cam[1] + math.sin(t_now * 3 + h.x) * 4
                img = a.img["heart_full"]
                screen.blit(self.shadow(40), self.shadow(40).get_rect(center=(sx, sy + 16)))
                screen.blit(img, img.get_rect(center=(sx, sy)))

        # boxes, mines and gems lie on the floor, under the characters
        for b in self.boxes:
            if self.on_screen(b.x, b.y, 60, cam):
                img = a.img["box_gilded" if b.gilded else "box_crate"]
                sx, sy = b.x - cam[0], b.y - cam[1]
                screen.blit(self.shadow(54), self.shadow(54).get_rect(center=(sx, sy + 18)))
                screen.blit(img, img.get_rect(center=(sx, sy)))
                if b.gilded:
                    g = a.glow(34 + 5 * math.sin(t_now * 4 + b.t), (60, 46, 14))
                    screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)
        for m in self.mines:
            if self.on_screen(m.x, m.y, 60, cam):
                sx, sy = m.x - cam[0], m.y - cam[1]
                screen.blit(a.img["mine"], a.img["mine"].get_rect(center=(sx, sy)))
                armed = m.age > 0.6
                pulse = 0.5 + 0.5 * math.sin(t_now * (9 if armed else 20))
                g = a.glow(20 + 6 * pulse, (150, 90, 20) if armed else (80, 80, 80))
                screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)
        for h in self.hazards:
            if self.on_screen(h.x, h.y, h.r + 20, cam):
                k, r, col = h.t / h.dur, int(h.r), HAZARD_COLORS[h.style]
                tmp = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(tmp, (*col, int(30 + 60 * k)), (r, r), r)
                pygame.draw.circle(tmp, (*col, int(60 + 80 * k)), (r, r), max(2, int(r * k)))
                pygame.draw.circle(tmp, (*col, 230), (r, r), r, 4)
                screen.blit(tmp, (h.x - cam[0] - r, h.y - cam[1] - r))
        for gm in self.gems:
            if self.on_screen(gm.x, gm.y, 40, cam):
                sx, sy = gm.x - cam[0], gm.y - cam[1] + math.sin(t_now * 5 + gm.t) * 3
                img = a.img["gem"]
                if gm.life < 5 and int(t_now * 10) % 2 == 0:
                    continue
                screen.blit(img, img.get_rect(center=(sx, sy)))
                g = a.glow(18, (20, 90, 80))
                screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)

        p = self.player
        # ferryman at the altar
        fx_, fy_ = S.ALTAR_POS[0] - 70, S.ALTAR_POS[1] + 12
        drawables = [(fy_, "ferry", None)]
        for e in self.enemies:
            drawables.append((e.y, "enemy", e))
        if self.state not in ("over", "dying"):
            drawables.append((p.y, "player", p))
        drawables.sort(key=lambda d: d[0])
        for _, kind, obj in drawables:
            if kind == "ferry":
                sx, sy = fx_ - cam[0], fy_ - cam[1]
                if -100 < sx < W_ + 100 and -100 < sy < H + 100:
                    ang = math.atan2(p.x - fx_, -(p.y - fy_))
                    img = a.rotated("ferryman", ang * 0.4)
                    screen.blit(self.shadow(56), self.shadow(56).get_rect(center=(sx, sy + 20)))
                    screen.blit(img, img.get_rect(center=(sx, sy + math.sin(t_now * 1.6) * 2)))
            elif kind == "enemy":
                self.draw_enemy(screen, cam, obj, t_now)
            else:
                self.draw_player(screen, cam, obj, t_now)

        # weapons' own visuals, then projectiles
        if self.state not in ("over", "dying"):
            for w in p.weapons.values():
                w.draw(self, screen, cam, t_now)
        for c in self.chakrams:
            img = a.rotated("chakram", c.spin)
            screen.blit(img, img.get_rect(center=(c.x - cam[0], c.y - cam[1])))
        for s in self.shots:
            sx, sy = s.x - cam[0], s.y - cam[1]
            if s.kind == "seeker":
                img = a.img["seeker"]
            elif s.kind == "pellet":
                img = a.heading("pellet", s.vx, s.vy)
            else:
                img = a.heading("needle", s.vx, s.vy)
            screen.blit(img, img.get_rect(center=(sx, sy)))
        for sp in self.spears:
            if sp.homing:
                img = a.img["love_bolt"]
                k = 1.0 + 0.12 * math.sin(t_now * 12 + sp.x)
                img = pygame.transform.rotozoom(img, 0, k)
            else:
                img = a.heading("spear", sp.vx, sp.vy)
            screen.blit(img, img.get_rect(center=(sp.x - cam[0], sp.y - cam[1])))
        self.draw_telegraphs(screen, cam)
        self.fx.draw(screen, cam)

        # lighting
        lights = list(lvl.static_lights(t_now))
        lights.append((p.x, p.y, 430, (235, 230, 250)))
        for s in self.shots:
            col = {"seeker": (150, 90, 220), "pellet": (170, 140, 70)}.get(s.kind, (60, 220, 205))
            lights.append((s.x, s.y, 100, col))
        for sp in self.spears:
            lights.append((sp.x, sp.y, 130, (255, 110, 170) if sp.homing else (255, 226, 140)))
        for c in self.chakrams:
            lights.append((c.x, c.y, 120, (170, 180, 230)))
        for w in p.weapons.values():
            lights += w.lights(self)
        n = 0
        for gm in self.gems:
            if self.on_screen(gm.x, gm.y, 100, cam):
                lights.append((gm.x, gm.y, 70, (40, 170, 150)))
                n += 1
                if n > 14:
                    break
        for m in self.mines:
            lights.append((m.x, m.y, 90, (180, 100, 30)))
        n = 0
        for e in self.enemies:
            if -200 < e.x - cam[0] < W_ + 200 and -200 < e.y - cam[1] < H + 200:
                if e.kind == "boss":
                    lights.append((e.x, e.y, 330, tuple(int(c * 0.6) for c in e.spec["color"])))
                    continue
                lights.append((e.x, e.y, 84 if e.kind != "elite" else 190, (150, 140, 110)))
                n += 1
                if n > 45:
                    break
        lights.append((S.ALTAR_POS[0] - 70, S.ALTAR_POS[1] - 20, 120, (60, 235, 215)))
        self.light.render(screen, cam, lights)
        lvl.draw_flames(screen, cam, t_now)
        W.draw_bolts(self, screen, cam)
        # additive bloom on top of the lit scene
        for s in self.shots:
            col = {"seeker": (150, 90, 220), "pellet": (150, 120, 50)}.get(s.kind, (50, 200, 190))
            g = a.glow(30, col)
            screen.blit(g, g.get_rect(center=(s.x - cam[0], s.y - cam[1])), special_flags=pygame.BLEND_RGB_ADD)
        if lvl.gate_open:
            g = a.glow(220, (110, 90, 40))
            screen.blit(g, g.get_rect(center=((S.GATE_X0 + S.GATE_X1) / 2 - cam[0], 30 - cam[1])),
                        special_flags=pygame.BLEND_RGB_ADD)
        # vignette
        vg = a.img["vignette"]
        screen.blit(pygame.transform.smoothscale(vg, (W_, H)), (0, 0))

        if self.state == "title":
            self.ui.draw_title(screen, self)
            return
        self.ui.draw_hud(screen, self)
        if self.state == "pause":
            self.ui.draw_pause(screen, self)
        elif self.state == "upgrade":
            self.ui.draw_upgrade(screen, self)
        elif self.state == "over":
            self.ui.draw_end(screen, self, False)
        elif self.state == "win":
            self.ui.draw_end(screen, self, True)

    def draw_enemy(self, screen, cam, e, t_now):
        a = self.assets
        sx, sy = e.x - cam[0], e.y - cam[1]
        if sx < -340 or sx > S.SCREEN_W + 340 or sy < -340 or sy > S.SCREEN_H + 340:
            return
        screen.blit(self.shadow(e.shadow), self.shadow(e.shadow).get_rect(center=(sx, sy + e.r * 0.55)))
        img = a.rotated(e.sprite, e.face)
        enraged = e.kind == "bulwark" and e.hp < e.max_hp * S.BULWARK_ENRAGE
        fused = e.kind == "bomber" and e.windup > 0 and int(e.t * 16) % 2 == 0
        if e.flash > 0 or enraged or fused or (e.kind == "skirmisher" and e.charge_t > 0):
            img = img.copy()
            if e.flash > 0:
                img.fill((130, 130, 130), special_flags=pygame.BLEND_RGB_ADD)
            else:
                img.fill((90, 10, 10), special_flags=pygame.BLEND_RGB_ADD)
        if e.spawn_t > 0:
            k = 1 - e.spawn_t / 0.35
            img = pygame.transform.rotozoom(img, 0, 0.6 + 0.4 * k)
            img.set_alpha(int(255 * k))
        bob = math.sin(e.t * 3) * 2
        screen.blit(img, img.get_rect(center=(sx, sy + bob)))
        n = {"sentinel": 3, "skirmisher": 0, "lancer": 2, "elite": 5, "swarmer": 0, "bulwark": 4, "bomber": 0, "banker": 2, "charmer": 3, "cupid": 0, "boss": 7}[e.kind]
        rad = e.r + 18 + (6 if e.kind in ("elite", "boss") else 0)
        shard = a.img["shard"]
        for i in range(n):
            ang = e.t * 1.6 + i * math.tau / n
            screen.blit(shard, shard.get_rect(center=(sx + math.cos(ang) * rad, sy + math.sin(ang) * rad * 0.9 + bob)))
        if e.kind in ("elite", "bulwark") and e.hp < e.max_hp:
            w = 70 if e.kind == "elite" else 54
            pygame.draw.rect(screen, (20, 18, 34), (sx - w / 2, sy - e.r - 34, w, 7))
            pygame.draw.rect(screen, (244, 204, 96), (sx - w / 2, sy - e.r - 34, w * max(0.0, e.hp) / e.max_hp, 7))

    def draw_player(self, screen, cam, p, t_now):
        a = self.assets
        sx, sy = p.x - cam[0], p.y - cam[1]
        screen.blit(self.shadow(46), self.shadow(46).get_rect(center=(sx, sy + 16)))
        img = a.rotated("hero", p.facing)
        if p.invuln > 0 and not p.dashing and int(t_now * 18) % 2 == 0:
            img = img.copy()
            img.set_alpha(110)
        screen.blit(img, img.get_rect(center=(sx, sy)))
        g = a.glow(40, (10, 52, 50))
        screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)

    def draw_telegraphs(self, screen, cam):
        p = self.player
        for e in self.enemies:
            if e.kind == "charmer" and e.charm_t > 0:          # the spell: a pink thread from her to you
                a = self.assets
                x0, y0, x1, y1 = e.x - cam[0], e.y - cam[1], p.x - cam[0], p.y - cam[1]
                pygame.draw.line(screen, (255, 90, 170), (x0, y0), (x1, y1), 4)
                pygame.draw.line(screen, (255, 200, 225), (x0, y0), (x1, y1), 1)
                g = a.glow(46, (150, 30, 90))
                screen.blit(g, g.get_rect(center=(x1, y1)), special_flags=pygame.BLEND_RGB_ADD)
        for e in self.enemies:                                   # boss wind-ups, in the boss's own colour
            if e.kind != "boss" or not e.act:
                continue
            a = self.assets
            sx, sy = e.x - cam[0], e.y - cam[1]
            col, k = e.spec["color"], e.tele
            if e.act in ("fan", "charge"):
                if k < 1.0:
                    ln = 760 if e.act == "fan" else 600
                    pygame.draw.line(screen, col, (sx, sy), (sx + e.aim[0] * ln, sy + e.aim[1] * ln), 3 if e.act == "fan" else 6)
            else:
                g = a.glow(70 + 190 * k, tuple(int(c * 0.45) for c in col))
                screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(screen, col, (int(sx), int(sy)), int(e.r + 20 + 110 * k), 3)
        for e in self.enemies:
            if e.windup <= 0:
                continue
            sx, sy = e.x - cam[0], e.y - cam[1]
            if e.kind == "lancer":
                k = 1 - e.windup / S.SPEAR_WINDUP
                n = 3 if self.stage >= self.cfg.fan_stage else 1
                for i in range(n):
                    a = (i - (n - 1) / 2) * 0.27
                    c, s = math.cos(a), math.sin(a)
                    dx, dy = e.cdx * c - e.cdy * s, e.cdx * s + e.cdy * c
                    pygame.draw.line(screen, (255, int(200 + 40 * k), 120), (sx, sy), (sx + dx * 520, sy + dy * 520), 2)
            elif e.kind == "bomber":
                k = 1 - e.windup / S.BOMBER_FUSE
                r = int(S.BOMBER_BLAST)
                tmp = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(tmp, (255, 60, 40, int(40 + 90 * k)), (r, r), r)
                pygame.draw.circle(tmp, (255, 170, 90, 220), (r, r), r, 4)
                pygame.draw.circle(tmp, (255, 90, 50, int(60 + 120 * k)), (r, r), max(2, int(r * k)))
                screen.blit(tmp, (sx - r, sy - r))
            elif e.kind == "banker":
                pygame.draw.line(screen, (255, 230, 120), (sx, sy), (sx + e.cdx * 560, sy + e.cdy * 560), 2)
            elif e.kind == "cupid":
                pygame.draw.line(screen, (255, 140, 190), (sx, sy), (sx + e.cdx * 300, sy + e.cdy * 300), 2)
            elif e.kind == "charmer":
                k = 1 - e.windup / S.CHARM_WINDUP
                g = self.assets.glow(40 + 70 * k, (200, 40, 130))
                screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(screen, (255, 120, 190), (int(sx), int(sy)), int(30 + 40 * k), 2)
            elif e.kind == "skirmisher":
                pygame.draw.line(screen, (255, 130, 110), (sx, sy), (sx + e.cdx * 190, sy + e.cdy * 190), 3)
            elif e.kind == "elite":
                k = 1 - e.windup / S.ELITE_WINDUP
                g = self.assets.glow(40 + 90 * k, (200, 150, 40))
                screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.line(screen, (255, 210, 110), (sx, sy), (sx + e.cdx * 360, sy + e.cdy * 360), 4)
