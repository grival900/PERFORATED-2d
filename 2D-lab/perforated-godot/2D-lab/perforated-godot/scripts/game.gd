extends Node2D
## PERFORATED, Level 1 (Pride): simulation and world drawing.
## A port of the pygame version in 2D-lab/game. Numbers come from cfg.gd (generated from settings.py).

const Ent = preload("res://scripts/entities.gd")
const LevelView = preload("res://scripts/level_view.gd")
const FxView = preload("res://scripts/fx_view.gd")
const Hud = preload("res://scripts/hud.gd")

const DOOR_NODES: Array = ["DoorSouth", "DoorEast", "DoorWest"]
const UPGRADE_IDS: Array = ["multi", "rate", "pierce", "power", "area", "dash", "speed", "heart"]
const UNLOCKABLE: Array = ["halo", "pulse", "arc"]
const SHARDS: Dictionary = {"sentinel": 3, "skirmisher": 0, "lancer": 2, "elite": 5, "swarmer": 0, "bulwark": 4, "miniboss": 7}
const GEM_COLOR: Color = Color(0.314, 0.922, 0.804)
# the swarmer and bulwark reuse the skirmisher / sentinel art, rescaled and tinted (like the pygame version)
const VARIANTS: Dictionary = {
	"swarmer": {"tex": "guardian_skirmisher", "scale": 0.72, "tint": Color(1.0, 0.647, 0.725)},
	"bulwark": {"tex": "guardian_sentinel", "scale": 1.45, "tint": Color(1.0, 0.804, 0.588)},
}
# sound key -> [file, volume]
const SOUND_SPEC: Dictionary = {
	"shoot": ["laser2", 0.16], "hit": ["hit2", 0.22], "kill": ["hit5", 0.30], "hurt": ["hurt1", 0.85],
	"dash": ["phaseJump1", 0.45], "upgrade_open": ["upgrade2", 0.6], "upgrade_pick": ["upgrade1", 0.7],
	"heart": ["coin3", 0.6], "spear": ["laser4", 0.22], "slam": ["rockHit2", 0.55],
	"gate": ["secret2", 0.8], "over": ["gameover1", 0.8], "win": ["secret4", 0.8],
	"elite": ["error1", 0.45], "box": ["hit4", 0.45], "gem": ["coin2", 0.14], "weapon": ["upgrade3", 0.7],
	"pulse": ["explosion2", 0.35], "arc": ["laser1", 0.2],
}

var lang: String = "mk"
var state: String = "title"   # title, play, pause, upgrade, dying, over, win
var clock: float = 0.0        # real time, runs in every state
var time: float = 0.0         # play time of the current run

var tex: Dictionary = {}
var snd: Dictionary = {}
var font: Font
var light_tex: Texture2D
var arena: Arena

# nodes
var camera: Camera2D
var level_view
var gate_sprite: Sprite2D
var brazier_lights: Array = []
var gate_light: PointLight2D
var player_light: PointLight2D
var fx_add
var fx_norm
var hud
var sfx_players: Array = []
var sfx_i: int = 0
var music: AudioStreamPlayer
var music_on: bool = true
var _last_play: Dictionary = {}

# run state
var player
var enemies: Array = []
var shots: Array = []
var spears: Array = []
var hearts: Array = []
var boxes: Array = []
var gems: Array = []
var parts: Array = []
var waves: Array = []      # pulse shockwaves: {x, y, radius, t, hit, dmg}
var bolts: Array = []      # arc lightning: {pts, life, max}
var weapons: Dictionary = {}
var grid: Dictionary = {}
var next_id: int = 0

var pride: float = 0.0
var pride_shown: float = 0.0
var bar_pulse: float = 0.0
var box_pulse: float = 0.0
var stage: int = 1
var stage_points: Array = []   # Pride points at which each wave begins (index 0 = wave 2)
var kills: int = 0
var banner_t: float = 0.0
var banner_text: String = ""
var spawn_t: float = 2.2
var recycle_t: float = 1.0
var pending_elites: int = 0
var elite_t: float = 0.0
var box_pts: int = 0
var box_total: int = 0
var box_upgrades: int = 0
var box_timer: float = 0.0
var gem_acc: int = 0
var gem_acc_t: float = 0.0
var queue: Array = []
var choice_kind: String = "stat"
var choices: Array = []
var choice_sel: int = 0
var exit_open: bool = false
var dying_t: float = 0.0
var shake: float = 0.0
var red_flash: float = 0.0
var enemy_speed_mult: float = 1.0
var ghost_t: float = 0.0
var cam_pos: Vector2 = Vector2.ZERO
var last_move: Vector2 = Vector2.ZERO
# positions read from the scene's marker nodes (PlayerStart, Ferryman, Altar)
var player_start: Vector2 = Cfg.PLAYER_START
var ferry_pos: Vector2 = Vector2(Cfg.ALTAR_POS.x - 70.0, Cfg.ALTAR_POS.y + 12.0)
var altar_pos: Vector2 = Cfg.ALTAR_POS
var hero                          # the Hero node: Body sprite + AnimationPlayer + Hurtbox (Area2D)
var sentries: Array = []          # the Sentry nodes: enemies that patrol a path
var deaths: int = 0
var brazier_positions: Array = []
var heart_spots: Array = []
var spawn_pts: Array = []
# mini-boss rooms
var room: int = 0                  # 0 = main arena, 1..3 = mini-boss rooms
var rooms_done: Array = [false, false, false]
var main_enemies: Array = []       # the guardians waiting in the main arena while you are in a room
var portal_open: bool = false      # the way back opens when the mini-boss is dead
var fade: float = 0.0              # screen fade after a teleport
var door_sprites: Array = []
var door_lights: Array = []


# ======================================================================== setup
func _ready() -> void:
	randomize()
	_load_assets()
	arena = Arena.new()
	arena.load_from_nodes(self)
	_read_markers()
	_build_nodes()
	_new_run()
	state = "title"
	cam_pos = Vector2(Cfg.ARENA / 2.0 - Cfg.SCREEN_W / 2.0, player_start.y - Cfg.SCREEN_H / 2.0 - 120.0)
	camera.position = Vector2(Cfg.ARENA / 2.0, player_start.y - 120.0)
	camera.reset_smoothing()


func _read_markers() -> void:
	## PlayerStart, Ferryman and Altar are nodes of main.tscn: move them in the editor to move the spawn / the Ferryman.
	## PlayerStart and Ferryman are only placeholders in the editor; the game draws those two itself.
	var n = get_node_or_null("PlayerStart")
	if n != null:
		player_start = n.position
		n.visible = false
	n = get_node_or_null("Ferryman")
	if n != null:
		ferry_pos = n.position
		n.visible = false
	n = get_node_or_null("Altar")
	if n != null:
		altar_pos = n.position
	hero = get_node_or_null("Hero")
	sentries = get_tree().get_nodes_in_group("sentry")
	brazier_positions = []
	for b in get_tree().get_nodes_in_group("brazier"):
		brazier_positions.append(b.position)
	if brazier_positions.is_empty():
		brazier_positions = Cfg.BRAZIERS.duplicate()
	heart_spots = []
	for h in get_tree().get_nodes_in_group("heart_spot"):
		heart_spots.append(h.position)
		h.visible = false   # editor placeholder; the game draws the hearts itself
	if heart_spots.is_empty():
		heart_spots = Cfg.HEART_SPOTS.duplicate()
	spawn_pts = []
	for sp in get_tree().get_nodes_in_group("spawn_point"):
		spawn_pts.append(sp.position)
	if spawn_pts.is_empty():
		spawn_pts = Cfg.SPAWN_POINTS.duplicate()
	arena.altar_pos = altar_pos
	arena.braziers = brazier_positions


func _load_assets() -> void:
	var tex_names: Array = ["altar", "brazier", "gate_closed", "gate_open", "glow", "pillar", "sigil", "vignette", "wall_block"]
	for i in range(8):
		tex_names.append("marble_%d" % i)
	for n in tex_names:
		tex[n] = load("res://assets/textures/%s.png" % n)
	for n in ["dash_empty", "dash_full", "ferryman", "guardian_elite", "guardian_lancer", "guardian_sentinel",
			"guardian_skirmisher", "heart_empty", "heart_full", "hero", "needle", "shard", "spear"]:
		tex[n] = load("res://assets/sprites/%s.png" % n)
	font = load("res://assets/fonts/DejaVuSans-Bold.ttf")
	for key in SOUND_SPEC:
		var spec: Array = SOUND_SPEC[key]
		snd[key] = {"stream": load("res://assets/sounds/%s.wav" % spec[0]), "vol": float(spec[1])}
	light_tex = _make_light_texture()

	# stage thresholds as Pride points (same as the pygame version)
	stage_points = Cfg.STAGE_AT_PTS.duplicate()


func _make_light_texture() -> Texture2D:
	## White-to-black radial falloff, opaque, so it lights the same whether alpha is used or not.
	var size: int = 256
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var c: float = size / 2.0
	for y in range(size):
		for x in range(size):
			var d: float = Vector2(x + 0.5 - c, y + 0.5 - c).length() / c
			var v: float = clampf(1.0 - d * d, 0.0, 1.0)
			img.set_pixel(x, y, Color(v, v, v, 1.0))
	return ImageTexture.create_from_image(img)


func _add_light(pos: Vector2, radius: float, color: Color, energy: float) -> PointLight2D:
	var l := PointLight2D.new()
	l.texture = light_tex
	l.texture_scale = radius / 128.0
	l.color = color
	l.energy = energy
	l.position = pos
	add_child(l)
	return l


