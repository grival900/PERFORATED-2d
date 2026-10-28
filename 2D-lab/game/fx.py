"""Particles, floating texts and afterimages."""
import math
import random

import pygame


class Particles:
    def __init__(self, assets):
        self.a = assets
        self.items = []          # [kind, x, y, vx, vy, life, max_life, color, size, extra]
        self._text_cache = {}

    # ---- spawning ---------------------------------------------------------
    def burst(self, x, y, color, n=10, speed=240.0, life=0.5, size=7):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.35, 1.0) * speed
            self.items.append(["spark", x, y, math.cos(a) * sp, math.sin(a) * sp, life * random.uniform(0.6, 1.0),
                               life, color, size * random.uniform(0.6, 1.1), None])

    def diamonds(self, x, y, n=8, speed=300.0, life=0.7):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.3, 1.0) * speed
            self.items.append(["diamond", x, y, math.cos(a) * sp, math.sin(a) * sp, life * random.uniform(0.7, 1.0),
                               life, random.choice([(244, 204, 96), (255, 244, 190), (255, 255, 255)]),
                               random.uniform(5, 9), random.uniform(0, math.tau)])

    def ring(self, x, y, color, radius=120.0, life=0.4, width=4):
        self.items.append(["ring", x, y, 0, 0, life, life, color, radius, width])

    def text(self, x, y, s, color=(255, 232, 150), size=22, life=0.8):
        self.items.append(["text", x, y, 0, -60.0, life, life, color, size, s])

    def afterimage(self, x, y, surf, life=0.22):
        self.items.append(["ghost", x, y, 0, 0, life, life, (255, 255, 255), 0, surf])

    # ---- update / draw ------------------------------------------------------
    def update(self, dt):
        keep = []
        for p in self.items:
            p[5] -= dt
            if p[5] <= 0:
                continue
            p[1] += p[3] * dt
            p[2] += p[4] * dt
            if p[0] in ("spark", "diamond"):
                drag = 1.0 - min(1.0, 4.0 * dt)
                p[3] *= drag
                p[4] *= drag
            keep.append(p)
        self.items = keep
        if len(self.items) > 900:
            self.items = self.items[-900:]

    def _text_surf(self, s, size, color):
        key = (s, size, color)
        surf = self._text_cache.get(key)
        if surf is None:
            surf = self.a.font(size).render(s, True, color)
            if len(self._text_cache) > 200:
                self._text_cache.clear()
            self._text_cache[key] = surf
        return surf

    def draw(self, screen, cam):
        w, h = screen.get_size()
        for kind, x, y, vx, vy, life, max_life, color, size, extra in self.items:
            sx, sy = x - cam[0], y - cam[1]
            if sx < -100 or sx > w + 100 or sy < -100 or sy > h + 100:
                continue
            k = life / max_life
            if kind == "spark":
                g = self.a.glow(max(3, size * (0.4 + 0.6 * k) * 1.6), tuple(int(c * k) for c in color))
                screen.blit(g, g.get_rect(center=(sx, sy)), special_flags=pygame.BLEND_RGB_ADD)
            elif kind == "diamond":
                s = size * (0.3 + 0.7 * k)
                a = extra + life * 8
                ca, sa = math.cos(a), math.sin(a)

                def rot(px, py):
                    return (sx + px * ca - py * sa, sy + px * sa + py * ca)

                pts = [rot(0, -s), rot(s * 0.55, 0), rot(0, s), rot(-s * 0.55, 0)]
                pygame.draw.polygon(screen, color, pts)
            elif kind == "ring":
                r = size * (1 - k) + 6
                col = tuple(int(c * k) for c in color)
                # additive ring: draw on a small temp surface
                rr = int(r) + extra + 2
                tmp = pygame.Surface((rr * 2, rr * 2))
                pygame.draw.circle(tmp, col, (rr, rr), int(r), max(1, int(extra * k) + 1))
                screen.blit(tmp, (sx - rr, sy - rr), special_flags=pygame.BLEND_RGB_ADD)
            elif kind == "text":
                surf = self._text_surf(extra, int(size), color)
                surf = surf.copy()
                surf.set_alpha(int(255 * min(1.0, k * 2)))
                screen.blit(surf, surf.get_rect(center=(sx, sy)))
            elif kind == "ghost":
                g = extra.copy()
                g.set_alpha(int(150 * k))
                screen.blit(g, g.get_rect(center=(sx, sy)))
