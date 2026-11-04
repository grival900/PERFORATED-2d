extends RefCounted
## Player, enemies and small world objects. Used as: const Ent = preload("res://scripts/entities.gd")


class Player:
	extends RefCounted
	var x: float = Cfg.PLAYER_START.x
	var y: float = Cfg.PLAYER_START.y
	var vx: float = 0.0
	var vy: float = 0.0
	var r: float = Cfg.PLAYER_RADIUS
	var hp: int = Cfg.PLAYER_MAX_HP
	var max_hp: int = Cfg.PLAYER_MAX_HP
	var invuln: float = 0.0
	var facing: float = 0.0
	# dash
	var dash_t: float = 0.0
	var dash_dx: float = 0.0
	var dash_dy: float = 0.0
	var dash_hit: Dictionary = {}
	var charges: int = Cfg.DASH_CHARGES
	var charge_cap: int = Cfg.DASH_CHARGES
	var recharge: float = Cfg.DASH_RECHARGE
	var recharge_t: float = 0.0
	# stats shared by every weapon (raised by the box-point upgrades)
	var dmg_mult: float = 1.0
	var rate_mult: float = 1.0
	var bonus: int = 0
	var pierce_bonus: int = 0
	var area: float = 1.0
	var speed: float = Cfg.PLAYER_SPEED

	func is_dashing() -> bool:
		return dash_t > 0.0

	func try_dash(mx: float, my: float) -> bool:
		if charges < 1 or dash_t > 0.0:
			return false
		var n: float = Vector2(mx, my).length()
		if n > 0.1:
			dash_dx = mx / n
			dash_dy = my / n
		else:
			var d: Vector2 = Util.angle_to_dir(facing)
			dash_dx = d.x
			dash_dy = d.y
		charges -= 1
		dash_t = Cfg.DASH_TIME
		invuln = maxf(invuln, Cfg.DASH_IFRAMES)
		dash_hit = {}
		return true

	func update(dt: float, mx_in: float, my_in: float, arena: Arena, target) -> void:
		var mx: float = mx_in
		var my: float = my_in
		var n: float = Vector2(mx, my).length()
		if n > 1.0:
			mx /= n
			my /= n
			n = 1.0
		# recharge dash charges one at a time
		if charges < charge_cap:
			recharge_t += dt
			if recharge_t >= recharge:
				recharge_t = 0.0
				charges += 1
		else:
			recharge_t = 0.0
		invuln = maxf(0.0, invuln - dt)

		if dash_t > 0.0:
			dash_t -= dt
			vx = dash_dx * Cfg.DASH_SPEED
			vy = dash_dy * Cfg.DASH_SPEED
			if dash_t <= 0.0:   # carry some momentum out of the dash
				vx = dash_dx * speed * 1.25
				vy = dash_dy * speed * 1.25
		else:
			var tx: float = mx * speed
			var ty: float = my * speed
			var dvx: float = tx - vx
			var dvy: float = ty - vy
			var dist: float = Vector2(dvx, dvy).length()
			var step: float = (Cfg.PLAYER_ACCEL if n > 0.05 else Cfg.PLAYER_FRICTION) * dt
			if dist <= step or dist < 0.000001:
				vx = tx
				vy = ty
			else:
				vx += dvx / dist * step
				vy += dvy / dist * step

		x += vx * dt
		y += vy * dt
		var np: Vector2 = arena.collide(Vector2(x, y), r, true)
		x = np.x
		y = np.y
		if arena.hit and dash_t > 0.0:
			dash_t = 0.0

		# facing: towards the target, else the direction of travel
		if target != null:
			facing = Util.turn(facing, Util.dir_to_angle(target.x - x, target.y - y), 18.0 * dt)
		elif Vector2(vx, vy).length() > 30.0:
			facing = Util.turn(facing, Util.dir_to_angle(vx, vy), 10.0 * dt)

	func hurt() -> void:
		hp -= 1
		invuln = Cfg.INVULN_TIME


