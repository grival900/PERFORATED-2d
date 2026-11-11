@tool
class_name Rooms
extends RefCounted
## The three mini-boss rooms, the extra obstacles of the main arena, and the texts for them.
## Rooms are separate areas far outside the arena; a door teleports the hero into them.
## Room index: 0 = south door, 1 = east door, 2 = west door.

const SPAN_LO: float = 1360.0   # the door openings are 280 wide, centred on the wall (same as the north gate)
const SPAN_HI: float = 1640.0
const OPEN_AT_STAGE: Array = [3, 4, 5]   # door i opens when this wave begins (the wave before is completed)

const EXTRA_PILLARS: Array = [
	Vector2(900, 1750), Vector2(2100, 1750), Vector2(1000, 2750), Vector2(2000, 2750),
	Vector2(1500, 950), Vector2(400, 2000), Vector2(2600, 2000), Vector2(1250, 2100),
	Vector2(1750, 2100), Vector2(700, 1150), Vector2(2200, 1250),
]
const EXTRA_WALLS: Array = [
	Rect2(600, 1950, 400, 54), Rect2(1996, 1950, 400, 54), Rect2(1473, 560, 54, 220),
	Rect2(700, 2560, 54, 300), Rect2(2246, 2560, 54, 300),
]

const ROOMS: Array = [
	{
		"side": "south", "color": Color(1.0, 0.63, 0.24), "tint": Color(1.0, 0.86, 0.72),
		"rect": Rect2(950, 3600, 1100, 800), "door": Vector2(1500, 3000), "ret": Vector2(1500, 2810),
		"spawn": Vector2(1500, 3730), "portal": Vector2(1500, 3730), "boss": Vector2(1500, 4180),
		"pillars": [Vector2(1180, 3860), Vector2(1820, 3860), Vector2(1180, 4150), Vector2(1820, 4150)],
		"braziers": [Vector2(1060, 3710), Vector2(1940, 3710), Vector2(1060, 4290), Vector2(1940, 4290)],
	},
	{
		"side": "east", "color": Color(0.31, 0.78, 1.0), "tint": Color(0.74, 0.88, 1.0),
		"rect": Rect2(3700, 1100, 1100, 800), "door": Vector2(3000, 1500), "ret": Vector2(2830, 1500),
		"spawn": Vector2(3800, 1500), "portal": Vector2(3800, 1500), "boss": Vector2(4620, 1500),
		"pillars": [Vector2(3960, 1330), Vector2(4540, 1330), Vector2(3960, 1670), Vector2(4540, 1670)],
		"braziers": [Vector2(3810, 1210), Vector2(4690, 1210), Vector2(3810, 1790), Vector2(4690, 1790)],
	},
	{
		"side": "west", "color": Color(1.0, 0.31, 0.51), "tint": Color(1.0, 0.76, 0.84),
		"rect": Rect2(-1800, 1100, 1100, 800), "door": Vector2(0, 1500), "ret": Vector2(170, 1500),
		"spawn": Vector2(-800, 1500), "portal": Vector2(-800, 1500), "boss": Vector2(-1620, 1500),
		"pillars": [Vector2(-1540, 1330), Vector2(-960, 1330), Vector2(-1540, 1670), Vector2(-960, 1670)],
		"braziers": [Vector2(-1690, 1210), Vector2(-810, 1210), Vector2(-1690, 1790), Vector2(-810, 1790)],
	},
]

# one mini-boss per room: hp, speed, radius, sprite scale and tint
const MINIBOSS: Array = [
	{"hp": 90.0, "speed": 125.0, "r": 44.0, "scale": 1.35, "tint": Color(1.0, 0.78, 0.55)},
	{"hp": 130.0, "speed": 110.0, "r": 44.0, "scale": 1.35, "tint": Color(0.62, 0.85, 1.0)},
	{"hp": 190.0, "speed": 140.0, "r": 46.0, "scale": 1.45, "tint": Color(1.0, 0.6, 0.76)},
]

const TEXT: Dictionary = {
	"mk": {
		"door_open": "Се отвори врата кон мини-бос!",
		"boss_dead": "Мини-босот падна! Бонус надградба",
		"reward_title": "Награда од мини-босот: избери надградба",
		"enter_room": "Мини-бос: еден на еден",
		"map": "МАПА",
		"legend": "врата со мини-бос",
		"names": ["Чуварот на јужната порта", "Копјаникот од исток", "Господарот на запад"],
		"to_portal": "Влези во порталот за да се вратиш",
		"restart": "Умре! Нивото се рестартира",
		"deaths": "Умирања",
	},
	"en": {
		"door_open": "A door to a mini-boss opened!",
		"boss_dead": "Mini-boss down! Bonus upgrade",
		"reward_title": "Mini-boss reward: choose an upgrade",
		"enter_room": "Mini-boss: one on one",
		"map": "MAP",
		"legend": "mini-boss door",
		"names": ["Warden of the south gate", "Spear Master of the east", "Lord of the west"],
		"to_portal": "Step into the portal to return",
		"restart": "You died! The level restarts",
		"deaths": "Deaths",
	},
}


static func t(lang: String, key: String):
	return TEXT[lang][key]


static func all_pillars() -> Array:
	return Cfg.PILLARS + EXTRA_PILLARS


static func all_low_walls() -> Array:
	return Cfg.LOW_WALLS + EXTRA_WALLS
