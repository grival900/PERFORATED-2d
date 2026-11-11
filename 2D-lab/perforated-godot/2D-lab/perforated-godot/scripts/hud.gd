extends Control
## HUD, menus and overlays, drawn in one place (the pygame ui.py, ported).

var g   # the Game node

const GOLD: Color = Color(0.957, 0.8, 0.376)
const WHITE: Color = Color(0.94, 0.965, 1.0)
const DIM: Color = Color(0.588, 0.643, 0.737)


func _draw() -> void:
	if g == null:
		return
	# vignette over the world
	draw_texture_rect(g.tex["vignette"], Rect2(0, 0, Cfg.SCREEN_W, Cfg.SCREEN_H), false)
	if g.state == "title":
		_draw_title()
		return
	_draw_hud()
	if g.state == "pause":
		_draw_pause()
	elif g.state == "upgrade":
		_draw_upgrade()
	elif g.state == "over":
		_draw_end(false)
	elif g.state == "win":
		_draw_end(true)
	if g.fade > 0.0:
		draw_rect(Rect2(0, 0, Cfg.SCREEN_W, Cfg.SCREEN_H), Color(0, 0, 0, clampf(g.fade, 0.0, 1.0)))


# ------------------------------------------------------------------ helpers
func txt(s: String, x: float, yc: float, size: int, color: Color, align: String = "center", shadow: bool = true) -> void:
	## Draw text with its vertical centre at yc. align: left | center | right (relative to x).
	var f: Font = g.font
	var h: float = f.get_height(size)
	var base: float = yc - h / 2.0 + f.get_ascent(size)
	var w: float = 1600.0
	var px: float = x - w / 2.0
	var ha: int = HORIZONTAL_ALIGNMENT_CENTER
	if align == "left":
		px = x
		ha = HORIZONTAL_ALIGNMENT_LEFT
	elif align == "right":
		px = x - w
		ha = HORIZONTAL_ALIGNMENT_RIGHT
	if shadow:
		draw_string(f, Vector2(px + 2.0, base + 2.0), s, ha, w, size, Color(0.02, 0.02, 0.05, color.a))
	draw_string(f, Vector2(px, base), s, ha, w, size, color)


func panel(rect: Rect2, bg: Color, border: Color, bw: int = 2, radius: int = 14) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.set_corner_radius_all(radius)
	sb.border_color = border
	sb.set_border_width_all(bw)
	draw_style_box(sb, rect)


func dim(alpha: float) -> void:
	draw_rect(Rect2(0, 0, Cfg.SCREEN_W, Cfg.SCREEN_H), Color(0.016, 0.016, 0.05, alpha))


