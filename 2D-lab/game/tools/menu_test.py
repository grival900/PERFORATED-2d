"""Headless check of menus, input handling and the game rules: python tools/menu_test.py"""
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
import weapons as W  # noqa: E402
from entities import Box, Enemy, Gem  # noqa: E402
from game import Game  # noqa: E402

pygame.init()
screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
g = Game(screen)
K = pygame
dt = 1 / 60
ok = []


def check(name, cond):
    ok.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def calm(g):
    """Remove everything that could hurt the hero so a rule can be checked in isolation."""
    g.enemies.clear()
    g.spears.clear()
    g.spawn_t = 999
    g.player.hp = g.player.max_hp


def foe(kind, dx, dy, hp=None):
    e = Enemy(kind, g.player.x + dx, g.player.y + dy)
    e.spawn_t = 0
    if hp is not None:
        e.hp = e.max_hp = hp
    g.enemies.append(e)
    return e


check("starts on title", g.state == "title")
g.handle_key(K.K_l)
check("L toggles language", strings.LANG == "en")
g.handle_key(K.K_l)
check("L toggles back", strings.LANG == "mk")
g.handle_key(K.K_RETURN)
check("ENTER starts play", g.state == "play")
check("arena is bigger than the old 1800", S.ARENA >= 2800 and g.level.floor.get_width() == S.ARENA + 2 * S.WALL)
check("level starts with plenty of boxes", len(g.boxes) >= 45)
check("starts with only the needle", list(g.player.weapons) == ["needle"])
g.boxes.clear()       # random starting crates must not interfere with the box-point checks below
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

# ---- dash --------------------------------------------------------------------------
calm(g)
c0 = g.player.charges
g.handle_key(K.K_LSHIFT)
check("dash spends a charge", g.player.charges == c0 - 1 and g.player.dashing)
check("dash grants i-frames", g.player.invuln >= S.DASH_IFRAMES - 0.01)
for _ in range(int(S.DASH_RECHARGE * 60) + 5):
    calm(g)
    g.update(dt, (0, 0))
check("charge recharges", g.player.charges == c0)

# ---- shooting and Pride points ----------------------------------------------------------
calm(g)
e = foe("sentinel", 200, 0)
p0 = g.pride
for _ in range(240):
    g.update(dt, (0, 0))
    if e.hp <= 0:
        break
check("auto-fire kills the guardian", e.hp <= 0 and g.kills >= 1)
check("kill fills the Pride bar by its points", g.pride >= p0 + S.ENEMIES["sentinel"]["pts"])
check("killing guardians gives no box points", g.box_total == 0)

# ---- contact damage -------------------------------------------------------------------
calm(g)
foe("sentinel", 5, 0)
g.player.invuln = 0
hp0 = g.player.hp
g.update(dt, (0, 0))
check("touching a guardian costs a heart", g.player.hp == hp0 - 1)
g.update(dt, (0, 0))
check("hit gives invulnerability (no double hit)", g.player.hp == hp0 - 1)

# ---- boxes and box points ------------------------------------------------------------------
calm(g)
g.boxes = [Box(g.player.x, g.player.y, False)]
g.update(dt, (0, 0))
check("walking over a box breaks it", not g.boxes)
n_gems = len(g.gems)
check("a broken box drops gems worth 12 box points", n_gems == len(S.BOX_CRATE_GEMS) and sum(x.val for x in g.gems) == 12)
for _ in range(120):
    calm(g)
    g.update(dt, (0, 0))
check("gems fly to the hero and are collected", not g.gems and g.box_total == 12 and g.box_pts == 12)
check("box points are separate from Pride points", g.pride >= 0 and g.box_total == 12)
# spend: enough box points opens a stat menu
calm(g)
g.gems.append(Gem(g.player.x, g.player.y, S.upgrade_cost(0)))
for _ in range(30):
    g.update(dt, (0, 0))
check("enough box points opens a stat upgrade menu", g.state == "upgrade" and g.choice_kind == "stat"
      and len(g.upgrade_choices) == 3)
