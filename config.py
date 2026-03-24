import random
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

    # Chatbox colors (state indicators)
    "CHATBOX_BASE": (186, 186, 177),    # Light grey (default)
    "CHATBOX_CRITICAL": (255, 150, 150),  # Red
}

# ICONS for UI
ICONS = {
    "THIRST": "assets/mug.png",
    "HUNGER": "assets/apple.png",
    "LOVE": "assets/love.png",
}

# Screen & World
# Display window (what pygame shows on screen)
DISPLAY_WIDTH, DISPLAY_HEIGHT = 1600, 900
# World coordinates (where agents actually live - larger world, zoomed out view)
WORLD_WIDTH, WORLD_HEIGHT = 2400, 1350
# For backward compatibility with existing code
WIDTH, HEIGHT = WORLD_WIDTH, WORLD_HEIGHT
FPS = 30

# Simulation Mode
HEADLESS_MODE = True  # Set to True for CSV-only mode (no visualization)
# Max seconds to run (0 = infinite, set to 3600 for 1 hour)
HEADLESS_MODE_DURATION = 0
HEADLESS_MODE_MAX_GENERATION = 30  # Stop at generation (0 = infinite)
# Auto-restart when population crashes (only in headless mode)
HEADLESS_MODE_AUTO_RESTART = True
# Min population to trigger restart (if population drops below this, restart)
HEADLESS_MODE_MIN_POPULATION = 5
# Min elapsed time before allowing restart (prevents restart spam)
HEADLESS_MODE_MIN_TIME_BETWEEN_RESTARTS = 60  # seconds

# Agents
NUM_AGENTS = 20
AGENT_RADIUS = 8
# Based off seconds (set to 180 for 3 minutes, 60 for 1 minute testing)
MAX_AGE = 60.0

# Disaster System (natural population control)
DISASTER_ENABLED = True  # Enable automatic disasters in headless mode
# Trigger disaster when population exceeds this
DISASTER_POPULATION_THRESHOLD = 5000
DISASTER_MIN_GENERATIONS_APART = 15  # Rare shocks, not routine culling
# If True, preferentially kill weaker agents (lower health)
DISASTER_TARGET_WEAK = True
DISASTER_MORTALITY_RATE = random.uniform(0.60, 0.75)  # Reduced from 0.65-0.85

# Logistic Growth Carrying Capacity (population density control)
LOGISTIC_GROWTH_ENABLED = True  # Enable natural density-dependent mortality
CARRYING_CAPACITY = 4000  # K: comfortable population limit for laptop
# Formula: P(survival) = 1 - (current_population / CARRYING_CAPACITY)
# At population = 2000: 50% extra survival penalty
# At population = 4000: 100% extra survival penalty (hard limit)
DISASTER_TYPES = ["Plague", "Drought", "Disease",
                  "Famine", "Storm", "Earthquake",
                  "Tornado", "Volcanic Eruption",
                  "Tsunami", "Meteor Strike",
                  "Global Warming", "Alien Invasion",
                  "Avengers Woop-sie", "Fire Nation",
                  "Thanos Snap", "Typhoon",
                  "Puppy Stampede", "Fungus Takeover",
                  "Zombie Outbreak", "Pigeon Coup",
                  "Giant Ant Colony", "Spaghetti Tornado",
                  "Cat Judgement Day", "Cheese Shortage Crisis",
                  "Banana Peel Pandemic", "Clown Invasion",
                  "Godzilla Attack", "Volcanic Winters",
                  "Asteroid"]  # Random disaster names

# Thresholds
THRESHOLDS = {
    # Hunger (0...100)
    # Start looking for food (lower = enter SEEK sooner)
    "HUNGER_SEEK": 45.0,
    "HUNGER_OK": 10.0,          # Stop eating
    "HUNGER_CRIT": 80.0,

    # Thirst (0...100)
    # Start looking for water (lower = enter SEEK sooner)
    "THIRST_SEEK": 45.0,
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
    # 0->100 in 42s (moderate-high)
    "HUNGER_UP": 2.4,
    # 0->100 in 42s (moderate-high)
    "THIRST_UP": 2.4,
    "ENERGY_DOWN": 0.8,        # 100->40 in 75s

    # Health model - balanced for early survival + late population control
    "HEALTH_REGEN": 0.35,               # increased for Gen 1 survival
    # moderate baseline drain
    "HEALTH_DRAIN_BASE": 0.85,

    # extra drain when hungry/thirsty (selection pressure)
    "HEALTH_DRAIN_SEEK": 3.0,
    # extra drain if critical - serious penalty
    "HEALTH_DRAIN_CRIT": 5.2,
}

RESOURCES = {
    # pond blob
    "POND_MARGIN": 100,
    "POND_CIRCLES": 8,
    "POND_RADIUS_MIN": 35,
    "POND_RADIUS_MAX": 80,

    # bushes + food dots
    "NUM_BUSHES": 4,  # Keep at 4 for moderate competition on larger world
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
    "VISION_RADIUS": 130.0,        # px; reduced to force competition on larger world
    "STEER_STRENGTH": 0.18,        # 0..1; higher = more direct steering
    "WANDER_JITTER": 0.35,         # how much random turn during wandering
    "TARGET_REACHED_DIST": 14.0,   # px; when close enough to food, treat as "arrived"

    "WAYPOINT_MARGIN": 120.0,      # keeps targets away from edges
    "WAYPOINT_REACHED": 35.0,      # how close before picking a new target
    "WAYPOINT_TIMEOUT": 4.0,       # seconds before forcing a new waypoint
}

MEMORY = {
    "TIMEOUT": 20.0,  # seconds before memory expires
}

REPRODUCTION = {
    "MIN_MATE_AGE": 12.0,                    # lowered for Gen 1 bootstrap
    # success rate when two mates are in proximity
    # reduced to control post-disaster population explosion
    "REPRODUCTION_PROBABILITY": 0.25,
    # px; agents must be within this distance to mate
    "MATE_RADIUS": 80.0,
    # seconds before SEEK_MATE fails and agent returns to wander
    "MATE_SEEK_TIMEOUT": 5.0,
    # seconds before parent can mate again (must be > 0 to prevent runaway loops)
    "REPRO_COOLDOWN": 3.5,
    # energy drained from each parent on successful reproduction
    "REPRO_ENERGY_COST": 35.0,
    "SPAWN_OFFSET_RANGE": 30.0,              # px; random offset from parent midpoint
    "REPRO_ANIMATION_DURATION": 1.0,         # seconds to show love icon
    # range of offspring per successful mating (random between min and max, inclusive)
    "OFFSPRING_MIN": 1,
    "OFFSPRING_MAX": 1,
}

MUTATION = {
    "MUTATION_RATE": 0.12,                   # 12% chance to mutate each trait
    "MUTATION_STD_DEV": 0.15,                # Gaussian std dev for mutation nudge
}
