"""Draws the PERFORATED 2D character art (pixel style, side profile) for Lab 1.

Run:  python3 2D-lab/tools/make_characters.py
Output: 2D-lab/images/main_character_side.png, 2D-lab/images/characters_sheet.png
Everything is drawn at a low logical resolution and scaled up with nearest
neighbour so the result reads as pixel art.
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

W, H = 96, 112  # logical size of one character cell
OUTLINE = (16, 11, 24, 255)
TEAL = (63, 245, 224, 255)
TEAL_D = (28, 150, 150, 255)
CORE = (225, 255, 250, 255)


def circle(d, cx, cy, r, fill):
	d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)


def perforation(d, cx, cy, r):
	"""A hole through the body: dark void, teal rim, bright core."""
	circle(d, cx, cy, r + 1, TEAL)
	circle(d, cx, cy, r, (8, 6, 14, 255))
	d.point((cx, cy), fill=CORE)
	if r >= 3:
		d.point((cx - 1, cy), fill=TEAL_D)
		d.point((cx + 1, cy), fill=TEAL_D)


def finish(layer, rim=True):
	"""Add a dark outline and a teal moon-rim to a flat-coloured layer."""
	alpha = layer.getchannel("A")
	mask = alpha.point(lambda a: 255 if a > 0 else 0)
	grown = mask.filter(ImageFilter.MaxFilter(3))
	out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
	out.paste(Image.new("RGBA", layer.size, OUTLINE), (0, 0), grown)
	if rim:
		shifted = ImageChops.offset(mask, 1, 0)
		edge = ImageChops.subtract(mask, shifted)  # right-facing edges
		tint = Image.new("RGBA", layer.size, (63, 245, 224, 150))
		layer = layer.copy()
		layer.paste(Image.alpha_composite(layer, tint), (0, 0), edge)
	out.alpha_composite(layer)
	return out


# --------------------------------------------------------------------------
# Main character: the Nameless, side profile facing right, mid-run.
# --------------------------------------------------------------------------
def draw_hero():
	COAT = (122, 63, 176, 255)
	COAT_D = (78, 38, 119, 255)
	COAT_L = (156, 98, 212, 255)
	HOOD = (91, 42, 134, 255)
	HOOD_D = (58, 26, 90, 255)
	SKIN = (190, 176, 192, 255)
	SKIN_D = (140, 124, 148, 255)
	PANTS = (38, 32, 58, 255)
	PANTS_L = (56, 48, 82, 255)
	BOOT = (22, 18, 32, 255)

	im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)

	# scarf streaming back (drawn first, behind the body)
	scarf = [(40, 31), (32, 33), (25, 31), (18, 35), (11, 33), (4, 37)]
	d.line(scarf, fill=TEAL_D, width=5, joint="curve")
	d.line([(x, y - 1) for x, y in scarf], fill=TEAL, width=2, joint="curve")
	d.polygon([(4, 35), (0, 39), (6, 41), (3, 44), (9, 40)], fill=TEAL_D)

	# back arm (swung back)
	d.line([(41, 36), (33, 45), (27, 54)], fill=COAT_D, width=5, joint="curve")
	circle(d, 26, 55, 2, SKIN_D)

	# back leg: pushing off behind
	d.line([(42, 66), (35, 79), (26, 92)], fill=PANTS, width=7, joint="curve")
	d.polygon([(21, 91), (30, 93), (30, 100), (19, 98)], fill=BOOT)

	# coat body, flaring back with the speed; ragged hem
	coat = [(37, 30), (51, 30), (54, 48), (56, 68), (52, 73), (49, 69), (45, 75),
	        (41, 70), (36, 77), (31, 70), (27, 76), (29, 62), (34, 46)]
	d.polygon(coat, fill=COAT)
	# shading on the back half, highlight on the chest
	d.polygon([(34, 46), (29, 62), (27, 76), (31, 70), (36, 77), (40, 50)], fill=COAT_D)
	d.line([(50, 33), (53, 50), (54, 66)], fill=COAT_L, width=2)
	# belt + teal trim
	d.rectangle((35, 54, 53, 56), fill=HOOD_D)
	d.rectangle((44, 54, 46, 56), fill=TEAL)

	# front leg: planted, forward
	d.line([(47, 66), (54, 78), (55, 93)], fill=PANTS_L, width=7, joint="curve")
	d.polygon([(51, 92), (60, 92), (66, 97), (66, 101), (51, 101)], fill=BOOT)
	d.line([(52, 100), (65, 100)], fill=TEAL_D, width=1)

	# neck + head (hood over the back, face in profile to the right)
	d.rectangle((41, 24, 47, 31), fill=SKIN_D)
	d.ellipse((35, 8, 54, 28), fill=HOOD)
	d.polygon([(37, 12), (28, 22), (30, 34), (38, 30), (40, 20)], fill=HOOD_D)  # hood tail
	d.polygon([(44, 11), (53, 14), (56, 20), (54, 21), (54, 25), (50, 28), (43, 27)], fill=SKIN)  # face
	d.polygon([(54, 20), (57, 22), (54, 23)], fill=SKIN)  # nose
	d.line([(51, 24), (54, 24)], fill=SKIN_D)  # mouth
	d.rectangle((49, 17, 51, 18), fill=TEAL)  # eye
	d.point((50, 17), fill=CORE)
	d.polygon([(40, 9), (48, 7), (54, 12), (50, 13), (43, 12)], fill=HOOD)  # hood brim

	# front arm: bent forward, running
	d.line([(48, 36), (55, 44), (63, 41)], fill=COAT, width=5, joint="curve")
	circle(d, 64, 41, 2, SKIN)

	# the holes: one per sin committed
	perforation(d, 45, 41, 3)
	perforation(d, 48, 60, 2)
	perforation(d, 38, 48, 2)
	perforation(d, 37, 65, 2)
	perforation(d, 52, 52, 1)
	perforation(d, 53, 83, 1)
	perforation(d, 34, 82, 1)

	return finish(im)


# --------------------------------------------------------------------------
# Enemy: the Holy Guardian, side view facing left. A hovering construct of
# white-gold light: no wings, no halo, no symbols, just radiant armour.
# --------------------------------------------------------------------------
WHITE = (242, 246, 255, 255)
SILVER = (178, 190, 220, 255)
SILVER_D = (122, 134, 170, 255)
GOLD = (246, 202, 92, 255)
GOLD_D = (178, 128, 40, 255)
GLOW = (255, 252, 205, 255)


def diamond(d, cx, cy, r, fill, edge=GOLD_D):
	d.polygon([(cx, cy - r - 2), (cx + r, cy), (cx, cy + r + 2), (cx - r, cy)], fill=fill, outline=edge)


def draw_guardian():
	im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)

	# floating shards orbiting the body
	for cx, cy, r in [(70, 30, 3), (76, 52, 4), (68, 74, 3), (22, 82, 2)]:
		diamond(d, cx, cy, r, GOLD)

	# tapering lower body (no legs: it hovers), segmented plates
	d.polygon([(38, 62), (64, 62), (58, 80), (52, 98), (48, 98), (42, 80)], fill=SILVER)
	d.polygon([(52, 62), (64, 62), (58, 80), (52, 98)], fill=SILVER_D)
	for y, hw in [(70, 11), (79, 8), (88, 5)]:
		d.line([(51 - hw, y), (51 + hw, y)], fill=GOLD_D, width=1)
	d.polygon([(48, 98), (52, 98), (50, 106)], fill=GOLD)

	# torso with glowing core
	d.polygon([(36, 34), (66, 34), (64, 62), (38, 62)], fill=WHITE)
	d.polygon([(52, 34), (66, 34), (64, 62), (52, 62)], fill=SILVER)
	d.polygon([(51, 42), (57, 46), (57, 52), (51, 56), (45, 52), (45, 46)], fill=GOLD)
	d.polygon([(51, 45), (54, 47), (54, 51), (51, 53), (48, 51), (48, 47)], fill=GLOW)
	d.rectangle((38, 58, 64, 60), fill=GOLD)

	# big angular pauldron + arm holding a light lance pointing left
	d.polygon([(30, 30), (46, 32), (48, 42), (36, 44)], fill=GOLD)
	d.polygon([(30, 30), (36, 44), (30, 40)], fill=GOLD_D)
	d.line([(38, 42), (30, 52), (22, 52)], fill=WHITE, width=5, joint="curve")
	d.line([(2, 56), (44, 46)], fill=SILVER, width=2)
	d.polygon([(0, 57), (12, 51), (12, 59)], fill=GLOW)
	d.line([(12, 55), (34, 50)], fill=GLOW, width=1)

	# smooth faceless helm with one bright visor line
	d.ellipse((38, 10, 62, 36), fill=WHITE)
	d.polygon([(52, 10), (62, 20), (60, 34), (52, 36)], fill=SILVER)
	d.polygon([(40, 14), (46, 7), (54, 9), (50, 14)], fill=GOLD)  # crest plate
	d.rectangle((39, 22, 50, 24), fill=GLOW)
	d.line([(39, 23), (50, 23)], fill=GOLD, width=1)
	return finish(im, rim=False)


# --------------------------------------------------------------------------
# NPC: the Ferryman, a hooded lantern keeper, facing right.
# --------------------------------------------------------------------------
def draw_ferryman():
	ROBE = (52, 58, 82, 255)
	ROBE_D = (30, 34, 54, 255)
	ROBE_L = (84, 94, 128, 255)
	WOOD = (110, 78, 50, 255)

	im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)

	# staff + lantern on the right
	d.line([(68, 30), (68, 104)], fill=WOOD, width=2)
	d.line([(68, 31), (60, 31), (60, 36)], fill=WOOD, width=1)
	d.rectangle((56, 36, 64, 48), fill=(20, 60, 64, 255))
	d.rectangle((57, 38, 63, 46), fill=TEAL)
	d.rectangle((59, 40, 61, 44), fill=CORE)

	# long ragged robe
	d.polygon([(38, 28), (56, 28), (62, 60), (66, 104), (60, 100), (56, 106), (50, 100),
	           (44, 106), (38, 100), (32, 106), (30, 80), (34, 50)], fill=ROBE)
	d.polygon([(34, 50), (30, 80), (32, 106), (38, 100), (44, 106), (46, 60)], fill=ROBE_D)
	d.line([(55, 34), (60, 60), (64, 100)], fill=ROBE_L, width=2)
	# rope belt
	d.rectangle((38, 62, 60, 64), fill=WOOD)

	# arm holding the staff
	d.line([(52, 40), (58, 52), (66, 50)], fill=ROBE_L, width=5, joint="curve")
	circle(d, 67, 50, 2, (150, 138, 156, 255))

	# deep hood with no face, only two dim eyes
	d.polygon([(36, 30), (40, 10), (50, 6), (58, 14), (60, 30)], fill=ROBE)
	d.polygon([(42, 14), (56, 16), (56, 28), (44, 28)], fill=(8, 8, 16, 255))
	d.rectangle((52, 20, 53, 21), fill=TEAL_D)
	d.rectangle((47, 20, 48, 21), fill=TEAL_D)

	return finish(im)


# --------------------------------------------------------------------------
# Demon (Repentance enemy), facing left.
# --------------------------------------------------------------------------
def draw_demon():
	SKIN = (120, 24, 40, 255)
	SKIN_D = (72, 12, 28, 255)
	SKIN_L = (176, 48, 56, 255)
	HORN = (226, 210, 190, 255)
	EYE = (255, 190, 60, 255)

	im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)

	# bat wings
	d.polygon([(56, 40), (70, 6), (76, 24), (84, 12), (88, 34), (94, 28), (84, 56), (62, 60)], fill=SKIN_D)
	d.line([(58, 42), (70, 8)], fill=SKIN_L, width=1)
	d.line([(60, 46), (84, 14)], fill=SKIN_L, width=1)
	# body
	d.polygon([(38, 34), (60, 34), (62, 66), (54, 80), (44, 80), (36, 66)], fill=SKIN)
	d.polygon([(52, 34), (60, 34), (62, 66), (54, 80), (52, 80)], fill=SKIN_D)
	# cracks of ember
	d.line([(44, 44), (48, 52), (45, 60)], fill=EYE, width=1)
	# legs, digitigrade
	d.line([(44, 78), (38, 92), (30, 100)], fill=SKIN, width=6, joint="curve")
	d.line([(54, 78), (58, 92), (52, 102)], fill=SKIN_D, width=6, joint="curve")
	d.polygon([(26, 99), (34, 99), (34, 103), (24, 103)], fill=HORN)
	d.polygon([(48, 100), (56, 100), (56, 104), (46, 104)], fill=HORN)
	# arm with claws
	d.line([(40, 40), (30, 50), (24, 58)], fill=SKIN_L, width=5, joint="curve")
	d.polygon([(20, 58), (26, 56), (24, 64)], fill=HORN)
	# head and horns
	d.ellipse((36, 16, 58, 36), fill=SKIN)
	d.polygon([(40, 18), (34, 4), (46, 14)], fill=HORN)
	d.polygon([(54, 18), (60, 2), (58, 18)], fill=HORN)
	d.polygon([(34, 26), (28, 30), (36, 31)], fill=SKIN_L)  # snout
	d.rectangle((38, 23, 42, 25), fill=EYE)
	d.line([(36, 32), (44, 32)], fill=(20, 4, 10, 255))
	return finish(im, rim=False)


# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Top-down in-game sprites (48x48 logical): hero and holy guardian.
# --------------------------------------------------------------------------
def topdown_hero():
	im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)
	d.polygon([(24, 30), (14, 44), (20, 46), (24, 40), (30, 46), (34, 44)], fill=TEAL_D)  # scarf trailing down
	d.ellipse((10, 16, 38, 36), fill=(122, 63, 176, 255))                              # shoulders / coat
	d.ellipse((13, 8, 35, 28), fill=(91, 42, 134, 255))                                # hood
	d.ellipse((19, 12, 29, 22), fill=(58, 26, 90, 255))
	d.rectangle((22, 10, 26, 11), fill=TEAL)                                           # face glint
	for cx, cy, r in [(17, 27, 1), (30, 25, 1), (24, 31, 1)]:
		perforation(d, cx, cy, r)
	return finish(im)


def topdown_guardian():
	im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)
	d.line([(24, 4), (24, 20)], fill=SILVER, width=2)                                   # lance forward
	d.polygon([(24, 0), (21, 7), (27, 7)], fill=GLOW)
	d.ellipse((9, 16, 39, 40), fill=WHITE)                                              # body
	d.ellipse((9, 16, 21, 28), fill=GOLD)                                               # pauldrons
	d.ellipse((27, 16, 39, 28), fill=GOLD)
	d.ellipse((17, 14, 31, 28), fill=SILVER)                                            # helm
	d.rectangle((20, 19, 28, 20), fill=GLOW)
	d.polygon([(24, 29), (28, 33), (24, 37), (20, 33)], fill=GOLD)                      # core
	d.point((24, 33), fill=GLOW)
	for cx, cy in [(6, 12), (42, 12), (6, 38), (42, 38)]:
		diamond(d, cx, cy, 2, GOLD)
	return finish(im, rim=False)


def background(w, h, floor_y):
	"""Dark teal fog gradient with a faint floor, same mood as the 3D game."""
	bg = Image.new("RGB", (w, h))
	px = bg.load()
	for y in range(h):
		t = y / h
		for x in range(w):
			px[x, y] = (int(10 + 10 * t), int(10 + 28 * t * t), int(22 + 30 * t))
	d = ImageDraw.Draw(bg)
	d.rectangle((0, floor_y, w, h), fill=(14, 12, 24))
	d.line((0, floor_y, w, floor_y), fill=(40, 190, 180), width=3)
	for gx in range(0, w, 48):
		d.line((gx, floor_y, gx - 40, h), fill=(24, 40, 52), width=2)
	return bg


def scale(im, k):
	return im.resize((im.width * k, im.height * k), Image.NEAREST)


def label(d, xy, text, size, fill, anchor="mm", bold=True):
	d.text(xy, text, font=ImageFont.truetype(FONT_B if bold else FONT_R, size), fill=fill, anchor=anchor)


def main():
	OUT.mkdir(parents=True, exist_ok=True)
	k = 8
	hero, guardian, ferry, demon = draw_hero(), draw_guardian(), draw_ferryman(), draw_demon()

	# --- main character image (side profile) ---
	w, h = W * k + 160, H * k + 60
	floor = 14 + 103 * k
	bg = background(w, h, floor)
	d = ImageDraw.Draw(bg, "RGBA")
	# soft teal glow behind the figure
	glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
	ImageDraw.Draw(glow).ellipse((w // 2 - 260, 80, w // 2 + 260, floor + 20), fill=(30, 200, 190, 55))
	glow = glow.filter(ImageFilter.GaussianBlur(60))
	bg = Image.alpha_composite(bg.convert("RGBA"), glow)
	d = ImageDraw.Draw(bg, "RGBA")
	d.ellipse((w // 2 - 220, floor - 12, w // 2 + 240, floor + 16), fill=(0, 0, 0, 130))  # shadow
	bg.alpha_composite(scale(hero, k), (80, 14))
	bg.convert("RGB").save(OUT / "main_character_side.png")

	# --- character sheet: hero, guardian, demon, ferryman ---
	k2 = 6
	cw, ch = W * k2, H * k2
	pad = 30
	sw, sh = pad + 4 * (cw + pad), ch + 170
	sheet = background(sw, sh, 14 + 103 * k2).convert("RGBA")
	d = ImageDraw.Draw(sheet, "RGBA")
	items = [
		(hero, "Безимениот", "главен лик"),
		(guardian, "Свет чувар", "непријатели (Гревови)"),
		(demon, "Демон", "непријатели (Покајание)"),
		(ferry, "Превозникот", "NPC, контролна точка"),
	]
	for i, (spr, name, role) in enumerate(items):
		x = pad + i * (cw + pad)
		sheet.alpha_composite(scale(spr, k2), (x, 14))
		label(d, (x + cw // 2, ch + 50), name, 28, (230, 245, 250))
		label(d, (x + cw // 2, ch + 88), role, 18, (120, 215, 210), bold=False)
	label(d, (sw // 2, sh - 28), "PERFORATED - ликови (прототип, пиксел-арт)", 16, (110, 130, 150), bold=False)
	sheet.convert("RGB").save(OUT / "characters_sheet.png")
	# --- top-down in-game sprites (what the player actually sees) ---
	k3 = 10
	tw, th = 48 * k3 * 2 + 90, 48 * k3 + 60
	td = background(tw, th, th - 1).convert("RGBA")
	td.alpha_composite(scale(topdown_hero(), k3), (30, 30))
	td.alpha_composite(scale(topdown_guardian(), k3), (60 + 48 * k3, 30))
	td.convert("RGB").save(OUT / "topdown_sprites.png")
	print("saved", OUT)


if __name__ == "__main__":
	main()
