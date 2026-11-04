@tool
class_name Util
extends RefCounted
## Small math helpers shared by the game scripts.
## Angles follow the pygame version: 0 = up, positive = clockwise (same as Godot's rotation).


static func angle_to_dir(a: float) -> Vector2:
	return Vector2(sin(a), -cos(a))


static func dir_to_angle(dx: float, dy: float) -> float:
	return atan2(dx, -dy)


static func turn(cur: float, target: float, rate: float) -> float:
	var d: float = fposmod(target - cur + PI, TAU) - PI
	return cur + d * minf(1.0, rate)


static func weighted_choice(weights: Dictionary) -> String:
	var total: float = 0.0
	for k in weights:
		total += float(weights[k])
	var r: float = randf() * total
	for k in weights:
		r -= float(weights[k])
		if r <= 0.0:
			return str(k)
	return str(weights.keys()[0])
