"""The hero's weapons. Every weapon updates itself each frame and fires automatically.

All of them read the shared stats on the player (dmg_mult, rate_mult, bonus, pierce_bonus, area),
which the box-point upgrades raise, so every upgrade helps every weapon in its own way.
"""
import math
import random

import pygame

import settings as S
from entities import Chakram, Mine, Shot


class Weapon:
    id = ""
    color = (255, 255, 255)

    def __init__(self):
        self.cd = 0.25

    def update(self, g, dt):
        raise NotImplementedError

    def draw(self, g, screen, cam, t_now):
        pass

    def lights(self, g):
        return []


def _aim(p, target):
    dx, dy = target.x - p.x, target.y - p.y
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


class Needle(Weapon):
    id = "needle"
    color = (63, 245, 224)

    def update(self, g, dt):
        self.cd = max(0.0, self.cd - dt)
        p = g.player
        if self.cd > 0 or p.dashing:
            return
        target = g.nearest_enemy(p.x, p.y, S.SHOT_RANGE)
        if target is None:
            return
        base = math.atan2(target.y - p.y, target.x - p.x)
        n = min(S.SHOT_MAX_COUNT, 1 + p.bonus)
        for i in range(n):
            a = base + math.radians((i - (n - 1) / 2) * S.SHOT_SPREAD_DEG)
            ux, uy = math.cos(a), math.sin(a)
            g.shots.append(Shot(p.x + ux * 26, p.y + uy * 26, ux * S.SHOT_SPEED, uy * S.SHOT_SPEED,
                                S.SHOT_DAMAGE * p.dmg_mult, S.SHOT_PIERCE + p.pierce_bonus))
        self.cd = S.SHOT_COOLDOWN * p.rate_mult
        g.assets.play("shoot", 0.05)


