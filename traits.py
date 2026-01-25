"""
Traits system for agents.
Traits are multipliers applied on top of base config values.
Effective value = base_config_value * trait_multiplier
"""
from dataclasses import dataclass
import random
import math


@dataclass
class Traits:
    """Per-agent trait multipliers."""
    vision_mult: float = 1.0      # 0.7–1.4
    speed_mult: float = 1.0       # 0.7–1.4
    metabolism_mult: float = 1.0  # 0.7–1.3 (lower = slower drain)
    memory_mult: float = 1.0      # 0.7–1.5


def random_traits(rng=None) -> Traits:
    """
    Generate randomized first-generation traits.
    First-gen traits are conservative and imperfect so many agents fail.
    """
    if rng is None:
        rng = random

    return Traits(
        vision_mult=rng.uniform(0.7, 1.4),
        speed_mult=rng.uniform(0.7, 1.4),
        metabolism_mult=rng.uniform(0.7, 1.3),
        memory_mult=rng.uniform(0.7, 1.5)
    )


def clamp_traits(traits: Traits) -> Traits:
    """Clamp trait multipliers to reasonable bounds."""
    return Traits(
        vision_mult=max(0.5, min(2.0, traits.vision_mult)),
        speed_mult=max(0.5, min(2.0, traits.speed_mult)),
        metabolism_mult=max(0.5, min(2.0, traits.metabolism_mult)),
        memory_mult=max(0.5, min(2.0, traits.memory_mult))
    )


# =========================================================
# Effective Value Helpers
# =========================================================

def effective_vision(base_vision: float, traits: Traits) -> float:
    """Compute effective vision radius with trait multiplier."""
    return base_vision * traits.vision_mult


def effective_max_speed(base_speed: float, traits: Traits) -> float:
    """Compute effective max speed with trait multiplier."""
    return base_speed * traits.speed_mult


def effective_drain(base_rate: float, traits: Traits) -> float:
    """
    Compute effective drain rate with metabolism trait multiplier.
    Lower metabolism_mult = slower drain (better).
    """
    return base_rate * traits.metabolism_mult


def effective_memory_ttl(base_ttl_seconds: float, traits: Traits) -> float:
    """
    Compute effective memory time-to-live with trait multiplier.
    Higher memory_mult = longer memory retention.
    """
    return base_ttl_seconds * traits.memory_mult
