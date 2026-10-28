"""Loads images, sounds, fonts and music, and caches rotated sprites."""
import math
import os
import time

import pygame

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

    # ---- images -----------------------------------------------------------
    def load_images(self):
        for folder in ("textures", "sprites"):
            path = os.path.join(ROOT, folder)
            for fn in sorted(os.listdir(path)):
                if fn.endswith(".png"):
                    self.img[fn[:-4]] = pygame.image.load(os.path.join(path, fn)).convert_alpha()

    def prewarm(self):
        """Build every rotation cache up front so no frame hitches mid-game."""
        for n in ("hero", "guardian_sentinel", "guardian_skirmisher", "guardian_lancer", "guardian_elite", "ferryman"):
            self.rotations(n)
        for n in ("needle", "spear"):
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