func _build_nodes() -> void:
	var cm := CanvasModulate.new()
	cm.color = Color8(Cfg.AMBIENT[0], Cfg.AMBIENT[1], Cfg.AMBIENT[2])
	add_child(cm)

	# the arena, the gate and the doors are real nodes of main.tscn (so they show in the editor);
	# they are created here only if the scene does not have them
	level_view = get_node_or_null("LevelView")
	if level_view == null:
		level_view = Node2D.new()
		level_view.set_script(LevelView)
		level_view.z_index = -10
		add_child(level_view)
	gate_sprite = get_node_or_null("Gate") as Sprite2D
	if gate_sprite == null:
		gate_sprite = Sprite2D.new()
		add_child(gate_sprite)
	gate_sprite.texture = tex["gate_closed"]
	gate_sprite.position = Vector2((Cfg.GATE_X0 + Cfg.GATE_X1) / 2.0, 20.0 - 85.0)
	gate_sprite.z_index = -5

	for b in brazier_positions:
		brazier_lights.append(_add_light(b, 330.0, Color8(255, 168, 78), 1.0))
	_add_light(altar_pos, 260.0, Color8(60, 235, 215), 1.0)
	_add_light(ferry_pos + Vector2(0, -32), 120.0, Color8(60, 235, 215), 1.0)
	for h in heart_spots:
		_add_light(h, 110.0, Color8(255, 90, 110), 0.8)
	gate_light = _add_light(Vector2((Cfg.GATE_X0 + Cfg.GATE_X1) / 2.0, 30.0), 240.0, Color8(214, 168, 86), 1.0)
	player_light = _add_light(Vector2.ZERO, 430.0, Color8(235, 230, 250), 1.0)
	for i in range(Rooms.ROOMS.size()):
		var rd: Dictionary = Rooms.ROOMS[i]
		var out := Vector2(-1, 0)
		var rot: float = -PI / 2.0
		if rd["side"] == "south":
			out = Vector2(0, 1)
			rot = PI
		elif rd["side"] == "east":
			out = Vector2(1, 0)
			rot = PI / 2.0
		var ds: Sprite2D = get_node_or_null(DOOR_NODES[i]) as Sprite2D
		if ds == null:
			ds = Sprite2D.new()
			add_child(ds)
		ds.texture = tex["gate_closed"]
		ds.position = rd["door"] + out * 65.0
		ds.rotation = rot
		ds.z_index = -5
		door_sprites.append(ds)
		door_lights.append(_add_light(rd["door"] - out * 30.0, 260.0, rd["color"], 0.0))
		for b in rd["braziers"]:
			brazier_lights.append(_add_light(b, 330.0, Color8(255, 168, 78), 1.0))

	# the Camera2D is a node of main.tscn (with its Limit properties); it follows the hero and is smoothed
	camera = get_node_or_null("Camera2D") as Camera2D
	if camera == null:
		camera = Camera2D.new()
		add_child(camera)
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 9.0
	_apply_camera_limits()
	camera.make_current()

	# glow / particle layers follow the camera but are not tinted by the ambient light
	var fx_layer := CanvasLayer.new()
	fx_layer.layer = 1
	fx_layer.follow_viewport_enabled = true
	add_child(fx_layer)
	fx_add = Node2D.new()
	fx_add.set_script(FxView)
	fx_add.g = self
	fx_add.mode = 0
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	fx_add.material = mat
	fx_layer.add_child(fx_add)
	fx_norm = Node2D.new()
	fx_norm.set_script(FxView)
	fx_norm.g = self
	fx_norm.mode = 1
	fx_layer.add_child(fx_norm)

	var ui_layer := CanvasLayer.new()
	ui_layer.layer = 10
	add_child(ui_layer)
	hud = Control.new()
	hud.set_script(Hud)
	hud.g = self
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_layer.add_child(hud)
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)

	for i in range(12):
		var p := AudioStreamPlayer.new()
		add_child(p)
		sfx_players.append(p)
	music = AudioStreamPlayer.new()
	var m = load("res://assets/music/pride_loop.wav")
	if m is AudioStreamWAV:
		m.loop_mode = AudioStreamWAV.LOOP_FORWARD
		m.loop_begin = 0
		m.loop_end = int(m.data.size() / 2)   # 16-bit mono
	music.stream = m
	music.volume_db = linear_to_db(0.5)
	add_child(music)


func sfx(key: String, min_gap: float = 0.0) -> void:
	var now: float = Time.get_ticks_msec() / 1000.0
	if min_gap > 0.0 and now - float(_last_play.get(key, -10.0)) < min_gap:
		return
	_last_play[key] = now
	if not snd.has(key):
		return
	var pl: AudioStreamPlayer = sfx_players[sfx_i]
	sfx_i = (sfx_i + 1) % sfx_players.size()
	pl.stream = snd[key]["stream"]
	pl.volume_db = linear_to_db(snd[key]["vol"])
	pl.play()


func T(key: String):
	return Tr.t(lang, key)


# ======================================================================== run control
func _new_run() -> void:
	next_id = 0
	arena.gate_open = false
	arena.door_open = [false, false, false]
	arena.set_room(0)
	room = 0
	rooms_done = [false, false, false]
	main_enemies = []
	portal_open = false
	fade = 0.0
	player = Ent.Player.new()
	player.x = player_start.x
	player.y = player_start.y
	weapons = {"needle": {"cd": 0.25}}
	enemies = []
	shots = []
	spears = []
	waves = []
	bolts = []
	parts = []
	grid = {}
	hearts = []
	for h in heart_spots:
		hearts.append(Ent.HeartPickup.new(h.x, h.y, true))
	time = 0.0
	kills = 0
	pride = 0.0
	pride_shown = 0.0
	bar_pulse = 0.0
	box_pulse = 0.0
	stage = 1
	banner_t = 0.0
	banner_text = ""
	spawn_t = 2.2
	recycle_t = 1.0
	pending_elites = 0
	elite_t = 0.0
	boxes = []
	gems = []
	box_pts = 0
	box_total = 0
	box_upgrades = 0
	box_timer = Cfg.BOX_RESPAWN
	gem_acc = 0
	gem_acc_t = 0.0
	_populate_boxes()
	queue = []
	choice_kind = "stat"
	choices = []
	choice_sel = 0
	exit_open = false
	dying_t = 0.0
	shake = 0.0
	red_flash = 0.0
	enemy_speed_mult = float(Cfg.STAGE_SPEED[1])
	ghost_t = 0.0
	cam_pos = Vector2(player_start.x - Cfg.SCREEN_W / 2.0, player_start.y - Cfg.SCREEN_H / 2.0)
	_apply_camera_limits()
	camera.position = Vector2(player_start.x, player_start.y)
	camera.reset_smoothing()
	get_tree().call_group("resettable", "reset")   # sentries (and anything else resettable) back to their start
	if hero != null:
		hero.reset_visual()
	state = "play"


func start_run() -> void:
	deaths = 0
	_new_run()
	if not music.playing and music_on:
		music.play()
	show_banner(T("stage").replace("{n}", "1") + ": " + T("stage_desc")[1])


func show_banner(text: String) -> void:
	banner_text = text
	banner_t = 2.8


# ======================================================================== input
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		_handle_key(event.keycode)
	elif event is InputEventMouseMotion:
		_handle_mouse(event.position, false)
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_handle_mouse(event.position, true)


func _handle_key(key: int) -> void:
	if key == KEY_F11:
		if DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		else:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		return
	if key == KEY_M:
		music_on = not music_on
		music.volume_db = linear_to_db(0.5) if music_on else -80.0
		return
	if state == "title":
		if key == KEY_ENTER or key == KEY_KP_ENTER or key == KEY_SPACE:
			start_run()
		elif key == KEY_L:
			lang = "en" if lang == "mk" else "mk"
		elif key == KEY_ESCAPE:
			get_tree().quit()
	elif state == "play":
		if key == KEY_ESCAPE or key == KEY_P:
			state = "pause"
			music.stream_paused = true
		elif key == KEY_SHIFT or key == KEY_SPACE:
			try_dash()
	elif state == "pause":
		if key == KEY_ESCAPE or key == KEY_P:
			state = "play"
			music.stream_paused = false
		elif key == KEY_R:
			music.stream_paused = false
			start_run()
		elif key == KEY_Q:
			get_tree().quit()
	elif state == "upgrade":
		if key == KEY_1 or key == KEY_2 or key == KEY_3:
			pick_upgrade(key - KEY_1)
		elif key == KEY_LEFT or key == KEY_A:
			choice_sel = (choice_sel + choices.size() - 1) % choices.size()
		elif key == KEY_RIGHT or key == KEY_D:
			choice_sel = (choice_sel + 1) % choices.size()
		elif key == KEY_ENTER or key == KEY_KP_ENTER or key == KEY_SPACE:
			pick_upgrade(choice_sel)
	elif state == "over" or state == "win":
		if key == KEY_ENTER or key == KEY_KP_ENTER:
			start_run()
		elif key == KEY_ESCAPE:
			get_tree().quit()


func card_rects() -> Array:
	var w: float = 310.0
	var h: float = 250.0
	var gap: float = 28.0
	var total: float = w * 3.0 + gap * 2.0
	var x0: float = (Cfg.SCREEN_W - total) / 2.0 + 70.0
	var out: Array = []
	for i in range(3):
		out.append(Rect2(x0 + i * (w + gap), 250.0, w, h))
	return out


func _handle_mouse(pos: Vector2, click: bool) -> void:
	if state != "upgrade":
		return
	var rects: Array = card_rects()
	for i in range(choices.size()):
		if rects[i].has_point(pos):
			choice_sel = i
			if click:
				pick_upgrade(i)


func _move_input() -> Vector2:
	var x: float = 0.0
	var y: float = 0.0
	if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT):
		x += 1.0
	if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT):
		x -= 1.0
	if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN):
		y += 1.0
	if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP):
		y -= 1.0
	return Vector2(x, y)


func try_dash() -> void:
	if player.try_dash(last_move.x, last_move.y):
		sfx("dash")
		fx_ring(player.x, player.y, Color8(90, 240, 225), 70.0, 0.25, 3.0)


# ======================================================================== main loop
func _process(delta: float) -> void:
	var dt: float = minf(delta, 1.0 / 30.0)
	clock += dt
	fade = maxf(0.0, fade - dt * 2.2)
	last_move = _move_input()
	_update(dt)
	_sync_nodes()
	queue_redraw()
	fx_add.queue_redraw()
	fx_norm.queue_redraw()
	hud.queue_redraw()


