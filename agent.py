import random
from dataclasses import dataclass
from typing import Tuple
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


def create_agent(agent_id: int, width: int, height: int, radius: int) -> Agent:
    return Agent(
        id=agent_id,
        x=float(random.randint(radius, width - radius)),
        y=float(random.randint(radius, height - radius)),
        velocityX=float(random.choice([-2, -1, 1, 2])),
        velocityY=float(random.choice([-2, -1, 1, 2])),
        colour=_random_alive_colour()
    )


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

    # Rest rules (energy critical)
    # If energy is critical, the agent "rests" and regains energy
    if (a.energy <= cfg.THRESHOLDS["ENERGY_CRIT"]):
        a.energy += cfg.RATES["REST_ENERGY_REGEN"] * dt
        a.energy = clamp(a.energy, 0.0, 100.0)

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
    Low energy slows the agent down smoothly.
    energy >= ENERGY_SLOW -> 1.0
    energy <= ENERGY_CRIT -> 0.0 (rest)
    """
    slow = cfg.THRESHOLDS["ENERGY_SLOW"]
    crit = cfg.THRESHOLDS["ENERGY_CRIT"]

    if a.energy <= crit:
        return 0.0
    if a.energy >= slow:
        return 1.0

    # linear scale between crit..slow
    return (a.energy - crit) / (slow - crit)
