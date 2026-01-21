# resources.py
import random
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

import pygame
import config as cfg


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _rand_point(margin: int) -> Tuple[float, float]:
    x = random.uniform(margin, cfg.WIDTH - margin)
    y = random.uniform(margin, cfg.HEIGHT - margin)
    return x, y


@dataclass
class FoodItem:
    x: float
    y: float


@dataclass
class FoodBush:
    x: float
    y: float
    capacity: int
    food: List[FoodItem] = field(default_factory=list)
    regen_timer: float = 0.0

    # for drawing a blob behind it
    blob_circles: List[Tuple[float, float, float]
                       ] = field(default_factory=list)

    def spawn_initial_food(self) -> None:
        safety = 200  # prevent infinite loops
        while len(self.food) < self.capacity and safety > 0:
            item = self._new_food_item()
            if item is not None:
                self.food.append(item)
            safety -= 1

    def _new_food_item(self) -> Optional[FoodItem]:

        food_r = cfg.RESOURCES["FOOD_RADIUS"]
        rim = cfg.RESOURCES["FOOD_RIM_THICKNESS"]
        edge_margin = cfg.RESOURCES["FOOD_EDGE_MARGIN"]
        attempts = cfg.RESOURCES["FOOD_SPAWN_ATTEMPTS"]

        circles_sorted = sorted(
            self.blob_circles, key=lambda c: c[2], reverse=True)
        top = circles_sorted[:2] if len(
            circles_sorted) >= 2 else circles_sorted

        # Start with normal spacing, then relax if needed
        base_gap = cfg.RESOURCES["FOOD_MIN_GAP"]
        gap = base_gap

        for phase in range(3):
            min_dist = (food_r * 2) + gap
            min_dist_sq = min_dist * min_dist

            for _ in range(attempts):
                cx, cy, r = random.choice(top)
                usable_r = max(0.0, r - edge_margin - food_r - rim - 2)

                angle = random.uniform(0, 2 * math.pi)
                radius = usable_r * (random.random() ** 0.5)
                fx = cx + math.cos(angle) * radius
                fy = cy + math.sin(angle) * radius

                fx = _clamp(fx, 10, cfg.WIDTH - 10)
                fy = _clamp(fy, 10, cfg.HEIGHT - 10)

                ok = True
                for f in self.food:
                    dx = fx - f.x
                    dy = fy - f.y
                    if (dx * dx + dy * dy) < min_dist_sq:
                        ok = False
                        break

                if ok:
                    return FoodItem(x=fx, y=fy)

            # relax gap a bit and try again
            gap = max(0, gap - 2)

        # too crowded: don't spawn a new one
        return None

    def update_regen(self, dt: float) -> None:
        # regen scaffolding for later (won't change anything until food gets eaten)
        if len(self.food) >= self.capacity:
            self.regen_timer = 0.0
            return

        self.regen_timer += dt
        if self.regen_timer >= cfg.RESOURCES["FOOD_REGEN_SECONDS"]:
            self.regen_timer = 0.0
            item = self._new_food_item()
            if item is not None:
                self.food.append(item)


@dataclass
class Pond:
    circles: List[Tuple[float, float, float]]
    sparkles: List[Tuple[float, float, int]]


def create_pond() -> Pond:
    margin = cfg.RESOURCES["POND_MARGIN"]
    cx, cy = _rand_point(margin)

    circles: List[Tuple[float, float, float]] = []
    for _ in range(cfg.RESOURCES["POND_CIRCLES"]):
        r = random.uniform(
            cfg.RESOURCES["POND_RADIUS_MIN"], cfg.RESOURCES["POND_RADIUS_MAX"])
        ox = random.uniform(-60, 60)
        oy = random.uniform(-50, 50)
        circles.append((cx + ox, cy + oy, r))

    # --- sparkles: random points inside random pond circles ---
    sparkles: List[Tuple[float, float, int]] = []
    import math
    for _ in range(cfg.RESOURCES["POND_SPARKLES"]):
        scx, scy, sr = random.choice(circles)
        angle = random.uniform(0, 2 * math.pi)
        radius = sr * (random.random() ** 0.5)
        sx = scx + math.cos(angle) * radius
        sy = scy + math.sin(angle) * radius
        srad = random.randint(
            cfg.RESOURCES["POND_SPARKLE_R_MIN"], cfg.RESOURCES["POND_SPARKLE_R_MAX"])
        sparkles.append((sx, sy, srad))

    return Pond(circles=circles, sparkles=sparkles)


