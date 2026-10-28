# PERFORATED: Level 1 (Pride)

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
| (automatic) | the hero fires piercing needles at the nearest guardian |
| 1 / 2 / 3, arrows + ENTER, or mouse | pick an upgrade |
| ESC or P | pause (R restarts, Q quits) |
| M | music on/off |
| L | language, on the title screen (Macedonian / English) |
| F11 | fullscreen |

## The level

Kill holy guardians to earn points that fill the **Pride bar**. At 25 %, 50 % and 75 % the Ferryman offers a choice of three upgrades.
The bar has four difficulty stages:

1. few slow sentinels
2. faster groups with skirmishers
3. lancers that telegraph and throw light spears
4. a swarm plus elite guardians that telegraph a charge

When the bar is full every guardian dissolves and the gate in the north wall opens. Walk into it to win. Lose all hearts and you dissolve.
Heart pickups sit in two corners (they respawn); elites drop a heart.

## Files

```
main.py        entry point and event loop
game.py        state machine, combat, spawning, upgrades, rendering
entities.py    Player, Enemy (4 kinds), Shot, Spear, HeartPickup
level.py       the arena: bakes the floor, collision, lights
ui.py          HUD, menus
fx.py          particles, floating text, afterimages
assets.py      loading, rotated sprite cache, glows, sound helper
settings.py    every tunable number (speeds, cooldowns, stages, spawn points)
strings.py     Macedonian and English texts
assets/        textures, sprites, sounds, music, fonts (see CREDITS.txt)
tools/         asset generators and tests
```

## Tests (no window or sound needed)

```
python tools/menu_test.py          # 27 checks: menus, dash, shooting, damage, upgrades, gate, win/lose, restart
python tools/bot_test.py 240 shots # a bot plays the level; saves screenshots into ./shots
```

## Regenerating the art and music

The textures and sprites are drawn by code (marble, stone, pillars, sigil, gate, hero, guardians, hearts...) and the music is synthesised:

```
pip install numpy Pillow
python tools/gen_assets.py
python tools/gen_music.py
```

Swap any PNG in `assets/textures` or `assets/sprites` for your own art with the same file name and size and the game uses it.