rates = g.player.rate_mult
dmg = g.player.dmg_mult
bonus = g.player.bonus
g.upgrade_choices = ["rate", "power", "multi"]
g.handle_key(K.K_1)
check("picking rate speeds up weapons", g.state == "play" and g.player.rate_mult < rates)
g.queue.append("stat")
g.update(dt, (0, 0))
g.upgrade_choices = ["power", "rate", "multi"]
g.handle_key(K.K_1)
check("picking power raises damage", g.player.dmg_mult > dmg)
g.queue.append("stat")
g.update(dt, (0, 0))
g.upgrade_choices = ["multi", "rate", "power"]
g.handle_key(K.K_1)
check("picking multi adds a bonus projectile", g.player.bonus == bonus + 1)
check("upgrade cost grows", S.upgrade_cost(3) > S.upgrade_cost(0))
# restock
g.boxes = []
g.box_timer = 0
calm(g)
g.update(dt, (0, 0))
check("boxes restock", len(g.boxes) == 1 and all(
    (b.x - g.player.x) ** 2 + (b.y - g.player.y) ** 2 > S.BOX_RESPAWN_MIN_DIST ** 2 for b in g.boxes))
# the dash also breaks boxes
g.boxes = [Box(g.player.x + 70, g.player.y, True)]
calm(g)
g.player.charges = 1
g.player.dash_t = 0
g.try_dash((1, 0))
for _ in range(14):
    g.update(dt, (1, 0))
check("dashing through a gilded box breaks it for 36 points", not g.boxes and sum(x.val for x in g.gems) >= 36)

# ---- waves unlock weapons ---------------------------------------------------------------------
check("six waves, ~3 min if you kill every spawn (about 5 in practice)", S.NUM_STAGES == 6 and 150 <= sum(S.STAGE_SECONDS) <= 260)
g.gems.clear()
for n, thr in enumerate(S.STAGE_AT_PTS, start=2):
    calm(g)
    g.add_pride(thr - g.pride + 1)
    g.update(dt, (0, 0))
    check(f"wave {n} opens the weapon menu", g.state == "upgrade" and g.choice_kind == "weapon" and g.stage == n)
    pick = g.upgrade_choices[0]
    before = len(g.player.weapons)
    rects = g.ui.upgrade_rects(len(g.upgrade_choices))
    g.handle_mouse(rects[0].center, True)
    check(f"wave {n}: mouse click unlocks {pick}", g.state == "play" and pick in g.player.weapons
          and len(g.player.weapons) == before + 1)
check("five unlocks plus the needle make six weapons", len(g.player.weapons) == 6)
check("elites are queued for the late waves", g.pending_elites + g.elites >= 3)

# ---- every weapon works --------------------------------------------------------------------
fails = []
for wid in W.UNLOCKABLE:
    g.reset()
    g.state = "play"
    g.player.weapons = {wid: W.WEAPONS[wid]()}
    g.player.invuln = 999
    calm(g)
    victims = [foe("sentinel", 120, 0, 8), foe("sentinel", 150, 40, 8), foe("sentinel", 110, -60, 8)]
    start = sum(v.hp for v in victims)
    for _ in range(360):
        calm_hp = g.player.hp
        g.spawn_t = 999
        g.update(dt, (0, 0))
        g.player.hp = calm_hp
    left = sum(max(0, v.hp) for v in victims)
    if not left < start:
        fails.append(wid)
check("every unlockable weapon damages guardians (" + ", ".join(W.UNLOCKABLE) + ")", not fails)
if fails:
    print("   no damage from:", fails)

# stat bonuses reach weapons: more orbs, more mines, longer arcs
g.reset()
g.state = "play"
g.player.bonus = 2
g.player.weapons = {"halo": W.Halo()}
g.update(dt, (0, 0))
check("multi adds halo orbs", len(g.player.weapons["halo"].orbs) == S.HALO_ORBS + 2)

