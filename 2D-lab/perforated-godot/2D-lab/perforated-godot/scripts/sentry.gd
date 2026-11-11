extends Node2D

@export var speed: float = 130.0
@export var max_hp: float = 8.0
@export var radius: float = 30.0   # used for obstacle collision and for being hit by shots

var hp: float = 8.0
var alive: bool = true
var waypoints: Array = []
var wp_i: int = 1
var start_pos: Vector2
var t: float = 0.0
var base_color: Color = Color(1.0, 0.45, 0.45)

@onready var body: Sprite2D = $Body
@onready var hitbox: Area2D = $HitBox


func _ready() -> void:
	add_to_group("sentry")
	add_to_group("resettable")
	start_pos = global_position
	for m in $Waypoints.get_children():
		waypoints.append(m.global_position)
	base_color = body.modulate
	reset()


func reset() -> void:
	global_position = start_pos
	hp = max_hp
	alive = true
	visible = true
	wp_i = 1 % maxi(1, waypoints.size())
	body.modulate = base_color
	hitbox.set_deferred("monitorable", true)


func step(dt: float, arena: Arena) -> void:
	if not alive or waypoints.is_empty():
		return
	t += dt
	body.modulate = body.modulate.lerp(base_color, minf(1.0, dt * 10.0))
	var d: Vector2 = waypoints[wp_i] - global_position
	if d.length() < 10.0:
		wp_i = (wp_i + 1) % waypoints.size()
		return
	var dir: Vector2 = d.normalized()
	var np: Vector2 = arena.collide(global_position + dir * speed * dt, radius, false)
	if arena.hit:   # blocked by a pillar or wall: head for the next waypoint
		wp_i = (wp_i + 1) % waypoints.size()
	global_position = np
	body.rotation = Util.dir_to_angle(dir.x, dir.y)
	body.position.y = sin(t * 6.0) * 2.0


func take_hit(dmg: float) -> void:
	if not alive:
		return
	hp -= dmg
	body.modulate = Color(2.2, 2.2, 2.2, 1.0)
	if hp <= 0.0:
		alive = false
		visible = false
		hitbox.set_deferred("monitorable", false)
