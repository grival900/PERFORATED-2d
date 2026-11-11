class_name Arena
extends RefCounted
## Geometry and collision (no drawing) for the main arena and the three mini-boss rooms.

var main_solid: Array = []      # Rect2: everything that blocks movement in the main arena
var main_blockers: Array = []   # Rect2: pillars only (low walls do not stop shots)
var room_solid: Array = []      # per mini-boss room: its pillars
var solid: Array = []           # the set for the current area
var shot_blockers: Array = []
var bounds: Rect2 = Rect2(0, 0, Cfg.ARENA, Cfg.ARENA)   # playable rectangle of the current area
var room: int = 0               # 0 = main arena, 1..3 = mini-boss rooms
var gate_open: bool = false
var door_open: Array = [false, false, false]   # south, east, west
var hit: bool = false           # set by collide(): did the last call push the circle?
var last_normal: Vector2 = Vector2.ZERO   # direction of the last push by a solid (steering hint)
var pillar_centers: Array = []   # main arena pillar positions (for the minimap)
var low_wall_rects: Array = []   # main arena low walls (for the minimap)
var altar_pos: Vector2 = Cfg.ALTAR_POS
var braziers: Array = Cfg.BRAZIERS
var hazard_rects: Array = []   # lethal zones (nodes in the group "hazard")


func _init() -> void:
	pillar_centers = Rooms.all_pillars()
	low_wall_rects = Rooms.all_low_walls()
	for c in Rooms.all_pillars():
		var rc := Rect2(c.x - Cfg.PILLAR_HALF, c.y - Cfg.PILLAR_HALF, Cfg.PILLAR_HALF * 2, Cfg.PILLAR_HALF * 2)
		main_solid.append(rc)
		main_blockers.append(rc)
	for w in Rooms.all_low_walls():
		main_solid.append(w)
	for d in Rooms.ROOMS:
		var list: Array = []
		for c in d["pillars"]:
			list.append(Rect2(c.x - Cfg.PILLAR_HALF, c.y - Cfg.PILLAR_HALF, Cfg.PILLAR_HALF * 2, Cfg.PILLAR_HALF * 2))
		room_solid.append(list)
	set_room(0)


func load_from_nodes(root: Node) -> void:
	## Take the main arena obstacles from the scene nodes (groups "pillar" and "low_wall"),
	## so they can be moved in the editor. If the scene has none, the data in rooms.gd / cfg.gd is used.
	hazard_rects = []
	for hz in root.get_tree().get_nodes_in_group("hazard"):
		var cs = hz.get_node_or_null("CollisionShape2D")
		if cs != null and cs.shape is RectangleShape2D:
			var sz: Vector2 = cs.shape.size
			hazard_rects.append(Rect2(hz.global_position - sz / 2.0, sz))
	var pils: Array = root.get_tree().get_nodes_in_group("pillar")
	var walls: Array = root.get_tree().get_nodes_in_group("low_wall")
	if pils.is_empty() and walls.is_empty():
		return
	main_solid = []
	main_blockers = []
	pillar_centers = []
	low_wall_rects = []
	for n in pils:
		var c: Vector2 = n.global_position
		pillar_centers.append(c)
		var rc := Rect2(c.x - Cfg.PILLAR_HALF, c.y - Cfg.PILLAR_HALF, Cfg.PILLAR_HALF * 2, Cfg.PILLAR_HALF * 2)
		main_solid.append(rc)
		main_blockers.append(rc)
	for n in walls:
		var wr := Rect2(n.global_position, n.size)
		low_wall_rects.append(wr)
		main_solid.append(wr)
	set_room(room)


func set_room(i: int) -> void:
	room = i
	if i == 0:
		solid = main_solid
		shot_blockers = main_blockers
		bounds = Rect2(0, 0, Cfg.ARENA, Cfg.ARENA)
	else:
		solid = room_solid[i - 1]
		shot_blockers = room_solid[i - 1]
		bounds = Rooms.ROOMS[i - 1]["rect"]