# ---- full bar: the gate opens and guardians STAY ---------------------------------------------
g.reset()
g.state = "play"
g.player.invuln = 999
for _ in range(S.NUM_STAGES - 1):
    g.queue.clear()
    g.add_pride(S.PRIDE_MAX / 40)
g.queue.clear()
calm(g)
for i in range(4):
    foe("sentinel", 400 + i * 40, 300)
n_before = len(g.enemies)
g.add_pride(S.PRIDE_MAX)
g.queue.clear()       # a jump straight to a full bar would queue every weapon menu
g.update(dt, (0, 0))
check("full bar opens the gate", g.exit_open and g.level.gate_open)
check("guardians stay when the gate opens", len(g.enemies) >= n_before - 1 and len(g.enemies) > 0)
for _ in range(120):
    g.update(dt, (0, 0))
    g.player.invuln = 999
check("no new guardians spawn after the gate opens", len(g.enemies) <= n_before)
pride_before = g.pride
k0 = g.kills
victim = foe("sentinel", 90, 0, 1)
for _ in range(120):
    g.update(dt, (0, 0))
    g.player.invuln = 999
check("kills after the gate opens still count but add no pride", g.kills > k0 and g.pride == pride_before)
g.player.x, g.player.y = (S.GATE_X0 + S.GATE_X1) / 2, 60
g.player.invuln = 999
for _ in range(90):
    g.update(dt, (0, -1))
check("walking into the gate wins (guardians still alive)", g.state == "win")
# ---- Level 1 -> Level 2: the hero keeps everything -------------------------------------------------
g.player.weapons = {k: W.WEAPONS[k]() for k in ("needle", "halo", "arc")}
g.player.dmg_mult, g.player.rate_mult, g.player.bonus, g.player.area = 1.5, 0.8, 2, 1.4
g.player.max_hp, g.player.hp, g.player.charge_cap = 5, 1, 3
l1_solid = len(g.level.solid)
g.handle_key(K.K_RETURN)
check("winning Level 1 and pressing ENTER starts Level 2", g.state == "play" and g.level_no == 2 and g.cfg.num == 2)
check("Level 2 has its own green look and layout", g.assets.theme is S.THEMES[2] and len(g.level.solid) != l1_solid
      and g.level.theme["style"] == "money")
check("weapons carry over", list(g.player.weapons) == ["needle", "halo", "arc"])
check("stat upgrades carry over", g.player.dmg_mult == 1.5 and g.player.rate_mult == 0.8 and g.player.bonus == 2
      and g.player.area == 1.4 and g.player.charge_cap == 3)
check("hearts carry over and are refilled", g.player.max_hp == 5 and g.player.hp == 5)
check("the new level starts clean", g.pride == 0 and not g.exit_open and not g.level.gate_open and g.stage == 1
      and g.kills == 0 and len(g.boxes) >= 45)
check("Level 2 enemies are far tougher and faster than Level 1",
      g.cfg.hp_mult >= 1.5 and g.cfg.speed_mult > 1 and g.cfg.stages[1]["cap"] > S.STAGES[1]["cap"] * 1.5
      and g.cfg.stages[1]["interval"] < S.STAGES[1]["interval"])
g.enemies.clear()
g.spawn_enemy("sentinel", g.player.x + 500, g.player.y)
check("a Level 2 sentinel has much more health than a Level 1 one", g.enemies[0].max_hp >= S.ENEMIES["sentinel"]["hp"] * 1.6)
g.handle_key(K.K_ESCAPE)
g.handle_key(K.K_r)
check("R restarts Level 2 with the loadout it was entered with", g.level_no == 2 and list(g.player.weapons) == ["needle", "halo", "arc"]
      and g.player.dmg_mult == 1.5)

# ---- enemies: new kinds behave --------------------------------------------------------------
calm(g)
g.player.invuln = 999
sw = foe("swarmer", 400, 0)
d0 = abs(sw.x - g.player.x)
for _ in range(30):
    g.update(dt, (0, 0))
    g.player.invuln = 999
