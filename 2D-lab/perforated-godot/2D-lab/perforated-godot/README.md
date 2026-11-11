# PERFORATED, Level 1 (Pride): Godot 4 port

A Godot 4 (GDScript, 2D) port of the pygame prototype in `../game`. Same arena, same guardians, same balance.

## Open it

1. Godot **4.3 or newer** (4.x is fine; it uses the GL Compatibility renderer).
2. Godot Project Manager, Import, pick `perforated-godot/project.godot`.
3. The first time you open it Godot imports the textures, sounds and font. Wait for that to finish, then press **F5**.

Main scene: `scenes/main.tscn`. The arena (`LevelView`, a `@tool` script), the north gate and the three mini-boss doors are real nodes, so the map shows in the 2D editor without pressing Play (press **F** in the 2D view to frame it, or zoom out). Enemies, lights, effects and the HUD are created by `scripts/game.gd` at runtime.

See `REQUIREMENTS.md` for which file / node implements each course requirement (camera + limits, animation, enemy, lives + restart, bonus).

### Editing the map in the editor

Everything in the main arena that is level design is a node in `scenes/main.tscn`:

- `Obstacles/Pillar01..20`: `Sprite2D` nodes in the group `pillar`. Move one and its collision (a 124 px square) moves with it.
- `Obstacles/LowWall01..12`: nodes with `scripts/low_wall.gd` (group `low_wall`). The position is the top-left corner, the `Size` property in the Inspector sets width and height. They block movement but not shots.
- `PlayerStart`: where the hero spawns (placeholder sprite, hidden in the game).
- `Ferryman`: where the Ferryman stands (placeholder sprite, hidden in the game; the game draws him so he can turn towards you). His lantern light follows this node.
- `Altar`: the altar sprite and its teal light.
- `Gate`, `DoorSouth`, `DoorEast`, `DoorWest`: the exit gate and the three mini-boss doors.
- `Camera2D`: follows the hero; its Limit properties keep the view inside the level.
- `Hero`: Body sprite, AnimationPlayer (idle, run, turn, dash, hurt, die) and a Hurtbox Area2D.
- `Sentries/Sentry01..02`: enemies that patrol their `Waypoints` (Marker2D); touching one is deadly, shooting or dashing through it kills it.
- `Hazards/Hazard01..04`: lethal zones (Area2D). Touching one kills the hero and the level restarts.
- `Braziers`, `HeartSpots`, `SpawnPoints`: positions of the braziers, the heart pickups and the guardian spawn points.

Duplicate a pillar or wall (Ctrl+D) to add more; the game picks up every node in those groups, and the minimap follows. The three mini-boss rooms' own pillars and the braziers are still data in `scripts/rooms.gd` and `scripts/cfg.gd`.
`python 2D-lab/tools/make_godot_scene.py` rewrites `main.tscn` from the original layout, which discards your editor changes.

## Controls

WASD / arrows move, Shift or Space dash, shooting is automatic, ESC or P pause, M music, L language (title screen), F11 fullscreen,
1 / 2 / 3 or the mouse to pick upgrades.

## What is ported

- Hero: momentum movement, dash with i-frames and dash damage, 4 hearts, auto needles.
- Six waves with the same spawn director, pincer groups, swarms, alive caps and elites.
- Guardians: sentinel, skirmisher (telegraphed lunge), lancer (telegraphed spear fans), swarmer, bulwark (enrages), elite (charge, spear nova).
- Pride bar with equal-width wave slices, stage thresholds computed from `STAGE_SECONDS` exactly like `settings.py`.
- Weapons: needle plus the Ferryman's pick of Halo, Pulse and Arc each wave, then stat upgrades bought with box points.
- Boxes and gems (offerings), heart pickups, the gate that opens when the bar is full, title / pause / upgrade / game over / win screens, Macedonian and English.
- Lighting with Godot's own `PointLight2D` + `CanvasModulate`, additive glow and particle layers.

## Mini-boss rooms, more obstacles, minimap (Godot version only)

- **Three doors** in the south, east and west walls open when wave 3, 4 and 5 begin (that is, once wave 2, 3 and 4 are completed). Walk through an open door to enter its room.
- **Rooms** are separate arenas. The guardians of the main arena stay behind, frozen, and never follow you in: a 1v1 fight with a strong mini-boss.
  South: the Warden (charges, spear fans). East: the Spear Master (keeps its distance, spear fans and rings). West: the Lord (charge, fan and ring combo, enrages at half health).
  Each one also throws a ring of spears at 66% and 33% health.
- **Reward:** beating a mini-boss gives an extra stat upgrade (the Ferryman's menu) and two hearts, and opens a portal back to the arena. The door is then sealed.
- **More obstacles:** 11 extra pillars and 5 extra low walls (see `scripts/rooms.gd`), with the door lanes kept clear.
- **Minimap** (bottom right): arena layout, the gate, heart pickups, guardians and you. Each mini-boss door shows as a grey square while locked, a pulsing coloured marker while open, and a green dot once done. Inside a room it shows that room.
- Tunables: room layout, boss stats, door timing and the extra obstacles are in `scripts/rooms.gd`; the boss attacks are in `scripts/entities.gd` (Enemy, kind "miniboss").

## Not ported yet (still only in the pygame version)

The Level 1 boss, the other four weapons (mines, chakram, scatter, seeker), and Levels 2 and 3 (Greed, Lust) with their extra guardians.

## Files

```
project.godot        window 1280x720, stretch canvas_items, GL Compatibility
scenes/main.tscn     the only scene
scripts/game.gd      simulation, spawning, weapons, upgrades, world drawing
scripts/entities.gd  Player, Enemy, Shot, Spear, Box, Gem, particles
scripts/arena.gd     geometry and collision (pillars, low walls, gate, doors, rooms)
scripts/rooms.gd     mini-boss rooms, extra obstacles, texts
scripts/level_view.gd  draws the static arena once
scripts/hud.gd       HUD, menus, overlays
scripts/fx_view.gd   additive glow / particle layers
scripts/util.gd      angle and random helpers
scripts/cfg.gd       GENERATED: balance numbers and layout from game/settings.py + level.py
scripts/tr.gd        GENERATED: Macedonian / English texts from game/strings.py
assets/              textures, sprites, sounds, music, font (copied from ../game/assets)
```

## Keeping it in sync with the pygame balance

`cfg.gd` and `tr.gd` are generated. After changing `game/settings.py`, `game/level.py` or `game/strings.py` run, from the repo root:

```
python 2D-lab/tools/export_to_godot.py
```

and reopen the Godot project.
