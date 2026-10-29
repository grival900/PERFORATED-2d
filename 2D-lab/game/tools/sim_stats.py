"""Balance check without rendering: python tools/sim_stats.py [runs] [--god] [--level 2|3] [--demo]

Plays many full runs with the kiting bot from bot_test (no drawing, so each run takes seconds) and
prints how far it got: outcome, time, wave reached, weapons and upgrades. Use it to tune pacing.
"""
import math
import os
import random
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pygame  # noqa: E402

import settings as S  # noqa: E402
from bot_test import bot_move  # noqa: E402
from game import Game  # noqa: E402


def play(g, god, limit=900.0):
    dt = 1 / 60
    frames = 0
    while g.time < limit and g.state not in ("over", "win"):
        if g.state == "upgrade":
            g.handle_key(pygame.K_1 + random.randrange(len(g.upgrade_choices)))
        move = bot_move(g) if g.state == "play" else (0, 0)
        if g.state == "play" and g.player.charges > 0 and frames % 5 == 0:
            if any(math.hypot(e.x - g.player.x, e.y - g.player.y) < 90 for e in g.enemies):
                g.try_dash(move)
        if god:
            g.player.invuln = max(g.player.invuln, 0.5)
        g.update(dt, move)
        frames += 1
    return g


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    level = int(sys.argv[sys.argv.index("--level") + 1]) if "--level" in sys.argv else 1
    args = [a for a in args if not (a in ("2", "3") and "--level" in sys.argv and a == sys.argv[sys.argv.index("--level") + 1] and len(args) > 1)]
    runs = int(args[0]) if args else 6
    god = "--god" in sys.argv
    pygame.init()
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
    g = Game(screen)
    times, wins, total_hits = [], 0, []
    for i in range(runs):
        random.seed(1000 + i)
        carry = dict(S.DEMO_CARRY_LATE if level == 3 else S.DEMO_CARRY) if (level > 1 or "--demo" in sys.argv) else None
        g.begin_level(level, carry)
        hits = [0]
        orig = g.hurt_player

        def counted(dx, dy, orig=orig, hits=hits):
            hits[0] += 1
            orig(dx, dy)
        g.hurt_player = counted
        play(g, god)
        g.hurt_player = orig
        wins += g.state == "win"
        times.append(g.time)
        print(f"run {i}: {g.state:4s} t={g.time:6.1f}s wave={g.stage} pride={g.pride:5.0f}/{g.cfg.pride_max} "
              f"weapons={len(g.player.weapons)} stat_ups={g.box_upgrades} kills={g.kills} hits_taken={hits[0]}")
        total_hits.append(hits[0])
    print(f"wins {wins}/{runs}, mean time {sum(times) / len(times):.0f}s, mean hits taken {sum(total_hits) / len(total_hits):.1f}")


if __name__ == "__main__":
    main()