check("swarmers run at the hero", abs(sw.x - g.player.x) < d0 - 40)
calm(g)
sk = foe("skirmisher", 240, 0, 99)
lunged = False
for _ in range(240):
    g.update(dt, (0, 0))
    g.player.invuln = 999
    lunged = lunged or sk.charge_t > 0
check("skirmishers telegraph and lunge", lunged)
calm(g)
bw = foe("bulwark", 300, 0, 100)
check("bulwarks are tough", bw.max_hp >= 10 and S.ENEMIES["bulwark"]["pts"] > S.ENEMIES["sentinel"]["pts"])
check("enemies are faster than before", S.ENEMIES["sentinel"]["speed"] > 88 and S.ENEMIES["skirmisher"]["speed"] > 175)

# ---- level 2 enemies ---------------------------------------------------------------------------
g.begin_level(2, dict(S.DEMO_CARRY))
check("F2-style demo loadout works", len(g.player.weapons) == 5 and g.player.max_hp == 5)
calm(g)
g.player.weapons = {}          # a Pulse would knock the bomber out of its own blast: test the bomb alone
g.player.invuln = 0
bm = foe("bomber", 400, 0, 50)
bm.t = 0
hp0 = g.player.hp
for _ in range(200):
    g.update(dt, (0, 0))
    if bm.windup > 0:
        break
check("a bomber lights its fuse when it gets close", bm.windup > 0 or bm.hp <= 0)
for _ in range(100):
    g.update(dt, (0, 0))
    if bm.hp <= 0:
        break
check("the bomber blows up and hurts a hero standing in the blast", bm.hp <= 0 and g.player.hp < hp0)
calm(g)
g.player.invuln = 0
bm = foe("bomber", 60, 0, 50)
bm.windup = bm.windup_max = S.BOMBER_FUSE
g.player.x, g.player.y = bm.x + 600, bm.y            # step out of the blast
g.player.vx = g.player.vy = 0
hp0 = g.player.hp
for _ in range(60):
    g.update(dt, (0, 0))
    g.player.x, g.player.y = bm.x + 600, bm.y
check("stepping away from the red circle avoids the blast", g.player.hp == hp0)
calm(g)
g.player.weapons = {}
bk = foe("banker", 380, 0, 999)
seen = 0
for _ in range(300):
    g.update(dt, (0, 0))
    g.player.invuln = 999
    seen = max(seen, len(g.spears))
    if seen >= S.BANKER_BURST:
        break
check("a banker fires a burst of coin spears", seen >= 2)
calm(g)
g.player.weapons = {}
el = foe("elite", 300, 0)
el.hp = el.max_hp * 0.2
g.player.invuln = 999
for _ in range(10):
    g.update(dt, (0, 0))
check("Level 2 elites throw a spear ring at several health marks", el.nova_i == len(g.cfg.nova_marks) and len(g.spears) >= g.cfg.nova_spears)
for k in S.LEVELS[2].stages[6]["weights"]:
    check(f"level 2 wave 6 can spawn {k}", S.LEVELS[2].stages[6]["weights"][k] > 0 and k in S.ENEMIES)
# every weapon owned: a wave gives a free upgrade instead of an empty weapon menu
g.reset()
g.player.weapons = {k: W.WEAPONS[k]() for k in W.WEAPONS}
g.state = "play"
g.queue.append("weapon")
g.update(dt, (0, 0))
check("with every weapon owned a wave offers a free stat upgrade", g.state == "upgrade" and g.choice_kind == "stat")
g.handle_key(K.K_1)
# the whole level 2 flow: win -> run restarts at level 1; lose -> retry level 2
g.begin_level(2, dict(S.DEMO_CARRY))
g.player.invuln = 999
g.add_pride(g.cfg.pride_max)
g.queue.clear()
g.update(dt, (0, 0))
check("full bar opens the gate in Level 2 too", g.exit_open and g.level.gate_open)
g.player.x, g.player.y = (S.GATE_X0 + S.GATE_X1) / 2, 60
for _ in range(90):
    g.update(dt, (0, -1))
    g.player.invuln = 999
