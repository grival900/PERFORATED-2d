extends Node2D
## The hero as a scene node: Body (Sprite2D), Shadow, AnimationPlayer and Hurtbox (Area2D).
## game.gd moves this node to the player's position and calls update_visual() every frame;
## the AnimationPlayer then plays the animation that matches the hero's state.
## Animations: idle, run, turn (quick change of direction), dash, hurt, die.

var last_facing: float = 0.0
var oneshot: String = ""   # hurt / turn / die: plays to the end before idle or run take over

@onready var body: Sprite2D = $Body
@onready var anim: AnimationPlayer = $AnimationPlayer


func _ready() -> void:
	_build_animations()
	anim.play("idle")


func reset_visual() -> void:
	oneshot = ""
	body.scale = Vector2.ONE
	body.position = Vector2.ZERO
	body.modulate = Color.WHITE
	anim.play("idle")


func play_hurt() -> void:
	oneshot = "hurt"
	anim.play("hurt")


func update_visual(px: float, py: float, facing: float, speed: float, dashing: bool, dying: bool) -> void:
	position = Vector2(px, py)
	body.rotation = facing   # the sprite always turns towards where the hero faces
	if dying:
		if oneshot != "die":
			oneshot = "die"
			anim.play("die")
		return
	var turned: float = absf(fposmod(facing - last_facing + PI, TAU) - PI)
	last_facing = facing
	if dashing:
		oneshot = ""
		_play_if_new("dash")
		return
	if (oneshot == "hurt" or oneshot == "turn") and anim.is_playing():
		return
	oneshot = ""
	if turned > 0.5:   # a sudden change of direction
		oneshot = "turn"
		anim.play("turn")
		return
	_play_if_new("run" if speed > 40.0 else "idle")


func _play_if_new(name: String) -> void:
	if anim.current_animation != name:
		anim.play(name)


# ---------------------------------------------------------------- animations (built in code)
func _make(length: float, looping: bool) -> Animation:
	var a := Animation.new()
	a.length = length
	a.loop_mode = Animation.LOOP_LINEAR if looping else Animation.LOOP_NONE
	return a


func _track(a: Animation, path: String, times: Array, values: Array) -> void:
	var t: int = a.add_track(Animation.TYPE_VALUE)
	a.track_set_path(t, NodePath(path))
	a.track_set_interpolation_type(t, Animation.INTERPOLATION_LINEAR)
	for i in range(times.size()):
		a.track_insert_key(t, float(times[i]), values[i])


func _build_animations() -> void:
	var lib := AnimationLibrary.new()
	var v1 := Vector2(1, 1)

	var idle: Animation = _make(1.4, true)   # slow breathing
	_track(idle, "Body:scale", [0.0, 0.7, 1.4], [v1, Vector2(1.04, 0.96), v1])
	lib.add_animation("idle", idle)

	var run: Animation = _make(0.36, true)   # quick squash and bob
	_track(run, "Body:scale", [0.0, 0.09, 0.18, 0.27, 0.36], [v1, Vector2(1.08, 0.92), v1, Vector2(0.94, 1.06), v1])
	_track(run, "Body:position", [0.0, 0.09, 0.18, 0.27, 0.36], [Vector2.ZERO, Vector2(0, -2), Vector2.ZERO, Vector2(0, -2), Vector2.ZERO])
	lib.add_animation("run", run)

	var turn: Animation = _make(0.18, false)   # direction change
	_track(turn, "Body:scale", [0.0, 0.09, 0.18], [Vector2(0.82, 1.18), Vector2(1.06, 0.94), v1])
	lib.add_animation("turn", turn)

	var dash: Animation = _make(0.16, false)   # stretch and teal tint
	_track(dash, "Body:scale", [0.0, 0.05, 0.16], [v1, Vector2(1.35, 0.7), Vector2(1.1, 0.9)])
	_track(dash, "Body:modulate", [0.0, 0.16], [Color(0.6, 1.0, 1.0, 1.0), Color.WHITE])
	lib.add_animation("dash", dash)

	var hurt: Animation = _make(0.4, false)   # red flashes
	_track(hurt, "Body:modulate", [0.0, 0.1, 0.2, 0.3, 0.4],
			[Color(1.0, 0.3, 0.3, 1.0), Color.WHITE, Color(1.0, 0.3, 0.3, 1.0), Color.WHITE, Color.WHITE])
	_track(hurt, "Body:scale", [0.0, 0.1, 0.4], [Vector2(1.2, 1.2), v1, v1])
	lib.add_animation("hurt", hurt)

	var die: Animation = _make(1.0, false)   # swell, redden, vanish
	_track(die, "Body:scale", [0.0, 0.3, 1.0], [v1, Vector2(1.3, 1.3), Vector2.ZERO])
	_track(die, "Body:modulate", [0.0, 0.5, 1.0], [Color.WHITE, Color(1.0, 0.5, 0.5, 1.0), Color(1.0, 1.0, 1.0, 0.0)])
	lib.add_animation("die", die)

	anim.add_animation_library("", lib)
