# PERFORATED: Pride, Greed and Lust

Top-down survivor-style game (Vampire Survivors-like) in Python + pygame, made for Lab 1, Task 8.

## Run

```
pip install pygame-ce        (plain `pygame` works too)
python main.py
```

Or just double-click `run_game.bat` (installs pygame-ce if missing, then starts the game).
To build a standalone `dist\PERFORATED.exe` (no Python needed to play it), double-click `build_exe.bat`.

Needs Python 3.9+ and a desktop with a display. Run it from this folder or anywhere (`python path/to/game/main.py`).

## Controls

| Key | Action |
|---|---|
| WASD / arrows | move (with a little momentum) |
| SHIFT or SPACE | dash: 2 charges, 3 s recharge each, brief invulnerability, the dash damages guardians it passes through |
| (automatic) | every weapon you own fires by itself at the nearest guardian |
| walk over boxes | breaks them; the gems they drop fly to you |
| 1 / 2 / 3, arrows + ENTER, or mouse | pick a weapon or an upgrade |
| ESC or P | pause (R restarts, Q quits) |
| M | music on/off |
| L | language, on the title screen (Macedonian / English) |
| F11 | fullscreen |
| F2 / F3 (title screen) | jump straight to Level 2 / Level 3 with a sample loadout (for testing) |

## The level

A 3000 x 3000 arena with pillars and low walls, a minimap in the corner, and a run of about **5 minutes**.

**Pride points (enemies).** Killing holy guardians fills the **Pride bar**. The bar has six waves; every new wave unlocks a weapon
(the Ferryman offers a choice of three, so every run ends up with a different combination):

| Wave | What comes | Notes |
|---|---|---|
| 1 | sentinels | they lead your movement and swing wide to surround you |
| 2 | + skirmishers | telegraph, then lunge |
| 3 | + lancers, swarmer packs | lancers throw telegraphed light spears; swarmers are fast and come in packs of 6-9 |
| 4 | + bulwarks, first elite | bulwarks are tanky and speed up when hurt; elites charge and throw a ring of spears at half health |
| 5 | pincer | groups split and arrive from both sides, lancers throw three spears at once |
| 6 | final onslaught | the biggest swarm and two elites |

When the bar is full the gate in the north wall opens. **The guardians stay** (no more are spawned, and they are worth nothing),
so you have to fight or dash your way to the gate. Lose all hearts and you dissolve. Heart pickups sit in four corners (they respawn); elites drop a heart.

**Box points (offerings).** Crates lie around the arena in clusters (gilded ones are worth three times as much) and slowly restock out of view.
Walking or dashing over one breaks it and it drops gems; collect them to fill the **Offerings** bar. Each time it fills, the next stat upgrade
(more projectiles, faster cooldowns, piercing, damage, reach, dash, speed, heart) is offered, and each one costs more than the last.
Box points and Pride points are separate: guardians never give box points and boxes never fill the Pride bar.

**Weapons** (all automatic, all affected by every stat upgrade):

| Weapon | What it does |
|---|---|
| Needles (start) | piercing shots at the nearest guardian |
| Halo Orbs | orbs circle you, cut what they touch and break thrown spears |
| Pride Pulse | a periodic shockwave: damage, knock-back, erases spears |
| Lightning | leaps from guardian to guardian |
| Sigil Mines | dropped behind you, explode when a guardian gets close |
| Chakram | a bladed ring that flies out, pierces everything and comes back |
| Scatter | a close-range fan of slivers |
| Seekers | homing orbs |

## Level 2: Greed

Win Level 1 and press ENTER: the next level is a green bank vault (checkerboard marble, vault safes, teller counters, coins and banknotes on the floor,
cash crates and gold-bar stacks instead of stone crates, coins instead of gems, emerald braziers).

