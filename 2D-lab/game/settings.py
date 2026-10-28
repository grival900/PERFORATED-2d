"""All tunable numbers for PERFORATED (Level 1: Pride) in one place."""

# ---- window ---------------------------------------------------------------
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
TITLE = "PERFORATED"

# ---- arena (1 unit = 1 pixel at 100% zoom) ---------------------------------
ARENA = 1800                 # playable floor is ARENA x ARENA
WALL = 128                   # thickness of the stone border around the floor
GATE_X0, GATE_X1 = 760, 1040  # opening of the exit gate in the north wall
PLAYER_START = (900, 1116)

# ---- player ---------------------------------------------------------------
PLAYER_RADIUS = 18
PLAYER_SPEED = 310.0
PLAYER_ACCEL = 2600.0        # reaches full speed in ~0.12 s (momentum feel)
PLAYER_FRICTION = 2000.0
PLAYER_MAX_HP = 3
PLAYER_HP_CAP = 6
INVULN_TIME = 1.0

DASH_SPEED = 980.0
DASH_TIME = 0.16
DASH_IFRAMES = 0.30
DASH_CHARGES = 2
DASH_CHARGES_CAP = 4
DASH_RECHARGE = 3.0
DASH_DAMAGE = 2              # the dash perforates enemies it passes through

SHOT_COOLDOWN = 0.45
SHOT_SPEED = 780.0
SHOT_DAMAGE = 1
SHOT_PIERCE = 2
SHOT_LIFE = 0.7
SHOT_RANGE = 440.0
SHOT_SPREAD_DEG = 9.0
SHOT_MAX_COUNT = 5

# ---- Pride bar --------------------------------------------------------------
PRIDE_MAX = 1500
UPGRADE_AT = (0.25, 0.50, 0.75)
STAGE_AT = (0.25, 0.50, 0.75)

# ---- enemies: kind -> stats ------------------------------------------------------
# hp, speed (px/s), radius, points for the Pride bar, contact damage
ENEMIES = {
    "sentinel":   dict(hp=2,  speed=88.0,  r=21, pts=6,   sprite="guardian_sentinel",   shadow=44, knock=1.0),
    "skirmisher": dict(hp=1,  speed=175.0, r=16, pts=5,   sprite="guardian_skirmisher", shadow=34, knock=1.3),
    "lancer":     dict(hp=3,  speed=105.0, r=22, pts=14,  sprite="guardian_lancer",     shadow=46, knock=0.8),
    "elite":      dict(hp=26, speed=112.0, r=36, pts=100, sprite="guardian_elite",      shadow=76, knock=0.0),
}
MAX_ENEMIES = 150
SPEAR_SPEED = 430.0
SPEAR_COOLDOWN = 2.4
SPEAR_WINDUP = 0.55
SPEAR_LIFE = 3.2
ELITE_CHARGE_COOLDOWN = 3.4
ELITE_WINDUP = 0.75
ELITE_CHARGE_SPEED = 560.0
ELITE_CHARGE_TIME = 0.55

# spawn director: per stage -> (interval s, (min, max) group size, alive cap, weights)
STAGES = {
    1: dict(interval=1.5, group=(2, 3), cap=14,  weights=dict(sentinel=1.0)),
    2: dict(interval=1.4, group=(3, 4), cap=22,  weights=dict(sentinel=0.6, skirmisher=0.4)),
    3: dict(interval=1.3, group=(3, 5), cap=30,  weights=dict(sentinel=0.45, skirmisher=0.3, lancer=0.25)),
    4: dict(interval=0.85, group=(4, 7), cap=55, weights=dict(sentinel=0.4, skirmisher=0.3, lancer=0.3)),
}
SPAWN_POINTS = [
    (70, 70), (900, 1750), (1730, 640), (70, 640), (1730, 1730), (70, 1730), (900, 70), (1730, 70),
    (70, 1260), (1730, 1260),
]
MIN_SPAWN_DISTANCE = 650

# ---- pickups -----------------------------------------------------------------
HEART_SPOTS = [(252, 1548), (1548, 252)]
HEART_RESPAWN = 40.0
ALTAR_POS = (1512, 630)