func _update(dt: float) -> void:
	red_flash = maxf(0.0, red_flash - dt)
	if state == "title":
		update_fx(dt)
		return
	if state == "pause" or state == "upgrade":
		return
	if state == "dying":
		dying_t -= dt
		update_fx(dt)
		shake = maxf(0.0, shake - dt * 2.0)
		if dying_t <= 0.0:
			restart_level()   # no game-over screen: the level restarts by itself
		return
	if state == "over" or state == "win":
		update_fx(dt)
		return

	var p = player
	time += dt
	banner_t = maxf(0.0, banner_t - dt)
	bar_pulse = maxf(0.0, bar_pulse - dt)
	box_pulse = maxf(0.0, box_pulse - dt)
	shake = maxf(0.0, shake - dt * 2.4)
	pride_shown += (pride - pride_shown) * minf(1.0, dt * 6.0)

	var target = nearest_enemy(p.x, p.y, Cfg.SHOT_RANGE)
	p.update(dt, last_move.x, last_move.y, arena, target)
	if p.is_dashing():
		ghost_t -= dt
		if ghost_t <= 0.0:
			ghost_t = 0.03
			fx_ghost(p.x, p.y, p.facing)
		dash_hits()
	update_weapons(dt)
	update_waves(dt)
	update_bolts(dt)
	purge_dead()

	update_director(dt)
	for e in enemies:
		e.update(dt, p, arena, self)
	grid = build_grid()
	separate_enemies()
	update_shots(dt)
	update_spears(dt)
	contact_damage()
	update_hearts(dt)
	update_sentries(dt)
	check_lethal()
	update_boxes(dt)
	update_fx(dt)
	check_progress()
	update_camera(dt)

	check_doors()
	check_portal()

	if room == 0 and exit_open and p.y < 8.0 and p.x > Cfg.GATE_X0 and p.x < Cfg.GATE_X1:
		state = "win"
		sfx("win")
		fx_diamonds(p.x, p.y, 40, 500.0, 1.4)
		fx_ring(p.x, p.y, Color8(255, 232, 150), 300.0, 0.9, 6.0)


func _sync_nodes() -> void:
	var off := Vector2.ZERO
	if shake > 0.0:
		var a: float = 10.0 * minf(1.0, shake)
		off = Vector2(randf_range(-a, a), randf_range(-a, a))
	camera.offset = off
	cam_pos = camera.get_screen_center_position() - Vector2(Cfg.SCREEN_W / 2.0, Cfg.SCREEN_H / 2.0)
	if hero != null:
		hero.visible = state != "over"
		hero.update_visual(player.x, player.y, player.facing, Vector2(player.vx, player.vy).length(), player.is_dashing(), state == "dying")
	player_light.position = Vector2(player.x, player.y)
	for i in range(brazier_lights.size()):
		var f: float = 0.82 + 0.18 * sin(clock * 9.0 + i * 1.7) * sin(clock * 5.3 + i)
		brazier_lights[i].energy = f
	for i in range(door_sprites.size()):
		var col: Color = Rooms.ROOMS[i]["color"]
		var ds: Sprite2D = door_sprites[i]
		if rooms_done[i]:
			ds.texture = tex["gate_closed"]
			ds.modulate = Color(0.32, 0.32, 0.36)
			door_lights[i].energy = 0.0
		elif arena.door_open[i]:
			ds.texture = tex["gate_open"]
			ds.modulate = col.lerp(Color.WHITE, 0.3)
			door_lights[i].energy = 0.85 + 0.15 * sin(clock * 4.0 + i)
		else:
			ds.texture = tex["gate_closed"]
			ds.modulate = Color(0.55, 0.55, 0.62)
			door_lights[i].energy = 0.0
	if arena.gate_open:
		gate_sprite.texture = tex["gate_open"]
		gate_light.texture_scale = 520.0 / 128.0
		gate_light.color = Color8(255, 232, 160)
	else:
		gate_sprite.texture = tex["gate_closed"]
		gate_light.texture_scale = 240.0 / 128.0
		gate_light.color = Color8(214, 168, 86)


func update_camera(dt: float) -> void:
	var p = player
	camera.position = Vector2(p.x + p.vx * 0.12, p.y + p.vy * 0.12)


# ======================================================================== combat
func nearest_enemy(x: float, y: float, max_d: float):
	var best = null
	var bd: float = max_d * max_d
	for e in enemies:
		if e.spawn_t > 0.0 or e.hp <= 0.0:
			continue
		var d: float = (e.x - x) * (e.x - x) + (e.y - y) * (e.y - y)
		if d < bd:
			best = e
			bd = d
	return best


func build_grid() -> Dictionary:
	var gd: Dictionary = {}
	for e in enemies:
		var key := Vector2i(int(floor(e.x / 80.0)), int(floor(e.y / 80.0)))
		if not gd.has(key):
			gd[key] = []
		gd[key].append(e)
	return gd


func enemies_near(x: float, y: float, r: float) -> Array:
	## Live guardians whose body overlaps the circle (x, y, r), via the spatial grid.
	var reach: float = r + 42.0
	var out: Array = []
	for gx in range(int(floor((x - reach) / 80.0)), int(floor((x + reach) / 80.0)) + 1):
		for gy in range(int(floor((y - reach) / 80.0)), int(floor((y + reach) / 80.0)) + 1):
			var key := Vector2i(gx, gy)
			if not grid.has(key):
				continue
			for e in grid[key]:
				if e.hp > 0.0 and (e.x - x) * (e.x - x) + (e.y - y) * (e.y - y) < (r + e.r) * (r + e.r):
					out.append(e)
	return out


func purge_dead() -> void:
	var keep: Array = []
	for e in enemies:
		if e.hp > 0.0:
			keep.append(e)
	enemies = keep


func damage_enemy(e, dmg: float, dx: float, dy: float, force: float = 220.0) -> void:
	if e.hp <= 0.0:
		return
	e.hit(dmg, dx, dy, force)
	fx_burst(e.x, e.y, Color8(230, 255, 252), 5, 200.0, 0.25, 6.0)
	sfx("hit", 0.04)
	if e.hp <= 0.0:
		kill_enemy(e, true)


func kill_enemy(e, award: bool) -> void:
	var big: bool = e.kind == "elite" or e.kind == "bulwark"
	fx_diamonds(e.x, e.y, 14 if e.kind == "elite" else 7, 320.0, 0.7)
	fx_burst(e.x, e.y, Color8(255, 240, 190), 12 if big else 7, 260.0, 0.5, 9.0)
	fx_ring(e.x, e.y, Color8(255, 236, 170), 150.0 if e.kind == "elite" else 70.0, 0.35, 3.0)
	if award:
		kills += 1
		sfx("kill", 0.04)
		if not exit_open and e.pts > 0:   # the bar is full: guardians stay, but are worth nothing
			fx_text(e.x, e.y - 20.0, "+%d" % e.pts, Color8(255, 232, 150), 34 if e.kind == "elite" else 22)
			add_pride(e.pts)
		if e.kind == "elite":
			hearts.append(Ent.HeartPickup.new(e.x, e.y, false))
			shake = maxf(shake, 0.6)
			sfx("slam")
		if e.kind == "miniboss":
			on_miniboss_defeated(e)
	e.hp = 0.0


func dash_hits() -> void:
	var p = player
	for e in enemies:
		if e.hp > 0.0 and not p.dash_hit.has(e.id) and (e.x - p.x) * (e.x - p.x) + (e.y - p.y) * (e.y - p.y) < (e.r + 34.0) * (e.r + 34.0):
			p.dash_hit[e.id] = true
			damage_enemy(e, Cfg.DASH_DAMAGE * p.dmg_mult, p.dash_dx, p.dash_dy)
			fx_ring(e.x, e.y, Color8(90, 240, 225), 60.0, 0.2, 3.0)
	for sn in sentries:
		if sn.alive and not p.dash_hit.has(sn.get_instance_id()) and Vector2(sn.global_position.x - p.x, sn.global_position.y - p.y).length() < sn.radius + 34.0:
			p.dash_hit[sn.get_instance_id()] = true
			damage_sentry(sn, Cfg.DASH_DAMAGE * p.dmg_mult, p.dash_dx, p.dash_dy)
	purge_dead()


func spawn_spear(x: float, y: float, ux: float, uy: float) -> void:
	spears.append(Ent.Spear.new(x, y, ux, uy))
	sfx("spear", 0.08)


func update_shots(dt: float) -> void:
	var keep: Array = []
	for s in shots:
		s.life -= dt
		s.x += s.vx * dt
		s.y += s.vy * dt
		var dead: bool = s.life <= 0.0
		if not dead and arena.shot_blocked(s.x, s.y):
			dead = true
			fx_burst(s.x, s.y, Color8(90, 240, 225), 4, 120.0, 0.25, 5.0)
		if not dead:
			var cx: int = int(floor(s.x / 80.0))
			var cy: int = int(floor(s.y / 80.0))
			for gx in range(cx - 1, cx + 2):
				for gy in range(cy - 1, cy + 2):
					var key := Vector2i(gx, gy)
					if dead or not grid.has(key):
						continue
					for e in grid[key]:
						if s.hit.has(e.id) or e.hp <= 0.0 or e.spawn_t > 0.2:
							continue
						if (e.x - s.x) * (e.x - s.x) + (e.y - s.y) * (e.y - s.y) < (e.r + s.r) * (e.r + s.r):
							s.hit[e.id] = true
							damage_enemy(e, s.dmg, s.vx, s.vy)
							s.pierce -= 1
							if s.pierce < 0:
								dead = true
							break
		if not dead:
			for sn in sentries:
				if not sn.alive or s.hit.has(sn.get_instance_id()):
					continue
				if Vector2(sn.global_position.x - s.x, sn.global_position.y - s.y).length() < sn.radius + s.r:
					s.hit[sn.get_instance_id()] = true
					damage_sentry(sn, s.dmg, s.vx, s.vy)
					s.pierce -= 1
					if s.pierce < 0:
						dead = true
						break
		if not dead:
			keep.append(s)
	shots = keep
	purge_dead()


func update_spears(dt: float) -> void:
	var p = player
	var keep: Array = []
	for sp in spears:
		sp.life -= dt
		sp.x += sp.vx * dt
		sp.y += sp.vy * dt
		if sp.life <= 0.0 or arena.shot_blocked(sp.x, sp.y):
			continue
		if (sp.x - p.x) * (sp.x - p.x) + (sp.y - p.y) * (sp.y - p.y) < (p.r + 10.0) * (p.r + 10.0) and p.invuln <= 0.0:
			hurt_player(sp.vx, sp.vy)
			continue
		keep.append(sp)
	spears = keep