check("winning Level 2 is not the end: Level 3 follows", g.state == "win" and not g.final_level)
g.player.dmg_mult, g.player.bonus = 2.2, 3
carried = list(g.player.weapons)
g.handle_key(K.K_RETURN)
check("ENTER after Level 2 starts Level 3 (Lust) with everything carried over",
      g.level_no == 3 and g.assets.theme is S.THEMES[3] and list(g.player.weapons) == carried
      and g.player.dmg_mult == 2.2 and g.player.bonus == 3 and g.player.hp == g.player.max_hp)
check("Level 3 is tougher than Level 2: health, speed, numbers, spawn rate",
      S.LEVELS[3].hp_mult > S.LEVELS[2].hp_mult and S.LEVELS[3].speed_mult > S.LEVELS[2].speed_mult
      and S.LEVELS[3].stages[6]["cap"] > S.LEVELS[2].stages[6]["cap"]
      and S.LEVELS[3].stages[6]["interval"] < S.LEVELS[2].stages[6]["interval"]
      and S.LEVELS[3].stages[1]["cap"] > S.LEVELS[2].stages[1]["cap"])
g.add_pride(g.cfg.pride_max)
g.queue.clear()
g.player.invuln = 999
g.update(dt, (0, 0))
g.player.x, g.player.y = (S.GATE_X0 + S.GATE_X1) / 2, 60
for _ in range(90):
    g.update(dt, (0, -1))
    g.player.invuln = 999
check("winning Level 3 is the final win", g.state == "win" and g.final_level)
g.handle_key(K.K_RETURN)
check("ENTER after the final win starts over at Level 1", g.level_no == 1 and g.assets.theme is S.THEMES[1]
      and list(g.player.weapons) == ["needle"])
g.begin_level(2, dict(S.DEMO_CARRY))
g.player.hp = 1
g.player.invuln = 0
g.spawn_t = 999
foe("sentinel", 5, 0)
for _ in range(120):
    g.update(dt, (0, 0))
check("dying in Level 2 ends the run", g.state == "over")
g.handle_key(K.K_RETURN)
check("ENTER after dying retries Level 2 with the same loadout", g.state == "play" and g.level_no == 2
      and len(g.player.weapons) == 5 and g.player.hp == 5)
g.start()
check("start() always begins a fresh Level 1", g.level_no == 1 and g.carry is None)
g.state = "title"
g.handle_key(K.K_F2)
check("F2 on the title screen jumps to Level 2", g.state == "play" and g.level_no == 2)
g.start()

# ---- level 3 (Lust) ---------------------------------------------------------------------------------
g.state = "title"
g.handle_key(K.K_F3)
check("F3 on the title screen jumps to Level 3 with a late-game loadout", g.state == "play" and g.level_no == 3
      and len(g.player.weapons) == 8 and g.level.theme["style"] == "lust")
check("Level 3 has its own layout", len(g.level.solid) != len(g.levels[2].solid) or g.level.pillars != g.levels[2].pillars)
calm(g)
g.player.weapons = {}
g.player.invuln = 999
ch = foe("charmer", 380, 0, 999)
x0 = g.player.x
for _ in range(240):
    g.update(dt, (0, 0))
    g.player.invuln = 999
    if ch.charm_t > 0:
        break
check("a charmer casts a charm spell after a telegraph", ch.charm_t > 0)
x1 = g.player.x
for _ in range(40):
    g.update(dt, (0, 0))
    g.player.invuln = 999
check("the charm drags the hero towards her", g.player.x > x1 + 40 or ch.charm_t <= 0 and g.player.x > x0 + 20)
calm(g)
g.player.weapons = {}
g.player.invuln = 999
ch = foe("charmer", 380, 0, 999)
ch.charm_t = S.CHARM_TIME
g.player.charges = 2
g.try_dash((-1, 0))
g.update(dt, (-1, 0))
check("dashing breaks the charm", ch.charm_t == 0.0)
calm(g)
g.player.weapons = {}
cu = foe("cupid", 420, 0, 999)
for _ in range(300):
    g.update(dt, (0, 0))
    g.player.invuln = 999
    if any(sp.homing for sp in g.spears):
        break