def pond_bounds(pond: Pond) -> Tuple[float, float, float]:
    """
    Returns (cx, cy, r_max) so we can keep bushes away from pond.
    """
    cx = sum(c[0] for c in pond.circles) / len(pond.circles)
    cy = sum(c[1] for c in pond.circles) / len(pond.circles)
    r_max = max(c[2] for c in pond.circles)
    return cx, cy, r_max


def create_bushes(pond: Pond) -> List[FoodBush]:
    bushes: List[FoodBush] = []

    min_dist = cfg.RESOURCES["BUSH_MIN_DIST"]
    min_dist_sq = min_dist * min_dist
    attempts = cfg.RESOURCES["BUSH_SPAWN_ATTEMPTS"]

    pcx, pcy, pr = pond_bounds(pond)
    pond_safe = pr + cfg.RESOURCES["POND_BUSH_BUFFER"]
    pond_safe_sq = pond_safe * pond_safe

    def valid_spot(x: float, y: float) -> bool:
        # keep away from pond
        dxp = x - pcx
        dyp = y - pcy
        if (dxp * dxp + dyp * dyp) < pond_safe_sq:
            return False

        # spacing check vs existing bushes
        for b in bushes:
            dx = x - b.x
            dy = y - b.y
            if (dx * dx + dy * dy) < min_dist_sq:
                return False

        return True

    for _ in range(cfg.RESOURCES["NUM_BUSHES"]):
        placed = False

        # main placement attempts
        for _try in range(attempts):
            bx, by = _rand_point(margin=80)
            if not valid_spot(bx, by):
                continue

            cap = random.randint(
                cfg.RESOURCES["FOOD_PER_BUSH_MIN"],
                cfg.RESOURCES["FOOD_PER_BUSH_MAX"]
            )
            bush = FoodBush(x=bx, y=by, capacity=cap)

            # bush blob circles (for visuals)
            for _ in range(cfg.RESOURCES["BUSH_BLOB_CIRCLES"]):
                r = random.uniform(
                    cfg.RESOURCES["BUSH_BLOB_RADIUS_MIN"],
                    cfg.RESOURCES["BUSH_BLOB_RADIUS_MAX"]
                )
                ox = random.uniform(-18, 18)
                oy = random.uniform(-18, 18)
                bush.blob_circles.append((bx + ox, by + oy, r))

            bush.spawn_initial_food()
            bushes.append(bush)
            placed = True
            break

        # fallback placement (still tries to respect constraints)
        if not placed:
            for _try in range(20):
                bx, by = _rand_point(margin=80)
                if not valid_spot(bx, by):
                    continue

                cap = random.randint(
                    cfg.RESOURCES["FOOD_PER_BUSH_MIN"],
                    cfg.RESOURCES["FOOD_PER_BUSH_MAX"]
                )
                bush = FoodBush(x=bx, y=by, capacity=cap)

                for _ in range(cfg.RESOURCES["BUSH_BLOB_CIRCLES"]):
                    r = random.uniform(
                        cfg.RESOURCES["BUSH_BLOB_RADIUS_MIN"],
                        cfg.RESOURCES["BUSH_BLOB_RADIUS_MAX"]
                    )
                    ox = random.uniform(-18, 18)
                    oy = random.uniform(-18, 18)
                    bush.blob_circles.append((bx + ox, by + oy, r))

                bush.spawn_initial_food()
                bushes.append(bush)
                placed = True
                break

        # last resort: place anywhere (rare, but prevents “missing bushes”)
        if not placed:
            bx, by = _rand_point(margin=80)

            cap = random.randint(
                cfg.RESOURCES["FOOD_PER_BUSH_MIN"],
                cfg.RESOURCES["FOOD_PER_BUSH_MAX"]
            )
            bush = FoodBush(x=bx, y=by, capacity=cap)

            for _ in range(cfg.RESOURCES["BUSH_BLOB_CIRCLES"]):
                r = random.uniform(
                    cfg.RESOURCES["BUSH_BLOB_RADIUS_MIN"],
                    cfg.RESOURCES["BUSH_BLOB_RADIUS_MAX"]
                )
                ox = random.uniform(-18, 18)
                oy = random.uniform(-18, 18)
                bush.blob_circles.append((bx + ox, by + oy, r))

            bush.spawn_initial_food()
            bushes.append(bush)

    return bushes