class Enemy:
	extends RefCounted
	var kind: String
	var id: int
	var x: float
	var y: float
	var vx: float = 0.0
	var vy: float = 0.0
	var kx: float = 0.0   # knock-back velocity
	var ky: float = 0.0
	var hp: float
	var max_hp: float
	var r: float
	var speed: float
	var pts: int
	var shadow: float
	var knock: float
	var flash: float = 0.0
	var face: float
	var t: float
	var cd: float          # lancer: time to next throw; elite/skirmisher: time to next charge
	var windup: float = 0.0
	var windup_max: float = 1.0
	var charge_t: float = 0.0
	var cdx: float = 0.0
	var cdy: float = 0.0
	var spawn_t: float = 0.35   # fade / scale in
	var detour_dx: float = 0.0
	var detour_dy: float = 0.0
	var detour_t: float = 0.0
	var flank: float
	var nova_i: int = 0
	var variant: int = 0   # mini-boss: which room's boss (0 south, 1 east, 2 west)
	var act: int = 0       # mini-boss: the telegraphed action (0 charge, 1 spear fan, 2 spear ring)
	var pattern: int = 0   # mini-boss: how many actions it has done

	func _init(kind_: String, x_: float, y_: float, hp_scale: float, id_: int, variant_: int = 0) -> void:
		variant = variant_
		var st: Dictionary = Cfg.ENEMIES["sentinel"]
		if kind_ == "miniboss":
			var mb: Dictionary = Rooms.MINIBOSS[variant_]
			st = {"hp": mb["hp"], "speed": mb["speed"], "r": mb["r"], "pts": 0, "shadow": 96.0, "knock": 0.0}
		else:
			st = Cfg.ENEMIES[kind_]
		kind = kind_
		id = id_
		x = x_
		y = y_
		hp = float(st["hp"]) * hp_scale
		max_hp = hp
		r = float(st["r"])
		speed = float(st["speed"]) * randf_range(0.92, 1.08)
		pts = int(st["pts"])
		shadow = float(st["shadow"])
		knock = float(st["knock"])
		face = randf_range(0.0, TAU)
		t = randf_range(0.0, 6.0)
		cd = randf_range(0.6, 1.8)
		flank = (1.0 if randf() < 0.5 else -1.0) * randf_range(0.25, 0.85)

	func hit(dmg: float, dx: float, dy: float, force: float) -> void:
		hp -= dmg
		flash = 0.12
		var n: float = Vector2(dx, dy).length()
		if n < 0.000001:
			n = 1.0
		kx += dx / n * force * knock
		ky += dy / n * force * knock

	func _miniboss_fire(g, enraged: bool) -> void:
		## Carry out the telegraphed action of a mini-boss.
		if act == 0:
			charge_t = 0.5
			g.sfx("slam")
		elif act == 1:
			var n: int = 3 if variant == 0 else (7 if enraged else 5)
			for i in range(n):
				var a: float = (float(i) - float(n - 1) / 2.0) * 0.26
				var c: float = cos(a)
				var s: float = sin(a)
				g.spawn_spear(x, y, cdx * c - cdy * s, cdx * s + cdy * c)
		else:
			var m: int = 10
			for i in range(m):
				var a2: float = float(i) * TAU / float(m) + t
				g.spawn_spear(x, y, cos(a2), sin(a2))
			g.sfx("elite")

	func steer(player, dist: float, ux: float, uy: float, lead: bool) -> Vector2:
		## Direction to run in: optionally aimed at where the hero is heading, bent sideways while far away.
		if lead:
			var tt: float = minf(0.6, dist / maxf(speed, 1.0) * 0.5)
			var dx: float = player.x + player.vx * tt - x
			var dy: float = player.y + player.vy * tt - y
			var d: float = Vector2(dx, dy).length()
			if d < 0.000001:
				d = 1.0
			if (dx * ux + dy * uy) / d > 0.5:   # only lead when it still points at the hero
				ux = dx / d
				uy = dy / d
		var a: float = flank * minf(1.0, maxf(0.0, (dist - 140.0) / 450.0))
		var c: float = cos(a)
		var s: float = sin(a)
		return Vector2(ux * c - uy * s, ux * s + uy * c)

	func update(dt: float, player, arena: Arena, g) -> void:
		t += dt
		flash = maxf(0.0, flash - dt)
		spawn_t = maxf(0.0, spawn_t - dt)
		var dx: float = player.x - x
		var dy: float = player.y - y
		var dist: float = Vector2(dx, dy).length()
		if dist < 0.000001:
			dist = 1.0
		var ux: float = dx / dist
		var uy: float = dy / dist
		var mx: float = 0.0
		var my: float = 0.0
		var sp: float = speed * g.enemy_speed_mult

		if kind == "sentinel" or kind == "swarmer":
			var sv: Vector2 = steer(player, dist, ux, uy, true)
			mx = sv.x * sp
			my = sv.y * sp
		elif kind == "bulwark":
			if hp < max_hp * Cfg.BULWARK_ENRAGE:
				sp *= 1.5
			var sv2: Vector2 = steer(player, dist, ux, uy, false)
			mx = sv2.x * sp
			my = sv2.y * sp
		elif kind == "skirmisher":
			if charge_t > 0.0:   # lunge
				charge_t -= dt
				mx = cdx * Cfg.LUNGE_SPEED
				my = cdy * Cfg.LUNGE_SPEED
			elif windup > 0.0:   # telegraph, aim until the last instant
				windup -= dt
				if windup > 0.08:
					cdx = ux
					cdy = uy
				if windup <= 0.0:
					charge_t = Cfg.LUNGE_TIME
			else:
				var wob: float = sin(t * 4.2) * 0.55   # weaves left/right on the way in
				var sv3: Vector2 = steer(player, dist, ux, uy, false)
				mx = (sv3.x - sv3.y * wob) * sp
				my = (sv3.y + sv3.x * wob) * sp
				cd -= dt
				if cd <= 0.0 and dist < Cfg.LUNGE_RANGE:
					windup = Cfg.LUNGE_WINDUP
					windup_max = Cfg.LUNGE_WINDUP
					cd = Cfg.LUNGE_COOLDOWN * randf_range(0.8, 1.3)
					cdx = ux
					cdy = uy
		elif kind == "lancer":
			var want: float = 340.0
			if dist > want + 40.0:
				mx = ux * sp
				my = uy * sp
			elif dist < want - 80.0:
				mx = -ux * sp * 0.7
				my = -uy * sp * 0.7
			else:
				mx = -uy * sp * 0.45   # circle the player
				my = ux * sp * 0.45
			cd -= dt
			var fan_on: bool = g.stage >= Cfg.FAN_STAGE
			if windup > 0.0:
				windup -= dt
				mx *= 0.2
				my *= 0.2
				if windup <= 0.0:
					var fan: int = 3 if fan_on else 1
					for i in range(fan):
						var a: float = (float(i) - float(fan - 1) / 2.0) * 0.27
						var c: float = cos(a)
						var s: float = sin(a)
						g.spawn_spear(x, y, cdx * c - cdy * s, cdx * s + cdy * c)
			elif cd <= 0.0 and dist < 560.0:
				windup = Cfg.SPEAR_WINDUP
				windup_max = Cfg.SPEAR_WINDUP
				cd = Cfg.SPEAR_COOLDOWN * randf_range(0.9, 1.2) * (0.85 if fan_on else 1.0)
				cdx = ux
				cdy = uy
			if windup > 0.0:   # keep aiming while winding up
				cdx = ux
				cdy = uy
		elif kind == "elite":
			if charge_t > 0.0:
				charge_t -= dt
				mx = cdx * Cfg.ELITE_CHARGE_SPEED
				my = cdy * Cfg.ELITE_CHARGE_SPEED
			elif windup > 0.0:
				windup -= dt
				mx = 0.0
				my = 0.0
				if windup <= 0.0:
					charge_t = Cfg.ELITE_CHARGE_TIME
					g.sfx("slam")
			elif nova_i < Cfg.NOVA_MARKS.size() and hp <= max_hp * float(Cfg.NOVA_MARKS[nova_i]):
				nova_i += 1   # at set health marks: a ring of light spears
				var n: int = int(Cfg.NOVA_SPEARS)
				for i in range(n):
					var a2: float = float(i) * TAU / float(n) + t
					g.spawn_spear(x, y, cos(a2), sin(a2))
				g.sfx("elite")
			else:
				mx = ux * sp
				my = uy * sp
				cd -= dt
				if cd <= 0.0 and dist < 700.0:
					windup = Cfg.ELITE_WINDUP
					windup_max = Cfg.ELITE_WINDUP
					cd = Cfg.ELITE_CHARGE_COOLDOWN * (0.8 if g.stage >= Cfg.ELITE_RAGE_STAGE else 1.0)
					cdx = ux
					cdy = uy
			if windup > 0.0:
				cdx = ux
				cdy = uy

		elif kind == "miniboss":
			var enr: bool = hp < max_hp * 0.5
			var spm: float = sp * (1.3 if enr else 1.0)
			if charge_t > 0.0:
				charge_t -= dt
				mx = cdx * 720.0
				my = cdy * 720.0
			elif windup > 0.0:
				windup -= dt
				if windup > 0.1:   # aim until the last instant
					cdx = ux
					cdy = uy
				if windup <= 0.0:
					_miniboss_fire(g, enr)
			elif nova_i < 2 and hp <= max_hp * (0.66 if nova_i == 0 else 0.33):
				nova_i += 1   # at two health marks: a ring of light spears
				for i in range(12):
					var a3: float = float(i) * TAU / 12.0 + t
					g.spawn_spear(x, y, cos(a3), sin(a3))
				g.sfx("elite")
			else:
				if variant == 1:   # the spear master keeps its distance and circles
					if dist > 400.0:
						mx = ux * spm
						my = uy * spm
					elif dist < 280.0:
						mx = -ux * spm * 0.8
						my = -uy * spm * 0.8
					else:
						mx = -uy * spm * 0.6
						my = ux * spm * 0.6
				else:
					var k: float = 1.0 if variant == 0 else 0.8
					mx = ux * spm * k
					my = uy * spm * k
				cd -= dt
				if cd <= 0.0 and dist < 900.0:
					if variant == 0:
						act = 1 if pattern % 3 == 2 else 0
					elif variant == 1:
						act = 2 if pattern % 4 == 3 else 1
					else:
						act = pattern % 3
					pattern += 1
					windup = 0.45 if act == 1 else 0.6
					windup_max = windup
					cd = (1.5 if variant == 1 else 2.0) * (0.7 if enr else 1.0)
					cdx = ux
					cdy = uy
			if windup > 0.0 and windup > 0.1:
				cdx = ux
				cdy = uy

		if Cfg.MELEE_KINDS.has(kind) and charge_t <= 0.0:
			var back: float = mx * ux + my * uy
			if back < 0.0:
				mx -= back * ux
				my -= back * uy

		if detour_t > 0.0:
			detour_t -= dt
			mx = mx * 0.35 + detour_dx * sp * 0.9
			my = my * 0.35 + detour_dy * sp * 0.9
		# knock-back decays quickly
		kx *= maxf(0.0, 1.0 - 9.0 * dt)
		ky *= maxf(0.0, 1.0 - 9.0 * dt)
		vx = mx + kx
		vy = my + ky
		x += vx * dt
		y += vy * dt
		var np: Vector2 = arena.collide(Vector2(x, y), r, false)
		x = np.x
		y = np.y
		if arena.last_normal != Vector2.ZERO and charge_t <= 0.0:
			var nx: float = arena.last_normal.x
			var ny: float = arena.last_normal.y
			var tx: float = -ny
			var ty: float = nx
			var side: float = tx * ux + ty * uy
			if absf(side) < 0.15:
				side = 1.0 if id % 2 == 0 else -1.0
			var sgn: float = 1.0 if side > 0.0 else -1.0
			detour_dx = tx * sgn
			detour_dy = ty * sgn
			detour_t = 0.7
		if (kind == "lancer" or kind == "elite" or kind == "skirmisher") and windup > 0.0:
			face = Util.turn(face, Util.dir_to_angle(cdx, cdy), 10.0 * dt)
		else:
			face = Util.turn(face, Util.dir_to_angle(ux, uy), 8.0 * dt)


