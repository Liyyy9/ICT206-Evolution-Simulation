# Define colours
COLOURS = {
    "GRASS": (120, 190, 114),

    "WATER": (70, 130, 180),
    "WATER_RIM": (95, 155, 205),
    "WATER_SPARKLE": (150, 200, 235),

    "FOOD": (200, 60, 60),
    "FOOD_RIM": (120, 20, 20),

    "BUSH": (80, 140, 90),
    "BUSH_OUTLINE": (55, 110, 70),

    "OUTLINE": (20, 20, 20),
}

# Screen
WIDTH, HEIGHT = 1280, 720
FPS = 60

# Agents
NUM_AGENTS = 20
AGENT_RADIUS = 8
# Based off seconds (set to 180 for 3 minutes, 60 for 1 minute testing)
MAX_AGE = 180.0

# Thresholds
THRESHOLDS = {
    # Hunger (0...100)
    "HUNGER_SEEK": 35.0,        # Start looking for food
    "HUNGER_OK": 10.0,          # Stop eating
    "HUNGER_CRIT": 80.0,

    # Thirst (0...100)
    "THIRST_SEEK": 25.0,        # Start looking for water
    "THIRST_OK": 8.0,           # Stop drinking
    "THIRST_CRIT": 80.0,

    # Energy (100...0)
    "ENERGY_SLOW": 40.0,        # Start slowing down
    "ENERGY_CRIT": 15.0,

    # Simplified energy speed behavior
    "ENERGY_MIN_MULT": 0.35,     # never fully stop
    "START_SPEED_MULT": 0.55,    # start slow
    "SPEED_RAMP_SECONDS": 45.0,  # reach full speed after ~45s
}

# Rates (per second)
RATES = {
    "HUNGER_UP": 1.5,          # 0->100 in 23s
    "THIRST_UP": 1.2,          # 0->100 in 21s
    "ENERGY_DOWN": 0.8,        # 100->40 in 75s

    # Health model
    "HEALTH_REGEN": 0.25,                # when doing okay
    "HEALTH_DRAIN_BASE": 0.06,           # baseline

    # extra drain when hunger/thirst past SEEK, or energy low
    "HEALTH_DRAIN_SEEK": 0.18,
    "HEALTH_DRAIN_CRIT": 0.9,           # extra drain if any critical
}

RESOURCES = {
    # pond blob
    "POND_MARGIN": 100,
    "POND_CIRCLES": 8,
    "POND_RADIUS_MIN": 35,
    "POND_RADIUS_MAX": 80,

    # bushes + food dots
    "NUM_BUSHES": 2,
    "BUSH_BLOB_CIRCLES": 3,
    "BUSH_BLOB_RADIUS_MIN": 26,
    "BUSH_BLOB_RADIUS_MAX": 42,
    "BUSH_MIN_DIST": 200,
    "BUSH_SPAWN_ATTEMPTS": 50,

    "FOOD_PER_BUSH_MIN": 2,
    "FOOD_PER_BUSH_MAX": 4,
    "FOOD_RADIUS": 6,
    "FOOD_RIM_THICKNESS": 2,
    "FOOD_EDGE_MARGIN": 8,
    "FOOD_MIN_GAP": 10,
    "FOOD_SPAWN_ATTEMPTS": 200,
    "FOOD_REGEN_SECONDS": 5.0,

    # Pond
    "POND_SPARKLES": 25,
    "POND_SPARKLE_R_MIN": 1,
    "POND_SPARKLE_R_MAX": 3,
    "POND_BUSH_BUFFER": 180,

    "EAT_AMOUNT": 30.0,
    "EAT_PAUSE": 0.25,

    "DRINK_FULL_LEVEL": 10.0,    # stop drinking
    "DRINK_INTERVAL": 0.5,      # how long they stop at a pond
    "DRINK_AMOUNT": 4.0,        # how much thirst is reduced
    "ENERGY_FROM_DRINK": 8.0,
    "ENERGY_FROM_EAT": 18.0,
}

SENSING = {
    "VISION_RADIUS": 220.0,        # px; try 180–280
    "STEER_STRENGTH": 0.18,        # 0..1; higher = more direct steering
    "WANDER_JITTER": 0.35,         # how much random turn during wandering
    "TARGET_REACHED_DIST": 14.0,   # px; when close enough to food, treat as "arrived"

    "WAYPOINT_MARGIN": 120.0,      # keeps targets away from edges
    "WAYPOINT_REACHED": 35.0,      # how close before picking a new target
    "WAYPOINT_TIMEOUT": 4.0,       # seconds before forcing a new waypoint
}
