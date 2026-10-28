"""Generates the PERFORATED level textures and sprites (top-down, painted style).

Run from anywhere:  python3 2D-lab/game/tools/gen_assets.py
Needs: numpy, Pillow.  Output: game/assets/textures/*.png and game/assets/sprites/*.png

Everything is drawn at 3-4x resolution and downsampled for clean anti-aliased edges,
with gradient fills, bevels, rim light and soft shadows. Colours are mid-tones on
purpose: the game multiplies a dark lightmap over them.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEX = ASSETS / "textures"
SPR = ASSETS / "sprites"

GOLD = (240, 200, 92)
GOLD_L = (255, 238, 170)
GOLD_D = (150, 104, 36)
TEAL = (63, 245, 224)
TEAL_D = (24, 130, 130)
WHITE = (244, 247, 255)
SILVER = (178, 190, 222)
SHADE = (104, 118, 160)
PURPLE = (122, 63, 176)
PURPLE_D = (70, 34, 112)
PURPLE_L = (176, 116, 232)
OUTLINE = (14, 10, 24)


# ------------------------------------------------------------------ helpers
def rgba(c, a=255):
	return (*c[:3], a)


def lerp(a, b, t):
	return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def fbm(w, h, octaves=5, base=4, seed=0, persistence=0.5):
	"""Fractal value noise in 0..1, shape (h, w)."""
	rng = np.random.default_rng(seed)
	out = np.zeros((h, w), np.float32)
	amp, total = 1.0, 0.0
	for o in range(octaves):
		n = base * 2 ** o
		g = rng.random((n + 1, n + 1)).astype(np.float32)
		im = Image.fromarray(g, mode="F").resize((w, h), Image.BICUBIC)
		out += np.asarray(im) * amp
		total += amp
		amp *= persistence
	out /= total
	return np.clip((out - out.min()) / (out.max() - out.min() + 1e-6), 0, 1)


def vgrad(w, h, c0, c1, a=255):
	t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
	arr = np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t
	arr = np.repeat(arr, w, axis=1)
	img = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
	img.putalpha(a)
	return img


def radial(size, c_in, c_out, power=1.0, a_in=255, a_out=0, center=None, radius=None):
	"""Radial gradient image (RGBA)."""
	w, h = size if isinstance(size, tuple) else (size, size)
	cx, cy = center or (w / 2, h / 2)
	r = radius or min(w, h) / 2
	y, x = np.mgrid[0:h, 0:w].astype(np.float32)
	d = np.clip(np.hypot(x - cx, y - cy) / r, 0, 1) ** power
	arr = np.zeros((h, w, 4), np.float32)
	for i in range(3):
		arr[..., i] = c_in[i] * (1 - d) + c_out[i] * d
	arr[..., 3] = a_in * (1 - d) + a_out * d
	return Image.fromarray(arr.astype(np.uint8), "RGBA")


def mask_of(size, drawfn, ss=1):
	m = Image.new("L", (size[0] * ss, size[1] * ss), 0)
	drawfn(ImageDraw.Draw(m), ss)
	return m


def paste_fill(canvas, mask, fill):
	"""Paste an RGBA/RGB fill image through a mask (alpha-correct)."""
	layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
	layer.paste(fill, (0, 0), mask)
	canvas.alpha_composite(layer)


def shift(mask, dx, dy):
	return ImageChops.offset(mask, dx, dy)


def bevel(canvas, mask, light, dark, depth=3):
	"""Rim light on top-left edges and shade on bottom-right edges of a shape."""
	inner_tl = ImageChops.subtract(mask, shift(mask, depth, depth))
	inner_br = ImageChops.subtract(mask, shift(mask, -depth, -depth))
	paste_fill(canvas, inner_tl.point(lambda v: v * 0.8), Image.new("RGBA", canvas.size, rgba(light)))
	paste_fill(canvas, inner_br.point(lambda v: v * 0.7), Image.new("RGBA", canvas.size, rgba(dark)))


def outline(canvas, mask, color=OUTLINE, width=2, alpha=255):
	grown = mask.filter(ImageFilter.MaxFilter(width * 2 + 1))
	ring = ImageChops.subtract(grown, mask)
	paste_fill(canvas, ring.point(lambda v: v * alpha // 255), Image.new("RGBA", canvas.size, rgba(color)))


def drop_shadow(canvas, mask, offset=(6, 8), blur=8, alpha=150):
	sh = shift(mask, *offset).filter(ImageFilter.GaussianBlur(blur))
	paste_fill(canvas, sh.point(lambda v: v * alpha // 255), Image.new("RGBA", canvas.size, (0, 0, 0, 255)))


def glow_layer(canvas, mask, color, radius=10, strength=1.0):
	g = mask.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * strength)))
	paste_fill(canvas, g, Image.new("RGBA", canvas.size, rgba(color)))


def down(img, ss):
	return img.resize((img.width // ss, img.height // ss), Image.LANCZOS)


def save(img, folder, name):
	folder.mkdir(parents=True, exist_ok=True)
	img.save(folder / name)


# ------------------------------------------------------------------ textures
def marble_slab(seed, size=128):
	"""Pale veined marble slab with a dark joint and bevel, mid-tone for lighting."""
	rng = np.random.default_rng(seed)
	base_lo = np.array((74, 80, 108), np.float32)
	base_hi = np.array((112, 118, 148), np.float32)
	cloud = fbm(size, size, 4, 2, seed)
	arr = base_lo[None, None] * (1 - cloud[..., None]) + base_hi[None, None] * cloud[..., None]
	# warped ridge veins
	warp = fbm(size, size, 3, 3, seed + 11)
	yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
	ang = rng.uniform(0, np.pi)
	proj = (xx * np.cos(ang) + yy * np.sin(ang)) / size
	vein = 1 - np.abs(np.sin((proj * rng.uniform(2.0, 3.6) + warp * 2.2) * np.pi))
	main = np.clip((vein - 0.90) / 0.10, 0, 1) ** 1.5
	warp2 = fbm(size, size, 3, 5, seed + 23)
	vein2 = 1 - np.abs(np.sin((proj * 7.0 + warp2 * 3.0) * np.pi))
	thin = np.clip((vein2 - 0.94) / 0.06, 0, 1) ** 2 * 0.5
	vcol = np.array((156, 170, 206), np.float32)
	arr = arr * (1 - 0.50 * main[..., None]) + vcol * 0.50 * main[..., None]
	arr = arr * (1 - 0.30 * thin[..., None]) + vcol * 0.30 * thin[..., None]
	# fine grain
	arr += (rng.random((size, size, 1), dtype=np.float32) - 0.5) * 8
	# gold flecks
	fl = rng.random((size, size)) > 0.9985
	arr[fl] = np.array(GOLD, np.float32) * 0.9
	img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
	d = np.minimum(np.minimum(xx, yy), np.minimum(size - 1 - xx, size - 1 - yy))
	px = np.asarray(img).astype(np.float32)
	joint = (d < 1.5)[..., None]
	px = np.where(joint, np.array([26, 28, 44, 255], np.float32), px)
	hi_band = ((d >= 1.5) & (d < 4) & ((xx < yy + 0) | (yy < xx + 0)))[..., None]
	tl = ((xx < size - 1 - yy) & (d >= 1.5) & (d < 5))[..., None]       # top-left half
	br = ((xx >= size - 1 - yy) & (d >= 1.5) & (d < 5))[..., None]      # bottom-right half
	px[..., :3] = np.where(tl, px[..., :3] * 0.84 + 255 * 0.16, px[..., :3])
	px[..., :3] = np.where(br, px[..., :3] * 0.80, px[..., :3])
	return Image.fromarray(np.clip(px, 0, 255).astype(np.uint8), "RGBA")


def wall_block(size=96, seed=3):
	"""Running-bond dark stone with mortar, bevelled bricks and grain."""
	rng = np.random.default_rng(seed)
	bw, bh = size // 2, size // 4
	img = np.zeros((size, size, 3), np.float32)
	cloud = fbm(size, size, 4, 3, seed)
	base = np.array((70, 64, 98), np.float32)
	for row in range(size // bh):
		off = (bw // 2) if row % 2 else 0
		for col in range(-1, size // bw + 1):
			x0, y0 = col * bw + off, row * bh
			shade = rng.uniform(0.82, 1.14)
			for yy in range(max(0, y0), min(size, y0 + bh)):
				for xx in range(max(0, x0), min(size, x0 + bw)):
					lx, ly = xx - x0, yy - y0
					c = base * shade * (0.88 + 0.24 * cloud[yy, xx])
					if lx < 2 or ly < 2:
						c = np.array((30, 28, 46), np.float32)            # mortar
					elif lx < 4 or ly < 4:
						c = c * 1.22                                       # lit edge
					elif lx > bw - 4 or ly > bh - 4:
						c = c * 0.78                                       # shaded edge
					img[yy % size, xx % size] = c
	img += (rng.random((size, size, 1), dtype=np.float32) - 0.5) * 10
	out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
	return out


def pillar(size=160):
	ss = 3
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2
	plinth = mask_of((S, S), lambda d, s: d.rounded_rectangle((c - 62 * ss, c - 62 * ss, c + 62 * ss, c + 62 * ss),
	                                                          radius=8 * ss, fill=255))
	drop_shadow(im, plinth, (10 * ss, 14 * ss), 10 * ss, 170)
	fill = vgrad(S, S, (96, 90, 128), (58, 52, 86))
	paste_fill(im, plinth, fill)
	bevel(im, plinth, (170, 164, 204), (30, 26, 48), 4 * ss)
	outline(im, plinth, OUTLINE, 2 * ss)
	# inner marble disc with radial shading
	disc = mask_of((S, S), lambda d, s: d.ellipse((c - 46 * ss, c - 46 * ss, c + 46 * ss, c + 46 * ss), fill=255))
	paste_fill(im, disc, radial((S, S), (212, 216, 232), (134, 140, 164), 1.2, 255, 255,
	                            center=(c - 14 * ss, c - 16 * ss), radius=70 * ss))
	# gold rings
	ring = mask_of((S, S), lambda d, s: (d.ellipse((c - 46 * ss, c - 46 * ss, c + 46 * ss, c + 46 * ss), outline=255,
	                                               width=4 * ss)))
	paste_fill(im, ring, vgrad(S, S, GOLD_L, GOLD_D))
	ring2 = mask_of((S, S), lambda d, s: (d.ellipse((c - 30 * ss, c - 30 * ss, c + 30 * ss, c + 30 * ss), outline=255,
	                                                width=2 * ss)))
	paste_fill(im, ring2, Image.new("RGBA", (S, S), rgba(GOLD_D)))
	# flutes: eight radial grooves
	for k in range(8):
		a = k * np.pi / 4 + np.pi / 8
		groove = mask_of((S, S), lambda d, s, a=a: d.line((c + np.cos(a) * 14 * ss, c + np.sin(a) * 14 * ss,
		                                                    c + np.cos(a) * 42 * ss, c + np.sin(a) * 42 * ss),
		                                                   fill=140, width=2 * ss))
		paste_fill(im, groove, Image.new("RGBA", (S, S), (70, 76, 104, 255)))
	cap = mask_of((S, S), lambda d, s: d.ellipse((c - 9 * ss, c - 9 * ss, c + 9 * ss, c + 9 * ss), fill=255))
	paste_fill(im, cap, radial((S, S), GOLD_L, GOLD_D, 1.0, 255, 255, center=(c - 3 * ss, c - 3 * ss), radius=14 * ss))
	outline(im, cap, OUTLINE, ss, 200)
	return down(im, ss)


def sigil(size=640):
	"""Gold inlay ring with seven teal perforations: the seven sins."""
	ss = 2
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2
	d = ImageDraw.Draw(im)
	gold = vgrad(S, S, GOLD_L, GOLD_D)

	def ringmask(r, w):
		return mask_of((S, S), lambda dd, s: dd.ellipse((c - r, c - r, c + r, c + r), outline=255, width=w))

	for r, w in [(290 * ss // 2 * 1, 5 * ss), (250 * ss // 2, 3 * ss), (170 * ss // 2, 3 * ss), (96 * ss // 2, 4 * ss)]:
		m = ringmask(r * 1, w)
		glow_layer(im, m, GOLD, 5 * ss, 0.5)
		paste_fill(im, m, gold)
	# twelve rays between the outer rings
	for k in range(24):
		a = k * 2 * np.pi / 24
		r0, r1 = (125 if k % 2 else 85) * ss, 145 * ss
		m = mask_of((S, S), lambda dd, s, a=a, r0=r0, r1=r1: dd.line(
			(c + np.cos(a) * r0, c + np.sin(a) * r0, c + np.cos(a) * r1, c + np.sin(a) * r1), fill=255, width=3 * ss))
		paste_fill(im, m, gold)
	# triangular points on the outer ring
	for k in range(12):
		a = k * 2 * np.pi / 12
		tip, base_r, hw = 160 * ss, 140 * ss, 0.07
		pts = [(c + np.cos(a) * tip, c + np.sin(a) * tip),
		       (c + np.cos(a - hw) * base_r, c + np.sin(a - hw) * base_r),
		       (c + np.cos(a + hw) * base_r, c + np.sin(a + hw) * base_r)]
		m = mask_of((S, S), lambda dd, s, pts=pts: dd.polygon(pts, fill=255))
		paste_fill(im, m, gold)
	# seven perforations on the ring
	for k in range(7):
		a = -np.pi / 2 + k * 2 * np.pi / 7
		px, py = c + np.cos(a) * 125 * ss * 0.0 + np.cos(a) * 110 * ss, c + np.sin(a) * 110 * ss
		hole = mask_of((S, S), lambda dd, s, px=px, py=py: dd.ellipse((px - 11 * ss, py - 11 * ss, px + 11 * ss, py + 11 * ss),
		                                                              fill=255))
		glow_layer(im, hole, TEAL, 9 * ss, 1.0)
		paste_fill(im, hole, Image.new("RGBA", (S, S), (8, 6, 16, 255)))
		rim = ImageChops.subtract(hole.filter(ImageFilter.MaxFilter(2 * ss + 1)), hole)
		paste_fill(im, rim, Image.new("RGBA", (S, S), rgba(TEAL)))
		core = mask_of((S, S), lambda dd, s, px=px, py=py: dd.ellipse((px - 3 * ss, py - 3 * ss, px + 3 * ss, py + 3 * ss),
		                                                              fill=255))
		paste_fill(im, core, Image.new("RGBA", (S, S), (225, 255, 250, 255)))
	return down(im, ss)


def gate(open_=False, w=400, h=170):
	ss = 3
	W, H = w * ss, h * ss
	im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	# stone frame
	frame = mask_of((W, H), lambda d, s: d.rounded_rectangle((0, 0, W - 1, H - 1), radius=14 * ss, fill=255))
	paste_fill(im, frame, vgrad(W, H, (104, 98, 138), (60, 54, 88)))
	bevel(im, frame, (176, 170, 210), (30, 26, 48), 5 * ss)
	outline(im, frame, OUTLINE, 2 * ss)
	# recess
	rec = (26 * ss, 22 * ss, W - 26 * ss, H - 22 * ss)
	recm = mask_of((W, H), lambda d, s: d.rounded_rectangle(rec, radius=8 * ss, fill=255))
	if open_:
		paste_fill(im, recm, vgrad(W, H, (255, 250, 220), (255, 214, 120)))
		for k in range(1, 6):   # light rays
			rm = mask_of((W, H), lambda d, s, k=k: d.polygon([(W // 2, rec[1]), (rec[0] + k * (rec[2] - rec[0]) // 6, rec[3]),
			                                                  (rec[0] + (k + 0.4) * (rec[2] - rec[0]) / 6, rec[3])], fill=255))
			paste_fill(im, rm, Image.new("RGBA", (W, H), (255, 255, 255, 70)))
		glow_layer(im, recm, (255, 240, 180), 14 * ss, 0.9)
	else:
		paste_fill(im, recm, vgrad(W, H, (40, 36, 60), (22, 20, 36)))
		# two golden door leaves
		half = (rec[2] - rec[0]) // 2
		for i in range(2):
			x0 = rec[0] + i * half
			leaf = mask_of((W, H), lambda d, s, x0=x0: d.rectangle((x0 + 3 * ss, rec[1] + 3 * ss, x0 + half - 3 * ss, rec[3] - 3 * ss),
			                                                       fill=255))
			paste_fill(im, leaf, vgrad(W, H, GOLD, GOLD_D))
			bevel(im, leaf, GOLD_L, (90, 60, 20), 3 * ss)
			outline(im, leaf, OUTLINE, ss)
			for k in range(1, 5):
				ly = rec[1] + k * (rec[3] - rec[1]) // 5
				pl = mask_of((W, H), lambda d, s, x0=x0, ly=ly: d.line((x0 + 8 * ss, ly, x0 + half - 8 * ss, ly), fill=255, width=ss))
				paste_fill(im, pl, Image.new("RGBA", (W, H), (110, 74, 24, 255)))
		# crown emblem in the middle
		cx, cy = W // 2, H // 2
		pts = [(cx - 26 * ss, cy + 14 * ss), (cx - 30 * ss, cy - 14 * ss), (cx - 14 * ss, cy), (cx, cy - 20 * ss),
		       (cx + 14 * ss, cy), (cx + 30 * ss, cy - 14 * ss), (cx + 26 * ss, cy + 14 * ss)]
		cm = mask_of((W, H), lambda d, s: d.polygon(pts, fill=255))
		glow_layer(im, cm, GOLD_L, 8 * ss, 0.8)
		paste_fill(im, cm, vgrad(W, H, GOLD_L, GOLD))
		outline(im, cm, OUTLINE, 2 * ss)
		for px, py in [(cx - 30 * ss, cy - 14 * ss), (cx, cy - 20 * ss), (cx + 30 * ss, cy - 14 * ss)]:
			jm = mask_of((W, H), lambda d, s, px=px, py=py: d.ellipse((px - 4 * ss, py - 4 * ss, px + 4 * ss, py + 4 * ss), fill=255))
			paste_fill(im, jm, Image.new("RGBA", (W, H), rgba(TEAL)))
	return down(im, ss)


def brazier(size=112):
	ss = 3
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2
	base = mask_of((S, S), lambda d, s: d.ellipse((c - 44 * ss, c - 44 * ss, c + 44 * ss, c + 44 * ss), fill=255))
	drop_shadow(im, base, (6 * ss, 10 * ss), 8 * ss, 150)
	paste_fill(im, base, radial((S, S), (120, 112, 150), (52, 46, 78), 1.0, 255, 255, center=(c - 12 * ss, c - 14 * ss), radius=62 * ss))
	bevel(im, base, (190, 184, 224), (24, 20, 40), 4 * ss)
	outline(im, base, OUTLINE, 2 * ss)
	rim = mask_of((S, S), lambda d, s: d.ellipse((c - 44 * ss, c - 44 * ss, c + 44 * ss, c + 44 * ss), outline=255, width=5 * ss))
	paste_fill(im, rim, vgrad(S, S, GOLD_L, GOLD_D))
	bowl = mask_of((S, S), lambda d, s: d.ellipse((c - 32 * ss, c - 32 * ss, c + 32 * ss, c + 32 * ss), fill=255))
	paste_fill(im, bowl, radial((S, S), (255, 200, 90), (60, 20, 10), 0.8, 255, 255, radius=34 * ss))
	return down(im, ss)


def altar(size=130):
	ss = 3
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2
	# teal rune ring on the floor
	ring = mask_of((S, S), lambda d, s: d.ellipse((c - 58 * ss, c - 58 * ss, c + 58 * ss, c + 58 * ss), outline=255, width=3 * ss))
	glow_layer(im, ring, TEAL, 8 * ss, 0.8)
	paste_fill(im, ring, Image.new("RGBA", (S, S), rgba(TEAL)))
	for k in range(12):
		a = k * np.pi / 6
		m = mask_of((S, S), lambda d, s, a=a: d.line((c + np.cos(a) * 46 * ss, c + np.sin(a) * 46 * ss,
		                                              c + np.cos(a) * 54 * ss, c + np.sin(a) * 54 * ss), fill=255, width=2 * ss))
		paste_fill(im, m, Image.new("RGBA", (S, S), rgba(TEAL_D)))
	slab = mask_of((S, S), lambda d, s: d.rounded_rectangle((c - 34 * ss, c - 34 * ss, c + 34 * ss, c + 34 * ss), radius=6 * ss, fill=255))
	drop_shadow(im, slab, (6 * ss, 8 * ss), 6 * ss, 160)
	paste_fill(im, slab, vgrad(S, S, (84, 90, 120), (44, 48, 72)))
	bevel(im, slab, (160, 170, 210), (20, 22, 36), 4 * ss)
	outline(im, slab, OUTLINE, 2 * ss)
	lam = mask_of((S, S), lambda d, s: d.rounded_rectangle((c - 11 * ss, c - 16 * ss, c + 11 * ss, c + 12 * ss), radius=4 * ss, fill=255))
	glow_layer(im, lam, TEAL, 12 * ss, 1.0)
	paste_fill(im, lam, vgrad(S, S, (210, 255, 250), TEAL))
	outline(im, lam, OUTLINE, 2 * ss)
	cap = mask_of((S, S), lambda d, s: d.rectangle((c - 13 * ss, c - 20 * ss, c + 13 * ss, c - 15 * ss), fill=255))
	paste_fill(im, cap, Image.new("RGBA", (S, S), rgba(GOLD_D)))
	return down(im, ss)


def glow_tex(size=256):
	return radial(size, (255, 255, 255), (255, 255, 255), 2.0, 255, 0)


def vignette(w=640, h=360):
	y, x = np.mgrid[0:h, 0:w].astype(np.float32)
	d = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
	a = np.clip((d - 0.55) / 0.75, 0, 1) ** 1.6 * 235
	arr = np.zeros((h, w, 4), np.uint8)
	arr[..., 3] = a.astype(np.uint8)
	arr[..., :3] = (6, 6, 14)
	return Image.fromarray(arr, "RGBA")


# ------------------------------------------------------------------ sprites
def hero(size=112):
	"""Top-down: facing UP. Shoulders, hood, trailing teal scarf, glowing perforations."""
	ss = 4
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2

	def E(x0, y0, x1, y1):
		return (c + x0 * ss, c + y0 * ss, c + x1 * ss, c + y1 * ss)

	# scarf streaming down behind
	sc = mask_of((S, S), lambda d, s: d.polygon([(c - 6 * ss, c + 4 * ss), (c + 8 * ss, c + 6 * ss), (c + 16 * ss, c + 34 * ss),
	                                             (c + 6 * ss, c + 44 * ss), (c + 2 * ss, c + 30 * ss), (c - 10 * ss, c + 40 * ss),
	                                             (c - 12 * ss, c + 24 * ss)], fill=255))
	drop_shadow(im, sc, (3 * ss, 5 * ss), 4 * ss, 90)
	glow_layer(im, sc, TEAL, 5 * ss, 0.5)
	paste_fill(im, sc, vgrad(S, S, (70, 230, 214), TEAL_D))
	outline(im, sc, OUTLINE, ss)
	# coat / shoulders
	body = mask_of((S, S), lambda d, s: d.ellipse(E(-30, -18, 30, 24), fill=255))
	drop_shadow(im, body, (4 * ss, 7 * ss), 6 * ss, 160)
	paste_fill(im, body, radial((S, S), PURPLE_L, PURPLE_D, 1.0, 255, 255, center=(c - 8 * ss, c - 10 * ss), radius=46 * ss))
	bevel(im, body, (206, 160, 255), (40, 18, 66), 3 * ss)
	outline(im, body, OUTLINE, 2 * ss)
	# arms reaching forward, hands glowing teal
	for sx in (-1, 1):
		arm = mask_of((S, S), lambda d, s, sx=sx: d.line((c + sx * 22 * ss, c - 4 * ss, c + sx * 16 * ss, c - 30 * ss), fill=255, width=11 * ss))
		paste_fill(im, arm, vgrad(S, S, PURPLE, PURPLE_D))
		outline(im, arm, OUTLINE, ss)
		hand = mask_of((S, S), lambda d, s, sx=sx: d.ellipse((c + sx * 16 * ss - 6 * ss, c - 36 * ss, c + sx * 16 * ss + 6 * ss, c - 24 * ss), fill=255))
		glow_layer(im, hand, TEAL, 8 * ss, 0.9)
		paste_fill(im, hand, Image.new("RGBA", (S, S), (190, 255, 248, 255)))
	# perforations on the coat
	for hx, hy, hr in [(-16, 10, 5), (14, 12, 4), (-4, 18, 3), (20, -2, 3)]:
		hole = mask_of((S, S), lambda d, s, hx=hx, hy=hy, hr=hr: d.ellipse(E(hx - hr, hy - hr, hx + hr, hy + hr), fill=255))
		glow_layer(im, hole, TEAL, 5 * ss, 1.0)
		paste_fill(im, hole, Image.new("RGBA", (S, S), (8, 6, 16, 255)))
		rim = ImageChops.subtract(hole.filter(ImageFilter.MaxFilter(ss + 1)), hole)
		paste_fill(im, rim, Image.new("RGBA", (S, S), rgba(TEAL)))
		core = mask_of((S, S), lambda d, s, hx=hx, hy=hy: d.ellipse(E(hx - 1.5, hy - 1.5, hx + 1.5, hy + 1.5), fill=255))
		paste_fill(im, core, Image.new("RGBA", (S, S), (230, 255, 252, 255)))
	# hood (top of head) with a peak towards the back
	hood = mask_of((S, S), lambda d, s: (d.ellipse(E(-17, -22, 17, 12), fill=255),
	                                      d.polygon([(c - 12 * ss, c + 4 * ss), (c + 12 * ss, c + 4 * ss), (c, c + 22 * ss)], fill=255)))
	drop_shadow(im, hood, (2 * ss, 4 * ss), 3 * ss, 120)
	paste_fill(im, hood, radial((S, S), (140, 84, 196), (52, 24, 86), 1.0, 255, 255, center=(c - 5 * ss, c - 12 * ss), radius=34 * ss))
	bevel(im, hood, (200, 150, 250), (30, 12, 50), 2 * ss)
	outline(im, hood, OUTLINE, 2 * ss)
	# face opening at the front: dark void with two teal eyes
	face = mask_of((S, S), lambda d, s: d.ellipse(E(-10, -22, 10, -6), fill=255))
	paste_fill(im, face, Image.new("RGBA", (S, S), (10, 6, 20, 255)))
	for ex in (-4.5, 4.5):
		eye = mask_of((S, S), lambda d, s, ex=ex: d.ellipse(E(ex - 1.8, -16.5, ex + 1.8, -13), fill=255))
		glow_layer(im, eye, TEAL, 3 * ss, 1.0)
		paste_fill(im, eye, Image.new("RGBA", (S, S), (210, 255, 250, 255)))
	return down(im, ss)


def guardian_body(size, kind, k=1.0):
	"""Top-down guardian, facing UP. White/gold plate armour made of light, faceless."""
	ss = 4
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2

	def E(x0, y0, x1, y1):
		return (c + x0 * k * ss, c + y0 * k * ss, c + x1 * k * ss, c + y1 * k * ss)

	trim = GOLD
	if kind == "skirmisher":
		trim = (170, 235, 255)
	if kind == "lancer":
		trim = (200, 220, 255)
	# aura plate behind
	aura = mask_of((S, S), lambda d, s: d.ellipse(E(-30, -26, 30, 30), fill=255))
	drop_shadow(im, aura, (4 * ss, 7 * ss), 6 * ss, 140)
	# weapon
	if kind in ("sentinel", "elite"):
		L = 52 if kind == "sentinel" else 62
		shaft = mask_of((S, S), lambda d, s: d.line((c, c + 8 * k * ss, c, c - L * k * ss), fill=255, width=int(4 * k * ss)))
		paste_fill(im, shaft, vgrad(S, S, SILVER, SHADE))
		tip = mask_of((S, S), lambda d, s: d.polygon([(c, c - (L + 14) * k * ss), (c - 6 * k * ss, c - L * k * ss), (c + 6 * k * ss, c - L * k * ss)], fill=255))
		glow_layer(im, tip, (255, 250, 200), 6 * ss, 1.0)
		paste_fill(im, tip, Image.new("RGBA", (S, S), (255, 252, 214, 255)))
	elif kind == "lancer":
		shaft = mask_of((S, S), lambda d, s: d.line((c, c + 14 * k * ss, c, c - 66 * k * ss), fill=255, width=int(3 * k * ss)))
		paste_fill(im, shaft, vgrad(S, S, SILVER, SHADE))
		tip = mask_of((S, S), lambda d, s: d.polygon([(c, c - 84 * k * ss), (c - 5 * k * ss, c - 66 * k * ss), (c + 5 * k * ss, c - 66 * k * ss)], fill=255))
		glow_layer(im, tip, (255, 250, 200), 6 * ss, 1.0)
		paste_fill(im, tip, Image.new("RGBA", (S, S), (255, 252, 214, 255)))
	else:  # skirmisher: twin light blades
		for sx in (-1, 1):
			bl = mask_of((S, S), lambda d, s, sx=sx: d.polygon([(c + sx * 22 * k * ss, c - 4 * k * ss), (c + sx * 30 * k * ss, c - 56 * k * ss),
			                                                    (c + sx * 25 * k * ss, c + 2 * k * ss)], fill=255))
			glow_layer(im, bl, (150, 230, 255), 6 * ss, 0.9)
			paste_fill(im, bl, Image.new("RGBA", (S, S), (235, 250, 255, 255)))
	# body
	if kind == "skirmisher":
		bx = E(-20, -16, 20, 26)
	elif kind == "elite":
		bx = E(-36, -24, 36, 34)
	else:
		bx = E(-28, -20, 28, 28)
	body = mask_of((S, S), lambda d, s: d.ellipse(bx, fill=255))
	paste_fill(im, body, radial((S, S), WHITE, SHADE, 1.1, 255, 255, center=(c - 8 * k * ss, c - 10 * k * ss), radius=48 * k * ss))
	bevel(im, body, (255, 255, 255), (70, 80, 120), 3 * ss)
	outline(im, body, OUTLINE, 2 * ss)
	# gold belt/trim lines on the body
	for off in (6, 14):
		trimm = mask_of((S, S), lambda d, s, off=off: d.arc(E(-24 + off * 0.3, -14 + off * 0.5, 24 - off * 0.3, 26),
		                                                    200, 340, fill=255, width=int(2.5 * ss)))
		paste_fill(im, trimm, Image.new("RGBA", (S, S), rgba(trim)))
	# pauldrons
	pr = 13 if kind != "elite" else 18
	for sx in (-1, 1):
		px = sx * (26 if kind != "skirmisher" else 20) * k
		pd = mask_of((S, S), lambda d, s, px=px: d.ellipse((c + px * ss - pr * k * ss, c - 14 * k * ss - pr * k * ss,
		                                                    c + px * ss + pr * k * ss, c - 14 * k * ss + pr * k * ss), fill=255))
		drop_shadow(im, pd, (2 * ss, 4 * ss), 3 * ss, 120)
		paste_fill(im, pd, radial((S, S), GOLD_L if kind != "skirmisher" else (220, 245, 255), GOLD_D if kind != "skirmisher" else (70, 120, 160),
		                          1.0, 255, 255, center=(c + px * ss - 4 * k * ss, c - 18 * k * ss), radius=pr * 1.6 * k * ss))
		bevel(im, pd, (255, 252, 220), (80, 54, 14), 2 * ss)
		outline(im, pd, OUTLINE, 2 * ss)
		if kind == "elite":
			sp = mask_of((S, S), lambda d, s, px=px, sx=sx: d.polygon([(c + px * ss + sx * 4 * ss, c - 30 * k * ss),
			                                                           (c + px * ss + sx * 12 * ss, c - 56 * k * ss),
			                                                           (c + px * ss + sx * 18 * ss, c - 30 * k * ss)], fill=255))
			paste_fill(im, sp, vgrad(S, S, GOLD_L, GOLD_D))
			outline(im, sp, OUTLINE, ss + 1)
	# helm: smooth faceless dome with a glowing visor line
	hr = 15 if kind != "elite" else 20
	helm = mask_of((S, S), lambda d, s: d.ellipse((c - hr * k * ss, c - 22 * k * ss - hr * k * ss, c + hr * k * ss, c - 22 * k * ss + hr * k * ss), fill=255))
	drop_shadow(im, helm, (2 * ss, 4 * ss), 3 * ss, 110)
	paste_fill(im, helm, radial((S, S), WHITE, SILVER, 1.0, 255, 255, center=(c - 5 * k * ss, c - 28 * k * ss), radius=hr * 1.8 * k * ss))
	bevel(im, helm, (255, 255, 255), (80, 92, 130), 2 * ss)
	outline(im, helm, OUTLINE, 2 * ss)
	visor = mask_of((S, S), lambda d, s: d.line((c - 9 * k * ss, c - 28 * k * ss, c + 9 * k * ss, c - 28 * k * ss), fill=255, width=int(3 * k * ss)))
	glow_layer(im, visor, (255, 244, 190), 5 * ss, 1.0)
	paste_fill(im, visor, Image.new("RGBA", (S, S), (255, 252, 226, 255)))
	crest = mask_of((S, S), lambda d, s: d.polygon([(c, c - (22 + hr + 12) * k * ss), (c - 5 * k * ss, c - (22 + hr - 4) * k * ss),
	                                                (c + 5 * k * ss, c - (22 + hr - 4) * k * ss)], fill=255))
	paste_fill(im, crest, vgrad(S, S, GOLD_L, GOLD_D))
	outline(im, crest, OUTLINE, ss)
	# glowing core on the chest
	cm = mask_of((S, S), lambda d, s: d.polygon([(c, c + 2 * k * ss), (c + 8 * k * ss, c + 10 * k * ss), (c, c + 19 * k * ss), (c - 8 * k * ss, c + 10 * k * ss)], fill=255))
	glow_layer(im, cm, GOLD_L, 7 * ss, 1.0)
	paste_fill(im, cm, vgrad(S, S, (255, 250, 210), GOLD))
	outline(im, cm, OUTLINE, ss)
	return down(im, ss)


def shard(size=24):
	ss = 6
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2
	m = mask_of((S, S), lambda d, s: d.polygon([(c, c - 10 * ss), (c + 5 * ss, c), (c, c + 10 * ss), (c - 5 * ss, c)], fill=255))
	glow_layer(im, m, GOLD, 3 * ss, 0.9)
	paste_fill(im, m, vgrad(S, S, GOLD_L, GOLD_D))
	outline(im, m, OUTLINE, ss // 2)
	return down(im, ss)


def needle(w=72, h=18):
	"""Teal piercing shard, pointing RIGHT."""
	ss = 4
	W, H = w * ss, h * ss
	im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	body = mask_of((W, H), lambda d, s: d.polygon([(W - 4 * ss, H // 2), (W // 2, H // 2 - 4 * ss), (10 * ss, H // 2), (W // 2, H // 2 + 4 * ss)], fill=255))
	glow_layer(im, body, TEAL, 5 * ss, 1.0)
	paste_fill(im, body, Image.new("RGBA", (W, H), (222, 255, 252, 255)))
	trail = mask_of((W, H), lambda d, s: d.polygon([(10 * ss, H // 2), (0, H // 2 - ss), (0, H // 2 + ss)], fill=255))
	paste_fill(im, trail, Image.new("RGBA", (W, H), (63, 245, 224, 150)))
	return down(im, ss)


def spear(w=96, h=18):
	"""Light spear thrown by lancers, pointing RIGHT."""
	ss = 4
	W, H = w * ss, h * ss
	im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	sh = mask_of((W, H), lambda d, s: d.line((6 * ss, H // 2, W - 12 * ss, H // 2), fill=255, width=3 * ss))
	glow_layer(im, sh, (255, 240, 170), 5 * ss, 0.9)
	paste_fill(im, sh, Image.new("RGBA", (W, H), (255, 250, 220, 255)))
	tip = mask_of((W, H), lambda d, s: d.polygon([(W - 2 * ss, H // 2), (W - 20 * ss, H // 2 - 5 * ss), (W - 20 * ss, H // 2 + 5 * ss)], fill=255))
	glow_layer(im, tip, GOLD, 5 * ss, 1.0)
	paste_fill(im, tip, Image.new("RGBA", (W, H), (255, 252, 230, 255)))
	return down(im, ss)


def heart(size=48, filled=True):
	ss = 6
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2

	def shape(d, s):
		r = 11 * ss
		d.ellipse((c - 21 * ss, c - 17 * ss, c + 1 * ss, c + 5 * ss), fill=255)
		d.ellipse((c - 1 * ss, c - 17 * ss, c + 21 * ss, c + 5 * ss), fill=255)
		d.polygon([(c - 20 * ss, c - 3 * ss), (c + 20 * ss, c - 3 * ss), (c, c + 21 * ss)], fill=255)

	m = mask_of((S, S), shape)
	if filled:
		drop_shadow(im, m, (2 * ss, 3 * ss), 2 * ss, 130)
		paste_fill(im, m, radial((S, S), (255, 130, 140), (170, 20, 50), 1.0, 255, 255, center=(c - 7 * ss, c - 9 * ss), radius=34 * ss))
		bevel(im, m, (255, 200, 205), (90, 6, 30), 2 * ss)
		gl = mask_of((S, S), lambda d, s: d.ellipse((c - 15 * ss, c - 12 * ss, c - 7 * ss, c - 6 * ss), fill=255))
		paste_fill(im, gl, Image.new("RGBA", (S, S), (255, 255, 255, 190)))
	else:
		paste_fill(im, m, Image.new("RGBA", (S, S), (40, 30, 52, 220)))
	outline(im, m, OUTLINE, ss + 2)
	return down(im, ss)


def dash_pip(size=36, filled=True):
	ss = 6
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2
	m = mask_of((S, S), lambda d, s: d.polygon([(c + 14 * ss, c), (c - 10 * ss, c - 13 * ss), (c - 4 * ss, c), (c - 10 * ss, c + 13 * ss)], fill=255))
	if filled:
		glow_layer(im, m, TEAL, 4 * ss, 0.9)
		paste_fill(im, m, vgrad(S, S, (210, 255, 250), TEAL))
	else:
		paste_fill(im, m, Image.new("RGBA", (S, S), (40, 56, 66, 200)))
	outline(im, m, OUTLINE, ss + 2)
	return down(im, ss)


def ferryman(size=112):
	"""Top-down Ferryman: hooded, lantern held forward."""
	ss = 4
	S = size * ss
	im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
	c = S // 2

	def E(x0, y0, x1, y1):
		return (c + x0 * ss, c + y0 * ss, c + x1 * ss, c + y1 * ss)

	body = mask_of((S, S), lambda d, s: d.ellipse(E(-28, -16, 28, 30), fill=255))
	drop_shadow(im, body, (4 * ss, 7 * ss), 6 * ss, 160)
	paste_fill(im, body, radial((S, S), (96, 108, 150), (30, 36, 62), 1.0, 255, 255, center=(c - 8 * ss, c - 8 * ss), radius=48 * ss))
	bevel(im, body, (150, 164, 210), (16, 18, 34), 3 * ss)
	outline(im, body, OUTLINE, 2 * ss)
	hood = mask_of((S, S), lambda d, s: d.ellipse(E(-17, -24, 17, 10), fill=255))
	paste_fill(im, hood, radial((S, S), (110, 124, 170), (38, 44, 74), 1.0, 255, 255, center=(c - 5 * ss, c - 14 * ss), radius=34 * ss))
	bevel(im, hood, (170, 184, 230), (20, 22, 40), 2 * ss)
	outline(im, hood, OUTLINE, 2 * ss)
	face = mask_of((S, S), lambda d, s: d.ellipse(E(-10, -24, 10, -8), fill=255))
	paste_fill(im, face, Image.new("RGBA", (S, S), (6, 6, 14, 255)))
	for ex in (-4.5, 4.5):
		eye = mask_of((S, S), lambda d, s, ex=ex: d.ellipse(E(ex - 1.4, -18, ex + 1.4, -15), fill=255))
		paste_fill(im, eye, Image.new("RGBA", (S, S), rgba(TEAL_D)))
	lam = mask_of((S, S), lambda d, s: d.ellipse(E(-8, -46, 8, -30), fill=255))
	glow_layer(im, lam, TEAL, 10 * ss, 1.0)
	paste_fill(im, lam, radial((S, S), (230, 255, 252), TEAL, 1.0, 255, 255, radius=10 * ss, center=(c, c - 38 * ss)))
	outline(im, lam, OUTLINE, ss)
	return down(im, ss)


# ------------------------------------------------------------------ main
def main():
	for i in range(8):
		save(marble_slab(100 + i), TEX, f"marble_{i}.png")
	save(wall_block(), TEX, "wall_block.png")
	save(pillar(), TEX, "pillar.png")
	save(sigil(), TEX, "sigil.png")
	save(gate(False), TEX, "gate_closed.png")
	save(gate(True), TEX, "gate_open.png")
	save(brazier(), TEX, "brazier.png")
	save(altar(), TEX, "altar.png")
	save(glow_tex(), TEX, "glow.png")
	save(vignette(), TEX, "vignette.png")

	save(hero(), SPR, "hero.png")
	save(guardian_body(144, "sentinel", 1.0), SPR, "guardian_sentinel.png")
	save(guardian_body(128, "skirmisher", 0.9), SPR, "guardian_skirmisher.png")
	save(guardian_body(200, "lancer", 1.05), SPR, "guardian_lancer.png")
	save(guardian_body(240, "elite", 1.55), SPR, "guardian_elite.png")
	save(ferryman(), SPR, "ferryman.png")
	save(shard(), SPR, "shard.png")
	save(needle(), SPR, "needle.png")
	save(spear(), SPR, "spear.png")
	save(heart(48, True), SPR, "heart_full.png")
	save(heart(48, False), SPR, "heart_empty.png")
	save(dash_pip(36, True), SPR, "dash_full.png")
	save(dash_pip(36, False), SPR, "dash_empty.png")
	print("assets written to", ASSETS)


if __name__ == "__main__":
	main()