check("a cupid fires slow homing hearts", sum(1 for sp in g.spears if sp.homing) >= 1)
hearts = [sp for sp in g.spears if sp.homing]
g.player.invuln = 999
speed = (hearts[0].vx ** 2 + hearts[0].vy ** 2) ** 0.5
check("hearts are slower than the hero", speed < S.PLAYER_SPEED)
heart = hearts[0]
g.spears = [heart]
heart.x, heart.y, heart.vx, heart.vy = g.player.x + 300, g.player.y + 300, 0.0, S.HEART_SPEED
import math as _m


def heading_error(sp):
    want = _m.atan2(g.player.y - sp.y, g.player.x - sp.x)
    return abs((_m.atan2(sp.vy, sp.vx) - want + _m.pi) % _m.tau - _m.pi)


err0 = heading_error(heart)
for _ in range(30):
    g.update(dt, (0, 0))
    g.player.invuln = 999
    g.spears = [sp for sp in g.spears if sp.homing] or g.spears
check("the heart curves towards the hero", heading_error(heart) < err0 - 0.3)
# the director never stacks charmers or ranged kinds beyond their caps
g.begin_level(3, dict(S.DEMO_CARRY_LATE))
g.player.invuln = 999
g.pending_elites = 0
for _ in range(1500):
    g.update(dt, (0, 0))
    g.player.invuln = 999
    g.player.hp = g.player.max_hp
    g.pending_elites = 0
check("charmers stay within their cap", sum(1 for e in g.enemies if e.kind == "charmer") <= S.CHARMER_CAP)
check("ranged guardians stay within the cap", sum(1 for e in g.enemies if e.kind in S.RANGED_KINDS) <= g.cfg.lancer_cap)
g.start()

# ---- death ------------------------------------------------------------------------------------
g.reset()
g.state = "play"
g.player.hp = 1
g.player.invuln = 0
g.spawn_t = 999
foe("sentinel", 5, 0)
for _ in range(120):
    g.update(dt, (0, 0))
check("losing all hearts ends the run", g.state == "over")
g.handle_key(K.K_RETURN)
check("ENTER restarts after game over", g.state == "play" and g.player.hp == S.PLAYER_MAX_HP)
check("Q in pause quits", (g.handle_key(K.K_ESCAPE), g.handle_key(K.K_q))[1] == "quit")
# draw every state once, both languages, to catch rendering errors
for lang in ("mk", "en"):
    strings.LANG = lang
    g.reset()
    g.player.weapons = {k: W.WEAPONS[k]() for k in W.WEAPONS}
    g.enemies = [Enemy(k, g.player.x + 100 + i * 50, g.player.y + 60) for i, k in enumerate(S.ENEMIES)]
    g.mines.append(__import__("entities").Mine(g.player.x - 80, g.player.y, 3, 100))
    g.update(dt, (0, 0))
    g.draw(screen)
    for lvl in (1, 2, 3):
        g.begin_level(lvl, None if lvl == 1 else dict(S.DEMO_CARRY_LATE if lvl == 3 else S.DEMO_CARRY))
        g.enemies = [Enemy(k, g.player.x + 100 + i * 50, g.player.y + 60) for i, k in enumerate(S.ENEMIES)]
        g.enemies[-1].windup = g.enemies[-1].windup_max = 0.5
        g.enemies[-2].charm_t = 0.5
        g.update(dt, (0, 0))
        g.draw(screen)
        for kind in ("weapon", "stat"):
            g.open_menu(kind)
            g.draw(screen)
            g.state = "play"
        for st in ("pause", "over", "win", "title"):
            g.state = st
            g.draw(screen)
check("all screens render in both languages", True)
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