func contact_damage() -> void:
	var p = player
	if p.invuln > 0.0 or state != "play":
		return
	for e in enemies:
		if e.spawn_t > 0.0:
			continue
		var reach: float = e.r + p.r - 4.0
		if (e.x - p.x) * (e.x - p.x) + (e.y - p.y) * (e.y - p.y) < reach * reach:
			hurt_player(p.x - e.x, p.y - e.y)
			return


func hurt_player(dx: float, dy: float) -> void:
	var p = player
	p.hurt()
	var n: float = Vector2(dx, dy).length()
	if n < 0.000001:
		n = 1.0
	p.vx = dx / n * 520.0
	p.vy = dy / n * 520.0
	shake = maxf(shake, 0.5)
	red_flash = 0.3
	fx_burst(p.x, p.y, Color8(255, 90, 110), 12, 300.0, 0.5, 8.0)
	sfx("hurt")
	if hero != null:
		hero.play_hurt()
	if p.hp <= 0:
		state = "dying"
		dying_t = 1.1
		fx_diamonds(p.x, p.y, 24, 420.0, 1.0)
		fx_ring(p.x, p.y, Color8(255, 120, 140), 200.0, 0.8, 5.0)
		enemies = []
		spears = []
		shots = []
		waves = []
		bolts = []


func separate_enemies() -> void:
	var p = player
	for e in enemies:
		var cx: int = int(floor(e.x / 80.0))
		var cy: int = int(floor(e.y / 80.0))
		for gx in range(cx - 1, cx + 2):
			for gy in range(cy - 1, cy + 2):
				var key := Vector2i(gx, gy)
				if not grid.has(key):
					continue
				for o in grid[key]:
					if o.id <= e.id:
						continue
					var dx: float = o.x - e.x
					var dy: float = o.y - e.y
					var d2: float = dx * dx + dy * dy
					var rr: float = (e.r + o.r) * 0.85
					if d2 > 0.000001 and d2 < rr * rr:
						var d: float = sqrt(d2)
						var push: float = (rr - d) * 0.5
						var ux: float = dx / d
						var uy: float = dy / d
						if e.kind != "elite":
							e.x -= ux * push
							e.y -= uy * push
						if o.kind != "elite":
							o.x += ux * push
							o.y += uy * push
		var ddx: float = e.x - p.x
		var ddy: float = e.y - p.y
		var dd2: float = ddx * ddx + ddy * ddy
		var rr2: float = (e.r + p.r) * 0.55
		if dd2 > 0.000001 and dd2 < rr2 * rr2:
			var dd: float = sqrt(dd2)
			e.x += ddx / dd * (rr2 - dd)
			e.y += ddy / dd * (rr2 - dd)


# ======================================================================== weapons
func update_weapons(dt: float) -> void:
	var p = player
	# needle: piercing shots at the nearest guardian
	var nd: Dictionary = weapons["needle"]
	nd["cd"] = maxf(0.0, float(nd["cd"]) - dt)
	if float(nd["cd"]) <= 0.0 and not p.is_dashing():
		var target = nearest_enemy(p.x, p.y, Cfg.SHOT_RANGE)
		if target != null:
			var base: float = atan2(target.y - p.y, target.x - p.x)
			var n: int = mini(Cfg.SHOT_MAX_COUNT, 1 + p.bonus)
			for i in range(n):
				var a: float = base + deg_to_rad((float(i) - float(n - 1) / 2.0) * Cfg.SHOT_SPREAD_DEG)
				var ux: float = cos(a)
				var uy: float = sin(a)
				shots.append(Ent.Shot.new(p.x + ux * 26.0, p.y + uy * 26.0, ux * Cfg.SHOT_SPEED, uy * Cfg.SHOT_SPEED,
						Cfg.SHOT_DAMAGE * p.dmg_mult, Cfg.SHOT_PIERCE + p.pierce_bonus))
			nd["cd"] = Cfg.SHOT_COOLDOWN * p.rate_mult
			sfx("shoot", 0.05)
	if weapons.has("halo"):
		_update_halo(dt)
	if weapons.has("pulse"):
		_update_pulse(dt)
	if weapons.has("arc"):
		_update_arc(dt)


func _update_halo(dt: float) -> void:
	var p = player
	var w: Dictionary = weapons["halo"]
	var n: int = mini(Cfg.HALO_ORBS + Cfg.STAT_BONUS_CAP, Cfg.HALO_ORBS + p.bonus)
	w["ang"] = float(w["ang"]) + Cfg.HALO_SPEED / maxf(0.6, p.rate_mult) * dt
	var rad: float = Cfg.HALO_RADIUS * p.area
	var orbs: Array = []
	for i in range(n):
		var a: float = float(w["ang"]) + float(i) * TAU / float(n)
		orbs.append(Vector2(p.x + cos(a) * rad, p.y + sin(a) * rad))
	w["orbs"] = orbs
	var gap: Dictionary = w["gap"]
	for k in gap.keys():
		gap[k] = float(gap[k]) - dt
		if float(gap[k]) <= 0.0:
			gap.erase(k)
	var dmg: float = Cfg.HALO_DAMAGE * p.dmg_mult
	for i in range(orbs.size()):
		var o: Vector2 = orbs[i]
		for e in enemies_near(o.x, o.y, 18.0):
			var key: String = "%d_%d" % [i, e.id]
			if gap.has(key) or e.spawn_t > 0.2:
				continue
			gap[key] = Cfg.HALO_HIT_GAP * p.rate_mult
			damage_enemy(e, dmg, e.x - p.x, e.y - p.y, 170.0)
		for sp in spears:
			if (sp.x - o.x) * (sp.x - o.x) + (sp.y - o.y) * (sp.y - o.y) < 28.0 * 28.0:
				sp.life = 0.0
				fx_burst(sp.x, sp.y, Color8(255, 226, 140), 5, 160.0, 0.25, 5.0)


func _update_pulse(dt: float) -> void:
	var p = player
	var w: Dictionary = weapons["pulse"]
	w["cd"] = maxf(0.0, float(w["cd"]) - dt)
	var radius: float = Cfg.PULSE_RADIUS * p.area
	var echoes: Array = w["echoes"]
	for i in range(echoes.size() - 1, -1, -1):
		echoes[i] = float(echoes[i]) - dt
		if float(echoes[i]) <= 0.0:
			echoes.remove_at(i)
			_pulse_wave(radius)
	if float(w["cd"]) > 0.0:
		return
	if enemies_near(p.x, p.y, radius * 0.9).is_empty():
		return
	w["cd"] = Cfg.PULSE_COOLDOWN * p.rate_mult
	_pulse_wave(radius)
	for i in range(p.bonus / 2):
		echoes.append(0.3 * float(i + 1))


func _pulse_wave(radius: float) -> void:
	var p = player
	waves.append({"x": p.x, "y": p.y, "radius": radius, "t": 0.0, "hit": {}, "dmg": Cfg.PULSE_DAMAGE * p.dmg_mult})
	fx_ring(p.x, p.y, Color8(190, 140, 255), radius, 0.32, 9.0)
	fx_ring(p.x, p.y, Color8(255, 240, 255), radius * 0.8, 0.26, 4.0)
	sfx("pulse", 0.1)
	shake = maxf(shake, 0.12)


func update_waves(dt: float) -> void:
	var keep: Array = []
	for w in waves:
		w["t"] = float(w["t"]) + dt
		var k: float = minf(1.0, float(w["t"]) / 0.3)
		var r: float = float(w["radius"]) * (0.15 + 0.85 * k)
		for e in enemies_near(w["x"], w["y"], r):
			if w["hit"].has(e.id) or e.spawn_t > 0.2:
				continue
			w["hit"][e.id] = true
			damage_enemy(e, float(w["dmg"]), e.x - float(w["x"]), e.y - float(w["y"]), 560.0)
		for sp in spears:
			if (sp.x - float(w["x"])) * (sp.x - float(w["x"])) + (sp.y - float(w["y"])) * (sp.y - float(w["y"])) < r * r:
				sp.life = 0.0
		if float(w["t"]) < 0.3:
			keep.append(w)
	waves = keep


func _update_arc(dt: float) -> void:
	var p = player
	var w: Dictionary = weapons["arc"]
	w["cd"] = maxf(0.0, float(w["cd"]) - dt)
	if float(w["cd"]) > 0.0:
		return
	var target = nearest_enemy(p.x, p.y, Cfg.ARC_RANGE)
	if target == null:
		return
	w["cd"] = Cfg.ARC_COOLDOWN * p.rate_mult
	var jumps: int = mini(9, Cfg.ARC_JUMPS + p.bonus + p.pierce_bonus / 2)
	var reach: float = Cfg.ARC_JUMP_RANGE * p.area
	var dmg: float = Cfg.ARC_DAMAGE * p.dmg_mult
	var pts: Array = [Vector2(p.x, p.y)]
	var hit: Dictionary = {}
	var cur = target
	for i in range(jumps + 1):
		var prev: Vector2 = pts[pts.size() - 1]
		pts.append(Vector2(cur.x, cur.y))
		hit[cur.id] = true
		damage_enemy(cur, dmg, cur.x - prev.x, cur.y - prev.y, 90.0)
		var nxt = null
		var bd: float = reach * reach
		for e in enemies:
			if hit.has(e.id) or e.hp <= 0.0 or e.spawn_t > 0.2:
				continue
			var d: float = (e.x - cur.x) * (e.x - cur.x) + (e.y - cur.y) * (e.y - cur.y)
			if d < bd:
				nxt = e
				bd = d
		if nxt == null:
			break
		cur = nxt
	bolts.append({"pts": pts, "life": 0.2, "max": 0.2})
	sfx("arc", 0.06)


func update_bolts(dt: float) -> void:
	var keep: Array = []
	for b in bolts:
		b["life"] = float(b["life"]) - dt
		if float(b["life"]) > 0.0:
			keep.append(b)
	bolts = keep


