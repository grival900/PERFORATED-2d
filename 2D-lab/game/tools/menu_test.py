"""Headless check of menus, input handling and a few rules: python3 tools/menu_test.py"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

import settings as S  # noqa: E402
import strings  # noqa: E402
from entities import Enemy  # noqa: E402
from game import Game  # noqa: E402

pygame.init()
screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
g = Game(screen)
K = pygame
dt = 1 / 60
ok = []


def check(name, cond):
    ok.append(cond)
    print(("PASS " if cond else "FAIL ") + name)


check("starts on title", g.state == "title")
g.handle_key(K.K_l)
check("L toggles language", strings.LANG == "en")
g.handle_key(K.K_l)
check("L toggles back", strings.LANG == "mk")
g.handle_key(K.K_RETURN)
check("ENTER starts play", g.state == "play")
for _ in range(30):
    g.update(dt, (1, 0))
check("player moves right", g.player.x > S.PLAYER_START[0] + 20)
g.handle_key(K.K_ESCAPE)
check("ESC pauses", g.state == "pause")
t0 = g.time
g.update(dt, (1, 0))
check("time frozen while paused", g.time == t0)
g.handle_key(K.K_ESCAPE)
check("ESC resumes", g.state == "play")
# dash: uses a charge, gives i-frames, recharges after DASH_RECHARGE
c0 = g.player.charges
g.handle_key(K.K_LSHIFT)
check("dash spends a charge", g.player.charges == c0 - 1 and g.player.dashing)
check("dash grants i-frames", g.player.invuln >= S.DASH_IFRAMES - 0.01)
for _ in range(int(S.DASH_RECHARGE * 60) + 5):
    g.update(dt, (0, 0))
check("charge recharges", g.player.charges == c0)
# shooting kills a sentinel in range and fills the bar
g.enemies.clear()
e = Enemy("sentinel", g.player.x + 200, g.player.y)
e.spawn_t = 0
g.enemies.append(e)
p0 = g.pride
for _ in range(120):
    g.update(dt, (0, 0))
check("auto-fire kills the guardian", e.hp <= 0 and g.kills >= 1)
check("kill fills the Pride bar by its points", g.pride >= p0 + S.ENEMIES["sentinel"]["pts"])
# contact damage and invulnerability
g.enemies.clear()
e = Enemy("sentinel", g.player.x + 5, g.player.y)
e.spawn_t = 0
g.enemies.append(e)
g.player.invuln = 0
hp0 = g.player.hp
g.update(dt, (0, 0))
check("touching a guardian costs a heart", g.player.hp == hp0 - 1)
g.update(dt, (0, 0))
check("hit gives invulnerability (no double hit)", g.player.hp == hp0 - 1)
# upgrade at 25%
g.enemies.clear()
g.player.hp = g.player.max_hp
g.add_pride(S.PRIDE_MAX * 0.25 - g.pride + 1)
g.update(dt, (0, 0))
check("25% opens the upgrade menu", g.state == "upgrade" and len(g.upgrade_choices) == 3)
shots_before = g.player.shots
first = g.upgrade_choices[0]
rects = g.ui.upgrade_rects()
g.handle_mouse(rects[0].center, True)
check("mouse click picks an upgrade", g.state == "play")
check("stage advanced to 2", g.stage == 2)
# 50% and 75% each give exactly one more upgrade
for frac in (0.5, 0.75):
    g.add_pride(S.PRIDE_MAX * frac - g.pride + 1)
    g.update(dt, (0, 0))
    check(f"{int(frac * 100)}% opens upgrade menu", g.state == "upgrade")
    g.handle_key(K.K_1)
check("three upgrades total, then none", g.upgrades_given == 3 and g.pending_upgrades == 0)
# full bar opens the gate and clears the arena
g.enemies.append(Enemy("sentinel", 100, 100))
g.add_pride(S.PRIDE_MAX)
check("full bar opens exit and clears enemies", g.exit_open and g.level.gate_open and not g.enemies)
g.player.x, g.player.y = 900, 40
for _ in range(60):
    g.update(dt, (0, -1))
check("walking into the gate wins", g.state == "win")
g.handle_key(K.K_RETURN)
check("ENTER restarts after win", g.state == "play" and g.pride == 0 and not g.exit_open)
# death
g.player.hp = 1
g.player.invuln = 0
e = Enemy("sentinel", g.player.x + 5, g.player.y)
e.spawn_t = 0
g.enemies.append(e)
for _ in range(120):
    g.update(dt, (0, 0))
check("losing all hearts ends the run", g.state == "over")
g.handle_key(K.K_RETURN)
check("ENTER restarts after game over", g.state == "play" and g.player.hp == S.PLAYER_MAX_HP)
check("Q in pause quits", (g.handle_key(K.K_ESCAPE), g.handle_key(K.K_q))[1] == "quit")
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
