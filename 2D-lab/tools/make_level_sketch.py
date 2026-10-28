"""Draws the Level 1 (Pride) top-down arena sketch for Lab 1, Task 4.

Run:  python3 2D-lab/tools/make_level_sketch.py
Output: 2D-lab/images/level1_pride_sketch.png
Left: the arena seen from above (start, obstacles, rewards, goal, enemy spawns).
Right: the Pride bar split into four difficulty stages.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "level1_pride_sketch.png"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

W, H = 1700, 1040
AX, AY, AS = 30, 80, 900          # arena origin and size (px)
BG = (13, 14, 26)
FLOOR = (24, 27, 44)
FLOOR_LINE = (33, 38, 60)
WALL = (58, 52, 92)
WALL_TOP = (63, 245, 224)
TEXT = (232, 245, 250)
DIM = (140, 158, 178)
GOLD = (244, 200, 90)
RED = (232, 72, 84)
GREEN = (110, 230, 130)
TEAL = (63, 245, 224)
WHITE = (242, 246, 255)


def font(size, bold=True):
	return ImageFont.truetype(FB if bold else FR, size)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img, "RGBA")


def a(x, y):
	"""Arena coords in 0..1 to pixels."""
	return AX + x * AS, AY + y * AS


def text(xy, s, size, fill=TEXT, bold=True, anchor="mm"):
	d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def arrow(p0, p1, col, w=5):
	d.line([p0, p1], fill=col, width=w)
	ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
	for da in (2.6, -2.6):
		d.line([p1, (p1[0] + 20 * math.cos(ang + da), p1[1] + 20 * math.sin(ang + da))], fill=col, width=w)


def guardian(cx, cy, s=1.0):
	r = 17 * s
	d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=(16, 11, 24), width=2)
	d.ellipse((cx - r * 0.55, cy - r * 0.95, cx + r * 0.55, cy - r * 0.05), fill=(178, 190, 220))
	d.ellipse((cx - r, cy - r * 0.5, cx - r * 0.4, cy + r * 0.2), fill=GOLD)
	d.ellipse((cx + r * 0.4, cy - r * 0.5, cx + r, cy + r * 0.2), fill=GOLD)
	for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
		px, py = cx + dx * r * 1.45, cy + dy * r * 1.45
		d.polygon([(px, py - 6 * s), (px + 4 * s, py), (px, py + 6 * s), (px - 4 * s, py)], fill=GOLD)


def gem(cx, cy):
	d.polygon([(cx, cy - 11), (cx + 9, cy), (cx, cy + 11), (cx - 9, cy)], fill=GOLD, outline=(120, 80, 20))


def heart(cx, cy):
	d.ellipse((cx - 16, cy - 14, cx, cy + 2), fill=RED)
	d.ellipse((cx, cy - 14, cx + 16, cy + 2), fill=RED)
	d.polygon([(cx - 16, cy - 5), (cx + 16, cy - 5), (cx, cy + 17)], fill=RED)


def pillar(x, y, w, h):
	x0, y0 = a(x, y)
	d.rectangle((x0, y0, x0 + w * AS, y0 + h * AS), fill=WALL, outline=WALL_TOP, width=3)
	d.line((x0 + 6, y0 + 6, x0 + w * AS - 6, y0 + h * AS - 6), fill=(80, 74, 120), width=2)


# ---------------------------------------------------------------- header
text((AX, 36), "НИВО 1: ГОРДОСТ  (поглед одозгора)", 38, TEXT, anchor="lm")

# ---------------------------------------------------------------- arena
d.rectangle((AX, AY, AX + AS, AY + AS), fill=FLOOR)
for i in range(0, 901, 60):
	d.line((AX + i, AY, AX + i, AY + AS), fill=FLOOR_LINE)
	d.line((AX, AY + i, AX + AS, AY + i), fill=FLOOR_LINE)
d.rectangle((AX, AY, AX + AS, AY + AS), outline=WALL_TOP, width=6)

# goal gate in the top wall
gx0, gy0 = a(0.40, 0.0)
d.rectangle((gx0, gy0 - 6, gx0 + 0.20 * AS, gy0 + 22), fill=GOLD, outline=(120, 80, 20), width=3)
text((a(0.5, 0.0)[0], AY + 52), "ЦЕЛ: излез (се отвора кога", 22, GOLD)
text((a(0.5, 0.0)[0], AY + 80), "е полн Барот на гордост)", 22, GOLD)

# obstacles
for (x, y, w, h) in [(0.20, 0.22, 0.07, 0.07), (0.73, 0.22, 0.07, 0.07),
                     (0.20, 0.70, 0.07, 0.07), (0.73, 0.70, 0.07, 0.07),
                     (0.40, 0.42, 0.20, 0.03), (0.08, 0.46, 0.03, 0.18), (0.89, 0.46, 0.03, 0.18)]:
	pillar(x, y, w, h)
text(a(0.235, 0.355), "столб", 20, DIM)
text(a(0.5, 0.40), "низок ѕид", 20, DIM)

# rewards: point gems left by dead guardians, hearts, upgrade altar
for x, y in [(0.30, 0.55), (0.34, 0.60), (0.62, 0.58), (0.66, 0.52), (0.45, 0.20), (0.55, 0.26), (0.30, 0.36)]:
	gem(*a(x, y))
for x, y in [(0.14, 0.86), (0.86, 0.14)]:
	heart(*a(x, y))
text(a(0.14, 0.915), "срце", 20, RED)
text(a(0.86, 0.19), "срце", 20, RED)

ax_, ay_ = a(0.84, 0.35)
d.rectangle((ax_ - 30, ay_ - 30, ax_ + 30, ay_ + 30), fill=(20, 60, 64), outline=TEAL, width=4)
d.rectangle((ax_ - 10, ay_ - 14, ax_ + 10, ay_ + 8), fill=TEAL)
text((ax_, ay_ + 50), "Превозник: надградба", 19, TEAL)
text((ax_, ay_ + 72), "на 25 / 50 / 75 %", 19, TEAL)

# enemy spawns: arrows from the edges, more guardians in later stages
spawns = [
	(a(0.04, 0.06), a(0.17, 0.17), 1), (a(0.50, 0.97), a(0.50, 0.85), 1),
	(a(0.96, 0.50), a(0.84, 0.50), 2), (a(0.04, 0.50), a(0.16, 0.50), 2),
	(a(0.96, 0.96), a(0.85, 0.85), 3), (a(0.04, 0.96), a(0.15, 0.85), 3),
]
for p0, p1, n in spawns:
	arrow(p0, p1, RED, 5)
	for i in range(n + 1):
		guardian(p0[0] + (i % 2) * 36 - 18, p0[1] + (i // 2) * 36 - 14, 0.8)

# start / player
px_, py_ = a(0.50, 0.62)
d.ellipse((px_ - 26, py_ - 26, px_ + 26, py_ + 26), fill=(122, 63, 176), outline=(16, 11, 24), width=3)
d.ellipse((px_ - 15, py_ - 21, px_ + 15, py_ + 5), fill=(91, 42, 134))
for dx, dy in [(-12, 8), (12, 6), (0, 16)]:
	d.ellipse((px_ + dx - 4, py_ + dy - 4, px_ + dx + 4, py_ + dy + 4), fill=TEAL)
d.ellipse((px_ - 62, py_ - 62, px_ + 62, py_ + 62), outline=GREEN, width=3)
text((px_, py_ + 88), "СТАРТ (играч)", 24, GREEN)
text((px_, py_ + 114), "пука автоматски", 19, GREEN, bold=False)

# ---------------------------------------------------------------- right panel
RX = AX + AS + 50
RW = W - RX - 30
text((RX, 112), "Бар на гордост", 34, TEXT, anchor="lm")
text((RX, 150), "убиј чувари = поени = полн бар", 22, DIM, bold=False, anchor="lm")

BY = 190
d.rectangle((RX, BY, RX + RW, BY + 54), outline=TEXT, width=3)
stage_cols = [(80, 200, 170), (240, 210, 90), (240, 140, 70), (232, 72, 84)]
for i, c in enumerate(stage_cols):
	x0 = RX + i * RW / 4
	d.rectangle((x0 + 2, BY + 2, x0 + RW / 4 - 2, BY + 52), fill=c + (190,))
	text((x0 + RW / 8, BY + 27), str(i + 1), 30, (10, 10, 20))
for i, lab in enumerate(["0%", "25%", "50%", "75%", "100%"]):
	text((RX + i * RW / 4, BY + 78), lab, 21, DIM, anchor="rm" if i == 4 else "mm")

stages = [
	("Етапа 1", "бавни чувари, по неколку", (80, 200, 170)),
	("Етапа 2", "побрзи групи, 1. надградба", (240, 210, 90)),
	("Етапа 3", "чувари со копја (од далеку),\n2. надградба", (240, 140, 70)),
	("Етапа 4", "рој + елитен чувар,\n3. надградба", (232, 72, 84)),
]
sy = 340
for name, desc, col in stages:
	d.rectangle((RX, sy - 30, RX + 10, sy + 56), fill=col)
	text((RX + 26, sy), name, 28, col, anchor="lm")
	d.multiline_text((RX + 26, sy + 22), desc, font=font(22, False), fill=TEXT, spacing=4)
	sy += 110

# difficulty arrow
text((RX, 790), "Тежина", 26, TEXT, anchor="lm")
for i in range(RW):
	t = i / RW
	d.line((RX + i, 812, RX + i, 836), fill=(int(60 + 175 * t), int(200 - 130 * t), int(170 - 90 * t)))
arrow((RX + RW - 40, 824), (RX + RW + 4, 824), TEXT, 4)

# legend
ly = 905
text((RX, ly - 34), "Легенда:", 22, TEXT, anchor="lm")
lx = RX + 18
gem(lx, ly); text((lx + 20, ly), "поени", 20, TEXT, bold=False, anchor="lm")
lx += 120
heart(lx, ly - 2); text((lx + 24, ly), "срце", 20, TEXT, bold=False, anchor="lm")
lx += 120
guardian(lx, ly, 0.7); text((lx + 26, ly), "свет чувар", 20, TEXT, bold=False, anchor="lm")
ly += 46
arrow((RX, ly), (RX + 40, ly), RED, 4)
text((RX + 52, ly), "од тука стигаат чуварите", 20, TEXT, bold=False, anchor="lm")
ly += 46
d.rectangle((RX, ly - 12, RX + 34, ly + 12), fill=WALL, outline=WALL_TOP, width=2)
text((RX + 44, ly), "пречка", 20, TEXT, bold=False, anchor="lm")
d.rectangle((RX + 160, ly - 12, RX + 194, ly + 12), fill=GOLD, outline=(120, 80, 20), width=2)
text((RX + 204, ly), "цел", 20, TEXT, bold=False, anchor="lm")

img.save(OUT)
print("saved", OUT, img.size)