# ======================================================================== progression
func add_pride(pts: int) -> void:
	if exit_open:
		return
	pride = minf(float(Cfg.PRIDE_MAX), pride + float(pts))
	bar_pulse = 0.25
	var new_stage: int = 1
	for m in stage_points:
		if pride >= float(m):
			new_stage += 1
	while stage < new_stage:
		stage += 1
		enemy_speed_mult = float(Cfg.STAGE_SPEED[stage])
		pending_elites += int(Cfg.ELITES_AT_STAGE.get(stage, 0))
		queue.append("weapon")   # every wave unlocks a weapon (a free upgrade once all are owned)
		show_banner(T("stage").replace("{n}", str(stage)) + ": " + T("stage_desc")[stage])
		for i in range(Rooms.OPEN_AT_STAGE.size()):
			if Rooms.OPEN_AT_STAGE[i] == stage and not rooms_done[i]:
				arena.door_open[i] = true
				sfx("gate")
				banner_text += "  |  " + Rooms.t(lang, "door_open")
	if pride >= float(Cfg.PRIDE_MAX):
		open_exit()


func open_exit() -> void:
	## The bar is full: the gate opens. The guardians that are out there stay.
	exit_open = true
	arena.gate_open = true
	sfx("gate")
	shake = maxf(shake, 0.7)


func bar_frac(pts: float) -> float:
	## Fill of the HUD bar: every wave gets an equal slice, whatever its point cost.
	var edges: Array = Cfg.BAR_EDGES
	var n: int = Cfg.NUM_STAGES
	for i in range(n):
		if pts <= float(edges[i + 1]):
			return (float(i) + (pts - float(edges[i])) / (float(edges[i + 1]) - float(edges[i]))) / float(n)
	return 1.0


func add_box_points(v: int) -> void:
	box_pts += v
	box_total += v
	box_pulse = 0.25
	while box_pts >= Cfg.upgrade_cost(box_upgrades):
		box_pts -= Cfg.upgrade_cost(box_upgrades)
		box_upgrades += 1
		queue.append("stat")


func check_progress() -> void:
	if state == "play" and not queue.is_empty():
		open_menu(queue.pop_front())


func open_menu(kind: String) -> void:
	var p = player
	var pool: Array = []
	if kind == "weapon":
		for w in UNLOCKABLE:
			if not weapons.has(w):
				pool.append(w)
	else:
		var has_area: bool = weapons.has("halo") or weapons.has("pulse") or weapons.has("arc")
		for u in UPGRADE_IDS:
			if u == "multi" and p.bonus >= Cfg.STAT_BONUS_CAP:
				continue
			if u == "rate" and p.rate_mult <= Cfg.STAT_RATE_FLOOR + 0.000001:
				continue
			if u == "pierce" and p.pierce_bonus >= Cfg.STAT_PIERCE_CAP:
				continue
			if u == "area" and not has_area:
				continue
			if u == "dash" and p.charge_cap >= Cfg.DASH_CHARGES_CAP:
				continue
			if u == "heart" and p.max_hp >= Cfg.PLAYER_HP_CAP:
				continue
			pool.append(u)
	if pool.is_empty() and kind == "weapon":   # every weapon owned: the wave gives a free upgrade instead
		open_menu("stat")
		return
	if pool.is_empty():
		return
	pool.shuffle()
	choice_kind = kind
	choices = pool.slice(0, mini(3, pool.size()))
	choice_sel = 0
	state = "upgrade"
	sfx("upgrade_open")


func pick_upgrade(idx: int) -> void:
	if idx >= choices.size():
		return
	var uid: String = choices[idx]
	var p = player
	if choice_kind == "weapon":
		if uid == "halo":
			weapons["halo"] = {"ang": 0.0, "gap": {}, "orbs": []}
		elif uid == "pulse":
			weapons["pulse"] = {"cd": 0.25, "echoes": []}
		else:
			weapons["arc"] = {"cd": 0.25}
		sfx("weapon")
		show_banner(T("weapon_new") + ": " + T("weapons")[uid][0])
	else:
		if uid == "multi":
			p.bonus = mini(Cfg.STAT_BONUS_CAP, p.bonus + 1)
		elif uid == "rate":
			p.rate_mult = maxf(Cfg.STAT_RATE_FLOOR, p.rate_mult * Cfg.STAT_RATE_STEP)
		elif uid == "pierce":
			p.pierce_bonus = mini(Cfg.STAT_PIERCE_CAP, p.pierce_bonus + 1)
		elif uid == "power":
			p.dmg_mult += Cfg.STAT_DAMAGE_STEP
		elif uid == "area":
			p.area += Cfg.STAT_AREA_STEP
		elif uid == "dash":
			p.charge_cap = mini(Cfg.DASH_CHARGES_CAP, p.charge_cap + 1)
			p.charges = mini(p.charge_cap, p.charges + 1)
			p.recharge *= 0.9
		elif uid == "speed":
			p.speed *= 1.10
		elif uid == "heart":
			p.max_hp = mini(Cfg.PLAYER_HP_CAP, p.max_hp + 1)
			p.hp = mini(p.max_hp, p.hp + 1)
		sfx("upgrade_pick")
	state = "play"
	fx_ring(p.x, p.y, Color8(255, 232, 150), 160.0, 0.5, 4.0)
	fx_diamonds(p.x, p.y, 12, 260.0, 0.7)


func update_hearts(dt: float) -> void:
	var p = player
	var keep: Array = []
	for h in hearts:
		if not h.alive:
			h.timer -= dt
			if h.respawns and h.timer <= 0.0:
				h.alive = true
			if h.respawns or h.alive:
				keep.append(h)
			continue
		if p.hp < p.max_hp and (h.x - p.x) * (h.x - p.x) + (h.y - p.y) * (h.y - p.y) < (p.r + 26.0) * (p.r + 26.0):
			p.hp += 1
			h.alive = false
			h.timer = Cfg.HEART_RESPAWN
			sfx("heart")
			fx_burst(h.x, h.y, Color8(255, 110, 130), 12, 260.0, 0.5, 8.0)
			fx_text(h.x, h.y - 26.0, "+1", Color8(255, 130, 150), 26)
			if not h.respawns:
				continue
		keep.append(h)
	hearts = keep


# ======================================================================== boxes and gems
func box_spot(min_player_dist: float):
	var p = player
	for i in range(40):
		var x: float = randf_range(140.0, Cfg.ARENA - 140.0)
		var y: float = randf_range(140.0, Cfg.ARENA - 140.0)
		if not arena.is_free(x, y, 34.0):
			continue
		if min_player_dist > 0.0 and (x - p.x) * (x - p.x) + (y - p.y) * (y - p.y) < min_player_dist * min_player_dist:
			continue
		if _box_near(x, y):
			continue
		return Vector2(x, y)
	return null


func _box_near(x: float, y: float) -> bool:
	for b in boxes:
		if (b.x - x) * (b.x - x) + (b.y - y) * (b.y - y) < 85.0 * 85.0:
			return true
	return false


func add_box(x: float, y: float) -> void:
	boxes.append(Ent.Box.new(x, y, randf() < Cfg.BOX_GILDED_CHANCE))


func _populate_boxes() -> void:
	var s: Vector2 = player_start
	for i in range(4):   # a few right by the start so the idea is obvious
		for k in range(20):
			var a: float = -PI / 2.0 + (float(i) - 1.5) * 0.7
			var d: float = randf_range(230.0, 330.0)
			var x: float = s.x + cos(a) * d
			var y: float = s.y + sin(a) * d
			if arena.is_free(x, y, 34.0) and not _box_near(x, y):
				boxes.append(Ent.Box.new(x, y, false))
				break
	var tries: int = 0
	while boxes.size() < Cfg.BOX_START and tries < 400:   # clusters of 3-6 across the map
		tries += 1
		var c = box_spot(0.0)
		if c == null:
			continue
		for n in range(randi_range(3, 6)):
			for k in range(10):
				var a2: float = randf_range(0.0, TAU)
				var d2: float = randf_range(60.0, 190.0)
				var x2: float = c.x + cos(a2) * d2
				var y2: float = c.y + sin(a2) * d2
				if arena.is_free(x2, y2, 34.0) and not _box_near(x2, y2):
					add_box(x2, y2)
					break


func break_box(b) -> void:
	var vals: Array = Cfg.BOX_GILDED_GEMS if b.gilded else Cfg.BOX_CRATE_GEMS
	var total: int = 0
	for v in vals:
		gems.append(Ent.Gem.new(b.x, b.y, int(v)))
		total += int(v)
	fx_burst(b.x, b.y, Color8(255, 220, 120) if b.gilded else Color8(200, 192, 232), 14, 300.0, 0.55, 9.0)
	fx_burst(b.x, b.y, Color8(80, 235, 205), 6, 220.0, 0.4, 7.0)
	fx_ring(b.x, b.y, Color8(200, 255, 240), 80.0, 0.3, 3.0)
	fx_text(b.x, b.y - 24.0, "+%d" % total, Color8(80, 235, 205), 20)
	sfx("box", 0.03)
	shake = maxf(shake, 0.06)


func update_boxes(dt: float) -> void:
	var p = player
	var reach: float = Ent.Box.RADIUS + p.r
	var alive: Array = []
	for b in boxes:
		if (b.x - p.x) * (b.x - p.x) + (b.y - p.y) * (b.y - p.y) < reach * reach:
			break_box(b)
		else:
			alive.append(b)
	boxes = alive
	# restock, always out of view
	box_timer -= dt
	if box_timer <= 0.0 and room == 0:
		box_timer = Cfg.BOX_RESPAWN
		if boxes.size() < Cfg.BOX_TARGET:
			var spot = box_spot(Cfg.BOX_RESPAWN_MIN_DIST)
			if spot != null:
				add_box(spot.x, spot.y)
	# gems: scatter, then fly to the hero
	var keep: Array = []
	for gm in gems:
		gm.age += dt
		gm.life -= dt
		if gm.life <= 0.0:
			continue
		var dx: float = p.x - gm.x
		var dy: float = p.y - gm.y
		var d: float = sqrt(dx * dx + dy * dy)
		if d < 0.000001:
			d = 1.0
		if gm.age > 0.3 and d < Cfg.GEM_MAGNET:
			var spd: float = 420.0 + (1.0 - d / Cfg.GEM_MAGNET) * (Cfg.GEM_SPEED - 420.0)
			var k: float = minf(1.0, 12.0 * dt)
			gm.vx += (dx / d * spd - gm.vx) * k
			gm.vy += (dy / d * spd - gm.vy) * k
		else:
			var f: float = maxf(0.0, 1.0 - 5.0 * dt)
			gm.vx *= f
			gm.vy *= f
		gm.x += gm.vx * dt
		gm.y += gm.vy * dt
		gm.x = clampf(gm.x, 20.0, Cfg.ARENA - 20.0)
		gm.y = clampf(gm.y, 20.0, Cfg.ARENA - 20.0)
		if d < p.r + 16.0 and gm.age > 0.15:
			add_box_points(gm.val)
			gem_acc += gm.val
			gem_acc_t = 0.35
			fx_burst(p.x, p.y, Color8(80, 235, 205), 3, 140.0, 0.25, 4.0)
			sfx("gem", 0.05)
			continue
		keep.append(gm)
	if keep.size() > 400:
		keep = keep.slice(keep.size() - 400)
	gems = keep
	if gem_acc > 0:
		gem_acc_t -= dt
		if gem_acc_t <= 0.0:
			fx_text(p.x, p.y - 38.0, "+%d" % gem_acc, Color8(80, 235, 205), 20)
			gem_acc = 0


