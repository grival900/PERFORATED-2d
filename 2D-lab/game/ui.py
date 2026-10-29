"""HUD, menus and overlays."""
import math

import pygame

import settings as S
import strings
import weapons as W
from level import MINIMAP as LEVEL_MINIMAP
from strings import t, tl

GOLD = (244, 204, 96)
WHITE = (240, 246, 255)
DIM = (150, 164, 188)
TEAL = (63, 245, 224)


def text(screen, assets, s, size, pos, color=WHITE, anchor="topleft", bold=True, shadow=True, alpha=255):
    f = assets.font(size, bold)
    surf = f.render(s, True, color)
    rect = surf.get_rect(**{anchor: pos})
    if shadow:
        sh = f.render(s, True, (4, 4, 12))
        if alpha < 255:
            sh.set_alpha(alpha)
        screen.blit(sh, rect.move(2, 2))
    if alpha < 255:
        surf.set_alpha(alpha)
    screen.blit(surf, rect)
    return rect


def panel(screen, rect, color=(10, 10, 22), alpha=190, radius=14, border=None, width=2):
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(s, border, s.get_rect(), width, border_radius=radius)
    screen.blit(s, rect.topleft)


class UI:
    def __init__(self, assets):
        self.a = assets
        self._bar = None

    # ---- Pride bar ---------------------------------------------------------
    def _bar_gradient(self, w, h):
        if self._bar is None or self._bar.get_size() != (w, h):
            s = pygame.Surface((w, h))
            for x in range(w):
                k = x / w
                c = (int(214 + 41 * k), int(158 + 90 * k), int(52 + 150 * k))
                pygame.draw.line(s, c, (x, 0), (x, h))
            hl = pygame.Surface((w, h // 2), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 60))
            s.blit(hl, (0, 0))
            self._bar = s
        return self._bar

    def draw_pride_bar(self, screen, g):
        a = self.a
        w, h = 560, 28
        x, y = (S.SCREEN_W - w) // 2, 50
        frac = min(1.0, g.bar_frac(g.pride_shown))
        panel(screen, pygame.Rect(x - 8, y - 8, w + 16, h + 16), (8, 8, 18), 200, 12, (140, 100, 36), 3)
        inner = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, (24, 22, 40), inner, border_radius=6)
        fw = int(w * frac)
        if fw > 2:
            grad = self._bar_gradient(w, h)
            screen.blit(grad, (x, y), pygame.Rect(0, 0, fw, h))
            sh = ((g.time * 0.45) % 1.4 - 0.2) * w                      # moving shimmer
            if 0 < sh < fw:
                glow = a.glow(26, (120, 110, 70))
                screen.blit(glow, glow.get_rect(center=(x + sh, y + h // 2)), special_flags=pygame.BLEND_RGB_ADD)
            if g.bar_pulse > 0:
                glow = a.glow(30, (120, 100, 50))
                screen.blit(glow, glow.get_rect(center=(x + fw, y + h // 2)), special_flags=pygame.BLEND_RGB_ADD)
        for i in range(1, g.cfg.num_stages):          # one tick per wave; each unlocks a weapon
            mark = i / g.cfg.num_stages
            mx = x + int(w * mark)
            done = frac >= mark
            pygame.draw.line(screen, (255, 244, 200) if done else (110, 100, 150), (mx, y - 4), (mx, y + h + 4), 2)
            col = GOLD if done else (90, 84, 130)
            pygame.draw.polygon(screen, col, [(mx, y + h + 6), (mx + 6, y + h + 13), (mx, y + h + 20), (mx - 6, y + h + 13)])
        pygame.draw.rect(screen, (200, 160, 70), inner, 2, border_radius=6)
        text(screen, a, f"{tl('pride', g.level_no)}  {int(frac * 100)}%", 17, (x, y - 12), WHITE, "bottomleft")
        text(screen, a, t("stage").format(n=g.stage) + ": " + tl("stage_desc", g.level_no)[g.stage], 15, (x + w, y - 12), DIM,
             "bottomright", bold=False)

    # ---- hearts + dash --------------------------------------------------------
    def draw_hearts(self, screen, g):
        a = self.a
        p = g.player
        full, empty = a.img["heart_full"], a.img["heart_empty"]
        for i in range(p.max_hp):
            img = full if i < p.hp else empty
            scale = 1.0
            if i < p.hp and p.hp == 1:
                scale = 1.0 + 0.12 * math.sin(g.time * 9)
            if scale != 1.0:
                img = pygame.transform.rotozoom(img, 0, scale)
            screen.blit(img, img.get_rect(center=(48 + i * 50, 48)))
        pip_full, pip_empty = a.img["dash_full"], a.img["dash_empty"]
        for i in range(p.charge_cap):
            cx, cy = 40 + i * 40, 96
            if i < p.charges:
                screen.blit(pip_full, pip_full.get_rect(center=(cx, cy)))
            else:
                screen.blit(pip_empty, pip_empty.get_rect(center=(cx, cy)))
                if i == p.charges:
                    frac = p.recharge_t / p.recharge
                    clip = pygame.Rect(0, 0, int(pip_full.get_width() * frac), pip_full.get_height())
                    screen.blit(pip_full, pip_full.get_rect(center=(cx, cy)).topleft, clip)

    # ---- offerings (box points) bar -------------------------------------------------
    def draw_offerings_bar(self, screen, g):
        a = self.a
        w, h = 360, 14
        x, y = (S.SCREEN_W - w) // 2, 124
        cost = S.upgrade_cost(g.box_upgrades)
        frac = min(1.0, g.box_pts / cost)
        panel(screen, pygame.Rect(x - 6, y - 6, w + 12, h + 12), (8, 8, 18), 190, 9, (40, 120, 110), 2)
        pygame.draw.rect(screen, (16, 28, 36), (x, y, w, h), border_radius=4)
        if frac > 0:
            pygame.draw.rect(screen, g.theme["bar"], (x, y, max(4, int(w * frac)), h), border_radius=4)
            pygame.draw.rect(screen, (190, 255, 240), (x, y, max(4, int(w * frac)), h // 3), border_radius=4)
        if g.box_pulse > 0:
            glow = a.glow(24, (30, 110, 95))
            screen.blit(glow, glow.get_rect(center=(x + int(w * frac), y + h // 2)), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.rect(screen, (60, 190, 170), (x, y, w, h), 2, border_radius=4)
        text(screen, a, f"{tl('offerings', g.level_no)}  {g.box_pts}/{cost}", 14, (x, y - 8), (170, 245, 230), "bottomleft")

    def draw_weapons(self, screen, g):
        a = self.a
        names = t("weapons")
        x, y = 24, S.SCREEN_H - 24
        for wid in reversed(list(g.player.weapons)):
            col = W.COLORS[wid]
            label = names[wid][0]
            f = a.font(15, True)
            wd = f.size(label)[0] + 36
            rect = pygame.Rect(x, y - 28, wd, 28)
            panel(screen, rect, (8, 8, 18), 205, 8, col, 2)
            pygame.draw.circle(screen, col, (rect.x + 14, rect.centery), 6)
            text(screen, a, label, 15, (rect.x + 28, rect.centery), WHITE, "midleft", shadow=False)
            y -= 34

    def draw_minimap(self, screen, g):
        size = LEVEL_MINIMAP
        x0, y0 = S.SCREEN_W - size - 20, S.SCREEN_H - size - 20
        panel(screen, pygame.Rect(x0 - 5, y0 - 5, size + 10, size + 10), (8, 8, 18), 215, 8, (110, 100, 150), 2)
        screen.blit(g.level.minimap, (x0, y0))
        k = size / S.ARENA

        def pt(x, y):
            return int(x0 + max(0, min(S.ARENA, x)) * k), int(y0 + max(0, min(S.ARENA, y)) * k)

        for b in g.boxes:
            pygame.draw.rect(screen, (255, 220, 110) if b.gilded else (80, 230, 205), (*pt(b.x, b.y), 3, 3))
        for e in g.enemies:
            pygame.draw.rect(screen, (235, 70, 80) if e.kind != "elite" else (255, 150, 60), (*pt(e.x, e.y), 2, 2))
        gx, gy = pt((S.GATE_X0 + S.GATE_X1) / 2, 0)
        pygame.draw.rect(screen, (255, 232, 140) if g.exit_open else (150, 120, 60), (gx - 6, gy, 12, 4))
        px, py = pt(g.player.x, g.player.y)
        pygame.draw.circle(screen, (255, 255, 255), (px, py), 4)
        pygame.draw.circle(screen, (60, 245, 224), (px, py), 4, 1)
        # view frame
        vx, vy = pt(g.cam[0], g.cam[1])
        pygame.draw.rect(screen, (200, 200, 230), (vx, vy, int(S.SCREEN_W * k), int(S.SCREEN_H * k)), 1)

    def draw_hud(self, screen, g):
        a = self.a
        self.draw_pride_bar(screen, g)
        self.draw_offerings_bar(screen, g)
        self.draw_hearts(screen, g)
        self.draw_weapons(screen, g)
        self.draw_minimap(screen, g)
        mins, secs = divmod(int(g.time), 60)
        text(screen, a, f"{t('kills')}: {g.kills}", 18, (S.SCREEN_W - 24, 20), WHITE, "topright")
        text(screen, a, f"{mins}:{secs:02d}", 18, (S.SCREEN_W - 24, 46), DIM, "topright", bold=False)
        # stage banner
        if g.banner_t > 0:
            k = min(1.0, g.banner_t / 0.5, (2.8 - g.banner_t) / 0.4 if g.banner_t > 2.4 else 1.0)
            alpha = int(255 * max(0.0, min(1.0, k)))
            text(screen, a, g.banner_text, 32, (S.SCREEN_W // 2, 200), GOLD, "center", alpha=alpha)
        if g.time < 18 and g.box_total == 0 and g.banner_t <= 0:
            text(screen, a, tl("hint_boxes", g.level_no), 24, (S.SCREEN_W // 2, 200), (170, 245, 230), "center",
                 alpha=int(255 * (0.6 + 0.4 * math.sin(g.time * 4))))
        # exit hint
        if g.exit_open and not g.over:
            pulse = 0.6 + 0.4 * math.sin(g.time * 5)
            text(screen, a, t("exit_open"), 26, (S.SCREEN_W // 2, 240), (255, 236, 160), "center",
                 alpha=int(255 * pulse))
            gx = (S.GATE_X0 + S.GATE_X1) / 2 - g.cam[0]
            gy = 0 - g.cam[1]
            if not (0 <= gx <= S.SCREEN_W and 0 <= gy <= S.SCREEN_H):
                cx, cy = S.SCREEN_W / 2, S.SCREEN_H / 2
                ang = math.atan2(gy - cy, gx - cx)
                px = max(40, min(S.SCREEN_W - 40, cx + math.cos(ang) * 600))
                py = max(40, min(S.SCREEN_H - 40, cy + math.sin(ang) * 600))
                pts = [(px + math.cos(ang) * 22, py + math.sin(ang) * 22),
                       (px + math.cos(ang + 2.5) * 18, py + math.sin(ang + 2.5) * 18),
                       (px + math.cos(ang - 2.5) * 18, py + math.sin(ang - 2.5) * 18)]
                pygame.draw.polygon(screen, (255, 232, 140), pts)
        if g.red_flash > 0:
            fl = pygame.Surface((S.SCREEN_W, S.SCREEN_H), pygame.SRCALPHA)
            fl.fill((200, 20, 40, int(110 * g.red_flash / 0.3)))
            screen.blit(fl, (0, 0))

    # ---- overlays ----------------------------------------------------------------
    def dim(self, screen, alpha=170):
        o = pygame.Surface((S.SCREEN_W, S.SCREEN_H), pygame.SRCALPHA)
        o.fill((4, 4, 12, alpha))
        screen.blit(o, (0, 0))

    def draw_title(self, screen, g):
        a = self.a
        self.dim(screen, 120)
        cx = S.SCREEN_W // 2
        glow = a.glow(330, (120, 90, 30))
        screen.blit(glow, glow.get_rect(center=(cx, 190)), special_flags=pygame.BLEND_RGB_ADD)
        big = a.font(118)
        for off, col in [(6, (6, 6, 14)), (0, (250, 236, 190))]:
            surf = big.render(t("title"), True, col)
            screen.blit(surf, surf.get_rect(center=(cx + off, 180 + off)))
        text(screen, a, t("subtitle"), 36, (cx, 268), GOLD, "center")
        text(screen, a, t("tagline"), 20, (cx, 312), DIM, "center", bold=False)
        panel(screen, pygame.Rect(cx - 300, 350, 600, 200), (8, 8, 20), 180, 14, (90, 80, 130), 2)
        for i, line in enumerate(t("controls")):
            text(screen, a, line, 20, (cx, 376 + i * 36), WHITE, "center", bold=False)
        blink = 0.55 + 0.45 * math.sin(g.clock * 4)
        text(screen, a, t("press_enter"), 30, (cx, 610), (255, 244, 200), "center", alpha=int(255 * blink))
        text(screen, a, "[L] MK / EN", 16, (S.SCREEN_W - 20, S.SCREEN_H - 14), DIM, "bottomright", bold=False)
        text(screen, a, t("f2_hint") + "     " + t("f3_hint"), 16, (20, S.SCREEN_H - 14), DIM, "bottomleft", bold=False)

    def draw_pause(self, screen, g):
        self.dim(screen, 170)
        cx, cy = S.SCREEN_W // 2, S.SCREEN_H // 2
        text(screen, self.a, t("paused"), 64, (cx, cy - 40), WHITE, "center")
        text(screen, self.a, t("pause_help"), 22, (cx, cy + 30), DIM, "center", bold=False)

    def upgrade_rects(self, n=3):
        w, h, gap = 310, 250, 28
        total = w * n + gap * (n - 1)
        x0 = (S.SCREEN_W - total) // 2 + 70
        return [pygame.Rect(x0 + i * (w + gap), 250, w, h) for i in range(n)]

    def draw_upgrade(self, screen, g):
        a = self.a
        self.dim(screen, 190)
        cx = S.SCREEN_W // 2
        weapon = g.choice_kind == "weapon"
        text(screen, a, t("weapon_title") if weapon else tl("upgrade_title", g.level_no), 38, (cx, 96),
             (170, 245, 230) if not weapon else GOLD, "center")
        text(screen, a, t("ferryman_line"), 20, (cx, 142), DIM, "center", bold=False)
        fm = pygame.transform.rotozoom(a.img["ferryman"], 0, 1.35)
        screen.blit(fm, fm.get_rect(center=(112, 380)))
        glow = a.glow(80, (30, 200, 190))
        screen.blit(glow, glow.get_rect(center=(112, 340)), special_flags=pygame.BLEND_RGB_ADD)
        names = t("weapons") if weapon else t("upgrades")
        for i, (rect, uid) in enumerate(zip(self.upgrade_rects(len(g.upgrade_choices)), g.upgrade_choices)):
            sel = (i == g.upgrade_sel)
            rr = rect.inflate(16, 16) if sel else rect
            accent = W.COLORS[uid] if weapon else GOLD
            panel(screen, rr, (14, 14, 30), 235, 16, accent if sel else (90, 80, 130), 4 if sel else 2)
            text(screen, a, str(i + 1), 54, (rr.centerx, rr.top + 54), accent if sel else DIM, "center")
            if weapon:
                pygame.draw.circle(screen, accent, (rr.centerx, rr.top + 96), 7)
            name, desc = names[uid]
            text(screen, a, name, 25, (rr.centerx, rr.top + 124), WHITE, "center")
            # wrap description
            words, lines, cur = desc.split(), [], ""
            f = a.font(18, False)
            for wd in words:
                trial = (cur + " " + wd).strip()
                if f.size(trial)[0] > rr.w - 36:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            lines.append(cur)
            for j, ln in enumerate(lines):
                text(screen, a, ln, 18, (rr.centerx, rr.top + 168 + j * 26), DIM, "center", bold=False)
        text(screen, a, t("upgrade_hint"), 20, (cx, 560), DIM, "center", bold=False)

    def draw_end(self, screen, g, won):
        a = self.a
        self.dim(screen, 190)
        cx, cy = S.SCREEN_W // 2, S.SCREEN_H // 2
        col = GOLD if won else (230, 90, 100)
        text(screen, a, tl("victory", g.level_no) if won else t("game_over"), 66, (cx, cy - 150), col, "center")
        text(screen, a, tl("victory_sub", g.level_no) if won else t("game_over_sub"), 22, (cx, cy - 90), DIM, "center", bold=False)
        mins, secs = divmod(int(g.time), 60)
        panel(screen, pygame.Rect(cx - 230, cy - 60, 460, 170), (8, 8, 20), 190, 14, (90, 80, 130), 2)
        text(screen, a, f"{t('kills')}: {g.kills}", 26, (cx, cy - 32), WHITE, "center")
        text(screen, a, f"{t('time')}: {mins}:{secs:02d}", 26, (cx, cy + 2), WHITE, "center")
        text(screen, a, f"{t('hearts')}: {g.player.hp}/{g.player.max_hp}", 26, (cx, cy + 36), WHITE, "center")
        text(screen, a, f"{tl('offerings', g.level_no)}: {g.box_total}", 26, (cx, cy + 70), (170, 245, 230), "center")
        blink = 0.6 + 0.4 * math.sin(g.clock * 4)
        text(screen, a, (t("next_level").format(name=tl("level_name", g.level_no + 1)) if not g.final_level else tl("again", g.level_no)) if won else t("retry"), 22, (cx, cy + 160), (255, 244, 200), "center",
             alpha=int(255 * blink))
