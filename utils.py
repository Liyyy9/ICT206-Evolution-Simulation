# utils.py
from typing import Tuple

Colour = Tuple[int, int, int]


def clamp01(t: float) -> float:
    """
    Clamp a value between 0.0 and 1.0
    """
    return max(0.0, min(1.0, t))


def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation between a and b
    """
    return a + (b - a) * t


def lerp_colour(c1: Colour, c2: Colour, t: float) -> Colour:
    """
    Interpolate smoothly between two RGB colours
    """
    t = clamp01(t)
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


def severity(value: float, start: float, span: float) -> float:
    """
    Convert a stat value into a 0–1 severity factor.

    value  <= start           -> 0.0
    value  >= start + span    -> 1.0
    """
    return clamp01((value - start) / span)

def step_toward_zero(v: int, step: int = 1) -> int:
    if v > 0:
        return max(0, v - step)
    if v < 0:
        return min(0, v + step)
    return 0