# ======================================================================== spawning
func spawn_center(ang_in: float = 999.0) -> Vector2:
	## A point on a ring just outside the screen, in a free spot of the arena.
	var p = player
	var ang: float = ang_in
	for i in range(14):
		var a: float = ang if ang < 900.0 else randf_range(0.0, TAU)
		var d: float = randf_range(Cfg.SPAWN_DIST[0], Cfg.SPAWN_DIST[1])
		var x: float = clampf(p.x + cos(a) * d, 40.0, Cfg.ARENA - 40.0)
		var y: float = clampf(p.y + sin(a) * d, 40.0, Cfg.ARENA - 40.0)
		if Vector2(x - p.x, y - p.y).length() >= Cfg.MIN_SPAWN_DISTANCE and arena.is_free(x, y, 30.0):
			return Vector2(x, y)
		ang = 999.0
	var far: Array = []
	for pt in spawn_pts:
		if Vector2(pt.x - p.x, pt.y - p.y).length() > Cfg.MIN_SPAWN_DISTANCE:
			far.append(pt)
	if far.is_empty():
		far = spawn_pts
	return far[randi() % far.size()]


func spawn_enemy(kind: String, x: float, y: float) -> void:
	var hp_scale: float = float(Cfg.STAGE_HP[stage])
	if kind == "elite":
		hp_scale = 1.0 + 0.15 * maxf(0.0, float(stage - 4))
	var st: Dictionary = Cfg.ENEMIES[kind]
	var np: Vector2 = arena.collide(Vector2(x, y), float(st["r"]), false)
	enemies.append(Ent.Enemy.new(kind, np.x, np.y, hp_scale, next_id))
	next_id += 1


func recycle_far() -> void:
	## Guardians left far behind jump back to the edge of the action so the alive cap is not wasted.
	var p = player
	var lim: float = Cfg.RECYCLE_DISTANCE * Cfg.RECYCLE_DISTANCE
	for e in enemies:
		if (e.x - p.x) * (e.x - p.x) + (e.y - p.y) * (e.y - p.y) > lim and e.charge_t <= 0.0:
			var c: Vector2 = spawn_center()
			e.x = c.x
			e.y = c.y
			e.spawn_t = 0.35


func update_director(dt: float) -> void:
	if room > 0:
		return
	if exit_open and not Cfg.SPAWN_AFTER_EXIT:
		return
	var st: Dictionary = Cfg.STAGES[stage]
	recycle_t -= dt
	if recycle_t <= 0.0:
		recycle_t = 0.5
		recycle_far()
	if pending_elites > 0:   # elites arrive one at a time when a wave begins
		elite_t -= dt
		if elite_t <= 0.0:
			pending_elites -= 1
			elite_t = 2.0
			var c: Vector2 = spawn_center()
			spawn_enemy("elite", c.x, c.y)
			sfx("elite")
			fx_ring(c.x, c.y, Color8(255, 220, 120), 220.0, 0.8, 6.0)
	spawn_t -= dt
	if spawn_t > 0.0:
		return
	spawn_t = float(st["interval"]) * randf_range(0.85, 1.15)
	var cap: float = float(mini(int(st["cap"]), Cfg.MAX_ENEMIES))
	var room: int = int(cap) - enemies.size()
	if room <= 0:
		return
	var kinds: Array = []
	var spread: float = 70.0
	var n: int = 0
	if randf() < float(st["swarm"]):   # a pack of fast swarmers
		n = mini(room, randi_range(int(Cfg.SWARM_PACK[0]), int(Cfg.SWARM_PACK[1])))
		for i in range(n):
			kinds.append("swarmer")
		spread = 95.0
	else:
		n = mini(room, randi_range(int(st["group"][0]), int(st["group"][1])))
		var lancers: int = 0
		for e in enemies:
			if e.kind == "lancer":
				lancers += 1
		for i in range(n):
			var k: String = Util.weighted_choice(st["weights"])
			if k == "lancer":   # never a storm of spears: extras become sentinels
				if lancers >= Cfg.LANCER_CAP:
					k = "sentinel"
				else:
					lancers += 1
			kinds.append(k)
	var centers: Array = [spawn_center()]
	if bool(st["pincer"]) and n >= 4:   # half the group comes from the opposite side
		var p = player
		var a: float = atan2(centers[0].y - p.y, centers[0].x - p.x) + PI + randf_range(-0.5, 0.5)
		centers.append(spawn_center(a))
	for i in range(kinds.size()):
		var cc: Vector2 = centers[i % centers.size()]
		var ang: float = randf_range(0.0, TAU)
		var rad: float = randf_range(0.0, spread)
		spawn_enemy(kinds[i], clampf(cc.x + cos(ang) * rad, 30.0, Cfg.ARENA - 30.0), clampf(cc.y + sin(ang) * rad, 30.0, Cfg.ARENA - 30.0))


# ======================================================================== lives, restart, sentries, camera limits
func _apply_camera_limits() -> void:
	var b: Rect2 = arena.bounds
	camera.limit_left = int(b.position.x - Cfg.WALL)
	camera.limit_top = int(b.position.y - Cfg.WALL)
	camera.limit_right = int(b.end.x + Cfg.WALL)
	camera.limit_bottom = int(b.end.y + Cfg.WALL)


func restart_level() -> void:
	deaths += 1
	_new_run()
	fade = 1.0
	show_banner(str(Rooms.t(lang, "restart")))


func kill_player() -> void:
	if state != "play":
		return
	player.hp = 1
	hurt_player(0.0, 0.0)


func check_lethal() -> void:
	if state != "play" or player.invuln > 0.0 or hero == null:
		return
	var hb = hero.get_node_or_null("Hurtbox")
	if hb == null:
		return
	for a in hb.get_overlapping_areas():
		if a.is_in_group("lethal"):
			kill_player()
			return


func update_sentries(dt: float) -> void:
	if room != 0:
		return
	for sn in sentries:
		sn.step(dt, arena)


func damage_sentry(sn, dmg: float, dx: float, dy: float) -> void:
	sn.take_hit(dmg)
	fx_burst(sn.global_position.x, sn.global_position.y, Color8(255, 190, 150), 5, 200.0, 0.25, 6.0)
	sfx("hit", 0.04)
	if not sn.alive:
		kills += 1
		sfx("kill", 0.04)
		fx_diamonds(sn.global_position.x, sn.global_position.y, 12, 320.0, 0.7)
		fx_ring(sn.global_position.x, sn.global_position.y, Color8(255, 190, 120), 110.0, 0.35, 3.0)
		fx_text(sn.global_position.x, sn.global_position.y - 24.0, "+10", Color8(255, 232, 150), 26)
		add_pride(10)


# ======================================================================== mini-boss rooms
func all_braziers() -> Array:
	var out: Array = brazier_positions.duplicate()
	for d in Rooms.ROOMS:
		out.append_array(d["braziers"])
	return out


func _snap_camera() -> void:
	var b: Rect2 = arena.bounds
	var tx: float = player.x - Cfg.SCREEN_W / 2.0
	var ty: float = player.y - Cfg.SCREEN_H / 2.0
	cam_pos.x = clampf(tx, b.position.x - Cfg.WALL, b.end.x + Cfg.WALL - Cfg.SCREEN_W)
	cam_pos.y = clampf(ty, b.position.y - Cfg.WALL, b.end.y + Cfg.WALL - Cfg.SCREEN_H)
	_apply_camera_limits()
	camera.position = Vector2(player.x, player.y)
	camera.reset_smoothing()


func check_doors() -> void:
	if room != 0 or state != "play":
		return
	var p = player
	for i in range(3):
		if not arena.door_open[i] or rooms_done[i]:
			continue
		var inside: bool = false
		if i == 0:
			inside = p.y > Cfg.ARENA + 20.0 and p.x > Rooms.SPAN_LO and p.x < Rooms.SPAN_HI
		elif i == 1:
			inside = p.x > Cfg.ARENA + 20.0 and p.y > Rooms.SPAN_LO and p.y < Rooms.SPAN_HI
		else:
			inside = p.x < -20.0 and p.y > Rooms.SPAN_LO and p.y < Rooms.SPAN_HI
		if inside:
			enter_room(i)
			return


func enter_room(i: int) -> void:
	## One on one: the guardians of the main arena stay behind, frozen, until you come back.
	var d: Dictionary = Rooms.ROOMS[i]
	main_enemies = enemies
	enemies = []
	spears = []
	shots = []
	waves = []
	bolts = []
	room = i + 1
	arena.set_room(room)
	var sp: Vector2 = d["spawn"]
	player.x = sp.x
	player.y = sp.y
	player.vx = 0.0
	player.vy = 0.0
	player.dash_t = 0.0
	player.invuln = maxf(player.invuln, 1.2)
	portal_open = false
	var bp: Vector2 = d["boss"]
	enemies.append(Ent.Enemy.new("miniboss", bp.x, bp.y, 1.0, next_id, i))
	next_id += 1
	grid = build_grid()
	fade = 1.0
	shake = 0.0
	sfx("elite")
	show_banner(str(Rooms.t(lang, "names")[i]) + "  |  " + str(Rooms.t(lang, "enter_room")))
	_snap_camera()


