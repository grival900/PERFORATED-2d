"""Level 1: the Pride arena. Builds the baked floor image, obstacles and static lights."""
import math
import random

import pygame

from settings import (ALTAR_POS, ARENA, GATE_X0, GATE_X1, HEART_SPOTS, THEMES, WALL)

SURF = ARENA + 2 * WALL          # size of the baked floor image
GOLD = (236, 196, 92)
GOLD_D = (140, 98, 34)

# pillar centres; footprint is a 124 px square
PILLARS = [(705, 765), (2295, 765), (705, 2235), (2295, 2235),
           (1500, 2500), (420, 1500), (2580, 1500), (1100, 1180), (1900, 1180)]
PILLAR_HALF = 62
# low walls block movement but not shots: (x, y, w, h)
LOW_WALLS = [(1200, 1410, 600, 54), (240, 1230, 54, 540), (2706, 1230, 54, 540),
             (900, 2330, 300, 54), (1800, 2330, 300, 54), (1130, 480, 54, 260), (1816, 480, 54, 260)]
BRAZIERS = [(150, 150), (ARENA - 150, 150), (150, ARENA - 150), (ARENA - 150, ARENA - 150),
            (ARENA // 2 - 345, 62), (ARENA // 2 + 345, 62),
            (150, ARENA // 2), (ARENA - 150, ARENA // 2), (ARENA // 2, ARENA - 150)]
MINIMAP = 200

LAYOUTS = {
    # Level 1, the open arena: a few pillars, short walls, lots of room to kite
    1: dict(pillars=PILLARS, low_walls=LOW_WALLS, braziers=BRAZIERS),
    # Level 2, the bank: a walled central vault with four doors, corner teller booths, side corridors
    2: dict(pillars=[(650, 1000), (2350, 1000), (650, 2000), (2350, 2000), (1500, 2650), (950, 2650), (2050, 2650),
                     (1500, 560)],
            low_walls=[(1100, 1000, 300, 54), (1600, 1000, 300, 54), (1100, 1600, 300, 54), (1600, 1600, 300, 54),
                       (1100, 1000, 54, 230), (1100, 1370, 54, 284), (1846, 1000, 54, 230), (1846, 1370, 54, 284),
                       (300, 500, 500, 54), (300, 500, 54, 400), (2200, 500, 500, 54), (2646, 500, 54, 400),
                       (300, 2446, 500, 54), (300, 2100, 54, 400), (2200, 2446, 500, 54), (2646, 2100, 54, 400),
                       (600, 1300, 54, 500), (2346, 1300, 54, 500)],
            braziers=BRAZIERS),
    # Level 3, the boudoir: two nested square rings with offset doorways, columns in the corners
    3: dict(pillars=[(350, 350), (2650, 350), (350, 2650), (2650, 2650), (800, 800), (2200, 800), (800, 2200),
                     (2200, 2200), (1500, 1300), (1500, 2650)],
            low_walls=[(600, 600, 700, 54), (1700, 600, 700, 54), (600, 2400, 100, 54), (900, 2400, 1200, 54),
                       (2300, 2400, 100, 54), (600, 600, 54, 600), (600, 1400, 54, 1000), (2346, 600, 54, 1200),
                       (2346, 2000, 54, 400),
                       (1100, 900, 400, 54), (1700, 900, 200, 54), (1100, 1700, 100, 54), (1400, 1700, 500, 54),
                       (1100, 900, 54, 350), (1100, 1450, 54, 304), (1846, 900, 54, 200), (1846, 1300, 54, 454)],
            braziers=BRAZIERS),
}


def _circle_rect_push(x, y, r, rect):
    """Push a circle out of a pygame.Rect. Returns (x, y, hit)."""
    cx = min(max(x, rect.left), rect.right)
    cy = min(max(y, rect.top), rect.bottom)
    dx, dy = x - cx, y - cy
    d2 = dx * dx + dy * dy
    if d2 >= r * r:
        return x, y, False
    if d2 > 1e-6:
        d = math.sqrt(d2)
        return cx + dx / d * r, cy + dy / d * r, True
    # centre is inside the rect: leave through the nearest side
    left, right = x - rect.left, rect.right - x
    top, bottom = y - rect.top, rect.bottom - y
    m = min(left, right, top, bottom)
    if m == left:
        return rect.left - r, y, True
    if m == right:
        return rect.right + r, y, True
    if m == top:
        return x, rect.top - r, True
    return x, rect.bottom + r, True


class Level:
    def __init__(self, assets, num=1):
        self.a = assets
        self.num = num
        self.theme = THEMES[num]
        lay = LAYOUTS[num]
        self.pillars, self.low_walls, self.braziers = lay["pillars"], lay["low_walls"], lay["braziers"]
        self.solid = [pygame.Rect(cx - PILLAR_HALF, cy - PILLAR_HALF, PILLAR_HALF * 2, PILLAR_HALF * 2)
                      for cx, cy in self.pillars]
        self.shot_blockers = list(self.solid)
        self.solid += [pygame.Rect(*r) for r in self.low_walls]
        self.floor = None
        self.minimap = None
        self.gate_open = False
        self.gate_open_t = 0.0
        self.last_normal = None      # direction we were pushed by the last solid (for steering)

    # ------------------------------------------------------------------ baking
    def bake(self):
        a = self.a
        money = self.theme["style"] == "money"
        rng = random.Random(11)
        s = pygame.Surface((SURF, SURF))
        s.fill((12, 12, 22))
        wall = a.img["wall_block"]
        for y in range(0, SURF, wall.get_height()):
            for x in range(0, SURF, wall.get_width()):
                s.blit(wall, (x, y))
        # marble floor
        floor_rect = pygame.Rect(WALL, WALL, ARENA, ARENA)
        s.set_clip(floor_rect)
        for gy in range(0, ARENA, 128):
            for gx in range(0, ARENA, 128):
                tile = a.img[f"marble_{rng.randrange(8)}"].copy()
                v = rng.randint(226, 255)
                if money and (gx // 128 + gy // 128) % 2:         # bank-lobby checkerboard
                    v = int(v * 0.74)
                tile.fill((v, v, min(255, v + 4)), special_flags=pygame.BLEND_RGB_MULT)
                s.blit(tile, (WALL + gx, WALL + gy))
        s.set_clip(None)

        def W(p):  # world -> baked image coordinates
            return (int(p[0] + WALL), int(p[1] + WALL))

        # gold inlay: inset square and two rings round the sigil
        inset = pygame.Rect(W((170, 170)), (ARENA - 340, ARENA - 340))
        gold_d, gold = self.theme.get("inlay", (GOLD_D, GOLD))
        for off, col, w in [(0, gold_d, 10), (3, gold, 4)]:
            pygame.draw.rect(s, col, inset.inflate(-off * 2, -off * 2), w)
        for cx, cy in [(170, 170), (ARENA - 170, 170), (170, ARENA - 170), (ARENA - 170, ARENA - 170)]:
            pygame.draw.circle(s, gold_d, W((cx, cy)), 26)
            pygame.draw.circle(s, gold, W((cx, cy)), 20)
            pygame.draw.circle(s, gold_d, W((cx, cy)), 9)
        for r, w in [(1150, 6), (1090, 3)]:
            pygame.draw.circle(s, gold_d, W((ARENA // 2, ARENA // 2)), r, w + 3)
            pygame.draw.circle(s, gold, W((ARENA // 2, ARENA // 2)), r, w)
        sig = pygame.transform.smoothscale(a.img["sigil"], (1500, 1500))
        if self.theme.get("decor"):
            sig.set_alpha(self.theme.get("emblem_alpha", 70))   # dim, so the floor does not drown the action
        s.blit(sig, sig.get_rect(center=W((ARENA // 2, ARENA // 2))))

        # soft dark band along the walls (ambient occlusion)
        for side in range(4):
            strip = pygame.Surface((ARENA, 110), pygame.SRCALPHA)
            for i in range(110):
                pygame.draw.line(strip, (0, 0, 10, int(150 * (1 - i / 110) ** 2)), (0, i), (ARENA, i))
            strip = pygame.transform.rotate(strip, side * 90)
            pos = {0: (WALL, WALL), 1: (WALL, WALL), 2: (WALL, WALL + ARENA - 110), 3: (WALL + ARENA - 110, WALL)}[side]
            s.blit(strip, pos)
        # bright lip where the floor meets the wall
        pygame.draw.rect(s, (132, 126, 170), floor_rect.inflate(6, 6), 3)
        pygame.draw.rect(s, (20, 18, 34), floor_rect.inflate(14, 14), 6)

        if self.theme.get("decor"):                 # loose coins, banknotes, petals... on the floor
            d1, d2 = self.theme["decor"]
            for _ in range(260):
                x, y = rng.uniform(150, ARENA - 150), rng.uniform(150, ARENA - 150)
                if any(r.inflate(60, 60).collidepoint(x, y) for r in self.solid):
                    continue
                spr = a.img[d1 if rng.random() < 0.65 else d2]
                spr = pygame.transform.rotate(spr, rng.uniform(0, 360))
                s.blit(spr, spr.get_rect(center=W((x, y))))

        # low walls
        for x, y, w, h in self.low_walls:
            r = pygame.Rect(W((x, y)), (w, h))
            shadow = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 8, 120), shadow.get_rect().inflate(-6, -6), border_radius=8)
            s.blit(pygame.transform.smoothscale(shadow, (w + 24, h + 24)), (r.x - 6, r.y - 2))
            s.set_clip(r)
            for ty in range(r.top - r.top % 96, r.bottom, 96):
                for tx in range(r.left - r.left % 96, r.right, 96):
                    s.blit(wall, (tx, ty))
            s.set_clip(None)
            pygame.draw.rect(s, gold_d, r, 6, border_radius=3)
            pygame.draw.rect(s, gold, r.inflate(-6, -6), 2, border_radius=2)
            pygame.draw.line(s, (200, 194, 236), r.topleft, (r.right, r.top), 2)

        # pillars (texture already has a baked drop shadow)
        for cx, cy in self.pillars:
            t = a.img["pillar"]
            s.blit(t, t.get_rect(center=W((cx, cy))))
        # braziers and altar
        for bx, by in self.braziers:
            t = a.img["brazier"]
            s.blit(t, t.get_rect(center=W((bx, by))))
        t = a.img["altar"]
        s.blit(t, t.get_rect(center=W(ALTAR_POS)))
        self.floor = s.convert()
        self.minimap = pygame.transform.smoothscale(self.floor.subsurface(pygame.Rect(WALL, WALL, ARENA, ARENA)),
                                                    (MINIMAP, MINIMAP))
        self.minimap.set_alpha(215)

    # ------------------------------------------------------------------ placement
    def is_free(self, x, y, margin=40):
        """True if a prop of radius `margin` fits at (x, y): inside the arena, off obstacles, away from props."""
        if not (110 < x < ARENA - 110 and 110 < y < ARENA - 110):
            return False
        for rect in self.solid:
            if rect.inflate(margin * 2, margin * 2).collidepoint(x, y):
                return False
        for bx, by in self.braziers:
            if (bx - x) ** 2 + (by - y) ** 2 < 120 ** 2:
                return False
        if (ALTAR_POS[0] - x) ** 2 + (ALTAR_POS[1] - y) ** 2 < 190 ** 2:
            return False
        if y < 330 and GATE_X0 - 120 < x < GATE_X1 + 120:      # keep the gate approach clear
            return False
        return True

    # ------------------------------------------------------------------ collision
    def collide(self, x, y, r, through_gate=None):
        """Keep a circle inside the arena and out of obstacles. Returns (x, y, hit)."""
        if through_gate is None:
            through_gate = self.gate_open
        hit = False
        self.last_normal = None
        lo_y = r
        if through_gate and GATE_X0 + r <= x <= GATE_X1 - r:
            lo_y = -110
        if x < r:
            x, hit = r, True
        elif x > ARENA - r:
            x, hit = ARENA - r, True
        if y < lo_y:
            y, hit = lo_y, True
        elif y > ARENA - r:
            y, hit = ARENA - r, True
        for rect in self.solid:
            if abs(x - rect.centerx) < rect.w / 2 + r + 2 and abs(y - rect.centery) < rect.h / 2 + r + 2:
                ox, oy = x, y
                x, y, h = _circle_rect_push(x, y, r, rect)
                if h:
                    n = math.hypot(x - ox, y - oy)
                    if n > 1e-6:
                        self.last_normal = ((x - ox) / n, (y - oy) / n)
                hit = hit or h
        return x, y, hit

    def shot_blocked(self, x, y):
        if x < 0 or x > ARENA or y > ARENA:
            return True
        if y < 0 and not (self.gate_open and GATE_X0 <= x <= GATE_X1):
            return True
        for r in self.shot_blockers:
            if r.collidepoint(x, y):
                return True
        return False

    # ------------------------------------------------------------------ lights
    def static_lights(self, t):
        """(x, y, radius, colour) of the level's own lights; braziers flicker."""
        out = []
        for i, (bx, by) in enumerate(self.braziers):
            f = 0.82 + 0.18 * math.sin(t * 9.0 + i * 1.7) * math.sin(t * 5.3 + i)
            out.append((bx, by, 330 * f, self.theme["brazier"]))
        out.append((ALTAR_POS[0], ALTAR_POS[1], 260, (60, 235, 215)))
        gx = (GATE_X0 + GATE_X1) / 2
        if self.gate_open:
            out.append((gx, 20, 520, (255, 232, 160)))
        else:
            out.append((gx, 30, 240, (214, 168, 86)))
        for hx, hy in HEART_SPOTS:
            out.append((hx, hy, 110, (255, 90, 110)))
        return out

    # ------------------------------------------------------------------ drawing
    def draw_floor(self, screen, cam):
        area = pygame.Rect(int(cam[0]) + WALL, int(cam[1]) + WALL, screen.get_width(), screen.get_height())
        area.clamp_ip(pygame.Rect(0, 0, SURF, SURF))
        screen.blit(self.floor, (0, 0), area)

    def draw_gate(self, screen, cam):
        img = self.a.img["gate_open" if self.gate_open else "gate_closed"]
        gx = (GATE_X0 + GATE_X1) / 2
        screen.blit(img, img.get_rect(midbottom=(gx - cam[0], 20 - cam[1])))

    def draw_flames(self, screen, cam, t):
        """Additive flames above the braziers (drawn after lighting so they stay bright)."""
        a = self.a
        for i, (bx, by) in enumerate(self.braziers):
            sx, sy = bx - cam[0], by - cam[1]
            if sx < -80 or sx > screen.get_width() + 80 or sy < -80 or sy > screen.get_height() + 80:
                continue
            f = 0.85 + 0.15 * math.sin(t * 11 + i * 2.1)
            g = a.glow(34 * f, self.theme["flame"])
            screen.blit(g, g.get_rect(center=(sx, sy - 4)), special_flags=pygame.BLEND_RGB_ADD)
            g2 = a.glow(16 * f, self.theme["flame_core"])
            screen.blit(g2, g2.get_rect(center=(sx + math.sin(t * 7 + i) * 2, sy - 8 - 3 * f)), special_flags=pygame.BLEND_RGB_ADD)
