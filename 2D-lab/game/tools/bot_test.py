"""Headless autoplay test: python3 tools/bot_test.py [seconds] [screenshot_dir]

Plays Level 1 with a simple kiting bot (no window, no sound) and reports the result,
frame cost and any exception. Screenshots are saved when a folder is given.
"""
import math
import os
import sys
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

import settings as S  # noqa: E402
from game import Game  # noqa: E402


def bot_move(g):
    p = g.player
    mx = my = 0.0
    for e in g.enemies:
        dx, dy = p.x - e.x, p.y - e.y
        d = math.hypot(dx, dy) + 1e-6
        if d < 420:
            w = (420 - d) / 420
            mx += dx / d * w * 2.0
            my += dy / d * w * 2.0
    for sp in g.spears:
        dx, dy = p.x - sp.x, p.y - sp.y
        d = math.hypot(dx, dy) + 1e-6
        if d < 220:
            mx += -sp.vy / 430 * 2.0
            my += sp.vx / 430 * 2.0
    # stay away from walls, drift to the middle
    cx, cy = S.ARENA / 2 - p.x, S.ARENA / 2 - p.y
    dc = math.hypot(cx, cy) + 1e-6
    k = 0.25 + 0.9 * min(1.0, dc / 800)
    mx += cx / dc * k
    my += cy / dc * k
    if g.exit_open:
        mx, my = (S.GATE_X0 + S.GATE_X1) / 2 - p.x, -80 - p.y
    n = math.hypot(mx, my)
    if n > 1:
        mx, my = mx / n, my / n
    return mx, my


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 240
    shots_dir = sys.argv[2] if len(sys.argv) > 2 else None
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
    g = Game(screen)
    if shots_dir:
        os.makedirs(shots_dir, exist_ok=True)
        g.draw(screen)
        pygame.image.save(screen, os.path.join(shots_dir, "00_title.png"))
    g.handle_key(pygame.K_RETURN)
    dt = 1 / 60
    frames = 0
    t_upd = t_draw = 0.0
    worst = 0.0
    shot_times = {20: "01_early", 60: "02_mid", 100: "03_late", 140: "04_late2"}
    saved = set()
    max_enemies = 0
    last_state = None
    while frames * dt < seconds:
        t0 = time.perf_counter()
        if g.state == "upgrade":
            if shots_dir and "upgrade" not in saved:
                g.draw(screen)
                pygame.image.save(screen, os.path.join(shots_dir, "05_upgrade.png"))
                saved.add("upgrade")
            g.handle_key(pygame.K_1 + (frames % 3))
        elif g.state in ("over", "win"):
            break
        move = bot_move(g) if g.state == "play" else (0, 0)
        if g.state == "play":
            near = [e for e in g.enemies if math.hypot(e.x - g.player.x, e.y - g.player.y) < 90]
            if near and g.player.charges > 0 and frames % 5 == 0:
                g.try_dash(move)
        g.update(dt, move)
        t1 = time.perf_counter()
        g.draw(screen)
        t2 = time.perf_counter()
        t_upd += t1 - t0
        t_draw += t2 - t1
        worst = max(worst, t2 - t0)
        max_enemies = max(max_enemies, len(g.enemies))
        frames += 1
        if g.state != last_state:
            print(f"[{g.time:6.1f}s] state -> {g.state}  pride={g.pride:.0f} stage={g.stage} hp={g.player.hp}")
            last_state = g.state
        if shots_dir and g.state == "play":
            onscreen = sum(1 for e in g.enemies if abs(e.x - g.cam[0] - 640) < 640 and abs(e.y - g.cam[1] - 360) < 360)
            key = f"busy_stage{g.stage}"
            if onscreen >= 7 and key not in saved:
                pygame.image.save(screen, os.path.join(shots_dir, key + ".png"))
                saved.add(key)
        sec = int(frames * dt)
        if shots_dir and sec in shot_times and shot_times[sec] not in saved and frames % 60 == 0:
            pygame.image.save(screen, os.path.join(shots_dir, f"{shot_times[sec]}.png"))
            saved.add(shot_times[sec])
    g.draw(screen)
    if shots_dir:
        pygame.image.save(screen, os.path.join(shots_dir, f"99_final_{g.state}.png"))
    print(f"result: state={g.state} time={g.time:.1f}s kills={g.kills} pride={g.pride:.0f}/{S.PRIDE_MAX} "
          f"hp={g.player.hp}/{g.player.max_hp} upgrades={g.upgrades_given} max_enemies={max_enemies}")
    print(f"frames={frames} avg update={t_upd / frames * 1000:.2f} ms  avg draw={t_draw / frames * 1000:.2f} ms  "
          f"worst frame={worst * 1000:.1f} ms")


if __name__ == "__main__":
    main()