func on_miniboss_defeated(e) -> void:
	rooms_done[room - 1] = true
	portal_open = true
	queue.append("reward")   # the extra upgrade
	hearts.append(Ent.HeartPickup.new(e.x - 70.0, e.y, false))
	hearts.append(Ent.HeartPickup.new(e.x + 70.0, e.y, false))
	spears = []
	shake = maxf(shake, 1.0)
	sfx("slam")
	sfx("win")
	fx_diamonds(e.x, e.y, 40, 600.0, 1.4)
	fx_ring(e.x, e.y, Color8(255, 226, 140), 420.0, 0.9, 12.0)
	show_banner(str(Rooms.t(lang, "boss_dead")) + "  |  " + str(Rooms.t(lang, "to_portal")))


func check_portal() -> void:
	if room == 0 or not portal_open or state != "play":
		return
	var pp: Vector2 = Rooms.ROOMS[room - 1]["portal"]
	if Vector2(player.x - pp.x, player.y - pp.y).length() < 70.0:
		leave_room()


func leave_room() -> void:
	var idx: int = room - 1
	var d: Dictionary = Rooms.ROOMS[idx]
	arena.door_open[idx] = false   # the door is sealed once its boss is beaten
	room = 0
	arena.set_room(0)
	portal_open = false
	enemies = main_enemies
	main_enemies = []
	spears = []
	shots = []
	var ret: Vector2 = d["ret"]
	player.x = ret.x
	player.y = ret.y
	player.vx = 0.0
	player.vy = 0.0
	player.invuln = maxf(player.invuln, 1.2)
	# guardians that were waiting near the door are moved back, so you do not land in a crowd
	for e in enemies:
		var off := Vector2(e.x - ret.x, e.y - ret.y)
		if off.length() < 420.0:
			if off.length() < 1.0:
				off = Vector2(Cfg.ARENA / 2.0 - ret.x, Cfg.ARENA / 2.0 - ret.y)
			var np: Vector2 = arena.collide(ret + off.normalized() * 420.0, e.r, false)
			e.x = np.x
			e.y = np.y
	grid = build_grid()
	fade = 1.0
	_snap_camera()


# ======================================================================== effects
func fx_burst(x: float, y: float, color: Color, n: int, speed: float, life: float, size: float) -> void:
	for i in range(n):
		var a: float = randf_range(0.0, TAU)
		var sp: float = randf_range(0.35, 1.0) * speed
		var pt := Ent.Particle.new()
		pt.kind = "spark"
		pt.x = x
		pt.y = y
		pt.vx = cos(a) * sp
		pt.vy = sin(a) * sp
		pt.max_life = life
		pt.life = life * randf_range(0.6, 1.0)
		pt.color = color
		pt.size = size * randf_range(0.6, 1.1)
		parts.append(pt)


func fx_diamonds(x: float, y: float, n: int, speed: float, life: float) -> void:
	var cols: Array = [Color8(244, 204, 96), Color8(255, 244, 190), Color8(255, 255, 255)]
	for i in range(n):
		var a: float = randf_range(0.0, TAU)
		var sp: float = randf_range(0.3, 1.0) * speed
		var pt := Ent.Particle.new()
		pt.kind = "diamond"
		pt.x = x
		pt.y = y
		pt.vx = cos(a) * sp
		pt.vy = sin(a) * sp
		pt.max_life = life
		pt.life = life * randf_range(0.7, 1.0)
		pt.color = cols[randi() % cols.size()]
		pt.size = randf_range(5.0, 9.0)
		pt.extra = randf_range(0.0, TAU)
		parts.append(pt)


func fx_ring(x: float, y: float, color: Color, radius: float, life: float, width: float) -> void:
	var pt := Ent.Particle.new()
	pt.kind = "ring"
	pt.x = x
	pt.y = y
	pt.life = life
	pt.max_life = life
	pt.color = color
	pt.size = radius
	pt.extra = width
	parts.append(pt)


func fx_text(x: float, y: float, s: String, color: Color, size: int) -> void:
	var pt := Ent.Particle.new()
	pt.kind = "text"
	pt.x = x
	pt.y = y
	pt.vy = -60.0
	pt.life = 0.8
	pt.max_life = 0.8
	pt.color = color
	pt.size = float(size)
	pt.text = s
	parts.append(pt)


func fx_ghost(x: float, y: float, facing: float) -> void:
	var pt := Ent.Particle.new()
	pt.kind = "ghost"
	pt.x = x
	pt.y = y
	pt.life = 0.22
	pt.max_life = 0.22
	pt.angle = facing
	parts.append(pt)


func update_fx(dt: float) -> void:
	var keep: Array = []
	for pt in parts:
		pt.life -= dt
		if pt.life <= 0.0:
			continue
		pt.x += pt.vx * dt
		pt.y += pt.vy * dt
		if pt.kind == "spark" or pt.kind == "diamond":
			var drag: float = 1.0 - minf(1.0, 4.0 * dt)
			pt.vx *= drag
			pt.vy *= drag
		keep.append(pt)
	if keep.size() > 900:
		keep = keep.slice(keep.size() - 900)
	parts = keep


# ======================================================================== drawing (world)
func _visible(x: float, y: float, pad: float) -> bool:
	return x > cam_pos.x - pad and x < cam_pos.x + Cfg.SCREEN_W + pad and y > cam_pos.y - pad and y < cam_pos.y + Cfg.SCREEN_H + pad


func draw_sprite(node: CanvasItem, t: Texture2D, pos: Vector2, angle: float, sc: float, mod: Color) -> void:
	node.draw_set_transform(pos, angle, Vector2(sc, sc))
	node.draw_texture(t, -t.get_size() * 0.5, mod)
	node.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func draw_glow(node: CanvasItem, pos: Vector2, radius: float, color: Color) -> void:
	var sc: float = radius / 128.0
	node.draw_set_transform(pos, 0.0, Vector2(sc, sc))
	node.draw_texture(tex["glow"], Vector2(-128.0, -128.0), color)
	node.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func draw_shadow(pos: Vector2, w: float) -> void:
	draw_set_transform(pos, 0.0, Vector2(w / 256.0, w * 0.55 / 256.0))
	draw_texture(tex["glow"], Vector2(-128.0, -128.0), Color(0, 0, 0, 0.6))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw() -> void:
	# heart pickups
	for h in hearts:
		if h.alive and _visible(h.x, h.y, 60.0):
			var bob: float = sin(clock * 3.0 + h.x) * 4.0
			draw_shadow(Vector2(h.x, h.y + 16.0), 40.0)
			draw_sprite(self, tex["heart_full"], Vector2(h.x, h.y + bob), 0.0, 1.0, Color.WHITE)
	# boxes
	for b in boxes:
		if _visible(b.x, b.y, 60.0):
			_draw_box(b)
	# gems
	for gm in gems:
		if _visible(gm.x, gm.y, 40.0):
			var s: float = 0.7 + 0.04 * float(gm.val)
			var pulse: float = 1.0 + 0.12 * sin(clock * 8.0 + gm.age * 5.0)
			s *= pulse
			var c := Vector2(gm.x, gm.y)
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -13) * s, c + Vector2(9, 0) * s, c + Vector2(0, 13) * s, c + Vector2(-9, 0) * s]), GEM_COLOR)
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -9) * s, c + Vector2(5, -1) * s, c + Vector2(0, 2) * s, c + Vector2(-5, -1) * s]), Color(0.85, 1.0, 0.97))

	# the Ferryman by the altar
	var fpos: Vector2 = ferry_pos
	var drawables: Array = [[fpos.y, "ferry", null]]
	for e in enemies:
		drawables.append([e.y, "enemy", e])
	drawables.sort_custom(func(a, b): return a[0] < b[0])
	for d in drawables:
		if d[1] == "ferry":
			draw_shadow(fpos + Vector2(0, 20), 56.0)
			var ang: float = atan2(player.x - fpos.x, -(player.y - fpos.y)) * 0.4
			draw_sprite(self, tex["ferryman"], fpos + Vector2(0, sin(clock * 1.6) * 2.0), ang, 1.0, Color.WHITE)
		elif d[1] == "enemy":
			_draw_enemy(d[2])
		else:
			_draw_player(d[2])

	# projectiles
	for s in shots:
		draw_sprite(self, tex["needle"], Vector2(s.x, s.y), atan2(s.vy, s.vx), 1.0, Color.WHITE)
	for sp in spears:
		draw_sprite(self, tex["spear"], Vector2(sp.x, sp.y), atan2(sp.vy, sp.vx), 1.0, Color.WHITE)
	_draw_telegraphs()
	if room > 0 and portal_open:
		var pp: Vector2 = Rooms.ROOMS[room - 1]["portal"]
		draw_arc(pp, 46.0 + 4.0 * sin(clock * 4.0), 0.0, TAU, 40, Color8(80, 235, 215), 4.0, true)
		draw_arc(pp, 30.0, 0.0, TAU, 32, Color8(255, 226, 140), 3.0, true)
	# halo orbs
	if weapons.has("halo"):
		for o in weapons["halo"]["orbs"]:
			draw_circle(o, 11.0, Color8(255, 226, 140))
			draw_circle(o, 6.0, Color8(255, 255, 240))


func _draw_box(b) -> void:
	var c := Vector2(b.x, b.y)
	var body: Color = Color8(232, 184, 74) if b.gilded else Color8(146, 138, 184)
	var edge: Color = Color8(96, 62, 18) if b.gilded else Color8(38, 32, 66)
	var band: Color = Color8(255, 236, 160) if b.gilded else Color8(236, 196, 92)
	var light: Color = Color8(255, 244, 196) if b.gilded else Color8(190, 182, 224)
	draw_rect(Rect2(c + Vector2(-23, -18), Vector2(48, 46)), Color(0, 0, 0, 0.28))
	draw_rect(Rect2(c + Vector2(-26, -24), Vector2(52, 48)), edge)
	draw_rect(Rect2(c + Vector2(-23, -21), Vector2(46, 42)), body)
	draw_rect(Rect2(c + Vector2(-23, -21), Vector2(46, 11)), light)
	draw_rect(Rect2(c + Vector2(-4, -24), Vector2(8, 48)), band)
	draw_rect(Rect2(c + Vector2(-26, -4), Vector2(52, 8)), band)
	for corner in [Vector2(-19, -17), Vector2(19, -17), Vector2(-19, 17), Vector2(19, 17)]:
		draw_circle(c + corner, 4.0, edge)
		draw_circle(c + corner, 3.0, band)
	draw_colored_polygon(PackedVector2Array([c + Vector2(0, -8), c + Vector2(8, 0), c + Vector2(0, 8), c + Vector2(-8, 0)]), edge)
	draw_colored_polygon(PackedVector2Array([c + Vector2(0, -6), c + Vector2(6, 0), c + Vector2(0, 6), c + Vector2(-6, 0)]), band)


