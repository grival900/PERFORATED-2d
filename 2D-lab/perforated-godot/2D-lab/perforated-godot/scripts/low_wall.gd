@tool
extends Node2D
## A low wall: blocks movement but not shots. The node position is its top-left corner;
## change `size` in the Inspector. Drawn in the editor too (@tool). The game reads the collision
## rectangle from every node in the group "low_wall".

const GOLD: Color = Color(0.925, 0.769, 0.361)
const GOLD_D: Color = Color(0.549, 0.384, 0.133)

@export var size: Vector2 = Vector2(300, 54):
	set(value):
		size = value
		queue_redraw()

var tex: Texture2D


func _ready() -> void:
	add_to_group("low_wall")
	tex = load("res://assets/textures/wall_block.png")
	queue_redraw()


func get_rect() -> Rect2:
	return Rect2(global_position, size)


func _draw() -> void:
	if tex == null:
		tex = load("res://assets/textures/wall_block.png")
	var rc := Rect2(Vector2.ZERO, size)
	draw_rect(Rect2(-6.0, -2.0, size.x + 24.0, size.y + 24.0), Color(0.0, 0.0, 0.03, 0.47))
	draw_texture_rect(tex, rc, true)
	draw_rect(rc, GOLD_D, false, 6.0)
	draw_rect(rc.grow(-3.0), GOLD, false, 2.0)
	draw_line(Vector2.ZERO, Vector2(size.x, 0.0), Color8(200, 194, 236), 2.0)
