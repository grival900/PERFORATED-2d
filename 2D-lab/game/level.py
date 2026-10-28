"""Level 1: the Pride arena. Builds the baked floor image, obstacles and static lights."""
import math
import random

import pygame

from settings import (ALTAR_POS, ARENA, GATE_X0, GATE_X1, HEART_SPOTS, WALL)

SURF = ARENA + 2 * WALL          # size of the baked floor image
GOLD = (236, 196, 92)
GOLD_D = (140, 98, 34)

# pillar centres (from the level sketch, scaled to the arena); footprint is a 124 px square
PILLARS = [(423, 459), (1377, 459), (423, 1323), (1377, 1323)]
PILLAR_HALF = 62
# low walls block movement but not shots: (x, y, w, h)
LOW_WALLS = [(720, 756, 360, 54), (144, 828, 54, 324), (1602, 828, 54, 324)]
BRAZIERS = [(150, 150), (1650, 150), (150, 1650), (1650, 1650), (655, 62), (1145, 62)]


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
    def __init__(self, assets):
        self.a = assets
        self.solid = [pygame.Rect(cx - PILLAR_HALF, cy - PILLAR_HALF, PILLAR_HALF * 2, PILLAR_HALF * 2)
                      for cx, cy in PILLARS]
        self.shot_blockers = list(self.solid)
        self.solid += [pygame.Rect(*r) for r in LOW_WALLS]
        self.floor = None
        self.gate_open = False
        self.gate_open_t = 0.0
        self.last_normal = None      # direction we were pushed by the last solid (for steering)

    # ------------------------------------------------------------------ baking
    def bake(self):
        a = self.a
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
                tile.fill((v, v, min(255, v + 4)), special_flags=pygame.BLEND_RGB_MULT)
                s.blit(tile, (WALL + gx, WALL + gy))
        s.set_clip(None)

        def W(p):  # world -> baked image coordinates
            return (int(p[0] + WALL), int(p[1] + WALL))

        # gold inlay: inset square and two rings round the sigil
        inset = pygame.Rect(W((170, 170)), (ARENA - 340, ARENA - 340))
        for off, col, w in [(0, GOLD_D, 10), (3, GOLD, 4)]:
            pygame.draw.rect(s, col, inset.inflate(-off * 2, -off * 2), w)
        for cx, cy in [(170, 170), (ARENA - 170, 170), (170, ARENA - 170), (ARENA - 170, ARENA - 170)]:
            pygame.draw.circle(s, GOLD_D, W((cx, cy)), 26)
            pygame.draw.circle(s, GOLD, W((cx, cy)), 20)
            pygame.draw.circle(s, GOLD_D, W((cx, cy)), 9)
        for r, w in [(700, 6), (640, 3)]:
            pygame.draw.circle(s, GOLD_D, W((ARENA // 2, ARENA // 2)), r, w + 3)
            pygame.draw.circle(s, GOLD, W((ARENA // 2, ARENA // 2)), r, w)
        sig = pygame.transform.smoothscale(a.img["sigil"], (900, 900))
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

        # low walls
        for x, y, w, h in LOW_WALLS:
            r = pygame.Rect(W((x, y)), (w, h))
            shadow = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 8, 120), shadow.get_rect().inflate(-6, -6), border_radius=8)
            s.blit(pygame.transform.smoothscale(shadow, (w + 24, h + 24)), (r.x - 6, r.y - 2))
            s.set_clip(r)
            for ty in range(r.top - r.top % 96, r.bottom, 96):
                for tx in range(r.left - r.left % 96, r.right, 96):
                    s.blit(wall, (tx, ty))
            s.set_clip(None)
            pygame.draw.rect(s, GOLD_D, r, 6, border_radius=3)
            pygame.draw.rect(s, GOLD, r.inflate(-6, -6), 2, border_radius=2)
            pygame.draw.line(s, (200, 194, 236), r.topleft, (r.right, r.top), 2)

        # pillars (texture already has a baked drop shadow)
        for cx, cy in PILLARS:
            t = a.img["pillar"]
            s.blit(t, t.get_rect(center=W((cx, cy))))
        # braziers and altar
        for bx, by in BRAZIERS:
            t = a.img["brazier"]
            s.blit(t, t.get_rect(center=W((bx, by))))
        t = a.img["altar"]
        s.blit(t, t.get_rect(center=W(ALTAR_POS)))
        self.floor = s.convert()

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
        for i, (bx, by) in enumerate(BRAZIERS):
            f = 0.82 + 0.18 * math.sin(t * 9.0 + i * 1.7) * math.sin(t * 5.3 + i)
            out.append((bx, by, 330 * f, (255, 168, 78)))
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
        for i, (bx, by) in enumerate(BRAZIERS):
            sx, sy = bx - cam[0], by - cam[1]
            if sx < -80 or sx > screen.get_width() + 80 or sy < -80 or sy > screen.get_height() + 80:
                continue
            f = 0.85 + 0.15 * math.sin(t * 11 + i * 2.1)
            g = a.glow(34 * f, (255, 150, 40))
            screen.blit(g, g.get_rect(center=(sx, sy - 4)), special_flags=pygame.BLEND_RGB_ADD)
            g2 = a.glow(16 * f, (255, 240, 170))
            screen.blit(g2, g2.get_rect(center=(sx + math.sin(t * 7 + i) * 2, sy - 8 - 3 * f)), special_flags=pygame.BLEND_RGB_ADD)