func _draw_enemy(e) -> void:
	if not _visible(e.x, e.y, 340.0):
		return
	var pos := Vector2(e.x, e.y)
	draw_shadow(pos + Vector2(0, e.r * 0.55), e.shadow)
	var t: Texture2D
	var sc: float = 1.0
	var mod: Color = Color.WHITE
	if VARIANTS.has(e.kind):
		var v: Dictionary = VARIANTS[e.kind]
		t = tex[v["tex"]]
		sc = float(v["scale"])
		mod = v["tint"]
	elif e.kind == "miniboss":
		var mbv: Dictionary = Rooms.MINIBOSS[e.variant]
		t = tex["guardian_elite"]
		sc = float(mbv["scale"])
		mod = mbv["tint"]
	else:
		t = tex["guardian_" + e.kind]
	var enraged: bool = e.kind == "bulwark" and e.hp < e.max_hp * Cfg.BULWARK_ENRAGE
	if e.flash > 0.0:
		mod = Color(2.2, 2.2, 2.2, 1.0)
	elif enraged or (e.kind == "skirmisher" and e.charge_t > 0.0):
		mod = Color(1.6, 0.6, 0.6, 1.0)
	if e.spawn_t > 0.0:
		var k: float = 1.0 - e.spawn_t / 0.35
		sc *= 0.6 + 0.4 * k
		mod.a = k
	var bob: float = sin(e.t * 3.0) * 2.0
	draw_sprite(self, t, pos + Vector2(0, bob), e.face, sc, mod)
	var n: int = int(SHARDS.get(e.kind, 0))
	var rad: float = e.r + 18.0 + (6.0 if e.kind == "elite" else 0.0)
	var shard: Texture2D = tex["shard"]
	for i in range(n):
		var a: float = e.t * 1.6 + float(i) * TAU / float(n)
		draw_texture(shard, pos + Vector2(cos(a) * rad, sin(a) * rad * 0.9 + bob) - shard.get_size() * 0.5)
	if (e.kind == "elite" or e.kind == "bulwark") and e.hp < e.max_hp:
		var w: float = 70.0 if e.kind == "elite" else 54.0
		draw_rect(Rect2(pos.x - w / 2.0, pos.y - e.r - 34.0, w, 7.0), Color8(20, 18, 34))
		draw_rect(Rect2(pos.x - w / 2.0, pos.y - e.r - 34.0, w * maxf(0.0, e.hp) / e.max_hp, 7.0), Color8(244, 204, 96))


func _draw_player(p) -> void:
	var pos := Vector2(p.x, p.y)
	draw_shadow(pos + Vector2(0, 16), 46.0)
	var mod: Color = Color.WHITE
	if p.invuln > 0.0 and not p.is_dashing() and int(clock * 18.0) % 2 == 0:
		mod.a = 0.43
	draw_sprite(self, tex["hero"], pos, p.facing, 1.0, mod)


func _draw_telegraphs() -> void:
	for e in enemies:
		if e.windup <= 0.0:
			continue
		var pos := Vector2(e.x, e.y)
		var dir := Vector2(e.cdx, e.cdy)
		if e.kind == "lancer":
			var k: float = 1.0 - e.windup / Cfg.SPEAR_WINDUP
			draw_line(pos, pos + dir * 520.0, Color(1.0, 0.78 + 0.16 * k, 0.47), 2.0)
		elif e.kind == "elite":
			draw_line(pos, pos + dir * 360.0, Color8(255, 210, 110), 4.0)
		elif e.kind == "skirmisher":
			draw_line(pos, pos + dir * Cfg.LUNGE_RANGE, Color8(255, 120, 120), 2.0)
		elif e.kind == "miniboss":
			if e.act == 2:
				draw_arc(pos, 70.0 + 120.0 * (1.0 - e.windup / e.windup_max), 0.0, TAU, 40, Color8(255, 210, 110), 3.0, true)
			else:
				draw_line(pos, pos + dir * (420.0 if e.act == 0 else 560.0), Color8(255, 210, 110), 4.0 if e.act == 0 else 2.0)


# ======================================================================== drawing (glow / particle layers)
func draw_fx(node: CanvasItem, mode: int) -> void:
	if mode == 0:
		_draw_fx_add(node)
	else:
		_draw_fx_norm(node)


func _draw_fx_add(node: CanvasItem) -> void:
	# brazier flames
	var bl: Array = all_braziers()
	for i in range(bl.size()):
		var b: Vector2 = bl[i]
		if not _visible(b.x, b.y, 80.0):
			continue
		var f: float = 0.85 + 0.15 * sin(clock * 11.0 + i * 2.1)
		draw_glow(node, b + Vector2(0, -4), 34.0 * f, Color8(255, 150, 40))
		draw_glow(node, b + Vector2(sin(clock * 7.0 + i) * 2.0, -8.0 - 3.0 * f), 16.0 * f, Color8(255, 240, 170))
	if arena.gate_open:
		draw_glow(node, Vector2((Cfg.GATE_X0 + Cfg.GATE_X1) / 2.0, 30.0), 220.0, Color(0.43, 0.35, 0.16, 1.0))
	if room > 0 and portal_open:
		draw_glow(node, Rooms.ROOMS[room - 1]["portal"], 80.0 + 8.0 * sin(clock * 4.0), Color(0.1, 0.5, 0.45, 1.0))
	for h in hearts:
		if h.alive and _visible(h.x, h.y, 80.0):
			draw_glow(node, Vector2(h.x, h.y), 40.0, Color(0.5, 0.12, 0.18, 1.0))
	for gm in gems:
		if _visible(gm.x, gm.y, 40.0):
			draw_glow(node, Vector2(gm.x, gm.y), 22.0, Color(0.12, 0.4, 0.34, 1.0))
	for s in shots:
		draw_glow(node, Vector2(s.x, s.y), 30.0, Color(0.2, 0.78, 0.75, 1.0))
	for sp in spears:
		draw_glow(node, Vector2(sp.x, sp.y), 34.0, Color(0.55, 0.45, 0.2, 1.0))
	if weapons.has("halo"):
		for o in weapons["halo"]["orbs"]:
			draw_glow(node, o, 30.0, Color(0.47, 0.39, 0.2, 1.0))
	draw_glow(node, Vector2(player.x, player.y), 40.0, Color(0.04, 0.2, 0.2, 1.0))
	for e in enemies:
		if e.kind == "elite" and e.windup > 0.0:
			var k: float = 1.0 - e.windup / Cfg.ELITE_WINDUP
			draw_glow(node, Vector2(e.x, e.y), 40.0 + 90.0 * k, Color(0.78, 0.59, 0.16, 1.0))
	# lethal zones: a pulsing red outline that stays visible in the dark
	for hz in arena.hazard_rects:
		var pulse: float = 0.5 + 0.5 * sin(clock * 4.0)
		node.draw_rect(hz, Color(0.3, 0.0, 0.08, 0.22 + 0.12 * pulse))
		node.draw_rect(hz, Color(0.9, 0.15, 0.25, 0.5 + 0.3 * pulse), false, 5.0)
	# arc lightning
	for b in bolts:
		var k2: float = float(b["life"]) / float(b["max"])
		var pts: Array = b["pts"]
		var jag: PackedVector2Array = PackedVector2Array()
		for i in range(pts.size() - 1):
			var a: Vector2 = pts[i]
			var c: Vector2 = pts[i + 1]
			var n: int = maxi(2, int(a.distance_to(c) / 34.0))
			for j in range(n):
				var fr: float = float(j) / float(n)
				var jit := Vector2(randf_range(-9.0, 9.0), randf_range(-9.0, 9.0)) if j > 0 else Vector2.ZERO
				jag.append(a.lerp(c, fr) + jit)
		jag.append(pts[pts.size() - 1])
		if jag.size() >= 2:
			node.draw_polyline(jag, Color(0.27, 0.43, 0.86, k2), 9.0)
			node.draw_polyline(jag, Color(0.59, 0.75, 1.0, k2), 5.0)
			node.draw_polyline(jag, Color(1, 1, 1, k2), 2.0)
	# particles that glow
	for pt in parts:
		var k3: float = pt.life / pt.max_life
		if pt.kind == "spark":
			var col: Color = pt.color
			col.a = k3
			draw_glow(node, Vector2(pt.x, pt.y), maxf(3.0, pt.size * (0.4 + 0.6 * k3) * 1.6), col)
		elif pt.kind == "ring":
			var r: float = pt.size * (1.0 - k3) + 6.0
			var col2: Color = pt.color
			col2.a = k3
			node.draw_arc(Vector2(pt.x, pt.y), r, 0.0, TAU, 48, col2, maxf(1.0, pt.extra * k3 + 1.0), true)


func _draw_fx_norm(node: CanvasItem) -> void:
	for pt in parts:
		var k: float = pt.life / pt.max_life
		var pos := Vector2(pt.x, pt.y)
		if pt.kind == "diamond":
			var s: float = pt.size * (0.3 + 0.7 * k)
			var a: float = pt.extra + pt.life * 8.0
			var ca: float = cos(a)
			var sa: float = sin(a)
			var pts := PackedVector2Array()
			for q in [Vector2(0, -s), Vector2(s * 0.55, 0), Vector2(0, s), Vector2(-s * 0.55, 0)]:
				pts.append(pos + Vector2(q.x * ca - q.y * sa, q.x * sa + q.y * ca))
			node.draw_colored_polygon(pts, pt.color)
		elif pt.kind == "text":
			var col: Color = pt.color
			col.a = minf(1.0, k * 2.0)
			node.draw_string(font, pos + Vector2(-60, 0), pt.text, HORIZONTAL_ALIGNMENT_CENTER, 120.0, int(pt.size), Color(0, 0, 0, col.a * 0.8))
			node.draw_string(font, pos + Vector2(-61, -1), pt.text, HORIZONTAL_ALIGNMENT_CENTER, 120.0, int(pt.size), col)
		elif pt.kind == "ghost":
			draw_sprite(node, tex["hero"], pos, pt.angle, 1.0, Color(1, 1, 1, 0.6 * k))
