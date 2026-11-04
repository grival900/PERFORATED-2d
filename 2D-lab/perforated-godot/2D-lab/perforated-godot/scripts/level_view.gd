@tool
extends Node2D
## Draws the static Level 1 arena once: stone border, marble floor, gold inlay, sigil,
## wall shadows, braziers and the three mini-boss rooms. Godot caches these draw commands.
## The main arena's pillars, low walls and the altar are their own nodes in main.tscn.

var tex: Dictionary = {}

const TEX_NAMES: Array = ["altar", "brazier", "glow", "pillar", "sigil", "wall_block", "marble_0", "marble_1",
		"marble_2", "marble_3", "marble_4", "marble_5", "marble_6", "marble_7"]


func _ready() -> void:
	## Runs in the editor too (@tool), so the arena shows in the 2D view without pressing Play.
	_load_textures()
	queue_redraw()


func _load_textures() -> void:
	for n in TEX_NAMES:
		tex[n] = load("res://assets/textures/%s.png" % n)

const GOLD: Color = Color(0.925, 0.769, 0.361)
const GOLD_D: Color = Color(0.549, 0.384, 0.133)


func _draw() -> void:
	if tex.is_empty():
		_load_textures()
	var A: float = float(Cfg.ARENA)
	var W: float = float(Cfg.WALL)
	var rng := RandomNumberGenerator.new()
	rng.seed = 11

	# stone border (four bands around the floor)
	var wall: Texture2D = tex["wall_block"]
	draw_texture_rect(wall, Rect2(-W, -W, A + 2.0 * W, W), true)
	draw_texture_rect(wall, Rect2(-W, A, A + 2.0 * W, W), true)
	draw_texture_rect(wall, Rect2(-W, 0.0, W, A), true)
	draw_texture_rect(wall, Rect2(A, 0.0, W, A), true)

	# marble floor
	var gy: float = 0.0
	while gy < A:
		var gx: float = 0.0
		while gx < A:
			var t: Texture2D = tex["marble_%d" % rng.randi_range(0, 7)]
			var v: float = float(rng.randi_range(226, 255)) / 255.0
			var w: float = minf(128.0, A - gx)
			var h: float = minf(128.0, A - gy)
			draw_texture_rect_region(t, Rect2(gx, gy, w, h), Rect2(0.0, 0.0, w, h), Color(v, v, minf(1.0, v + 0.016), 1.0))
			gx += 128.0
		gy += 128.0

	# gold inlay: inset square, corner rosettes, two rings round the sigil
	var inset := Rect2(170.0, 170.0, A - 340.0, A - 340.0)
	draw_rect(inset, GOLD_D, false, 10.0)
	draw_rect(inset.grow(-3.0), GOLD, false, 4.0)
	for c in [Vector2(170, 170), Vector2(A - 170.0, 170), Vector2(170, A - 170.0), Vector2(A - 170.0, A - 170.0)]:
		draw_circle(c, 26.0, GOLD_D)
		draw_circle(c, 20.0, GOLD)
		draw_circle(c, 9.0, GOLD_D)
	var centre := Vector2(A / 2.0, A / 2.0)
	draw_arc(centre, 1150.0, 0.0, TAU, 256, GOLD_D, 9.0, true)
	draw_arc(centre, 1150.0, 0.0, TAU, 256, GOLD, 6.0, true)
	draw_arc(centre, 1090.0, 0.0, TAU, 256, GOLD_D, 6.0, true)
	draw_arc(centre, 1090.0, 0.0, TAU, 256, GOLD, 3.0, true)
	draw_texture_rect(tex["sigil"], Rect2(centre - Vector2(750, 750), Vector2(1500, 1500)), false)

	# soft dark band along the walls (ambient occlusion)
	var dark := Color(0.0, 0.0, 0.04, 0.59)
	var clear := Color(0.0, 0.0, 0.04, 0.0)
	draw_polygon(PackedVector2Array([Vector2(0, 0), Vector2(A, 0), Vector2(A, 110), Vector2(0, 110)]), PackedColorArray([dark, dark, clear, clear]))
	draw_polygon(PackedVector2Array([Vector2(0, A), Vector2(A, A), Vector2(A, A - 110.0), Vector2(0, A - 110.0)]), PackedColorArray([dark, dark, clear, clear]))
	draw_polygon(PackedVector2Array([Vector2(0, 0), Vector2(0, A), Vector2(110, A), Vector2(110, 0)]), PackedColorArray([dark, dark, clear, clear]))
	draw_polygon(PackedVector2Array([Vector2(A, 0), Vector2(A, A), Vector2(A - 110.0, A), Vector2(A - 110.0, 0)]), PackedColorArray([dark, dark, clear, clear]))
	# bright lip where the floor meets the wall
	draw_rect(Rect2(-3.0, -3.0, A + 6.0, A + 6.0), Color8(132, 126, 170), false, 3.0)
	draw_rect(Rect2(-7.0, -7.0, A + 14.0, A + 14.0), Color8(20, 18, 34), false, 6.0)

	# braziers. The pillars, low walls and altar are separate scene nodes (see main.tscn).
	var br: Texture2D = tex["brazier"]
	for c in Cfg.BRAZIERS:
		draw_texture(br, c - br.get_size() * 0.5)

	for d in Rooms.ROOMS:
		_draw_room(d)