func _push_from_rect(p: Vector2, r: float, rc: Rect2) -> Array:
	## Push a circle out of a rect. Returns [new_position, hit].
	var cx: float = clampf(p.x, rc.position.x, rc.end.x)
	var cy: float = clampf(p.y, rc.position.y, rc.end.y)
	var dx: float = p.x - cx
	var dy: float = p.y - cy
	var d2: float = dx * dx + dy * dy
	if d2 >= r * r:
		return [p, false]
	if d2 > 0.000001:
		var d: float = sqrt(d2)
		return [Vector2(cx + dx / d * r, cy + dy / d * r), true]
	# the centre is inside the rect: leave through the nearest side
	var left: float = p.x - rc.position.x
	var right: float = rc.end.x - p.x
	var top: float = p.y - rc.position.y
	var bottom: float = rc.end.y - p.y
	var m: float = minf(minf(left, right), minf(top, bottom))
	if m == left:
		return [Vector2(rc.position.x - r, p.y), true]
	if m == right:
		return [Vector2(rc.end.x + r, p.y), true]
	if m == top:
		return [Vector2(p.x, rc.position.y - r), true]
	return [Vector2(p.x, rc.end.y + r), true]


func collide(p: Vector2, r: float, through: bool) -> Vector2:
	## Keep a circle inside the current area and out of obstacles.
	## `through` = may use the openings (the north gate and the open mini-boss doors); only the hero does.
	hit = false
	last_normal = Vector2.ZERO
	var lo_x: float = bounds.position.x + r
	var hi_x: float = bounds.end.x - r
	var lo_y: float = bounds.position.y + r
	var hi_y: float = bounds.end.y - r
	if through and room == 0:
		if gate_open and p.x >= Cfg.GATE_X0 + r and p.x <= Cfg.GATE_X1 - r:
			lo_y = -110.0
		if door_open[0] and p.x >= Rooms.SPAN_LO + r and p.x <= Rooms.SPAN_HI - r:
			hi_y = Cfg.ARENA + 110.0
		if door_open[1] and p.y >= Rooms.SPAN_LO + r and p.y <= Rooms.SPAN_HI - r:
			hi_x = Cfg.ARENA + 110.0
		if door_open[2] and p.y >= Rooms.SPAN_LO + r and p.y <= Rooms.SPAN_HI - r:
			lo_x = -110.0
	var x: float = p.x
	var y: float = p.y
	if x < lo_x:
		x = lo_x
		hit = true
	elif x > hi_x:
		x = hi_x
		hit = true
	if y < lo_y:
		y = lo_y
		hit = true
	elif y > hi_y:
		y = hi_y
		hit = true
	var pos := Vector2(x, y)
	for rc in solid:
		var c: Vector2 = rc.get_center()
		if absf(pos.x - c.x) < rc.size.x / 2.0 + r + 2.0 and absf(pos.y - c.y) < rc.size.y / 2.0 + r + 2.0:
			var res: Array = _push_from_rect(pos, r, rc)
			if res[1]:
				var np: Vector2 = res[0]
				var moved: Vector2 = np - pos
				if moved.length() > 0.000001:
					last_normal = moved.normalized()
				pos = np
				hit = true
	return pos


func shot_blocked(x: float, y: float) -> bool:
	if not bounds.has_point(Vector2(x, y)):
		if room == 0 and y < 0.0 and gate_open and x >= Cfg.GATE_X0 and x <= Cfg.GATE_X1:
			return false
		return true
	for rc in shot_blockers:
		if rc.has_point(Vector2(x, y)):
			return true
	return false


func is_free(x: float, y: float, margin: float) -> bool:
	## True if a prop of radius `margin` fits at (x, y) in the main arena.
	if not (x > 110.0 and x < Cfg.ARENA - 110.0 and y > 110.0 and y < Cfg.ARENA - 110.0):
		return false
	for rc in main_solid:
		if rc.grow(margin).has_point(Vector2(x, y)):
			return false
	for hz in hazard_rects:
		if hz.grow(margin + 30.0).has_point(Vector2(x, y)):
			return false
	for b in braziers:
		if (b.x - x) * (b.x - x) + (b.y - y) * (b.y - y) < 120.0 * 120.0:
			return false
	var a: Vector2 = altar_pos
	if (a.x - x) * (a.x - x) + (a.y - y) * (a.y - y) < 190.0 * 190.0:
		return false
	if y < 330.0 and x > Cfg.GATE_X0 - 120 and x < Cfg.GATE_X1 + 120:
		return false
	# keep the three mini-boss doors clear
	if y > Cfg.ARENA - 330.0 and x > Rooms.SPAN_LO - 120.0 and x < Rooms.SPAN_HI + 120.0:
		return false
	if y > Rooms.SPAN_LO - 120.0 and y < Rooms.SPAN_HI + 120.0 and (x < 330.0 or x > Cfg.ARENA - 330.0):
		return false
	return true
