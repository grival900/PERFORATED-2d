extends Node2D
## A thin drawing surface: asks the game to draw glows (mode 0, additive) or particles (mode 1).

var g
var mode: int = 0


func _draw() -> void:
	if g != null:
		g.draw_fx(self, mode)
