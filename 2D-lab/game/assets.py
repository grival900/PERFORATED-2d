"""Loads images, sounds, fonts and music, and caches rotated sprites."""
import math
import os
import time

import pygame

import settings as S

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

ROT_STEPS = 32


class _NullSound:
    def play(self, *a, **k):
        pass

    def set_volume(self, *a):
        pass


class Assets:
    def __init__(self):
        self.img = {}
        self._rot = {}
        self._glow = {}
        self._font = {}
        self.sounds = {}
        self._last_played = {}
        self.audio_ok = pygame.mixer.get_init() is not None
        self.music_on = True
        self.theme = S.THEMES[1]
        self._raw = {}

    # ---- images -----------------------------------------------------------
    def load_images(self):
        for folder in ("textures", "sprites"):
            path = os.path.join(ROOT, folder)
            for fn in sorted(os.listdir(path)):
                if fn.endswith(".png"):
                    self.img[fn[:-4]] = pygame.image.load(os.path.join(path, fn)).convert_alpha()
        self._raw = dict(self.img)
        self.set_theme(S.THEMES[1])

    def set_theme(self, theme):
        """Rebuild every image for a level: tinted textures/sprites plus the code-drawn props."""
        self.theme = theme
        self.img = dict(self._raw)
        for key, tint in theme["tints"].items():
            for name in list(self.img):
                if name == key or (key == "marble" and name.startswith("marble_")):
                    t = self.img[name].copy()
                    t.fill((*tint, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    self.img[name] = t
        self.make_procedural()
        self._rot = {}
        if self.img.get("glow") is not None and "guardian_swarmer" in self.img:
            self.prewarm()

    # ---- sprites drawn by code (boxes, gems, extra weapons, enemy variants) ----------
    def make_procedural(self):
        img = self.img
        theme = self.theme
        raw = self._raw
        D = pygame.draw

        def surf(w, h):
            return pygame.Surface((w, h), pygame.SRCALPHA)

        # enemy variants: the existing guardians, rescaled and tinted
        def variant(src, scale, tint):
            w, h = src.get_size()
            v = pygame.transform.smoothscale(src, (int(w * scale), int(h * scale)))
            v.fill((*tint, 255), special_flags=pygame.BLEND_RGBA_MULT)
            return v

        img["guardian_swarmer"] = variant(img["guardian_skirmisher"], 0.72, theme.get("swarmer_tint", (255, 165, 185)))
        img["guardian_bulwark"] = variant(img["guardian_sentinel"], 1.45, theme.get("bulwark_tint", (255, 205, 150)))
        img["guardian_bomber"] = variant(raw["guardian_sentinel"], 0.9, (255, 120, 80))
        img["guardian_banker"] = variant(raw["guardian_lancer"], 1.05, (255, 222, 110))
        img["guardian_charmer"] = variant(raw["guardian_sentinel"], 1.15, (255, 110, 210))
        img["guardian_cupid"] = variant(raw["guardian_skirmisher"], 1.0, (255, 215, 235))

        def heart(sf, cx, cy, r, col):
            rr = int(r * 0.52)
            D.circle(sf, col, (int(cx - r * 0.48), int(cy - r * 0.2)), rr)
            D.circle(sf, col, (int(cx + r * 0.48), int(cy - r * 0.2)), rr)
            D.polygon(sf, col, [(cx - r * 0.97, cy - r * 0.05), (cx + r * 0.97, cy - r * 0.05), (cx, cy + r * 0.95)])

        lb = surf(30, 28)
        heart(lb, 15, 14, 14, (120, 10, 60))
        heart(lb, 15, 14, 11, (255, 80, 150))
        D.ellipse(lb, (255, 230, 245), (8, 6, 6, 4))
        img["love_bolt"] = lb

        if theme["style"] == "stone":
            # crate: carved stone with gold bands; gilded crate: solid gold
            for name, body, edge, band, light in (
                    ("box_crate", (146, 138, 184), (38, 32, 66), (236, 196, 92), (190, 182, 224)),
                    ("box_gilded", (232, 184, 74), (96, 62, 18), (255, 236, 160), (255, 244, 196))):
                c = surf(64, 64)
                D.rect(c, (0, 0, 0, 70), (9, 14, 48, 46), border_radius=8)
                D.rect(c, edge, (6, 8, 52, 48), border_radius=7)
                D.rect(c, body, (9, 11, 46, 42), border_radius=5)
                D.rect(c, light, (9, 11, 46, 11), border_radius=5)
                D.rect(c, band, (28, 8, 8, 48))
                D.rect(c, band, (6, 28, 52, 8))
                D.rect(c, edge, (28, 8, 8, 48), 1)
                D.rect(c, edge, (6, 28, 52, 8), 1)
                for cx, cy in ((13, 15), (51, 15), (13, 49), (51, 49)):
                    D.circle(c, edge, (cx, cy), 4)
                    D.circle(c, band, (cx, cy), 3)
                D.polygon(c, edge, [(32, 24), (40, 32), (32, 40), (24, 32)])
                D.polygon(c, band, [(32, 26), (38, 32), (32, 38), (26, 32)])
                img[name] = c

            # gem (box points)
            g = surf(22, 26)
            pts = [(11, 1), (20, 11), (11, 25), (2, 11)]
            D.polygon(g, (20, 110, 100), pts)
            D.polygon(g, (70, 235, 205), [(11, 3), (18, 11), (11, 22), (4, 11)])
            D.polygon(g, (200, 255, 245), [(11, 3), (18, 11), (11, 11)])
            D.polygon(g, (30, 170, 150), [(11, 11), (18, 11), (11, 22)])
            img["gem"] = g

        elif theme["style"] == "money":
            # Greed: cash crates, gold bars and coins
            f = self.font(34, True)
            c = surf(64, 64)
            D.rect(c, (0, 0, 0, 70), (9, 14, 48, 46), border_radius=8)
            D.rect(c, (8, 40, 22), (6, 8, 52, 48), border_radius=7)
            D.rect(c, (36, 130, 76), (9, 11, 46, 42), border_radius=5)
            D.rect(c, (90, 190, 120), (9, 11, 46, 11), border_radius=5)
            for cx, cy in ((13, 15), (51, 15), (13, 49), (51, 49)):
                D.circle(c, (8, 40, 22), (cx, cy), 4)
                D.circle(c, (236, 196, 92), (cx, cy), 3)
            D.rect(c, (8, 40, 22), (6, 26, 52, 12))
            D.rect(c, (236, 196, 92), (8, 28, 48, 8))
            d = f.render("$", True, (10, 60, 30))
            c.blit(d, d.get_rect(center=(32, 33)))
            img["box_crate"] = c
            gb = surf(64, 64)
            D.ellipse(gb, (0, 0, 0, 80), (6, 40, 52, 20))

            def ingot(x, y, w=26, h=14):
                D.polygon(gb, (120, 80, 14), [(x + 3, y), (x + w - 3, y), (x + w, y + h), (x, y + h)])
                D.polygon(gb, (240, 190, 56), [(x + 4, y + 1), (x + w - 4, y + 1), (x + w - 2, y + h - 3), (x + 2, y + h - 3)])
                D.polygon(gb, (255, 238, 150), [(x + 5, y + 2), (x + w - 5, y + 2), (x + w - 6, y + 5), (x + 6, y + 5)])

            ingot(8, 38)
            ingot(30, 38)
            ingot(19, 24)
            ingot(8, 24 + 0)
            ingot(30, 24)
            ingot(19, 10)
            D.circle(gb, (255, 255, 235), (30, 14), 2)
            img["box_gilded"] = gb
            g = surf(24, 24)
            D.circle(g, (120, 80, 10), (12, 12), 11)
            D.circle(g, (250, 200, 60), (12, 12), 10)
            D.circle(g, (190, 135, 20), (12, 12), 7, 2)
            D.circle(g, (255, 242, 160), (9, 9), 3)
            img["gem"] = g
            # the floor emblem and loose decoration
            big = surf(700, 700)
            D.circle(big, (150, 108, 24), (350, 350), 340)
            D.circle(big, (244, 200, 70), (350, 350), 326)
            D.circle(big, (184, 134, 30), (350, 350), 296, 14)
            D.circle(big, (150, 108, 24), (350, 350), 250, 6)
            for i in range(48):
                a_ = i * math.tau / 48
                D.circle(big, (150, 108, 24), (int(350 + math.cos(a_) * 313), int(350 + math.sin(a_) * 313)), 5)
            d = self.font(520, True).render("$", True, (150, 108, 24))
            big.blit(d, d.get_rect(center=(350, 360)))
            img["sigil"] = big
            cn = surf(30, 22)
            D.ellipse(cn, (110, 74, 10), (0, 3, 30, 19))
            D.ellipse(cn, (250, 200, 60), (0, 0, 30, 19))
            D.ellipse(cn, (190, 135, 20), (5, 4, 20, 11), 2)
            img["coin_decor"] = cn
            bl = surf(48, 26)
            D.rect(bl, (10, 60, 30), (0, 0, 48, 26), border_radius=3)
            D.rect(bl, (96, 190, 120), (2, 2, 44, 22), border_radius=2)
            D.ellipse(bl, (40, 130, 70), (14, 4, 20, 18))
            D.ellipse(bl, (200, 240, 210), (18, 7, 12, 12), 2)
            img["bill_decor"] = bl

        else:
            # Lust: velvet gift boxes, heart jewel boxes, heart gems
            c = surf(64, 64)
            D.rect(c, (0, 0, 0, 70), (9, 14, 48, 46), border_radius=8)
            D.rect(c, (60, 6, 28), (6, 8, 52, 48), border_radius=7)
            D.rect(c, (190, 24, 78), (9, 11, 46, 42), border_radius=5)
            D.rect(c, (240, 90, 135), (9, 11, 46, 11), border_radius=5)
            D.rect(c, (255, 214, 120), (28, 8, 8, 48))
            D.rect(c, (255, 214, 120), (6, 28, 52, 8))
            D.ellipse(c, (255, 214, 120), (16, 2, 18, 12))
            D.ellipse(c, (255, 214, 120), (30, 2, 18, 12))
            D.ellipse(c, (200, 150, 50), (16, 2, 18, 12), 2)
            D.ellipse(c, (200, 150, 50), (30, 2, 18, 12), 2)
            D.circle(c, (255, 236, 170), (32, 8), 5)
            img["box_crate"] = c
            gb = surf(64, 64)
            D.ellipse(gb, (0, 0, 0, 80), (8, 46, 48, 14))
            heart(gb, 32, 30, 28, (110, 14, 56))
            heart(gb, 32, 30, 24, (255, 140, 185))
            heart(gb, 30, 26, 14, (255, 190, 215))
            D.rect(gb, (255, 214, 120), (28, 8, 8, 44))
            D.circle(gb, (255, 236, 170), (32, 30), 5)
            D.ellipse(gb, (255, 255, 255), (14, 14, 8, 5))
            img["box_gilded"] = gb
            g = surf(24, 24)
            heart(g, 12, 12, 11, (110, 14, 56))
            heart(g, 12, 12, 9, (255, 90, 150))
            D.ellipse(g, (255, 225, 240), (6, 5, 5, 3))
            img["gem"] = g
            big = surf(700, 700)
            heart(big, 350, 330, 330, (110, 14, 56))
            heart(big, 350, 330, 300, (230, 70, 130))
            heart(big, 350, 320, 220, (255, 130, 175))
            heart(big, 350, 310, 120, (255, 200, 220))
            img["sigil"] = big
            pt = surf(26, 16)
            D.ellipse(pt, (120, 10, 40), (0, 2, 26, 14))
            D.ellipse(pt, (215, 30, 80), (0, 0, 26, 13))
            D.ellipse(pt, (255, 120, 150), (5, 3, 14, 5))
            img["petal_decor"] = pt
            hd = surf(22, 20)
            heart(hd, 11, 10, 10, (255, 130, 175))
            img["heart_decor"] = hd

        # halo orb
        o = surf(34, 34)
        D.circle(o, (140, 96, 30), (17, 17), 16)
        D.circle(o, (244, 204, 96), (17, 17), 14)
        D.circle(o, (255, 244, 200), (17, 17), 9)
        D.circle(o, (255, 255, 255), (15, 14), 4)
        img["orb"] = o

        # seeker: violet homing orb
        k = surf(28, 28)
        D.circle(k, (70, 36, 130), (14, 14), 13)
        D.circle(k, (190, 120, 255), (14, 14), 10)
        D.circle(k, (240, 215, 255), (14, 14), 5)
        img["seeker"] = k

        # scatter pellet (faces right)
        pl = surf(26, 12)
        D.ellipse(pl, (150, 100, 30), (0, 1, 26, 10))
        D.ellipse(pl, (255, 224, 140), (2, 2, 22, 8))
        D.ellipse(pl, (255, 255, 235), (8, 3, 12, 4))
        img["pellet"] = pl

        # chakram (faces up; spins by rotation)
        ch = surf(60, 60)
        for i in range(8):
            a = i * math.tau / 8
            tip = (30 + math.cos(a) * 29, 30 + math.sin(a) * 29)
            l = (30 + math.cos(a - 0.28) * 20, 30 + math.sin(a - 0.28) * 20)
            r = (30 + math.cos(a + 0.28) * 20, 30 + math.sin(a + 0.28) * 20)
            D.polygon(ch, (110, 118, 150), [tip, l, r])
        D.circle(ch, (90, 98, 130), (30, 30), 21)
        D.circle(ch, (214, 222, 246), (30, 30), 19)
        D.circle(ch, (0, 0, 0, 0), (30, 30), 11)
        D.circle(ch, (90, 98, 130), (30, 30), 11, 2)
        img["chakram"] = ch

        # mine
        m = surf(44, 44)
        D.circle(m, (0, 0, 0, 80), (22, 25), 18)
        D.circle(m, (50, 30, 20), (22, 22), 18)
        D.circle(m, (200, 130, 40), (22, 22), 16, 3)
        D.circle(m, (255, 190, 80), (22, 22), 7)
        D.circle(m, (255, 245, 200), (22, 22), 3)
        img["mine"] = m

    def prewarm(self):
        """Build every rotation cache up front so no frame hitches mid-game."""
        for n in ("hero", "guardian_sentinel", "guardian_skirmisher", "guardian_lancer", "guardian_elite",
                  "guardian_swarmer", "guardian_bulwark", "guardian_bomber", "guardian_banker", "guardian_charmer", "guardian_cupid",
                  "ferryman", "chakram"):
            self.rotations(n)
        for n in ("needle", "spear", "pellet"):
            self.rot_right(n)
        for r, c in ((40, (10, 52, 50)), (30, (50, 200, 190)), (46, (30, 150, 140))):
            self.glow(r, c)

    def rotations(self, name):
        """ROT_STEPS pre-rotated copies of a sprite that faces UP."""
        if name not in self._rot:
            src = self.img[name]
            self._rot[name] = [pygame.transform.rotozoom(src, i * 360.0 / ROT_STEPS, 1.0) for i in range(ROT_STEPS)]
        return self._rot[name]

    def rotated(self, name, angle_rad):
        """Sprite facing UP rotated so it faces `angle_rad` (0 = up, clockwise positive)."""
        steps = self.rotations(name)
        idx = int(round(-angle_rad / (2 * math.pi) * ROT_STEPS)) % ROT_STEPS
        return steps[idx]

    def rot_right(self, name):
        """Rotations of a sprite that faces RIGHT (projectiles); index by heading."""
        key = name + "#r"
        if key not in self._rot:
            src = self.img[name]
            self._rot[key] = [pygame.transform.rotozoom(src, -i * 360.0 / ROT_STEPS, 1.0) for i in range(ROT_STEPS)]
        return self._rot[key]

    def heading(self, name, vx, vy):
        steps = self.rot_right(name)
        idx = int(round(math.atan2(vy, vx) / (2 * math.pi) * ROT_STEPS)) % ROT_STEPS
        return steps[idx]

    # ---- glows (used for lighting and additive bloom) ----------------------------
    def glow(self, radius, color):
        """Soft radial glow, RGB = colour * falloff on black, for additive blending."""
        radius = int(max(2, radius))
        key = (radius, color)
        g = self._glow.get(key)
        if g is None:
            base = pygame.transform.smoothscale(self.img["glow"], (radius * 2, radius * 2))
            tinted = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            tinted.blit(base, (0, 0))
            tinted.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            g = pygame.Surface((radius * 2, radius * 2))
            g.fill((0, 0, 0))
            g.blit(tinted, (0, 0))
            self._glow[key] = g
        return g

    # ---- fonts ------------------------------------------------------------------
    def font(self, size, bold=True):
        key = (size, bold)
        if key not in self._font:
            fn = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
            self._font[key] = pygame.font.Font(os.path.join(ROOT, "fonts", fn), size)
        return self._font[key]

    # ---- audio -----------------------------------------------------------------
    def load_sounds(self):
        spec = {
            "shoot": ("laser2", 0.16), "hit": ("hit2", 0.22), "kill": ("hit5", 0.30), "hurt": ("hurt1", 0.85),
            "dash": ("phaseJump1", 0.45), "upgrade_open": ("upgrade2", 0.6), "upgrade_pick": ("upgrade1", 0.7),
            "heart": ("coin3", 0.6), "spear": ("laser4", 0.22), "slam": ("rockHit2", 0.55),
            "gate": ("secret2", 0.8), "over": ("gameover1", 0.8), "win": ("secret4", 0.8),
            "elite": ("error1", 0.45), "points": ("coin1", 0.12),
            "box": ("hit4", 0.45), "gem": ("coin2", 0.14), "weapon": ("upgrade3", 0.7),
            "pulse": ("explosion2", 0.35), "mine_set": ("coin1", 0.2), "mine": ("explosion1", 0.45),
            "arc": ("laser1", 0.2), "chakram": ("jump3", 0.3), "scatter": ("laser3", 0.2), "seeker": ("laser5", 0.16),
        }
        for key, (fn, vol) in spec.items():
            if not self.audio_ok:
                self.sounds[key] = _NullSound()
                continue
            try:
                s = pygame.mixer.Sound(os.path.join(ROOT, "sounds", fn + ".wav"))
                s.set_volume(vol)
                self.sounds[key] = s
            except pygame.error:
                self.sounds[key] = _NullSound()

    def play(self, key, min_gap=0.0):
        """Play a sound, skipping it if the same one played less than min_gap seconds ago."""
        now = time.perf_counter()
        if min_gap and now - self._last_played.get(key, 0.0) < min_gap:
            return
        self._last_played[key] = now
        self.sounds[key].play()

    def start_music(self, volume=0.5):
        if not self.audio_ok:
            return
        try:
            pygame.mixer.music.load(os.path.join(ROOT, "music", "pride_loop.wav"))
            pygame.mixer.music.set_volume(volume if self.music_on else 0.0)
            pygame.mixer.music.play(-1)
        except pygame.error:
            self.audio_ok = False

    def toggle_music(self):
        self.music_on = not self.music_on
        if self.audio_ok:
            pygame.mixer.music.set_volume(0.5 if self.music_on else 0.0)
