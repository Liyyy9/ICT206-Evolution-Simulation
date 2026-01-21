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
MAX_AGE = 900.0

# Thresholds
THRESHOLDS = {
    "HUNGER_SEEK": 3.0,
    "HUNGER_CRIT": 20.0,

    "THIRST_SEEK": 3.0,
    "THIRST_CRIT": 20.0,

    "ENERGY_SLOW": 30.0,
    "ENERGY_CRIT": 10.0
}

# Rates (per second)
RATES = {
    "HUNGER_UP": 0.05,
    "THIRST_UP": 0.07,
    "ENERGY_DOWN": 0.03,

    # Health model
    "HEALTH_REGEN": 0.8,                # when doing okay
    "HEALTH_DRAIN_BASE": 0.4,           # baseline
    # extra drain when hunger/thirst past SEEK, or energy low
    "HEALTH_DRAIN_SEEK": 0.8,
    "HEALTH_DRAIN_CRIT": 2.0,           # extra drain if any critical
    # per second energy regen when resting (energy <= crit)
    "REST_ENERGY_REGEN": 6.0
}

RESOURCES = {
    # pond blob
    "POND_MARGIN": 100,
    "POND_CIRCLES": 8,
    "POND_RADIUS_MIN": 35,
    "POND_RADIUS_MAX": 80,

    # bushes + food dots
    "NUM_BUSHES": 4,
    "BUSH_BLOB_CIRCLES": 3,
    "BUSH_BLOB_RADIUS_MIN": 26,
    "BUSH_BLOB_RADIUS_MAX": 42,
    "BUSH_MIN_DIST": 200,
    "BUSH_SPAWN_ATTEMPTS": 50,

    "FOOD_PER_BUSH_MIN": 2,
    "FOOD_PER_BUSH_MAX": 5,
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

    # Consumption
    "EAT_AMOUNT": 30.0,
    "EAT_PAUSE": 1.5,

    "DRINK_FULL_LEVEL": 10.0,
    "DRINK_INTERVAL": 1.0,
    "DRINK_AMOUNT": 1.0,
}
