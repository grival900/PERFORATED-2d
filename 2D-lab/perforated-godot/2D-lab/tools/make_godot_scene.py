"""Writes perforated-godot/scenes/main.tscn with every main-arena obstacle, the gate, the doors,
the altar, the Ferryman and the player start as real nodes.

Run from the repo root:  python 2D-lab/tools/make_godot_scene.py
Only needed to reset the scene to the pygame layout: it overwrites main.tscn, so any edits you made
to the nodes in the Godot editor are lost.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "game"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import level as L  # noqa: E402

PILLARS = list(L.LAYOUTS[1]["pillars"]) + [
    (900, 1750), (2100, 1750), (1000, 2750), (2000, 2750), (1500, 950), (400, 2000), (2600, 2000),
    (1250, 2100), (1750, 2100), (700, 1150), (2200, 1250)]
WALLS = list(L.LAYOUTS[1]["low_walls"]) + [
    (600, 1950, 400, 54), (1996, 1950, 400, 54), (1473, 560, 54, 220), (700, 2560, 54, 300), (2246, 2560, 54, 300)]

out = ['''[gd_scene load_steps=9 format=3]

[ext_resource type="Script" path="res://scripts/game.gd" id="1"]
[ext_resource type="Script" path="res://scripts/level_view.gd" id="2"]
[ext_resource type="Texture2D" path="res://assets/textures/gate_closed.png" id="3"]
[ext_resource type="Texture2D" path="res://assets/textures/pillar.png" id="4"]
[ext_resource type="Script" path="res://scripts/low_wall.gd" id="5"]
[ext_resource type="Texture2D" path="res://assets/textures/altar.png" id="6"]
[ext_resource type="Texture2D" path="res://assets/sprites/ferryman.png" id="7"]
[ext_resource type="Texture2D" path="res://assets/sprites/hero.png" id="8"]

[node name="Game" type="Node2D"]
script = ExtResource("1")

[node name="LevelView" type="Node2D" parent="."]
z_index = -10
script = ExtResource("2")
''']


def sprite(name, pos, tex, z, rot=None, parent=".", groups=None):
    g = f' groups=["{groups}"]' if groups else ""
    s = f'\n[node name="{name}" type="Sprite2D" parent="{parent}"{g}]\nz_index = {z}\nposition = Vector2({pos[0]}, {pos[1]})\n'
    if rot is not None:
        s += f"rotation = {rot}\n"
    return s + f'texture = ExtResource("{tex}")\n'


out.append(sprite("Gate", (1500, -65), 3, -5))
out.append(sprite("DoorSouth", (1500, 3065), 3, -5, 3.14159))
out.append(sprite("DoorEast", (3065, 1500), 3, -5, 1.5708))
out.append(sprite("DoorWest", (-65, 1500), 3, -5, -1.5708))
out.append(sprite("Altar", (2520, 1050), 6, -9))
out.append(sprite("Ferryman", (2450, 1062), 7, -4))
out.append(sprite("PlayerStart", (1500, 1860), 8, -4))
out.append('\n[node name="Obstacles" type="Node2D" parent="."]\n')
for i, (x, y) in enumerate(PILLARS, 1):
    out.append(sprite(f"Pillar{i:02d}", (x, y), 4, -8, parent="Obstacles", groups="pillar"))
for i, (x, y, w, h) in enumerate(WALLS, 1):
    out.append(f'\n[node name="LowWall{i:02d}" type="Node2D" parent="Obstacles" groups=["low_wall"]]\nz_index = -8\n'
               f'position = Vector2({x}, {y})\nscript = ExtResource("5")\nsize = Vector2({w}, {h})\n')
path = os.path.join(ROOT, "perforated-godot", "scenes", "main.tscn")
open(path, "w", newline="\n").write("".join(out))
print("wrote", path, len(PILLARS), "pillars,", len(WALLS), "low walls")