def update_resources(bushes: List[FoodBush], dt: float) -> None:
    for b in bushes:
        b.update_regen(dt)


def draw_resources(screen: pygame.Surface, pond: Pond, bushes: List[FoodBush]) -> None:
    # --- POND: draw rim first (bigger circles), then water fill ---
    RIM_THICKNESS = 10
    for (x, y, r) in pond.circles:
        pygame.draw.circle(
            screen,
            cfg.COLOURS["WATER_RIM"],
            (int(x), int(y)),
            int(r + RIM_THICKNESS)
        )

    for (x, y, r) in pond.circles:
        pygame.draw.circle(
            screen,
            cfg.COLOURS["WATER"],
            (int(x), int(y)),
            int(r)
        )

    # sparkles (after pond fill so they sit on top)
    for (sx, sy, sr) in pond.sparkles:
        pygame.draw.circle(
            screen, cfg.COLOURS["WATER_SPARKLE"], (int(sx), int(sy)), sr)

    # --- BUSHES: draw outline first, then fill ---
    BUSH_OUTLINE_THICKNESS = 4
    for b in bushes:
        # outline
        for (x, y, r) in b.blob_circles:
            pygame.draw.circle(
                screen,
                cfg.COLOURS["BUSH_OUTLINE"],
                (int(x), int(y)),
                int(r + BUSH_OUTLINE_THICKNESS)
            )
        # fill
        for (x, y, r) in b.blob_circles:
            pygame.draw.circle(
                screen,
                cfg.COLOURS["BUSH"],
                (int(x), int(y)),
                int(r)
            )

    fr = cfg.RESOURCES["FOOD_RADIUS"]
    rim = cfg.RESOURCES["FOOD_RIM_THICKNESS"]

    for b in bushes:
        for f in b.food:
            pygame.draw.circle(
                screen, cfg.COLOURS["FOOD_RIM"], (int(f.x), int(f.y)), fr + rim)
            pygame.draw.circle(
                screen, cfg.COLOURS["FOOD"], (int(f.x), int(f.y)), fr)

# --------------------------
# COLLISION HELPERS (solid)
# --------------------------


def _closest_collision_circle(x: float, y: float, radius: float, circles):
    best = None
    best_overlap = 0.0
    for (cx, cy, cr) in circles:
        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)
        overlap = (radius + cr) - dist
        if overlap > best_overlap:
            best_overlap = overlap
            best = (cx, cy, cr, dist, overlap)
    return best


def collide_with_pond(x: float, y: float, agent_r: float, pond: Pond):
    return _closest_collision_circle(x, y, agent_r, pond.circles)


def collide_with_bush(x: float, y: float, agent_r: float, bush: FoodBush):
    return _closest_collision_circle(x, y, agent_r, bush.blob_circles)


def bounce_off_circle(nx: float, ny: float, vx: float, vy: float,
                      cx: float, cy: float, cr: float, dist: float, overlap: float):
    if dist == 0:
        nxn, nyn = 1.0, 0.0
    else:
        nxn = (nx - cx) / dist
        nyn = (ny - cy) / dist

    push = overlap + 1.0
    nx += nxn * push
    ny += nyn * push

    dot = vx * nxn + vy * nyn
    rvx = vx - 2 * dot * nxn
    rvy = vy - 2 * dot * nyn

    return nx, ny, rvx, rvy


def pick_food_from_bush(bush: FoodBush) -> bool:
    if not bush.food:
        return False
    idx = random.randrange(len(bush.food))
    bush.food.pop(idx)
    return True


def touch_circle(x: float, y: float, agent_r: float, circles, eps: float = 2.0):
    """
    Returns (cx, cy, cr, dist) if agent is within contact distance of any circle,
    else None.
    Contact distance: dist <= agent_r + cr + eps
    """
    best = None
    best_dist = float("inf")
    for (cx, cy, cr) in circles:
        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)
        if dist <= (agent_r + cr + eps):
            if dist < best_dist:
                best_dist = dist
                best = (cx, cy, cr, dist)
    return best


def touch_pond(x: float, y: float, agent_r: float, pond: Pond, eps: float = 2.0):
    return touch_circle(x, y, agent_r, pond.circles, eps)


def touch_bush(x: float, y: float, agent_r: float, bush: FoodBush, eps: float = 2.0):
    return touch_circle(x, y, agent_r, bush.blob_circles, eps)