class Shot:
	extends RefCounted
	var x: float
	var y: float
	var vx: float
	var vy: float
	var life: float = Cfg.SHOT_LIFE
	var dmg: float
	var pierce: int
	var hit: Dictionary = {}
	var r: float = 9.0

	func _init(x_: float, y_: float, vx_: float, vy_: float, dmg_: float, pierce_: int) -> void:
		x = x_
		y = y_
		vx = vx_
		vy = vy_
		dmg = dmg_
		pierce = pierce_


class Spear:
	extends RefCounted
	var x: float
	var y: float
	var vx: float
	var vy: float
	var life: float = Cfg.SPEAR_LIFE

	func _init(x_: float, y_: float, ux: float, uy: float) -> void:
		x = x_ + ux * 30.0
		y = y_ + uy * 30.0
		vx = ux * Cfg.SPEAR_SPEED
		vy = uy * Cfg.SPEAR_SPEED


class HeartPickup:
	extends RefCounted
	var x: float
	var y: float
	var alive: bool = true
	var timer: float = 0.0
	var respawns: bool = true

	func _init(x_: float, y_: float, respawns_: bool) -> void:
		x = x_
		y = y_
		respawns = respawns_


class Box:
	extends RefCounted
	const RADIUS: float = 26.0
	var x: float
	var y: float
	var gilded: bool
	var t: float = randf_range(0.0, 6.0)

	func _init(x_: float, y_: float, gilded_: bool) -> void:
		x = x_
		y = y_
		gilded = gilded_


class Gem:
	extends RefCounted
	var x: float
	var y: float
	var vx: float
	var vy: float
	var val: int
	var life: float = Cfg.GEM_LIFE
	var age: float = 0.0

	func _init(x_: float, y_: float, val_: int) -> void:
		var a: float = randf_range(0.0, TAU)
		var sp: float = randf_range(120.0, 300.0)
		x = x_
		y = y_
		vx = cos(a) * sp
		vy = sin(a) * sp
		val = val_


class Particle:
	extends RefCounted
	var kind: String   # spark | diamond | ring | text | ghost
	var x: float
	var y: float
	var vx: float = 0.0
	var vy: float = 0.0
	var life: float
	var max_life: float
	var color: Color = Color.WHITE
	var size: float = 6.0
	var extra: float = 0.0   # diamond: rotation, ring: line width
	var text: String = ""
	var angle: float = 0.0   # ghost: facing
