"""All tunable numbers for PERFORATED (Level 1: Pride) in one place."""

# ---- window ---------------------------------------------------------------
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
TITLE = "PERFORATED"

# ---- arena (1 unit = 1 pixel at 100% zoom) ---------------------------------
ARENA = 3000                 # playable floor is ARENA x ARENA
WALL = 128                   # thickness of the stone border around the floor
GATE_X0, GATE_X1 = ARENA // 2 - 140, ARENA // 2 + 140   # opening of the exit gate in the north wall
PLAYER_START = (ARENA // 2, int(ARENA * 0.62))

# ---- player ---------------------------------------------------------------
PLAYER_RADIUS = 18
PLAYER_SPEED = 310.0
PLAYER_ACCEL = 2600.0        # reaches full speed in ~0.12 s (momentum feel)
PLAYER_FRICTION = 2000.0
PLAYER_MAX_HP = 4
PLAYER_HP_CAP = 7
INVULN_TIME = 1.0

DASH_SPEED = 980.0
DASH_TIME = 0.16
DASH_IFRAMES = 0.30
DASH_CHARGES = 2
DASH_CHARGES_CAP = 4
DASH_RECHARGE = 3.0
DASH_DAMAGE = 2              # the dash perforates enemies it passes through

# ---- weapons -----------------------------------------------------------------
# Every weapon fires on its own; the needle is the starting one and each new wave
# lets the Ferryman unlock another (a choice of three), so runs end up with different combos.
SHOT_COOLDOWN = 0.45
SHOT_SPEED = 780.0
SHOT_DAMAGE = 1.0
SHOT_PIERCE = 2
SHOT_LIFE = 0.7
SHOT_RANGE = 440.0
SHOT_SPREAD_DEG = 9.0
SHOT_MAX_COUNT = 5

HALO_ORBS = 2                # orbs orbiting the hero
HALO_RADIUS = 105.0
HALO_SPEED = 3.4             # radians / s
HALO_DAMAGE = 1.2
HALO_HIT_GAP = 0.45          # s before the same orb can hit the same guardian again

PULSE_COOLDOWN = 2.6
PULSE_RADIUS = 210.0
PULSE_DAMAGE = 2.0

ARC_COOLDOWN = 1.35
ARC_RANGE = 360.0
ARC_JUMPS = 3
ARC_JUMP_RANGE = 210.0
ARC_DAMAGE = 1.7

MINE_COOLDOWN = 2.2
MINE_MAX = 3
MINE_RADIUS = 120.0
MINE_DAMAGE = 3.5
MINE_ARM = 0.6
MINE_LIFE = 30.0

CHAKRAM_COOLDOWN = 2.4
CHAKRAM_DAMAGE = 2.0
CHAKRAM_DIST = 360.0
CHAKRAM_SPEED = 620.0

SCATTER_COOLDOWN = 1.15
SCATTER_PELLETS = 5
SCATTER_DAMAGE = 1.0
SCATTER_RANGE = 340.0

SEEKER_COOLDOWN = 1.7
SEEKER_COUNT = 2
SEEKER_DAMAGE = 1.5
SEEKER_SPEED = 380.0

# stat upgrades (bought with box points)
STAT_DAMAGE_STEP = 0.25      # +25 % damage per pick
STAT_RATE_STEP = 0.85        # cooldowns x0.85 per pick
STAT_RATE_FLOOR = 0.35
STAT_AREA_STEP = 0.20
STAT_BONUS_CAP = 4           # max extra projectiles / orbs / jumps from "multi"
STAT_PIERCE_CAP = 6

# ---- Pride bar -----------------------------------------------------------------
# Waves are timed on paper: STAGE_SECONDS is how long each wave lasts if the hero kills
# everything that spawns. The bar size and the wave thresholds are derived from that,
# so changing a spawn rate or a duration automatically re-balances the whole level.
STAGE_SECONDS = (26, 28, 30, 33, 35, 38)      # 3.2 min if you kill every spawn; ~5 min in practice
NUM_STAGES = len(STAGE_SECONDS)

# ---- enemies: kind -> stats ------------------------------------------------------
# hp, speed (px/s), radius, points for the Pride bar
ENEMIES = {
    "sentinel":   dict(hp=3,  speed=120.0, r=21, pts=5,  sprite="guardian_sentinel",   shadow=44, knock=1.0),
    "skirmisher": dict(hp=2,  speed=215.0, r=16, pts=4,  sprite="guardian_skirmisher", shadow=34, knock=1.3),
    "lancer":     dict(hp=4,  speed=135.0, r=22, pts=8,  sprite="guardian_lancer",     shadow=46, knock=0.8),
    "swarmer":    dict(hp=1,  speed=225.0, r=12, pts=1,  sprite="guardian_swarmer",    shadow=26, knock=1.6),
    "bulwark":    dict(hp=14, speed=92.0,  r=31, pts=14, sprite="guardian_bulwark",    shadow=66, knock=0.3),
    "elite":      dict(hp=40, speed=140.0, r=36, pts=60, sprite="guardian_elite",      shadow=76, knock=0.0),
    # level 2 (Greed) only
    "bomber":     dict(hp=3,  speed=205.0, r=20, pts=7,  sprite="guardian_bomber",     shadow=40, knock=0.9),
    "banker":     dict(hp=5,  speed=130.0, r=22, pts=10, sprite="guardian_banker",     shadow=46, knock=0.7),
    # level 3 (Lust) only
    "charmer":    dict(hp=7,  speed=118.0, r=22, pts=12, sprite="guardian_charmer",    shadow=46, knock=0.6),
    "cupid":      dict(hp=4,  speed=150.0, r=20, pts=9,  sprite="guardian_cupid",      shadow=42, knock=0.9),
}
CHARM_RANGE = 650.0          # a charmer starts luring you from this far
CHARM_WINDUP = 0.6
CHARM_TIME = 1.1
CHARM_PULL = 330.0           # px/s she drags you towards her (about your own speed); a dash breaks free
CHARM_COOLDOWN = 4.2
CHARMER_CAP = 3              # alive at once
CUPID_HEARTS = 2             # slow homing hearts per volley
HEART_SPEED = 270.0
HEART_TURN = 1.7             # rad/s: they curve after you, but you can outrun and shoot them
HEART_LIFE = 4.5
BOMBER_RANGE = 150.0         # starts its fuse this close
BOMBER_FUSE = 0.7
BOMBER_BLAST = 150.0         # blast radius: step out of the red circle
BANKER_BURST = 3             # coin spears per burst, each aimed at where you are right then
BANKER_GAP = 0.2
MAX_ENEMIES = 150
SPEAR_SPEED = 450.0
SPEAR_COOLDOWN = 2.2
SPEAR_WINDUP = 0.55
SPEAR_LIFE = 2.2
ELITE_CHARGE_COOLDOWN = 3.0
ELITE_WINDUP = 0.65
ELITE_CHARGE_SPEED = 620.0
ELITE_CHARGE_TIME = 0.55
LUNGE_RANGE = 300.0          # skirmishers telegraph then lunge from this far
LUNGE_WINDUP = 0.4
LUNGE_SPEED = 540.0
LUNGE_TIME = 0.32
LUNGE_COOLDOWN = 3.0
BULWARK_ENRAGE = 0.5         # below this hp fraction the bulwark speeds up
RECYCLE_DISTANCE = 1500.0    # guardians left this far behind are teleported back to the action

# per wave: hp multiplier, speed multiplier (index 1..NUM_STAGES)
STAGE_HP = (0, 1.0, 1.0, 1.1, 1.2, 1.35, 1.5)
STAGE_SPEED = (0, 1.0, 1.04, 1.09, 1.14, 1.2, 1.26)

# spawn director per wave: interval (s), group size, alive cap, weights per kind,
# swarm = chance that a spawn tick is a pack of swarmers, pincer = group splits to both sides
STAGES = {
    1: dict(interval=1.5,  group=(1, 2), cap=12, weights=dict(sentinel=1.0), swarm=0.0, pincer=False),
    2: dict(interval=1.25, group=(3, 4), cap=22, weights=dict(sentinel=0.55, skirmisher=0.45), swarm=0.0, pincer=False),
    3: dict(interval=1.2,  group=(3, 4), cap=32, weights=dict(sentinel=0.45, skirmisher=0.3, lancer=0.25), swarm=0.2, pincer=False),
    4: dict(interval=1.1,  group=(3, 5), cap=44, weights=dict(sentinel=0.35, skirmisher=0.2, lancer=0.2, bulwark=0.25), swarm=0.2, pincer=False),
    5: dict(interval=0.95, group=(4, 6), cap=56, weights=dict(sentinel=0.3, skirmisher=0.2, lancer=0.2, bulwark=0.3), swarm=0.25, pincer=True),
    6: dict(interval=0.8,  group=(4, 7), cap=70, weights=dict(sentinel=0.3, skirmisher=0.2, lancer=0.2, bulwark=0.3), swarm=0.3, pincer=True),
}
SWARM_PACK = (6, 9)
LANCER_CAP = 4               # at most this many spear throwers alive at once
ELITES_AT_STAGE = {4: 1, 5: 1, 6: 2}   # elites that arrive when a wave begins
SPAWN_DIST = (780.0, 980.0)            # ring around the hero (just off screen)
MIN_SPAWN_DISTANCE = 700.0
SPAWN_POINTS = [(70, 70), (ARENA // 2, ARENA - 70), (ARENA - 70, 70), (70, ARENA - 70), (ARENA - 70, ARENA - 70),
                (70, ARENA // 2), (ARENA - 70, ARENA // 2), (ARENA // 2, 70)]
SPAWN_AFTER_EXIT = False     # once the gate is open, the guardians already out stay; no new ones


def _stage_rate(n):
    """Expected Pride points per second of wave n if every spawn is killed."""
    st = STAGES[n]
    wsum = sum(st["weights"].values())
    avg = sum(ENEMIES[k]["pts"] * w for k, w in st["weights"].items()) / wsum
    group = (st["group"][0] + st["group"][1]) / 2
    swarm_pts = (SWARM_PACK[0] + SWARM_PACK[1]) / 2 * ENEMIES["swarmer"]["pts"]
    per_tick = (1 - st["swarm"]) * group * avg + st["swarm"] * swarm_pts
    return per_tick / st["interval"]


_cum, STAGE_AT_PTS = 0.0, []
for _i, _sec in enumerate(STAGE_SECONDS, 1):
    _cum += _stage_rate(_i) * _sec
    STAGE_AT_PTS.append(_cum)
PRIDE_MAX = int(round(_cum, -1))
# points at which wave 2, 3, ... begin, and the same as a fraction of the bar
STAGE_AT_PTS = tuple(STAGE_AT_PTS[:-1])
STAGE_AT = tuple(p / PRIDE_MAX for p in STAGE_AT_PTS)
BAR_EDGES = (0.0,) + STAGE_AT_PTS + (float(PRIDE_MAX),)   # the HUD bar gives every wave an equal slice

# ---- boxes and box points ("offerings") ---------------------------------------------
BOX_START = 58               # boxes lying around at the start
BOX_TARGET = 84              # the level slowly restocks up to this many
BOX_RESPAWN = 3.5            # s between restocks (never in view)
BOX_RESPAWN_MIN_DIST = 650.0
BOX_GILDED_CHANCE = 0.12
BOX_CRATE_GEMS = (5, 4, 3)           # gem values dropped by a crate (12 box points)
BOX_GILDED_GEMS = (8, 7, 7, 7, 7)    # a gilded crate (36 box points)
GEM_MAGNET = 190.0
GEM_SPEED = 950.0
GEM_LIFE = 40.0


def upgrade_cost(n):
    """Box points needed for the (n+1)-th stat upgrade."""
    return 60 + 25 * n + 8 * n * n


# ---- pickups -----------------------------------------------------------------
HEART_SPOTS = [(420, 2580), (2580, 420), (420, 420), (2580, 2580)]
HEART_RESPAWN = 30.0
ALTAR_POS = (2520, 1050)


# ======================================================================================
# Levels. Level 1 (Pride) is described by the module-level constants above; every level
# gets a LevelCfg with its own waves, difficulty multipliers and theme.
# ======================================================================================
class LevelCfg:
    def __init__(self, num, stages, stage_seconds, stage_hp, stage_speed, elites, lancer_cap, swarm_pack,
                 hp_mult=1.0, speed_mult=1.0, elite_hp_mult=1.0, fan_stage=5, elite_rage_stage=6,
                 nova_marks=(0.5,), nova_spears=10):
        self.num = num
        self.stages = stages
        self.stage_seconds = stage_seconds
        self.num_stages = len(stage_seconds)
        self.stage_hp = stage_hp
        self.stage_speed = stage_speed
        self.elites = elites
        self.lancer_cap = lancer_cap          # lancers + bankers alive at once
        self.swarm_pack = swarm_pack
        self.hp_mult = hp_mult                # on top of the per-wave hp table
        self.speed_mult = speed_mult
        self.elite_hp_mult = elite_hp_mult
        self.fan_stage = fan_stage            # wave from which lancers throw three spears
        self.elite_rage_stage = elite_rage_stage
        self.nova_marks = nova_marks          # elite hp fractions at which it throws a ring of spears
        self.nova_spears = nova_spears
        cum, pts = 0.0, []
        for i, sec in enumerate(stage_seconds, 1):
            cum += self.rate(i) * sec
            pts.append(cum)
        self.pride_max = int(round(cum, -1))
        self.stage_at_pts = tuple(pts[:-1])
        self.bar_edges = (0.0,) + self.stage_at_pts + (float(self.pride_max),)

    def rate(self, n):
        """Expected Pride points per second of wave n if every spawn is killed."""
        st = self.stages[n]
        wsum = sum(st["weights"].values())
        avg = sum(ENEMIES[k]["pts"] * w for k, w in st["weights"].items()) / wsum
        group = (st["group"][0] + st["group"][1]) / 2
        swarm_pts = (self.swarm_pack[0] + self.swarm_pack[1]) / 2 * ENEMIES["swarmer"]["pts"]
        per_tick = (1 - st["swarm"]) * group * avg + st["swarm"] * swarm_pts
        return per_tick / st["interval"]


LEVEL1 = LevelCfg(1, STAGES, STAGE_SECONDS, STAGE_HP, STAGE_SPEED, ELITES_AT_STAGE, LANCER_CAP, SWARM_PACK)

# Level 2 (Greed): the same guardians, but far tougher, faster and more numerous, plus bombers and bankers.
STAGES_2 = {
    1: dict(interval=1.1,  group=(3, 4), cap=26, weights=dict(sentinel=0.45, skirmisher=0.35, lancer=0.2), swarm=0.1, pincer=False),
    2: dict(interval=1.0,  group=(3, 5), cap=36, weights=dict(sentinel=0.3, skirmisher=0.3, lancer=0.2, banker=0.2), swarm=0.2, pincer=False),
    3: dict(interval=0.9,  group=(4, 5), cap=46, weights=dict(sentinel=0.25, skirmisher=0.2, lancer=0.15, banker=0.15, bomber=0.15, bulwark=0.1), swarm=0.2, pincer=True),
    4: dict(interval=0.8,  group=(4, 6), cap=58, weights=dict(sentinel=0.2, skirmisher=0.2, lancer=0.15, banker=0.15, bomber=0.15, bulwark=0.15), swarm=0.25, pincer=True),
    5: dict(interval=0.7,  group=(5, 7), cap=72, weights=dict(sentinel=0.15, skirmisher=0.2, lancer=0.15, banker=0.15, bomber=0.15, bulwark=0.2), swarm=0.25, pincer=True),
    6: dict(interval=0.6,  group=(5, 8), cap=88, weights=dict(sentinel=0.15, skirmisher=0.2, lancer=0.15, banker=0.15, bomber=0.15, bulwark=0.2), swarm=0.3, pincer=True),
}
LEVEL2 = LevelCfg(2, STAGES_2, (34, 36, 40, 43, 46, 50),
                  stage_hp=(0, 1.0, 1.1, 1.25, 1.4, 1.6, 1.8), stage_speed=(0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3),
                  elites={2: 1, 3: 2, 4: 2, 5: 3, 6: 4}, lancer_cap=8, swarm_pack=(8, 12),
                  hp_mult=2.1, speed_mult=1.16, elite_hp_mult=1.6, fan_stage=3, elite_rage_stage=4,
                  nova_marks=(0.75, 0.5, 0.25), nova_spears=14)

# Level 3 (Lust): the guardians again, tougher still, with charmers that drag you in and cupids that fire homing hearts.
STAGES_3 = {
    1: dict(interval=0.72, group=(4, 6), cap=48,  weights=dict(sentinel=0.3, skirmisher=0.25, lancer=0.1, banker=0.1, cupid=0.15, bulwark=0.1), swarm=0.2, pincer=True),
    2: dict(interval=0.64, group=(5, 7), cap=62,  weights=dict(sentinel=0.2, skirmisher=0.2, lancer=0.1, banker=0.1, cupid=0.15, charmer=0.1, bulwark=0.15), swarm=0.2, pincer=True),
    3: dict(interval=0.55, group=(5, 8), cap=78,  weights=dict(sentinel=0.15, skirmisher=0.2, lancer=0.1, banker=0.1, cupid=0.15, charmer=0.1, bomber=0.1, bulwark=0.15), swarm=0.25, pincer=True),
    4: dict(interval=0.48, group=(6, 9), cap=94,  weights=dict(sentinel=0.15, skirmisher=0.2, lancer=0.1, banker=0.1, cupid=0.15, charmer=0.1, bomber=0.1, bulwark=0.2), swarm=0.25, pincer=True),
    5: dict(interval=0.42, group=(6, 10), cap=110,  weights=dict(sentinel=0.1, skirmisher=0.2, lancer=0.1, banker=0.1, cupid=0.15, charmer=0.1, bomber=0.15, bulwark=0.2), swarm=0.3, pincer=True),
    6: dict(interval=0.38, group=(7, 11), cap=130, weights=dict(sentinel=0.1, skirmisher=0.2, lancer=0.1, banker=0.1, cupid=0.15, charmer=0.1, bomber=0.15, bulwark=0.2), swarm=0.3, pincer=True),
}
LEVEL3 = LevelCfg(3, STAGES_3, (36, 38, 42, 46, 50, 54),
                  stage_hp=(0, 1.0, 1.1, 1.25, 1.4, 1.6, 1.8), stage_speed=(0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3),
                  elites={2: 2, 3: 3, 4: 3, 5: 4, 6: 6}, lancer_cap=14, swarm_pack=(12, 16),
                  hp_mult=4.2, speed_mult=1.25, elite_hp_mult=2.6, fan_stage=2, elite_rage_stage=3,
                  nova_marks=(0.8, 0.6, 0.4, 0.2), nova_spears=16)
LEVELS = {1: LEVEL1, 2: LEVEL2, 3: LEVEL3}
NUM_LEVELS = len(LEVELS)
RANGED_KINDS = ("lancer", "banker", "cupid")      # share one alive-at-once cap per level

# what the hero keeps when Level 1 is won (used by the F2 shortcut on the title screen)
DEMO_CARRY = dict(weapons=["needle", "halo", "pulse", "arc", "chakram"], dmg_mult=1.75, rate_mult=0.72, bonus=2,
                  pierce_bonus=2, area=1.4, speed=PLAYER_SPEED * 1.1, max_hp=5, charge_cap=3, recharge=2.7)

# a late-game hero, for the F3 shortcut and for balancing Level 3
DEMO_CARRY_LATE = dict(weapons=["needle", "halo", "pulse", "arc", "chakram", "mine", "scatter", "seeker"], dmg_mult=2.0,
                       rate_mult=0.62, bonus=3, pierce_bonus=3, area=1.6, speed=PLAYER_SPEED * 1.2, max_hp=6,
                       charge_cap=4, recharge=2.4)

# per-level look: lighting, colours, texture tints (multiplied into the textures/sprites)
THEMES = {
    1: dict(name="pride", style="stone", ambient=(62, 68, 98), gem=(80, 235, 205), bar=(70, 225, 195),
            brazier=(255, 168, 78), flame=(255, 150, 40), flame_core=(255, 240, 170), tints={}),
    2: dict(name="greed", style="money", ambient=(46, 80, 64), gem=(255, 215, 80), bar=(255, 205, 70),
            brazier=(110, 255, 150), flame=(60, 230, 110), flame_core=(210, 255, 190),
            inlay=((20, 90, 50), (255, 214, 90)), decor=("coin_decor", "bill_decor"), emblem_alpha=70,
            tints={"marble": (150, 232, 170), "wall_block": (120, 190, 140), "pillar": (150, 230, 170),
                   "brazier": (160, 255, 190), "gate_closed": (170, 255, 190), "gate_open": (170, 255, 190),
                   "guardian_sentinel": (170, 255, 190), "guardian_skirmisher": (160, 255, 175),
                   "guardian_lancer": (200, 255, 170), "guardian_elite": (255, 240, 140)},
            swarmer_tint=(255, 235, 130), bulwark_tint=(150, 235, 160)),
    3: dict(name="lust", style="lust", ambient=(88, 52, 78), gem=(255, 105, 170), bar=(255, 105, 170),
            brazier=(255, 90, 170), flame=(255, 60, 150), flame_core=(255, 215, 235),
            inlay=((110, 20, 60), (255, 170, 200)), decor=("petal_decor", "heart_decor"), emblem_alpha=90,
            tints={"marble": (255, 190, 215), "wall_block": (190, 110, 150), "pillar": (255, 190, 220),
                   "brazier": (255, 190, 230), "gate_closed": (255, 190, 225), "gate_open": (255, 190, 225),
                   "guardian_sentinel": (255, 175, 205), "guardian_skirmisher": (255, 160, 195),
                   "guardian_lancer": (235, 175, 255), "guardian_elite": (255, 130, 170)},
            swarmer_tint=(255, 200, 235), bulwark_tint=(235, 170, 255)),
}
