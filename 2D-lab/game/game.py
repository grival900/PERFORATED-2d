"""PERFORATED, Level 1 (Pride): game state, simulation and rendering."""
import math
import random

import pygame

import settings as S
import strings
from assets import Assets
from entities import Enemy, HeartPickup, Player, Shot, Spear
from fx import Particles
from level import Level
from strings import t
from ui import UI

AMBIENT = (62, 68, 98)
UPGRADE_IDS = ["multi", "rate", "pierce", "power", "dash", "speed", "heart"]


class Lighting:
    """Low-resolution additive light map, multiplied over the frame."""

    def __init__(self, assets, w, h, scale=4):
        self.a, self.w, self.h, self.s = assets, w, h, scale
        self.lm = pygame.Surface((w // scale, h // scale))

    def render(self, screen, cam, lights):
        lm, s = self.lm, self.s
        lm.fill(AMBIENT)
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
        self.level = Level(self.assets)
        self.level.bake()
        self.fx = Particles(self.assets)
        self.ui = UI(self.assets)
        self.light = Lighting(self.assets, S.SCREEN_W, S.SCREEN_H)
        self._shadow = {}
        self.clock = 0.0                 # real time, runs in every state
        self.state = "title"
        self.cam = [0.0, 0.0]
        self.reset()
        self.state = "title"
        self.cam = [S.ARENA / 2 - S.SCREEN_W / 2, S.ARENA / 2 - S.SCREEN_H / 2 + 100]

    # ------------------------------------------------------------------ run control
    def reset(self):
        random.seed()
        Enemy._next_id = 0
        self.level.gate_open = False
        self.player = Player()
        self.enemies, self.shots, self.spears = [], [], []
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
        self.elites = 0
        self.upgrades_given = 0
        self.pending_upgrades = 0
        self.upgrade_choices = []
        self.upgrade_sel = 0
        self.exit_open = False
        self.over = False
        self.dying_t = 0.0
        self.shake = 0.0
        self.red_flash = 0.0
        self.enemy_speed_mult = 1.0
        self.ghost_t = 0.0
        self.cam = [S.PLAYER_START[0] - S.SCREEN_W / 2, S.PLAYER_START[1] - S.SCREEN_H / 2]
        self.state = "play"

    def start(self):
        self.reset()
        self.assets.start_music()
        self.show_banner(t("stage").format(n=1) + ": " + t("stage_desc")[1])

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
                self.start()
            elif key == K.K_q:
                return "quit"
        elif st == "upgrade":
            if key in (K.K_1, K.K_2, K.K_3):
                self.pick_upgrade(key - K.K_1)
            elif key in (K.K_LEFT, K.K_a):
                self.upgrade_sel = (self.upgrade_sel - 1) % 3
            elif key in (K.K_RIGHT, K.K_d):
                self.upgrade_sel = (self.upgrade_sel + 1) % 3
            elif key in (K.K_RETURN, K.K_KP_ENTER, K.K_SPACE):
                self.pick_upgrade(self.upgrade_sel)
        elif st in ("over", "win"):
            if key in (K.K_RETURN, K.K_KP_ENTER):
                self.start()
            elif key == K.K_ESCAPE:
                return "quit"
        return None

    def handle_mouse(self, pos, click):
        if self.state != "upgrade":
            return
        for i, r in enumerate(self.ui.upgrade_rects()):
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
        self.auto_fire(target)

        self.update_director(dt)
        for e in self.enemies:
            e.update(dt, p, self.level, self)
        self.separate_enemies(dt)
        self.update_shots(dt)
        self.update_spears(dt)
        self.contact_damage()
        self.update_pickups(dt)
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
            if e.spawn_t > 0:
                continue
            d = (e.x - x) ** 2 + (e.y - y) ** 2
            if d < bd:
                best, bd = e, d
        return best

    def try_dash(self, move):
        p = self.player
        if p.try_dash(*move):
            self.assets.play("dash")
            self.fx.ring(p.x, p.y, (90, 240, 225), 70, 0.25, 3)

    def auto_fire(self, target):
        p = self.player
        if target is None or p.shot_cd > 0 or p.dashing:
            return
        dx, dy = target.x - p.x, target.y - p.y
        d = math.hypot(dx, dy) or 1.0
        base = math.atan2(dy, dx)
        n = p.shots
        for i in range(n):
            a = base + math.radians((i - (n - 1) / 2) * S.SHOT_SPREAD_DEG)
            ux, uy = math.cos(a), math.sin(a)
            self.shots.append(Shot(p.x + ux * 26, p.y + uy * 26, ux * S.SHOT_SPEED, uy * S.SHOT_SPEED, p.damage, p.pierce))
        p.shot_cd = p.cooldown
        self.assets.play("shoot", 0.05)

    def build_grid(self):
        grid = {}
        for e in self.enemies:
            grid.setdefault((int(e.x // 80), int(e.y // 80)), []).append(e)
        return grid

    def update_shots(self, dt):
        grid = self.build_grid()
        keep = []
        for s in self.shots:
            s.life -= dt
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
                            if (e.x - s.x) ** 2 + (e.y - s.y) ** 2 < (e.r + 9) ** 2:
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

    def damage_enemy(self, e, dmg, dx, dy):
        e.hit(dmg, dx, dy)
        self.fx.burst(e.x, e.y, (230, 255, 252), 5, 200, 0.25, 6)
        self.assets.play("hit", 0.04)
        if e.hp <= 0:
            self.kill_enemy(e)

    def kill_enemy(self, e, award=True):
        self.kills += 1 if award else 0
        self.fx.diamonds(e.x, e.y, 14 if e.kind == "elite" else 7, 320)
        self.fx.burst(e.x, e.y, (255, 240, 190), 12 if e.kind == "elite" else 7, 260, 0.5, 9)
        self.fx.ring(e.x, e.y, (255, 236, 170), 70 if e.kind != "elite" else 150, 0.35, 3)
        if award:
            self.fx.text(e.x, e.y - 20, f"+{e.pts}", (255, 232, 150), 22 if e.kind != "elite" else 34)
            self.assets.play("kill", 0.04)
            self.add_pride(e.pts)
            if e.kind == "elite":
                self.pickups.append(HeartPickup(e.x, e.y, respawns=False))
                self.shake = max(self.shake, 0.6)
                self.assets.play("slam")
        e.hp = 0

    def dash_hits(self):
        p = self.player
        for e in self.enemies:
            if e.hp > 0 and e.id not in p.dash_hit and (e.x - p.x) ** 2 + (e.y - p.y) ** 2 < (e.r + 34) ** 2:
                p.dash_hit.add(e.id)
                self.damage_enemy(e, S.DASH_DAMAGE, p.dash_dx, p.dash_dy)
                self.fx.ring(e.x, e.y, (90, 240, 225), 60, 0.2, 3)
        self.enemies = [e for e in self.enemies if e.hp > 0]

    def spawn_spear(self, x, y, ux, uy):
        self.spears.append(Spear(x, y, ux, uy))
        self.assets.play("spear", 0.08)

    def update_spears(self, dt):
        p = self.player
        keep = []
        for sp in self.spears:
            sp.life -= dt
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

    def separate_enemies(self, dt):
        grid = self.build_grid()
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
                            if e.kind != "elite":
                                e.x -= ux * push
                                e.y -= uy * push
                            if o.kind != "elite":
                                o.x += ux * push
                                o.y += uy * push
            dx, dy = e.x - p.x, e.y - p.y
            d2 = dx * dx + dy * dy
            rr = (e.r + p.r) * 0.55
            if 1e-6 < d2 < rr * rr:
                d = math.sqrt(d2)
                e.x += dx / d * (rr - d)
                e.y += dy / d * (rr - d)

    # ---- progression -----------------------------------------------------------
    def add_pride(self, pts):
        if self.exit_open:
            return
        self.pride = min(S.PRIDE_MAX, self.pride + pts)
        self.bar_pulse = 0.25
        frac = self.pride / S.PRIDE_MAX
        while self.upgrades_given < len(S.UPGRADE_AT) and frac >= S.UPGRADE_AT[self.upgrades_given]:
            self.upgrades_given += 1
            self.pending_upgrades += 1
        new_stage = 1 + sum(1 for m in S.STAGE_AT if frac >= m)
        if new_stage != self.stage:
            self.stage = new_stage
            self.enemy_speed_mult = (1.0, 1.0, 1.05, 1.1, 1.18)[self.stage]
            self.show_banner(t("stage").format(n=self.stage) + ": " + t("stage_desc")[self.stage])
        if self.pride >= S.PRIDE_MAX:
            self.open_exit()

    def open_exit(self):
        self.exit_open = True
        self.level.gate_open = True
        self.assets.play("gate")
        for e in list(self.enemies):
            self.kill_enemy(e, award=False)
        self.enemies.clear()
        self.spears.clear()
        self.shake = max(self.shake, 0.7)

    def check_progress(self):
        if self.state == "play" and self.pending_upgrades > 0 and not self.exit_open:
            self.open_upgrades()

    def open_upgrades(self):
        p = self.player
        pool = [u for u in UPGRADE_IDS
                if not (u == "multi" and p.shots >= S.SHOT_MAX_COUNT)
                and not (u == "dash" and p.charge_cap >= S.DASH_CHARGES_CAP)
                and not (u == "heart" and p.max_hp >= S.PLAYER_HP_CAP)]
        self.upgrade_choices = random.sample(pool, 3)
        self.upgrade_sel = 0
        self.state = "upgrade"
        self.assets.play("upgrade_open")

    def pick_upgrade(self, idx):
        if idx >= len(self.upgrade_choices):
            return
        uid = self.upgrade_choices[idx]
        p = self.player
        if uid == "multi":
            p.shots = min(S.SHOT_MAX_COUNT, p.shots + 1)
        elif uid == "rate":
            p.cooldown *= 0.82
        elif uid == "pierce":
            p.pierce += 1
        elif uid == "power":
            p.damage += 1
        elif uid == "dash":
            p.charge_cap = min(S.DASH_CHARGES_CAP, p.charge_cap + 1)
            p.charges = min(p.charge_cap, p.charges + 1)
            p.recharge *= 0.9
        elif uid == "speed":
            p.speed *= 1.10
        elif uid == "heart":
            p.max_hp = min(S.PLAYER_HP_CAP, p.max_hp + 1)
            p.hp = min(p.max_hp, p.hp + 1)
        self.pending_upgrades -= 1
        self.state = "play"
        self.assets.play("upgrade_pick")
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

    # ---- spawning ------------------------------------------------------------------
    def pick_spawn_point(self):
        p = self.player
        pts = [pt for pt in S.SPAWN_POINTS if math.hypot(pt[0] - p.x, pt[1] - p.y) > S.MIN_SPAWN_DISTANCE]
        return random.choice(pts or S.SPAWN_POINTS)

    def spawn_enemy(self, kind, x, y):
        self.enemies.append(Enemy(kind, x, y))

    def update_director(self, dt):
        if self.exit_open:
            return
        st = S.STAGES[self.stage]
        self.spawn_t -= dt
        # elites: one when stage 4 begins, a second near the end
        if self.stage == 4 and self.elites == 0 or (self.pride >= 0.9 * S.PRIDE_MAX and self.elites == 1):
            self.elites += 1
            x, y = self.pick_spawn_point()
            self.spawn_enemy("elite", x, y)
            self.assets.play("elite")
            self.fx.ring(x, y, (255, 220, 120), 220, 0.8, 6)
        if self.spawn_t > 0:
            return
        self.spawn_t = st["interval"] * random.uniform(0.85, 1.15)
        alive = len(self.enemies)
        room = min(st["cap"], S.MAX_ENEMIES) - alive
        if room <= 0:
            return
        n = min(room, random.randint(*st["group"]))
        px, py = self.pick_spawn_point()
        kinds, weights = zip(*st["weights"].items())
        for _ in range(n):
            kind = random.choices(kinds, weights)[0]
            ang = random.uniform(0, math.tau)
            rad = random.uniform(0, 70)
            self.spawn_enemy(kind, min(S.ARENA - 30, max(30, px + math.cos(ang) * rad)),
                             min(S.ARENA - 30, max(30, py + math.sin(ang) * rad)))

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

    def draw(self, screen):
        a = self.assets
        cam = self.view_cam()
        W, H = S.SCREEN_W, S.SCREEN_H
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
                ang = math.atan2(p.x - fx_, -(p.y - fy_))
                img = a.rotated("ferryman", ang * 0.4)
                screen.blit(self.shadow(56), self.shadow(56).get_rect(center=(sx, sy + 20)))
                screen.blit(img, img.get_rect(center=(sx, sy + math.sin(t_now * 1.6) * 2)))
            elif kind == "enemy":
                self.draw_enemy(screen, cam, obj, t_now)
            else:
                self.draw_player(screen, cam, obj, t_now)

        # projectiles
        for s in self.shots:
            img = a.heading("needle", s.vx, s.vy)
            screen.blit(img, img.get_rect(center=(s.x - cam[0], s.y - cam[1])))
        for sp in self.spears:
            img = a.heading("spear", sp.vx, sp.vy)
            screen.blit(img, img.get_rect(center=(sp.x - cam[0], sp.y - cam[1])))
        self.draw_telegraphs(screen, cam)
        self.fx.draw(screen, cam)

        # lighting
        lights = list(lvl.static_lights(t_now))
        lights.append((p.x, p.y, 430, (235, 230, 250)))
        for s in self.shots:
            lights.append((s.x, s.y, 100, (60, 220, 205)))
        for sp in self.spears:
            lights.append((sp.x, sp.y, 130, (255, 226, 140)))
        n = 0
        for e in self.enemies:
            if -200 < e.x - cam[0] < W + 200 and -200 < e.y - cam[1] < H + 200:
                lights.append((e.x, e.y, 84 if e.kind != "elite" else 190, (150, 140, 110)))
                n += 1
                if n > 45:
                    break
        lights.append((S.ALTAR_POS[0] - 70, S.ALTAR_POS[1] - 20, 120, (60, 235, 215)))
        self.light.render(screen, cam, lights)
        lvl.draw_flames(screen, cam, t_now)
        # additive bloom on top of the lit scene
        for s in self.shots:
            g = a.glow(30, (50, 200, 190))
            screen.blit(g, g.get_rect(center=(s.x - cam[0], s.y - cam[1])), special_flags=pygame.BLEND_RGB_ADD)
        if lvl.gate_open:
            g = a.glow(220, (110, 90, 40))
            screen.blit(g, g.get_rect(center=((S.GATE_X0 + S.GATE_X1) / 2 - cam[0], 30 - cam[1])),
                        special_flags=pygame.BLEND_RGB_ADD)
        # vignette
        vg = a.img["vignette"]
        screen.blit(pygame.transform.smoothscale(vg, (W, H)), (0, 0))

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
        if sx < -220 or sx > S.SCREEN_W + 220 or sy < -220 or sy > S.SCREEN_H + 220:
            return
        screen.blit(self.shadow(e.shadow), self.shadow(e.shadow).get_rect(center=(sx, sy + e.r * 0.55)))
        img = a.rotated(e.sprite, e.face)
        if e.flash > 0:
            img = img.copy()
            img.fill((130, 130, 130), special_flags=pygame.BLEND_RGB_ADD)
        if e.spawn_t > 0:
            k = 1 - e.spawn_t / 0.35
            img = pygame.transform.rotozoom(img, 0, 0.6 + 0.4 * k)
            img.set_alpha(int(255 * k))
        bob = math.sin(e.t * 3) * 2
        screen.blit(img, img.get_rect(center=(sx, sy + bob)))
        n = {"sentinel": 3, "skirmisher": 0, "lancer": 2, "elite": 5}[e.kind]
        rad = e.r + 18 + (6 if e.kind == "elite" else 0)
        shard = a.img["shard"]
        for i in range(n):
            ang = e.t * 1.6 + i * math.tau / n
            screen.blit(shard, shard.get_rect(center=(sx + math.cos(ang) * rad, sy + math.sin(ang) * rad * 0.9 + bob)))
        if e.kind == "elite" and e.hp < e.max_hp:
            w = 70
            pygame.draw.rect(screen, (20, 18, 34), (sx - w / 2, sy - e.r - 34, w, 7))
            pygame.draw.rect(screen, (244, 204, 96), (sx - w / 2, sy - e.r - 34, w * e.hp / e.max_hp, 7))

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
        for e in self.enemies:
            if e.windup <= 0:
                continue
            sx, sy = e.x - cam[0], e.y - cam[1]
            if e.kind == "lancer":
                k = 1 - e.windup / S.SPEAR_WINDUP
                pygame.draw.line(screen, (255, int(200 + 40 * k), 120), (sx, sy), (sx + e.cdx * 520, sy + e.cdy * 520), 2)
            elif e.kind == "elite":
                k = 1 - e.windup / S.ELITE_WINDUP
                g = self.assets.glow(40 + 90 * k, (200, 150, 40))
                screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.line(screen, (255, 210, 110), (sx, sy), (sx + e.cdx * 360, sy + e.cdy * 360), 4)