class Halo(Weapon):
    """Orbs of light circle the hero, cutting what they touch and breaking thrown spears."""
    id = "halo"
    color = (244, 204, 96)

    def __init__(self):
        super().__init__()
        self.ang = 0.0
        self.gap = {}
        self.orbs = []

    def update(self, g, dt):
        p = g.player
        n = min(S.HALO_ORBS + S.STAT_BONUS_CAP, S.HALO_ORBS + p.bonus)
        self.ang += S.HALO_SPEED / max(0.6, p.rate_mult) * dt
        rad = S.HALO_RADIUS * p.area
        self.orbs = [(p.x + math.cos(self.ang + i * math.tau / n) * rad,
                      p.y + math.sin(self.ang + i * math.tau / n) * rad) for i in range(n)]
        for k in list(self.gap):
            self.gap[k] -= dt
            if self.gap[k] <= 0:
                del self.gap[k]
        dmg = S.HALO_DAMAGE * p.dmg_mult
        for i, (ox, oy) in enumerate(self.orbs):
            for e in g.enemies_near(ox, oy, 18):
                key = (i, e.id)
                if key in self.gap or e.spawn_t > 0.2:
                    continue
                self.gap[key] = S.HALO_HIT_GAP * p.rate_mult
                g.damage_enemy(e, dmg, e.x - p.x, e.y - p.y, 170.0)
            for sp in g.spears:
                if (sp.x - ox) ** 2 + (sp.y - oy) ** 2 < 28 ** 2:
                    sp.life = 0
                    g.fx.burst(sp.x, sp.y, (255, 226, 140), 5, 160, 0.25, 5)

    def draw(self, g, screen, cam, t_now):
        a = g.assets
        for i, (ox, oy) in enumerate(self.orbs):
            sx, sy = ox - cam[0], oy - cam[1]
            for k, (da, size) in enumerate(((0.16, 16), (0.32, 11))):
                ang = self.ang + i * math.tau / len(self.orbs) - da
                rad = S.HALO_RADIUS * g.player.area
                tx = g.player.x + math.cos(ang) * rad - cam[0]
                ty = g.player.y + math.sin(ang) * rad - cam[1]
                gl = a.glow(size, (110 - k * 40, 90 - k * 30, 40 - k * 14))
                screen.blit(gl, gl.get_rect(center=(tx, ty)), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(a.img["orb"], a.img["orb"].get_rect(center=(sx, sy)))
            gl = a.glow(30, (120, 100, 50))
            screen.blit(gl, gl.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)

    def lights(self, g):
        return [(x, y, 130, (255, 220, 130)) for x, y in self.orbs]


class Pulse(Weapon):
    """A shockwave around the hero: damage, strong knock-back, and it erases spears."""
    id = "pulse"
    color = (190, 140, 255)

    def __init__(self):
        super().__init__()
        self.echoes = []

    def update(self, g, dt):
        p = g.player
        self.cd = max(0.0, self.cd - dt)
        radius = S.PULSE_RADIUS * p.area
        for i in range(len(self.echoes) - 1, -1, -1):
            self.echoes[i] -= dt
            if self.echoes[i] <= 0:
                del self.echoes[i]
                self.wave(g, radius)
        if self.cd > 0:
            return
        if not g.enemies_near(p.x, p.y, radius * 0.9):
            return
        self.cd = S.PULSE_COOLDOWN * p.rate_mult
        self.wave(g, radius)
        self.echoes += [0.3 * (i + 1) for i in range(p.bonus // 2)]

    def wave(self, g, radius):
        p = g.player
        g.waves.append([p.x, p.y, radius, 0.0, set(), S.PULSE_DAMAGE * p.dmg_mult])
        g.fx.ring(p.x, p.y, (190, 140, 255), radius, 0.32, 9)
        g.fx.ring(p.x, p.y, (255, 240, 255), radius * 0.8, 0.26, 4)
        g.assets.play("pulse", 0.1)
        g.shake = max(g.shake, 0.12)


class Arc(Weapon):
    """Lightning that leaps from guardian to guardian."""
    id = "arc"
    color = (150, 190, 255)

    def update(self, g, dt):
        p = g.player
        self.cd = max(0.0, self.cd - dt)
        if self.cd > 0:
            return
        target = g.nearest_enemy(p.x, p.y, S.ARC_RANGE)
        if target is None:
            return
        self.cd = S.ARC_COOLDOWN * p.rate_mult
        jumps = min(9, S.ARC_JUMPS + p.bonus + p.pierce_bonus // 2)
        reach = S.ARC_JUMP_RANGE * p.area
        dmg = S.ARC_DAMAGE * p.dmg_mult
        pts = [(p.x, p.y)]
        hit = set()
        cur = target
        for _ in range(jumps + 1):
            pts.append((cur.x, cur.y))
            hit.add(cur.id)
            g.damage_enemy(cur, dmg, cur.x - pts[-2][0], cur.y - pts[-2][1], 90.0)
            nxt, bd = None, reach * reach
            for e in g.enemies:
                if e.id in hit or e.hp <= 0 or e.spawn_t > 0.2:
                    continue
                d = (e.x - cur.x) ** 2 + (e.y - cur.y) ** 2
                if d < bd:
                    nxt, bd = e, d
            if nxt is None:
                break
            cur = nxt
        g.bolts.append([pts, 0.2, 0.2])
        g.assets.play("arc", 0.06)


class MineLayer(Weapon):
    """Drops sigil mines that detonate when a guardian walks close."""
    id = "mine"
    color = (255, 170, 70)

    def update(self, g, dt):
        p = g.player
        self.cd = max(0.0, self.cd - dt)
        if self.cd > 0 or len(g.mines) >= S.MINE_MAX + p.bonus:
            return
        if g.nearest_enemy(p.x, p.y, 650) is None:
            return
        if any((m.x - p.x) ** 2 + (m.y - p.y) ** 2 < 80 ** 2 for m in g.mines):
            self.cd = 0.3
            return
        g.mines.append(Mine(p.x, p.y, S.MINE_DAMAGE * p.dmg_mult, S.MINE_RADIUS * p.area))
        self.cd = S.MINE_COOLDOWN * p.rate_mult
        g.assets.play("mine_set", 0.1)


class ChakramThrower(Weapon):
    """A bladed ring thrown at the nearest guardian; it pierces on the way out and on the way back."""
    id = "chakram"
    color = (214, 222, 246)

    def update(self, g, dt):
        p = g.player
        self.cd = max(0.0, self.cd - dt)
        if self.cd > 0:
            return
        target = g.nearest_enemy(p.x, p.y, 540)
        if target is None:
            return
        ux, uy = _aim(p, target)
        n = min(1 + S.STAT_BONUS_CAP, 1 + p.bonus)
        base = math.atan2(uy, ux)
        for i in range(n):
            a = base + (i - (n - 1) / 2) * 0.42
            g.chakrams.append(Chakram(p.x, p.y, math.cos(a), math.sin(a), S.CHAKRAM_DIST * p.area,
                                      S.CHAKRAM_DAMAGE * p.dmg_mult))
        self.cd = S.CHAKRAM_COOLDOWN * p.rate_mult
        g.assets.play("chakram", 0.1)


class Scatter(Weapon):
    """A close-range fan of sharp slivers."""
    id = "scatter"
    color = (255, 224, 140)

    def update(self, g, dt):
        p = g.player
        self.cd = max(0.0, self.cd - dt)
        if self.cd > 0 or p.dashing:
            return
        target = g.nearest_enemy(p.x, p.y, S.SCATTER_RANGE)
        if target is None:
            return
        base = math.atan2(target.y - p.y, target.x - p.x)
        n = min(13, S.SCATTER_PELLETS + 2 * p.bonus)
        spread = math.radians(38 + 3 * p.bonus)
        for i in range(n):
            a = base + (i / (n - 1) - 0.5) * spread + random.uniform(-0.03, 0.03)
            sp = 900.0 * random.uniform(0.9, 1.1)
            g.shots.append(Shot(p.x + math.cos(a) * 24, p.y + math.sin(a) * 24, math.cos(a) * sp, math.sin(a) * sp,
                                S.SCATTER_DAMAGE * p.dmg_mult, p.pierce_bonus // 2, "pellet",
                                S.SCATTER_RANGE / 900.0 * 1.05, 8))
        self.cd = S.SCATTER_COOLDOWN * p.rate_mult
        g.assets.play("scatter", 0.05)


class Seeker(Weapon):
    """Homing orbs that curve after the nearest guardian."""
    id = "seeker"
    color = (190, 120, 255)

    def update(self, g, dt):
        p = g.player
        self.cd = max(0.0, self.cd - dt)
        if self.cd > 0:
            return
        target = g.nearest_enemy(p.x, p.y, 620)
        if target is None:
            return
        base = math.atan2(target.y - p.y, target.x - p.x)
        n = min(6, S.SEEKER_COUNT + p.bonus)
        for i in range(n):
            a = base + (i - (n - 1) / 2) * 0.7
            g.shots.append(Shot(p.x + math.cos(a) * 24, p.y + math.sin(a) * 24, math.cos(a) * S.SEEKER_SPEED,
                                math.sin(a) * S.SEEKER_SPEED, S.SEEKER_DAMAGE * p.dmg_mult, p.pierce_bonus // 3,
                                "seeker", 2.4, 12))
        self.cd = S.SEEKER_COOLDOWN * p.rate_mult
        g.assets.play("seeker", 0.08)


WEAPONS = {c.id: c for c in (Needle, Halo, Pulse, Arc, MineLayer, ChakramThrower, Scatter, Seeker)}
UNLOCKABLE = ["halo", "pulse", "arc", "mine", "chakram", "scatter", "seeker"]
COLORS = {k: c.color for k, c in WEAPONS.items()}


# ---- things the weapons leave behind: waves, mines, chakrams, bolts, homing -----------------
def update_waves(g, dt):
    keep = []
    for w in g.waves:
        w[3] += dt
        k = min(1.0, w[3] / 0.3)
        r = w[2] * (0.15 + 0.85 * k)
        for e in g.enemies_near(w[0], w[1], r):
            if e.id in w[4] or e.spawn_t > 0.2:
                continue
            w[4].add(e.id)
            g.damage_enemy(e, w[5], e.x - w[0], e.y - w[1], 560.0)
        for sp in g.spears:
            if (sp.x - w[0]) ** 2 + (sp.y - w[1]) ** 2 < r * r:
                sp.life = 0
        if w[3] < 0.3:
            keep.append(w)
    g.waves = keep


def update_mines(g, dt):
    keep = []
    for m in g.mines:
        m.age += dt
        m.life -= dt
        if m.life <= 0:
            continue
        if m.age > S.MINE_ARM:
            trig = None
            for e in g.enemies_near(m.x, m.y, 62):
                if e.spawn_t <= 0.2:
                    trig = e
                    break
            if trig is not None:
                g.fx.burst(m.x, m.y, (255, 190, 80), 22, 420, 0.5, 11)
                g.fx.ring(m.x, m.y, (255, 170, 70), m.radius, 0.35, 8)
                g.fx.diamonds(m.x, m.y, 6, 260, 0.5)
                g.assets.play("mine", 0.05)
                g.shake = max(g.shake, 0.22)
                for e in g.enemies_near(m.x, m.y, m.radius):
                    g.damage_enemy(e, m.dmg, e.x - m.x, e.y - m.y, 480.0)
                continue
        keep.append(m)
    g.mines = keep


def update_chakrams(g, dt):
    p = g.player
    keep = []
    for c in g.chakrams:
        c.life -= dt
        c.spin += 14.0 * dt
        if c.going:
            step = S.CHAKRAM_SPEED * dt
            c.x += c.dx * step
            c.y += c.dy * step
            c.traveled += step
            c.x = min(S.ARENA, max(0, c.x))
            c.y = min(S.ARENA, max(0, c.y))
            if c.traveled >= c.dist:
                c.going = False
                c.hit = set()
        else:
            dx, dy = p.x - c.x, p.y - c.y
            d = math.hypot(dx, dy) or 1.0
            step = S.CHAKRAM_SPEED * 1.2 * dt
            c.x += dx / d * step
            c.y += dy / d * step
            if d < 34:
                continue
        if c.life <= 0:
            continue
        for e in g.enemies_near(c.x, c.y, 28):
            if e.id in c.hit or e.spawn_t > 0.2:
                continue
            c.hit.add(e.id)
            g.damage_enemy(e, c.dmg, c.dx if c.going else p.x - c.x, c.dy if c.going else p.y - c.y, 200.0)
        keep.append(c)
    g.chakrams = keep


def update_bolts(g, dt):
    for b in g.bolts:
        b[1] -= dt
    g.bolts = [b for b in g.bolts if b[1] > 0]


def steer_seeker(g, s, dt):
    """Bend a seeker's velocity towards the nearest guardian."""
    target = g.nearest_enemy(s.x, s.y, 700)
    if target is None:
        return
    want = math.atan2(target.y - s.y, target.x - s.x)
    cur = math.atan2(s.vy, s.vx)
    d = (want - cur + math.pi) % math.tau - math.pi
    cur += max(-5.0 * dt, min(5.0 * dt, d))
    s.vx, s.vy = math.cos(cur) * s.speed, math.sin(cur) * s.speed


def draw_bolts(g, screen, cam):
    for pts, life, max_life in g.bolts:
        k = life / max_life
        jag = []
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 34))
            for j in range(n):
                f = j / n
                jx = (random.uniform(-9, 9) if j else 0)
                jy = (random.uniform(-9, 9) if j else 0)
                jag.append((x0 + (x1 - x0) * f + jx - cam[0], y0 + (y1 - y0) * f + jy - cam[1]))
        jag.append((pts[-1][0] - cam[0], pts[-1][1] - cam[1]))
        if len(jag) < 2:
            continue
        xs, ys = [q[0] for q in jag], [q[1] for q in jag]
        pad = 14
        left, top = int(min(xs)) - pad, int(min(ys)) - pad
        w, h = int(max(xs) - min(xs)) + pad * 2, int(max(ys) - min(ys)) + pad * 2
        if w <= 0 or h <= 0 or w > 3000 or h > 3000:
            continue
        tmp = pygame.Surface((w, h))
        loc = [(x - left, y - top) for x, y in jag]
        pygame.draw.lines(tmp, tuple(int(c * k) for c in (70, 110, 220)), False, loc, 9)
        pygame.draw.lines(tmp, tuple(int(c * k) for c in (150, 190, 255)), False, loc, 5)
        pygame.draw.lines(tmp, tuple(int(255 * k) for _ in range(3)), False, loc, 2)
        screen.blit(tmp, (left, top), special_flags=pygame.BLEND_RGB_ADD)