func wrap_lines(s: String, size: int, max_w: float) -> Array:
	var words: PackedStringArray = s.split(" ")
	var lines: Array = []
	var cur: String = ""
	for wd in words:
		var trial: String = (cur + " " + wd).strip_edges()
		if g.font.get_string_size(trial, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > max_w and cur != "":
			lines.append(cur)
			cur = wd
		else:
			cur = trial
	lines.append(cur)
	return lines


# ------------------------------------------------------------------ in-game HUD
func _draw_hud() -> void:
	var p = g.player
	# hearts
	for i in range(p.max_hp):
		var t: Texture2D = g.tex["heart_full"] if i < p.hp else g.tex["heart_empty"]
		var c := Vector2(48.0 + i * 50.0, 48.0)
		var sc: float = 1.0
		if i < p.hp and p.hp == 1:
			sc = 1.0 + 0.12 * sin(g.clock * 9.0)
		draw_set_transform(c, 0.0, Vector2(sc, sc))
		draw_texture(t, -t.get_size() * 0.5)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# dash charges
	var full: Texture2D = g.tex["dash_full"]
	var empty: Texture2D = g.tex["dash_empty"]
	for i in range(p.charge_cap):
		var c2 := Vector2(40.0 + i * 40.0, 96.0)
		if i < p.charges:
			draw_texture(full, c2 - full.get_size() * 0.5)
		else:
			draw_texture(empty, c2 - empty.get_size() * 0.5)
			if i == p.charges:
				var frac: float = p.recharge_t / p.recharge
				var fw: float = full.get_size().x * frac
				draw_texture_rect_region(full, Rect2(c2 - full.get_size() * 0.5, Vector2(fw, full.get_size().y)), Rect2(0, 0, fw, full.get_size().y))
	_draw_pride_bar()
	_draw_offerings_bar()
	var mins: int = int(g.time) / 60
	var secs: int = int(g.time) % 60
	txt("%s: %d" % [g.T("kills"), g.kills], Cfg.SCREEN_W - 24.0, 30.0, 18, WHITE, "right")
	txt("%d:%02d" % [mins, secs], Cfg.SCREEN_W - 24.0, 56.0, 18, DIM, "right")
	txt("%s: %d" % [Rooms.t(g.lang, "deaths"), g.deaths], Cfg.SCREEN_W - 24.0, 80.0, 16, DIM, "right")
	if g.time < 25.0 and g.box_total == 0 and g.state == "play":
		txt(g.T("hint_boxes"), Cfg.SCREEN_W / 2.0, Cfg.SCREEN_H - 40.0, 20, Color(0.7, 0.95, 0.9, 0.85))
	if g.banner_t > 0.0:
		var k: float = minf(1.0, g.banner_t / 0.5)
		if g.banner_t > 2.4:
			k = minf(k, (2.8 - g.banner_t) / 0.4)
		txt(g.banner_text, Cfg.SCREEN_W / 2.0, 196.0 if g.room > 0 else 150.0, 32, Color(GOLD.r, GOLD.g, GOLD.b, clampf(k, 0.0, 1.0)))
	if g.exit_open and g.state == "play":
		var pulse: float = 0.6 + 0.4 * sin(g.clock * 5.0)
		txt(g.T("exit_open"), Cfg.SCREEN_W / 2.0, 190.0, 26, Color(1.0, 0.925, 0.627, pulse))
		var gate := Vector2((Cfg.GATE_X0 + Cfg.GATE_X1) / 2.0 - g.cam_pos.x, 0.0 - g.cam_pos.y)
		if gate.x < 0.0 or gate.x > Cfg.SCREEN_W or gate.y < 0.0 or gate.y > Cfg.SCREEN_H:
			var centre := Vector2(Cfg.SCREEN_W / 2.0, Cfg.SCREEN_H / 2.0)
			var ang: float = (gate - centre).angle()
			var pos := Vector2(clampf(centre.x + cos(ang) * 600.0, 40.0, Cfg.SCREEN_W - 40.0), clampf(centre.y + sin(ang) * 600.0, 40.0, Cfg.SCREEN_H - 40.0))
			draw_colored_polygon(PackedVector2Array([
				pos + Vector2(cos(ang), sin(ang)) * 22.0,
				pos + Vector2(cos(ang + 2.5), sin(ang + 2.5)) * 18.0,
				pos + Vector2(cos(ang - 2.5), sin(ang - 2.5)) * 18.0]), Color(1.0, 0.91, 0.55))
	_draw_boss_bar()
	_draw_minimap()
	if g.red_flash > 0.0:
		draw_rect(Rect2(0, 0, Cfg.SCREEN_W, Cfg.SCREEN_H), Color(0.78, 0.08, 0.16, 0.43 * g.red_flash / 0.3))


func _draw_pride_bar() -> void:
	var w: float = 560.0
	var h: float = 28.0
	var x: float = (Cfg.SCREEN_W - w) / 2.0
	var y: float = 50.0
	var frac: float = g.bar_frac(g.pride_shown)
	var n: int = Cfg.NUM_STAGES
	panel(Rect2(x - 8.0, y - 8.0, w + 16.0, h + 16.0), Color(0.03, 0.03, 0.07, 0.78), Color8(140, 100, 36), 3, 12)
	draw_rect(Rect2(x, y, w, h), Color8(24, 22, 40))
	var fw: float = w * frac
	if fw > 2.0:
		var c0 := Color8(214, 158, 52)
		var c1 := Color8(255, 248, 202)
		draw_polygon(PackedVector2Array([Vector2(x, y), Vector2(x + fw, y), Vector2(x + fw, y + h), Vector2(x, y + h)]),
				PackedColorArray([c0, c0.lerp(c1, frac), c0.lerp(c1, frac), c0]))
		draw_rect(Rect2(x, y, fw, h * 0.45), Color(1, 1, 1, 0.22))
		if g.bar_pulse > 0.0:
			draw_rect(Rect2(x + fw - 4.0, y, 8.0, h), Color(1.0, 0.95, 0.7, 0.8))
	for i in range(1, n):
		var mx: float = x + w * float(i) / float(n)
		var done: bool = frac >= float(i) / float(n)
		draw_line(Vector2(mx, y - 4.0), Vector2(mx, y + h + 4.0), Color8(255, 244, 200) if done else Color8(110, 100, 150), 2.0)
		var col: Color = GOLD if done else Color8(90, 84, 130)
		draw_colored_polygon(PackedVector2Array([Vector2(mx, y + h + 6.0), Vector2(mx + 6.0, y + h + 13.0), Vector2(mx, y + h + 20.0), Vector2(mx - 6.0, y + h + 13.0)]), col)
	draw_rect(Rect2(x, y, w, h), Color8(200, 160, 70), false, 2.0)
	txt("%s  %d%%" % [g.T("pride"), int(frac * 100.0)], x, y - 22.0, 17, WHITE, "left")
	txt(g.T("stage").replace("{n}", str(g.stage)) + ": " + g.T("stage_desc")[g.stage], x + w, y - 22.0, 15, DIM, "right")


func _draw_offerings_bar() -> void:
	var w: float = 560.0
	var x: float = (Cfg.SCREEN_W - w) / 2.0
	var y: float = 100.0
	var cost: int = Cfg.upgrade_cost(g.box_upgrades)
	var frac: float = clampf(float(g.box_pts) / float(cost), 0.0, 1.0)
	draw_rect(Rect2(x, y, w, 10.0), Color8(20, 26, 36))
	draw_rect(Rect2(x, y, w * frac, 10.0), Color8(80, 235, 205))
	if g.box_pulse > 0.0:
		draw_rect(Rect2(x + w * frac - 3.0, y - 2.0, 6.0, 14.0), Color(0.8, 1.0, 0.95, 0.9))
	draw_rect(Rect2(x, y, w, 10.0), Color8(60, 130, 120), false, 1.5)
	txt("%s  %d/%d" % [g.T("offerings"), g.box_pts, cost], x, y + 22.0, 13, Color8(120, 220, 205), "left")


# ------------------------------------------------------------------ overlays
func _draw_title() -> void:
	dim(0.47)
	var cx: float = Cfg.SCREEN_W / 2.0
	var gl: Texture2D = g.tex["glow"]
	draw_texture_rect(gl, Rect2(cx - 330.0, 190.0 - 330.0, 660.0, 660.0), false, Color(0.5, 0.36, 0.12, 0.55))
	txt(g.T("title"), cx + 6.0, 186.0, 118, Color(0.02, 0.02, 0.05, 1.0), "center", false)
	txt(g.T("title"), cx, 180.0, 118, Color(0.98, 0.925, 0.745), "center", false)
	txt(g.T("subtitle"), cx, 268.0, 36, GOLD)
	txt(g.T("tagline"), cx, 312.0, 20, DIM)
	panel(Rect2(cx - 300.0, 346.0, 600.0, 200.0), Color(0.03, 0.03, 0.08, 0.7), Color8(90, 80, 130), 2, 14)
	var lines: Array = g.T("controls")
	for i in range(lines.size()):
		txt(lines[i], cx, 376.0 + i * 36.0, 20, WHITE)
	var blink: float = 0.55 + 0.45 * sin(g.clock * 4.0)
	txt(g.T("press_enter"), cx, 600.0, 30, Color(1.0, 0.957, 0.784, blink))
	txt("[L] MK / EN", Cfg.SCREEN_W - 20.0, Cfg.SCREEN_H - 24.0, 16, DIM, "right")


func _draw_pause() -> void:
	dim(0.67)
	txt(g.T("paused"), Cfg.SCREEN_W / 2.0, Cfg.SCREEN_H / 2.0 - 40.0, 64, WHITE)
	txt(g.T("pause_help"), Cfg.SCREEN_W / 2.0, Cfg.SCREEN_H / 2.0 + 30.0, 22, DIM)


func _draw_upgrade() -> void:
	dim(0.75)
	var cx: float = Cfg.SCREEN_W / 2.0
	var weapon: bool = g.choice_kind == "weapon"
	var title: String = g.T("weapon_title") if weapon else g.T("upgrade_title")
	if g.choice_kind == "reward":
		title = Rooms.t(g.lang, "reward_title")
	txt(title, cx, 96.0, 38, GOLD)
	txt(g.T("ferryman_line"), cx, 142.0, 20, DIM)
	var fm: Texture2D = g.tex["ferryman"]
	draw_set_transform(Vector2(112, 380), 0.0, Vector2(1.35, 1.35))
	draw_texture(fm, -fm.get_size() * 0.5)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var rects: Array = g.card_rects()
	var names: Dictionary = g.T("weapons") if weapon else g.T("upgrades")
	for i in range(g.choices.size()):
		var sel: bool = i == g.choice_sel
		var rc: Rect2 = rects[i]
		if sel:
			rc = rc.grow(8.0)
		panel(rc, Color(0.055, 0.055, 0.12, 0.92), GOLD if sel else Color8(90, 80, 130), 4 if sel else 2, 16)
		var info: Array = names[g.choices[i]]
		txt(str(i + 1), rc.get_center().x, rc.position.y + 54.0, 54, GOLD if sel else DIM)
		txt(info[0], rc.get_center().x, rc.position.y + 124.0, 25, WHITE)
		var lines: Array = wrap_lines(info[1], 18, rc.size.x - 36.0)
		for j in range(lines.size()):
			txt(lines[j], rc.get_center().x, rc.position.y + 168.0 + j * 26.0, 18, DIM)
	txt(g.T("upgrade_hint"), cx, 560.0, 20, DIM)


func _draw_end(won: bool) -> void:
	dim(0.75)
	var cx: float = Cfg.SCREEN_W / 2.0
	var cy: float = Cfg.SCREEN_H / 2.0
	var col: Color = GOLD if won else Color(0.9, 0.35, 0.4)
	txt(g.T("victory") if won else g.T("game_over"), cx, cy - 150.0, 66, col)
	txt(g.T("victory_sub") if won else g.T("game_over_sub"), cx, cy - 90.0, 22, DIM)
	var mins: int = int(g.time) / 60
	var secs: int = int(g.time) % 60
	panel(Rect2(cx - 230.0, cy - 66.0, 460.0, 170.0), Color(0.03, 0.03, 0.08, 0.78), Color8(90, 80, 130), 2, 14)
	txt("%s: %d" % [g.T("kills"), g.kills], cx, cy - 34.0, 26, WHITE)
	txt("%s: %d:%02d" % [g.T("time"), mins, secs], cx, cy + 4.0, 26, WHITE)
	txt("%s: %d/%d" % [g.T("hearts"), g.player.hp, g.player.max_hp], cx, cy + 42.0, 26, WHITE)
	txt("%s: %d" % [g.T("boxes"), g.box_total], cx, cy + 80.0, 26, WHITE)
	var blink: float = 0.6 + 0.4 * sin(g.clock * 4.0)
	txt(g.T("again") if won else g.T("retry"), cx, cy + 150.0, 24, Color(1.0, 0.957, 0.784, blink))


# ------------------------------------------------------------------ mini-boss bar and minimap
func _draw_boss_bar() -> void:
	if g.room == 0:
		return
	var boss = null
	for e in g.enemies:
		if e.kind == "miniboss":
			boss = e
	if boss == null:
		return
	var col: Color = Rooms.ROOMS[g.room - 1]["color"]
	var w: float = 560.0
	var x: float = (Cfg.SCREEN_W - w) / 2.0
	var y: float = 160.0
	panel(Rect2(x - 8.0, y - 8.0, w + 16.0, 28.0), Color(0.03, 0.03, 0.07, 0.8), col, 2, 8)
	draw_rect(Rect2(x, y, w, 12.0), Color8(24, 22, 40))
	draw_rect(Rect2(x, y, w * clampf(boss.hp / boss.max_hp, 0.0, 1.0), 12.0), col)
	txt(str(Rooms.t(g.lang, "names")[g.room - 1]), Cfg.SCREEN_W / 2.0, y - 22.0, 18, WHITE)


func _minimap_door(i: int, o: Vector2, s: float) -> void:
	var d: Dictionary = Rooms.ROOMS[i]
	var col: Color = d["color"]
	var dp: Vector2 = d["door"]
	var out := Vector2(-1, 0)
	if d["side"] == "south":
		out = Vector2(0, 1)
	elif d["side"] == "east":
		out = Vector2(1, 0)
	var pos: Vector2 = o + dp * s + out * 3.0
	if g.rooms_done[i]:
		draw_circle(pos, 4.5, Color(0.3, 0.7, 0.4))
		draw_circle(pos, 2.2, Color8(20, 40, 28))
	elif g.arena.door_open[i]:
		var pulse: float = 0.5 + 0.5 * sin(g.clock * 5.0)
		draw_circle(pos, 6.0 + 3.0 * pulse, Color(col.r, col.g, col.b, 0.35))
		draw_circle(pos, 5.0, col)
		draw_circle(pos, 2.2, Color.WHITE)
	else:
		draw_rect(Rect2(pos - Vector2(3, 3), Vector2(6, 6)), Color(0.4, 0.4, 0.46))


func _minimap_main(x0: float, y0: float, size: float) -> void:
	var s: float = size / float(Cfg.ARENA)
	var o := Vector2(x0, y0)
	draw_rect(Rect2(o, Vector2(size, size)), Color(0.09, 0.11, 0.19, 1.0))
	for c in g.arena.pillar_centers:
		draw_rect(Rect2(o + (c - Vector2(62, 62)) * s, Vector2(124.0, 124.0) * s), Color(0.52, 0.48, 0.72))
	for w in g.arena.low_wall_rects:
		var r2 := Rect2(o + w.position * s, (w.size * s).max(Vector2(2.0, 2.0)))
		draw_rect(r2, Color(0.42, 0.39, 0.6))
	for hz in g.arena.hazard_rects:
		draw_rect(Rect2(o + hz.position * s, hz.size * s), Color(0.8, 0.1, 0.2, 0.85))
	for sn in g.sentries:
		if sn.alive:
			draw_circle(o + sn.global_position * s, 3.0, Color8(255, 150, 60))
	for hh in g.hearts:
		if hh.alive:
			draw_circle(o + Vector2(hh.x, hh.y) * s, 2.0, Color8(255, 90, 110))
	draw_rect(Rect2(o, Vector2(size, size)), Color8(160, 150, 210), false, 2.0)
	var gc: Color = Color8(255, 226, 140) if g.exit_open else Color8(110, 98, 70)
	draw_rect(Rect2(o.x + Cfg.GATE_X0 * s, o.y - 3.0, (Cfg.GATE_X1 - Cfg.GATE_X0) * s, 6.0), gc)
	for i in range(3):
		_minimap_door(i, o, s)
	for e in g.enemies:
		draw_circle(o + Vector2(e.x, e.y) * s, 2.8 if e.kind == "elite" else 1.6, Color8(255, 90, 90))
	var pp: Vector2 = o + Vector2(g.player.x, g.player.y) * s
	draw_circle(pp, 4.6, Color8(20, 20, 40))
	draw_circle(pp, 3.2, Color8(80, 235, 215))


func _minimap_room(x0: float, y0: float, size: float) -> void:
	var d: Dictionary = Rooms.ROOMS[g.room - 1]
	var rc: Rect2 = d["rect"]
	var col: Color = d["color"]
	var s: float = size / maxf(rc.size.x, rc.size.y)
	var o := Vector2(x0, y0 + (size - rc.size.y * s) / 2.0)
	draw_rect(Rect2(o, rc.size * s), Color(0.09, 0.11, 0.19, 1.0))
	for c in d["pillars"]:
		draw_rect(Rect2(o + (c - rc.position - Vector2(62, 62)) * s, Vector2(124.0, 124.0) * s), Color(0.52, 0.48, 0.72))
	draw_rect(Rect2(o, rc.size * s), col, false, 2.0)
	if g.portal_open:
		var pe: Vector2 = d["portal"]
		draw_circle(o + (pe - rc.position) * s, 5.0 + 2.0 * sin(g.clock * 5.0), Color8(255, 226, 140))
	for e in g.enemies:
		draw_circle(o + (Vector2(e.x, e.y) - rc.position) * s, 5.0, col)
	var pp: Vector2 = o + (Vector2(g.player.x, g.player.y) - rc.position) * s
	draw_circle(pp, 4.6, Color8(20, 20, 40))
	draw_circle(pp, 3.2, Color8(80, 235, 215))


func _draw_minimap() -> void:
	var size: float = 190.0
	var x0: float = Cfg.SCREEN_W - size - 30.0
	var y0: float = Cfg.SCREEN_H - size - 58.0
	panel(Rect2(x0 - 12.0, y0 - 34.0, size + 24.0, size + 78.0), Color(0.03, 0.03, 0.07, 0.8), Color8(90, 80, 130), 2, 10)
	txt(str(Rooms.t(g.lang, "map")), x0, y0 - 18.0, 14, DIM, "left")
	if g.room == 0:
		_minimap_main(x0, y0, size)
	else:
		_minimap_room(x0, y0, size)
	var ly: float = y0 + size + 22.0
	draw_circle(Vector2(x0 + 6.0, ly), 5.0, GOLD)
	txt(str(Rooms.t(g.lang, "legend")), x0 + 18.0, ly, 12, DIM, "left", false)