**Everything you earned carries over**: every weapon, the damage / cooldown / reach / piercing / extra-projectile upgrades, speed, dash charges and max hearts
(you start the level with full hearts). Box points and the Pride bar start from zero. Once you own all eight weapons, a new wave gives a free stat upgrade instead.
Dying retries Level 2 with the loadout you entered it with (R in the pause menu does the same); winning it ends the game and ENTER starts over at Level 1.

**The guardians are far harder**: about 2x health, faster, about twice as many alive at once, spawning faster, with new types from the first waves:

| Enemy | Behaviour |
|---|---|
| Bomber | runs at you, plants itself and lights a fuse; a red circle shows the blast, step out of it (a Pulse can knock it away) |
| Banker | keeps its distance and fires a burst of three coin spears, each aimed where you are at that moment |
| Lancers | throw three spears at once from wave 3 (wave 5 in Level 1) |
| Swarmers | packs of 8-12 |
| Elites | up to four per wave late on; they throw a ring of spears at 75 %, 50 % and 25 % health |

## Level 3: Lust

Win Level 2 and press ENTER. A rose-and-velvet boudoir: pink marble with petals and little hearts scattered on it, a big heart emblem on the floor,
a ring of columns with curtains between them, magenta flames, red gift boxes (heart-shaped jewel boxes are the gilded ones) and heart gems.

Same rules as Level 2: **everything you earned carries over** (all weapons, every stat upgrade, speed, dashes, max hearts; full hearts at the start),
dying retries the level with the loadout you entered it with, and the guardians are stronger still: about 4x health, 25 % faster, up to 130 alive at once
and spawning more than twice as fast as Level 2. Winning Level 3 ends the game.

| New enemy | Behaviour |
|---|---|
| Charmer | telegraphs a pink ring, then drags you towards her for a second; **dash to break free** (at most 3 alive) |
| Cupid | keeps its distance and fires slow homing hearts that curve after you; outrun them, shoot them down, or let a Halo or Pulse erase them |

Bombers, bankers and everything from Level 2 are mixed in too, lancers fan three spears from wave 2, and elites throw spear rings at 80, 60, 40 and 20 % health.

Everything above is tuned in `settings.py`. The bar size and the wave thresholds are derived from `STAGE_SECONDS` and the spawn tables,
so changing a spawn rate or a duration re-balances the whole level.

## Files

```
main.py        entry point and event loop
game.py        state machine, levels and carry-over, combat, spawning, waves, boxes, upgrades, rendering
weapons.py     the eight weapons and what they leave behind (waves, mines, chakrams, bolts)
entities.py    Player, Enemy (10 kinds), Shot, Spear, Box, Gem, Mine, Chakram, HeartPickup
level.py       the arena: bakes the floor and minimap, collision, lights, prop placement
ui.py          HUD, menus
fx.py          particles, floating text, afterimages
assets.py      loading, rotated sprite cache, glows, sound helper
settings.py    every tunable number (speeds, cooldowns, waves, per-level configs and themes)
strings.py     Macedonian and English texts
assets/        textures, sprites, sounds, music, fonts (see CREDITS.txt)
tools/         asset generators, tests and balance simulation
```

## Tests (no window or sound needed)

```
python tools/menu_test.py          # 100 checks: menus, dash, boxes and gems, waves and weapons, gate, win/lose, restart
python tools/bot_test.py 330 shots # a bot plays the level; saves screenshots into ./shots (add --god to keep it alive)
python tools/sim_stats.py 10       # many full runs without drawing: how far the bot gets (--god: how long a full run takes)
python tools/sim_stats.py 10 --level 3   # the same for Level 2 or 3 (the bot starts with a sample carried-over loadout; --demo gives one to Level 1 too)
```

## Regenerating the art and music

The textures and sprites are drawn by code (marble, stone, pillars, sigil, gate, hero, guardians, hearts...) and the music is synthesised:

```
pip install numpy Pillow
python tools/gen_assets.py
python tools/gen_music.py
```

Swap any PNG in `assets/textures` or `assets/sprites` for your own art with the same file name and size and the game uses it.
