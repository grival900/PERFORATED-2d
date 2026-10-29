"""Headless autoplay test: python tools/bot_test.py [seconds] [screenshot_dir] [--god] [--level 2|3]

Plays Level 1 with a simple kiting bot that also hunts boxes and gems (no window, no sound) and
reports the result, pacing, frame cost and any exception. Screenshots are saved when a folder is given.
--god keeps the hero alive so the pure pacing of the level can be measured.
"""
import math
import os
import random
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


def nearest(items, p, limit):
    best, bd = None, limit * limit
    for it in items:
        d = (it.x - p.x) ** 2 + (it.y - p.y) ** 2
        if d < bd:
            best, bd = it, d
    return best


def bot_move(g):
    p = g.player
    mx = my = 0.0
    threat = 0.0
    for e in g.enemies:
        dx, dy = p.x - e.x, p.y - e.y
        d = math.hypot(dx, dy) + 1e-6
        if d < 380:
            w = (380 - d) / 380
            threat += w
            mx += dx / d * w * 2.0
            my += dy / d * w * 2.0
    for sp in g.spears:                          # sidestep spears that are heading for us
        v = math.hypot(sp.vx, sp.vy) or 1.0
        ux, uy = sp.vx / v, sp.vy / v
        rx, ry = p.x - sp.x, p.y - sp.y
        along, lat = rx * ux + ry * uy, rx * uy - ry * ux
        if 0 < along < 420 and abs(lat) < 70:
            side = 1.0 if lat >= 0 else -1.0
            mx += uy * side * 2.5
            my += -ux * side * 2.5
    for e in g.enemies:                          # and step out of telegraphed lines (lancers, lunges, charges)
        if e.windup > 0 and e.kind in ("lancer", "skirmisher", "elite"):
            rx, ry = p.x - e.x, p.y - e.y
            along, lat = rx * e.cdx + ry * e.cdy, rx * e.cdy - ry * e.cdx
            if 0 < along < 560 and abs(lat) < 80:
                side = 1.0 if lat >= 0 else -1.0
                mx += e.cdy * side * 2.5
                my += -e.cdx * side * 2.5
    # when it is calm enough, go for gems, then boxes
    goal = nearest(g.gems, p, 700) or nearest(g.boxes, p, 1800)
    if goal is not None and threat < 1.4:
        dx, dy = goal.x - p.x, goal.y - p.y
        d = math.hypot(dx, dy) + 1e-6
        k = 1.4 if threat < 0.6 else 0.7
        mx += dx / d * k
        my += dy / d * k
    # stay away from walls, drift to the middle only when nothing else to do
    edge = 220
    if p.x < edge:
        mx += (edge - p.x) / edge * 2
    if p.x > S.ARENA - edge:
        mx -= (p.x - (S.ARENA - edge)) / edge * 2
    if p.y < edge:
        my += (edge - p.y) / edge * 2
    if p.y > S.ARENA - edge:
        my -= (p.y - (S.ARENA - edge)) / edge * 2
    if goal is None:
        cx, cy = S.ARENA / 2 - p.x, S.ARENA / 2 - p.y
        dc = math.hypot(cx, cy) + 1e-6
        mx += cx / dc * 0.5
        my += cy / dc * 0.5
    if g.exit_open:
        mx, my = (S.GATE_X0 + S.GATE_X1) / 2 - p.x, -80 - p.y
    n = math.hypot(mx, my)
    if n > 1:
        mx, my = mx / n, my / n
    return mx, my


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    god = "--god" in sys.argv
    level = int(sys.argv[sys.argv.index("--level") + 1]) if "--level" in sys.argv else 1
    args = [a for a in args if a != str(level) or len(args) > 2]
    seconds = float(args[0]) if args else 420
    shots_dir = args[1] if len(args) > 1 else None
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
    g = Game(screen)
    if shots_dir:
        os.makedirs(shots_dir, exist_ok=True)
        g.draw(screen)
        pygame.image.save(screen, os.path.join(shots_dir, "00_title.png"))
    if level > 1:
        g.begin_level(level, dict(S.DEMO_CARRY_LATE if level == 3 else S.DEMO_CARRY))   # a sample carried-over loadout
    else:
        g.handle_key(pygame.K_RETURN)
    dt = 1 / 60
    frames = 0
    t_upd = t_draw = 0.0
    worst = 0.0
    max_enemies = 0
    last_state = None
    last_stage = 1
    saved = set()
    while frames * dt < seconds:
        t0 = time.perf_counter()
        if g.state == "upgrade":
            if shots_dir and ("menu_" + g.choice_kind) not in saved:
                g.draw(screen)
                pygame.image.save(screen, os.path.join(shots_dir, f"menu_{g.choice_kind}.png"))
                saved.add("menu_" + g.choice_kind)
            g.handle_key(pygame.K_1 + random.randrange(len(g.upgrade_choices)))
        elif g.state in ("over", "win"):
            break
        move = bot_move(g) if g.state == "play" else (0, 0)
        if g.state == "play":
            near = [e for e in g.enemies if math.hypot(e.x - g.player.x, e.y - g.player.y) < 90]
            if near and g.player.charges > 0 and frames % 5 == 0:
                g.try_dash(move)
        if god:
            g.player.invuln = max(g.player.invuln, 0.5)
        g.update(dt, move)
        t1 = time.perf_counter()
        g.draw(screen)
        t2 = time.perf_counter()
        t_upd += t1 - t0
        t_draw += t2 - t1
        worst = max(worst, t2 - t0)
        if t2 - t0 > 0.06:
            print(f"  slow frame {frames}: {(t2 - t0) * 1000:.0f} ms (update {(t1 - t0) * 1000:.0f}, draw {(t2 - t1) * 1000:.0f}) at {g.time:.1f}s")
        max_enemies = max(max_enemies, len(g.enemies))
        frames += 1
        if g.state != last_state or g.stage != last_stage:
            print(f"[{g.time:6.1f}s] state={g.state:8s} wave={g.stage} pride={g.pride:6.0f}/{g.cfg.pride_max} "
                  f"hp={g.player.hp}/{g.player.max_hp} weapons={len(g.player.weapons)} box_pts={g.box_total} "
                  f"stat_ups={g.box_upgrades} enemies={len(g.enemies)}")
            last_state, last_stage = g.state, g.stage
        if shots_dir and g.state == "play":
            onscreen = sum(1 for e in g.enemies if abs(e.x - g.cam[0] - 640) < 640 and abs(e.y - g.cam[1] - 360) < 360)
            key = f"busy_wave{g.stage}"
            if onscreen >= 7 and key not in saved and len(g.player.weapons) >= g.stage - 1:
                pygame.image.save(screen, os.path.join(shots_dir, key + ".png"))
                saved.add(key)
    g.draw(screen)
    if shots_dir:
        pygame.image.save(screen, os.path.join(shots_dir, f"99_final_{g.state}.png"))
    print(f"result: state={g.state} time={g.time:.1f}s kills={g.kills} pride={g.pride:.0f}/{g.cfg.pride_max} "
          f"hp={g.player.hp}/{g.player.max_hp} weapons={list(g.player.weapons)} box_points={g.box_total} "
          f"stat_upgrades={g.box_upgrades} max_enemies={max_enemies}")
    print(f"frames={frames} avg update={t_upd / frames * 1000:.2f} ms  avg draw={t_draw / frames * 1000:.2f} ms  "
          f"worst frame={worst * 1000:.1f} ms")


if __name__ == "__main__":
    main()
