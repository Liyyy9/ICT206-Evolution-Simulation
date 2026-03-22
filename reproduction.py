"""
Reproduction system for agent evolution simulator.
Handles partner-seeking, mate eligibility, and offspring creation.
"""

import random
import math
from typing import Optional, Tuple
import agent as ag
import traits as tr
import config as cfg


def is_eligible_for_mate_seeking(agent: ag.Agent) -> bool:
    """
    Check if agent can enter SEEK_MATE state.
    Requires: age >= 25s, hunger and thirst below SEEK thresholds.
    """
    if agent.age < cfg.REPRODUCTION.get("MIN_MATE_AGE", 25.0):
        return False

    if agent.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]:
        return False

    if agent.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]:
        return False

    # Not on cooldown from previous reproduction
    repro_cooldown = getattr(agent, "repro_cooldown", 0.0)
    if repro_cooldown > 0.0:
        return False

    return True


def should_abort_mate_seeking(agent: ag.Agent) -> bool:
    """
    Check if agent should abort SEEK_MATE state.
    Aborts if hunger or thirst crosses SEEK threshold.
    """
    if agent.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]:
        return True

    if agent.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]:
        return True

    return False


def find_closest_mate(
    agent: ag.Agent,
    all_agents: list[ag.Agent],
    cfg_obj=None
) -> Optional[ag.Agent]:
    """
    Find the closest agent also in SEEK_MATE state and eligible.
    Returns the closest mate, or None if no valid mate exists.
    """
    if cfg_obj is None:
        cfg_obj = cfg

    closest_mate = None
    min_dist = float('inf')

    for other in all_agents:
        if other.id == agent.id:
            continue

        # Check if other is also seeking
        if getattr(other, "action", "WANDER") != "SEEK_MATE":
            continue

        # Check eligibility
        if not is_eligible_for_mate_seeking(other):
            continue

        # Calculate distance
        dx = other.x - agent.x
        dy = other.y - agent.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < min_dist:
            min_dist = dist
            closest_mate = other

    return closest_mate


def attempt_reproduction(
    parent_a: ag.Agent,
    parent_b: ag.Agent,
    cfg_obj=None
) -> Optional[ag.Agent]:
    """
    Attempt reproduction between two agents.
    Success is probabilistic (REPRODUCTION_PROBABILITY).
    On success, returns the new child agent.
    On failure, returns None.
    """
    if cfg_obj is None:
        cfg_obj = cfg

    prob = cfg_obj.REPRODUCTION.get("REPRODUCTION_PROBABILITY", 0.7)

    if random.random() > prob:
        return None  # Reproduction attempt failed

    # Success: create child
    child = make_child(parent_a, parent_b)

    # Apply cooldown to both parents
    cooldown = cfg_obj.REPRODUCTION.get("REPRO_COOLDOWN", 15.0)
    parent_a.repro_cooldown = cooldown
    parent_b.repro_cooldown = cooldown

    # Start reproduction animation (show love icon above them)
    animation_duration = cfg_obj.REPRODUCTION.get(
        "REPRO_ANIMATION_DURATION", 1.0)
    parent_a.repro_animation_timer = animation_duration
    parent_b.repro_animation_timer = animation_duration

    # Freeze parents during animation
    parent_a.velocityX = 0.0
    parent_a.velocityY = 0.0
    parent_b.velocityX = 0.0
    parent_b.velocityY = 0.0

    # Optional energy cost to parents
    energy_cost = cfg_obj.REPRODUCTION.get("REPRO_ENERGY_COST", 20.0)
    parent_a.energy = max(0.0, parent_a.energy - energy_cost)
    parent_b.energy = max(0.0, parent_b.energy - energy_cost)

    return child


def make_child(parent_a: ag.Agent, parent_b: ag.Agent) -> ag.Agent:
    """
    Create offspring inheriting averaged traits and color from both parents.
    No mutation yet.
    """
    # Get parent traits (with defaults if missing)
    traits_a = getattr(parent_a, "traits", None) or tr.Traits()
    traits_b = getattr(parent_b, "traits", None) or tr.Traits()

    # Average trait multipliers
    child_vision_mult = (traits_a.vision_mult + traits_b.vision_mult) / 2.0
    child_speed_mult = (traits_a.speed_mult + traits_b.speed_mult) / 2.0
    child_metabolism_mult = (traits_a.metabolism_mult +
                             traits_b.metabolism_mult) / 2.0
    child_memory_mult = (traits_a.memory_mult + traits_b.memory_mult) / 2.0

    # Clamp to valid ranges
    child_traits = tr.Traits(
        vision_mult=tr.clamp_trait(child_vision_mult, tr.VISION_MULT_RANGE),
        speed_mult=tr.clamp_trait(child_speed_mult, tr.SPEED_MULT_RANGE),
        metabolism_mult=tr.clamp_trait(
            child_metabolism_mult, tr.METABOLISM_MULT_RANGE),
        memory_mult=tr.clamp_trait(child_memory_mult, tr.MEMORY_MULT_RANGE)
    )

    # Average colors (RGB channels)
    color_a = parent_a.colour
    color_b = parent_b.colour

    child_r = int((color_a[0] + color_b[0]) / 2.0)
    child_g = int((color_a[1] + color_b[1]) / 2.0)
    child_b = int((color_a[2] + color_b[2]) / 2.0)

    child_colour = (
        max(0, min(255, child_r)),
        max(0, min(255, child_g)),
        max(0, min(255, child_b))
    )

    # Spawn near midpoint of parents with small random offset
    spawn_x = (parent_a.x + parent_b.x) / 2.0
    spawn_y = (parent_a.y + parent_b.y) / 2.0

    offset_range = cfg.REPRODUCTION.get("SPAWN_OFFSET_RANGE", 30.0)
    spawn_x += random.uniform(-offset_range, offset_range)
    spawn_y += random.uniform(-offset_range, offset_range)

    # Clamp to screen bounds
    spawn_x = max(cfg.AGENT_RADIUS, min(cfg.WIDTH - cfg.AGENT_RADIUS, spawn_x))
    spawn_y = max(cfg.AGENT_RADIUS, min(
        cfg.HEIGHT - cfg.AGENT_RADIUS, spawn_y))

    # Create agent dataclass instance directly
    next_id = max((a.id for a in [parent_a, parent_b]), default=0) + 1

    # Get parent generation and increment
    parent_gen = max(
        getattr(parent_a, "generation", 1),
        getattr(parent_b, "generation", 1)
    )
    child_gen = parent_gen + 1

    child = ag.Agent(
        id=next_id,
        x=spawn_x,
        y=spawn_y,
        velocityX=random.choice([-1.0, -0.5, 0.5, 1.0]),
        velocityY=random.choice([-1.0, -0.5, 0.5, 1.0]),
        colour=child_colour,
        traits=child_traits,
        food_memory=[],
        action="WANDER",
        generation=child_gen
    )

    return child
