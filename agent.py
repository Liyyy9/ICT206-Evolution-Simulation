import random
from dataclasses import dataclass
from typing import Tuple, Optional
import config as cfg

Colour = Tuple[int, int, int]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _random_alive_colour() -> Colour:
    return (
        random.randint(90, 230),
        random.randint(90, 230),
        random.randint(90, 230)
    )


@dataclass
class Agent:
    id: int
    x: float
    y: float
    velocityX: float
    velocityY: float

    # internal state
    age: float = 0
    hunger: float = 0.0
    thirst: float = 0.0
    energy: float = 100.0
    health: float = 100.0

    colour: Colour = (255, 255, 255)    # randomised at spawn
    alive: bool = True

    # action state
    action: str = "WANDER"
    eat_pause: float = 0.0
    drink_timer: float = 0.0

    interact_cooldown: float = 0.0

    # vision
    vision_radius: float = 220.0
    steer_strength: float = 0.18
    wander_angle: float = 0.0
    waypoint: Tuple[float, float] = (0.0, 0.0)
    waypoint_timer: float = 0.0


def create_agent(agent_id: int, width: int, height: int, radius: int) -> Agent:
    a = Agent(
        id=agent_id,
        x=float(random.randint(radius, width - radius)),
        y=float(random.randint(radius, height - radius)),
        velocityX=float(random.choice([-2, -1, 1, 2])),
        velocityY=float(random.choice([-2, -1, 1, 2])),
        colour=_random_alive_colour()
    )

    a.vision_radius = cfg.SENSING["VISION_RADIUS"]
    a.steer_strength = cfg.SENSING["STEER_STRENGTH"]
    a.wander_angle = random.uniform(0, 6.28318)

    m = cfg.SENSING["WAYPOINT_MARGIN"]
    a.waypoint = (
        random.uniform(m, width - m),
        random.uniform(m, height - m)
    )
    a.waypoint_timer = random.uniform(0.0, cfg.SENSING["WAYPOINT_TIMEOUT"])

    return a


def update_internal_state(a: Agent, dt: float) -> None:
    """
    Updates stats using dt (seconds).
    Sets a.alive=False when dead. (main.py removes dead agents)
    """

    if not a.alive:
        return

    a.age += dt

    # Change over time (dt-based)
    a.hunger += cfg.RATES["HUNGER_UP"] * dt
    a.thirst += cfg.RATES["THIRST_UP"] * dt
    a.energy -= cfg.RATES["ENERGY_DOWN"] * dt

    # Clamp core stats
    a.hunger = clamp(a.hunger, 0.0, 100.0)
    a.thirst = clamp(a.thirst, 0.0, 100.0)
    a.energy = clamp(a.energy, 0.0, 100.0)
    a.health = clamp(a.health, 0.0, 100.0)

    # Health
    drain = cfg.RATES["HEALTH_DRAIN_BASE"]

    # SEEK-level penalties
    if a.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]:
        drain += cfg.RATES["HEALTH_DRAIN_SEEK"]
    if a.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]:
        drain += cfg.RATES["HEALTH_DRAIN_SEEK"]
    if a.energy <= cfg.THRESHOLDS["ENERGY_SLOW"]:
        drain += cfg.RATES["HEALTH_DRAIN_SEEK"]

    # CRITICAL-level penalties
    if a.thirst >= cfg.THRESHOLDS["THIRST_CRIT"]:
        drain += cfg.RATES["HEALTH_DRAIN_CRIT"]
    if a.hunger >= cfg.THRESHOLDS["HUNGER_CRIT"]:
        drain += cfg.RATES["HEALTH_DRAIN_CRIT"]
    if a.energy <= cfg.THRESHOLDS["ENERGY_CRIT"]:
        drain += cfg.RATES["HEALTH_DRAIN_CRIT"]

    # Small regen if doing okay (not in SEEK zones and energy not low)
    doing_okay = (
        a.hunger < cfg.THRESHOLDS["HUNGER_SEEK"]
        and a.thirst < cfg.THRESHOLDS["THIRST_SEEK"]
        and a.energy > cfg.THRESHOLDS["ENERGY_SLOW"]
    )
    if doing_okay:
        a.health += cfg.RATES["HEALTH_REGEN"] * dt

    # Apply drain
    a.health -= drain * dt
    a.health = clamp(a.health, 0.0, 100.0)

    # --- death conditions ---
    if a.health <= 0.0 or a.age >= cfg.MAX_AGE:
        a.alive = False


def movement_multiplier(a: Agent) -> float:
    """
    Simplified energy:
    - Energy only affects speed (no resting state)
    - Agents start slow and ramp up over time (Option A)
    """
    # 1) Energy → speed factor (never 0)
    slow = cfg.THRESHOLDS["ENERGY_SLOW"]
    crit = cfg.THRESHOLDS["ENERGY_CRIT"]

    # floor multiplier so they never "stop in place"
    min_mult = cfg.THRESHOLDS.get("ENERGY_MIN_MULT", 0.35)

    if a.energy >= slow:
        energy_mult = 1.0
    elif a.energy <= crit:
        energy_mult = min_mult
    else:
        # linear between crit..slow
        t = (a.energy - crit) / (slow - crit)
        energy_mult = min_mult + t * (1.0 - min_mult)

    # 2) Option A: "start slow" ramp (time-based)
    # ramps from START_SPEED_MULT -> 1.0 over SPEED_RAMP_SECONDS
    start_mult = cfg.THRESHOLDS.get("START_SPEED_MULT", 0.55)
    ramp_s = cfg.THRESHOLDS.get("SPEED_RAMP_SECONDS", 45.0)

    if ramp_s <= 0:
        ramp_mult = 1.0
    else:
        ramp_mult = min(1.0, start_mult + (a.age / ramp_s)
                        * (1.0 - start_mult))

    return energy_mult * ramp_mult