func _draw_room(d: Dictionary) -> void:
	## One mini-boss room: stone walls, tinted marble floor, inlay in the room colour, pillars, braziers.
	var rc: Rect2 = d["rect"]
	var wd: float = float(Cfg.WALL)
	var tint: Color = d["tint"]
	var col: Color = d["color"]
	var wall: Texture2D = tex["wall_block"]
	draw_texture_rect(wall, Rect2(rc.position.x - wd, rc.position.y - wd, rc.size.x + 2.0 * wd, wd), true)
	draw_texture_rect(wall, Rect2(rc.position.x - wd, rc.end.y, rc.size.x + 2.0 * wd, wd), true)
	draw_texture_rect(wall, Rect2(rc.position.x - wd, rc.position.y, wd, rc.size.y), true)
	draw_texture_rect(wall, Rect2(rc.end.x, rc.position.y, wd, rc.size.y), true)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(absf(rc.position.x)) + 7
	var gy: float = rc.position.y
	while gy < rc.end.y:
		var gx: float = rc.position.x
		while gx < rc.end.x:
			var mt: Texture2D = tex["marble_%d" % rng.randi_range(0, 7)]
			var v: float = float(rng.randi_range(226, 255)) / 255.0
			var cw: float = minf(128.0, rc.end.x - gx)
			var ch: float = minf(128.0, rc.end.y - gy)
			draw_texture_rect_region(mt, Rect2(gx, gy, cw, ch), Rect2(0.0, 0.0, cw, ch), Color(v * tint.r, v * tint.g, v * tint.b, 1.0))
			gx += 128.0
		gy += 128.0
	var dark := Color(col.r * 0.45, col.g * 0.45, col.b * 0.45, 1.0)
	draw_rect(rc.grow(-70.0), dark, false, 8.0)
	draw_rect(rc.grow(-73.0), col, false, 3.0)
	var centre: Vector2 = rc.get_center()
	draw_arc(centre, 240.0, 0.0, TAU, 128, dark, 8.0, true)
	draw_arc(centre, 240.0, 0.0, TAU, 128, col, 3.0, true)
	draw_texture_rect(tex["sigil"], Rect2(centre - Vector2(300, 300), Vector2(600, 600)), false, Color(col.r, col.g, col.b, 0.55))
	var shade := Color(0.0, 0.0, 0.04, 0.59)
	var clear := Color(0.0, 0.0, 0.04, 0.0)
	var cols := PackedColorArray([shade, shade, clear, clear])
	var x0: float = rc.position.x
	var y0: float = rc.position.y
	var x1: float = rc.end.x
	var y1: float = rc.end.y
	draw_polygon(PackedVector2Array([Vector2(x0, y0), Vector2(x1, y0), Vector2(x1, y0 + 110.0), Vector2(x0, y0 + 110.0)]), cols)
	draw_polygon(PackedVector2Array([Vector2(x0, y1), Vector2(x1, y1), Vector2(x1, y1 - 110.0), Vector2(x0, y1 - 110.0)]), cols)
	draw_polygon(PackedVector2Array([Vector2(x0, y0), Vector2(x0, y1), Vector2(x0 + 110.0, y1), Vector2(x0 + 110.0, y0)]), cols)
	draw_polygon(PackedVector2Array([Vector2(x1, y0), Vector2(x1, y1), Vector2(x1 - 110.0, y1), Vector2(x1 - 110.0, y0)]), cols)
	draw_rect(rc.grow(3.0), Color8(132, 126, 170), false, 3.0)
	draw_rect(rc.grow(7.0), Color8(20, 18, 34), false, 6.0)
	var pil: Texture2D = tex["pillar"]
	for c in d["pillars"]:
		draw_texture(pil, c - pil.get_size() * 0.5)
	var br: Texture2D = tex["brazier"]
	for c in d["braziers"]:
		draw_texture(br, c - br.get_size() * 0.5)
	var pe: Vector2 = d["portal"]
	draw_arc(pe, 46.0, 0.0, TAU, 40, Color(col.r, col.g, col.b, 0.45), 3.0, true)
