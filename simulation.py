import math
import random
import pygame

import config as cfg
import resources as res
import agent as ag

# ---------------------------------------------------------
# Stability / feel tuning
# ---------------------------------------------------------
INTERACT_COOLDOWN = 0.8     # seconds after eat/drink before interacting again
MAX_SPEED = 3.5             # clamp velocity so it can't explode
BOUNCE_DAMP = 0.92          # damp bounce so energy doesn't grow


def _is_memory_expired(timestamp_ms: int) -> bool:
    """Check if a memory entry is older than MEMORY_TIMEOUT."""
    if timestamp_ms < 0:
        return True
    current_time_ms = pygame.time.get_ticks()
    timeout_ms = cfg.MEMORY["TIMEOUT"] * 1000
    return (current_time_ms - timestamp_ms) > timeout_ms


def _clean_food_memory(a: ag.Agent) -> None:
    """Remove expired food memories."""
    if not hasattr(a, "food_memory") or not a.food_memory:
        return
    a.food_memory = [
        (x, y, ts) for x, y, ts in a.food_memory
        if not _is_memory_expired(ts)
    ]


def _clean_water_memory(a: ag.Agent) -> None:
    """Clear water memory if expired."""
    if not hasattr(a, "last_water_time_ms"):
        return
    if _is_memory_expired(a.last_water_time_ms):
        a.last_water_pos = None
        a.last_water_time_ms = -1


def update_agent(a: ag.Agent, dt: float, pond: res.Pond, bushes: list[res.FoodBush]) -> bool:
    """
    Update one agent for one frame.
    Returns True if agent remains alive, False if dead (caller removes it).
    """
    ag.update_internal_state(a, dt)
    if not a.alive:
        return False

    _safe_pos(a)
    _clamp_speed(a)

    # timers
    if getattr(a, "interact_cooldown", 0.0) > 0.0:
        a.interact_cooldown = max(0.0, a.interact_cooldown - dt)

    if getattr(a, "eat_pause", 0.0) > 0.0:
        a.eat_pause = max(0.0, a.eat_pause - dt)
        return True

    # ---------------------------------------------------------
    # DRINK STATE: freeze position, sip over time until THIRST_OK
    # ---------------------------------------------------------
    if getattr(a, "action", "WANDER") == "DRINK":
        touching = res.touch_pond(a.x, a.y, cfg.AGENT_RADIUS, pond, eps=6.0)

        # Release condition (prevents camping)
        if touching is None or a.thirst <= cfg.THRESHOLDS["THIRST_OK"]:
            a.action = "WANDER"
            a.drink_timer = 0.0
            a.interact_cooldown = INTERACT_COOLDOWN
            a.has_drunk = True

            # If first successful eat+drink cycle, set home location
            if a.has_eaten and a.home_pos is None and a.last_water_pos:
                home_x = (a.last_water_pos[0] + a.x) / 2.0
                home_y = (a.last_water_pos[1] + a.y) / 2.0
                a.home_pos = (home_x, home_y)

            _nudge_velocity(a)
            _clamp_speed(a)

            # pick a new waypoint away from resources so they move off nicely
            a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
            a.waypoint_timer = random.uniform(
                0.0, cfg.SENSING["WAYPOINT_TIMEOUT"])
            return True

        a.drink_timer += dt
        while a.drink_timer >= cfg.RESOURCES["DRINK_INTERVAL"]:
            a.drink_timer -= cfg.RESOURCES["DRINK_INTERVAL"]
            a.thirst = max(0.0, a.thirst - cfg.RESOURCES["DRINK_AMOUNT"])

            # optional simplified energy boost
            if "ENERGY_FROM_DRINK" in cfg.RESOURCES:
                a.energy = min(100.0, a.energy +
                               cfg.RESOURCES["ENERGY_FROM_DRINK"])

        return True  # frozen while drinking

    # ---------------------------------------------------------
    # SENSING + STEERING
    # ---------------------------------------------------------
    target = _choose_target(a, pond, bushes)

    if target is None:
        _wander_steer(a, dt, pond, bushes)
    else:
        tx, ty = target
        _steer_towards(a, tx, ty)

    _clamp_speed(a)

    # ---------------------------------------------------------
    # PROPOSED MOVE
    # ---------------------------------------------------------
    move_scale = 60.0 * dt
    mult = ag.movement_multiplier(a)

    vx, vy = a.velocityX, a.velocityY
    nx = a.x + vx * mult * move_scale
    ny = a.y + vy * mult * move_scale

    # ---------------------------------------------------------
    # WATER MEMORY: Log pond location on any contact
    # ---------------------------------------------------------
    if res.touch_pond(nx, ny, cfg.AGENT_RADIUS, pond, eps=6.0) is not None:
        px, py = _pond_center(pond)
        a.last_water_pos = (px, py)
        a.last_water_time_ms = pygame.time.get_ticks()

    # ---------------------------------------------------------
    # START DRINK if thirsty + touching pond rim
    # ---------------------------------------------------------
    if (
        a.interact_cooldown <= 0.0
        and a.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]
        and res.touch_pond(nx, ny, cfg.AGENT_RADIUS, pond, eps=6.0) is not None
    ):
        a.action = "DRINK"
        a.drink_timer = 0.0
        return True  # freeze this frame

    # ---------------------------------------------------------
    # BUSH INTERACTION
    # ---------------------------------------------------------
    for b in bushes:
        touching = res.touch_bush(nx, ny, cfg.AGENT_RADIUS, b, eps=4.0)
        if touching is None:
            continue

        # LOG BUSH IN MEMORY (discovery or update)
        if touching is not None:
            if not hasattr(a, "food_memory") or a.food_memory is None:
                a.food_memory = []
            bush_pos = (b.x, b.y)
            already_remembered = any(
                abs(mem[0] - bush_pos[0]) < 5 and abs(mem[1] - bush_pos[1]) < 5
                for mem in a.food_memory
            )
            if not already_remembered:
                a.food_memory.append((b.x, b.y, pygame.time.get_ticks()))

        # TRY EAT: only if hungry, cooldown ready, and food exists
        if a.interact_cooldown <= 0.0 and a.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"] and len(b.food) > 0:
            ate = res.pick_food_from_bush(b)
            if ate:
                a.hunger = max(0.0, a.hunger - cfg.RESOURCES["EAT_AMOUNT"])
                if "ENERGY_FROM_EAT" in cfg.RESOURCES:
                    a.energy = min(100.0, a.energy +
                                   cfg.RESOURCES["ENERGY_FROM_EAT"])
                a.eat_pause = cfg.RESOURCES["EAT_PAUSE"]
                a.interact_cooldown = INTERACT_COOLDOWN
                a.has_eaten = True

                # If first successful eat+drink cycle, set home location
                if a.has_drunk and a.home_pos is None and a.last_water_pos is not None:
                    home_x = (b.x + a.last_water_pos[0]) / 2.0
                    home_y = (b.y + a.last_water_pos[1]) / 2.0
                    a.home_pos = (home_x, home_y)

                _nudge_velocity(a)
                _clamp_speed(a)
                return True

        # ALWAYS BOUNCE (prevent camping)
        # NOTE: set cooldown and force waypoint to prevent re-engagement with empty bushes
        hit = res.collide_with_bush(nx, ny, cfg.AGENT_RADIUS, b)
        if hit is not None:
            _apply_bounce(a, hit)

            # If bush is empty: force them away with a longer cooldown
            if len(b.food) == 0:
                # Long cooldown to force them to wander away
                a.interact_cooldown = max(a.interact_cooldown, 2.0)
                a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
                a.waypoint_timer = 0.0
            elif a.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"] and len(b.food) == 0:
                # Tried to eat but no food - set cooldown to avoid spam
                a.interact_cooldown = max(
                    a.interact_cooldown, INTERACT_COOLDOWN)
                a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
                a.waypoint_timer = 0.0
            else:
                # Bush has food - short cooldown for natural spacing
                a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
                a.waypoint_timer = 0.0

            return True

    # ---------------------------------------------------------
    # SOLID POND COLLISION (when not drinking)
    # ---------------------------------------------------------
    if a.action != "DRINK":
        # NOT THIRSTY: bounce away immediately
        if a.thirst < cfg.THRESHOLDS["THIRST_SEEK"]:
            hit = res.collide_with_pond(nx, ny, cfg.AGENT_RADIUS, pond)
            if hit is not None:
                _apply_bounce(a, hit)
                if a.action == "WANDER":
                    a.waypoint = _random_waypoint_avoiding_resources(
                        pond, bushes)
                    a.waypoint_timer = 0.0
                return True

        # Otherwise handle normal collision
        hit = res.collide_with_pond(nx, ny, cfg.AGENT_RADIUS, pond)
        if hit is not None:
            _apply_bounce(a, hit)

            if a.action == "WANDER":
                a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
                a.waypoint_timer = 0.0
            return True

    # ---------------------------------------------------------
    # SCREEN BOUNDS
    # ---------------------------------------------------------
    if nx < cfg.AGENT_RADIUS:
        nx = cfg.AGENT_RADIUS
        a.velocityX *= -1
    elif nx > cfg.WIDTH - cfg.AGENT_RADIUS:
        nx = cfg.WIDTH - cfg.AGENT_RADIUS
        a.velocityX *= -1

    if ny < cfg.AGENT_RADIUS:
        ny = cfg.AGENT_RADIUS
        a.velocityY *= -1
    elif ny > cfg.HEIGHT - cfg.AGENT_RADIUS:
        ny = cfg.HEIGHT - cfg.AGENT_RADIUS
        a.velocityY *= -1

    a.x, a.y = nx, ny

    _safe_pos(a)
    _clamp_speed(a)
    return True


# =========================================================
# SENSING: pick target (thirst > hunger)
# =========================================================

def _choose_target(a: ag.Agent, pond: res.Pond, bushes: list[res.FoodBush]):
    vision = getattr(a, "vision_radius", cfg.SENSING["VISION_RADIUS"])

    # Check what's available in vision
    pond_visible = False
    pcx, pcy = _pond_center(pond)
    if _dist(a.x, a.y, pcx, pcy) <= vision:
        pond_visible = True

    food_visible = None
    if bushes:
        food_visible = _nearest_food_in_vision(a, bushes, vision)

    # Clean expired memories before using them
    _clean_food_memory(a)
    _clean_water_memory(a)

    # Check discovery status
    has_food_memory = len(getattr(a, "food_memory", [])) > 0
    has_water_memory = getattr(a, "last_water_pos", None) is not None

    # ===== DISCOVERY PHASE =====
    # Must find BOTH resources before normal behavior
    if not has_water_memory:
        # Haven't found water yet - go to pond
        if pond_visible:
            return (pcx, pcy)
        # Otherwise wander

    if not has_food_memory:
        # Haven't found food yet - go to any visible bush
        if bushes:
            # Target nearest bush (even if empty, just to discover)
            nearest_bush = min(bushes, key=lambda b: _dist(a.x, a.y, b.x, b.y))
            return (nearest_bush.x, nearest_bush.y)
        # Otherwise wander

    # ===== NORMAL PHASE (both resources discovered) =====
    thirsty = a.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]
    hungry = a.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]

    # If home region established and not urgent, prefer wandering near home
    if a.home_pos is not None and not thirsty and not hungry:
        # Comfortable state - stay near home region
        dist_to_home = _dist(a.x, a.y, a.home_pos[0], a.home_pos[1])
        if dist_to_home > a.home_region_radius:
            # Outside home region - generate waypoint within home region
            return _random_waypoint_in_home_region(a.home_pos[0], a.home_pos[1],
                                                   a.home_region_radius, pond, bushes)
        else:
            # Inside home region - wander normally (return None lets normal wandering happen)
            return None

    # PRIORITY: If extremely thirsty, ALWAYS go to water (don't camp at bushes)
    if a.thirst > 80:  # Critical thirst
        if pond_visible:
            return (pcx, pcy)
        elif a.last_water_pos:
            return a.last_water_pos

    # If both needs active: prioritize by urgency
    if thirsty and hungry:
        if a.thirst >= a.hunger:
            if pond_visible:
                return (pcx, pcy)
            elif food_visible is not None:
                return food_visible
        else:
            if food_visible is not None:
                return food_visible
            elif pond_visible:
                return (pcx, pcy)

    # Only thirsty
    elif thirsty:
        if pond_visible:
            return (pcx, pcy)
        # Use memory
        if a.last_water_pos:
            return a.last_water_pos

    # Only hungry
    elif hungry:
        if food_visible is not None:
            return food_visible
        # Use memory: prioritize bush nearest to water, but only target bushes with food
        food_memory = getattr(a, "food_memory", [])
        if food_memory and a.last_water_pos:
            water_x, water_y = a.last_water_pos
            # Sort by distance to water, then pick best one with food
            sorted_bushes = sorted(food_memory,
                                   key=lambda pos: _dist(pos[0], pos[1], water_x, water_y))
            # Find first bush that has food
            for bx, by, _ in sorted_bushes:
                # Check if any bush at this location has food
                for b in bushes:
                    if abs(b.x - bx) < 15 and abs(b.y - by) < 15 and len(b.food) > 0:
                        return (bx, by)
            # If no bush in memory has food, just wander
            return None
        elif food_memory:
            # No water memory but have food memory - target nearest with food
            for bx, by, _ in food_memory:
                for b in bushes:
                    if abs(b.x - bx) < 15 and abs(b.y - by) < 15 and len(b.food) > 0:
                        return (bx, by)
            return None

    return None


def _pond_center(pond: res.Pond):
    circles = pond.circles  # list of (x,y,r)
    sx = 0.0
    sy = 0.0
    n = len(circles)
    for (x, y, _r) in circles:
        sx += x
        sy += y
    return (sx / max(1, n), sy / max(1, n))


def _nearest_food_in_vision(a: ag.Agent, bushes: list[res.FoodBush], vision: float):
    best = None
    best_d2 = None
    v2 = vision * vision

    for b in bushes:
        for f in getattr(b, "food", []):
            dx = f.x - a.x
            dy = f.y - a.y
            d2 = dx * dx + dy * dy
            if d2 <= v2:
                if best is None or d2 < best_d2:
                    best = (f.x, f.y)
                    best_d2 = d2

    return best


# =========================================================
# STEERING
# =========================================================

def _steer_towards(a: ag.Agent, tx: float, ty: float):
    steer = getattr(a, "steer_strength", cfg.SENSING["STEER_STRENGTH"])

    dx = tx - a.x
    dy = ty - a.y
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return

    ux = dx / d
    uy = dy / d

    # blend toward desired direction
    a.velocityX = (1 - steer) * a.velocityX + steer * ux
    a.velocityY = (1 - steer) * a.velocityY + steer * uy


# =========================================================
# WAYPOINT WANDERING (Option B)
# =========================================================

def _wander_steer(a: ag.Agent, dt: float, pond: res.Pond, bushes: list[res.FoodBush]):
    # init if missing or invalid
    if getattr(a, "waypoint", None) is None:
        a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
        a.waypoint_timer = random.uniform(0.0, cfg.SENSING["WAYPOINT_TIMEOUT"])

    a.waypoint_timer += dt

    wx, wy = a.waypoint
    reached_dist = cfg.SENSING["WAYPOINT_REACHED"]
    dist_to_wp = _dist(a.x, a.y, wx, wy)

    timeout = cfg.SENSING["WAYPOINT_TIMEOUT"] * random.uniform(0.85, 1.25)
    if dist_to_wp <= reached_dist or a.waypoint_timer >= timeout:
        a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
        a.waypoint_timer = 0.0
        wx, wy = a.waypoint

    _steer_towards(a, wx, wy)

    # tiny noise so wandering isn't robotic / synchronized
    j = cfg.SENSING["WANDER_JITTER"]
    a.velocityX += random.uniform(-j, j) * 0.05
    a.velocityY += random.uniform(-j, j) * 0.05


def _random_waypoint_in_home_region(home_x: float, home_y: float,
                                    region_radius: float,
                                    pond: res.Pond, bushes: list[res.FoodBush]):
    """Generate a random waypoint within the home region."""
    avoid_pad = 60.0

    for _ in range(100):
        # Random point within home region
        angle = random.uniform(0, 6.28318)
        distance = random.uniform(0, region_radius)
        x = home_x + math.cos(angle) * distance
        y = home_y + math.sin(angle) * distance

        # Clamp to screen bounds
        m = cfg.SENSING["WAYPOINT_MARGIN"]
        x = max(m, min(cfg.WIDTH - m, x))
        y = max(m, min(cfg.HEIGHT - m, y))

        # avoid pond blobs
        bad = False
        for (cx, cy, cr) in pond.circles:
            if _dist(x, y, cx, cy) < (cr + avoid_pad):
                bad = True
                break
        if bad:
            continue

        # avoid bush blobs
        for b in bushes:
            for (cx, cy, cr) in b.blob_circles:
                if _dist(x, y, cx, cy) < (cr + avoid_pad):
                    bad = True
                    break
            if bad:
                break

        if not bad:
            return (x, y)

    # Fallback: just return home center if can't find valid waypoint
    return (home_x, home_y)


def _random_waypoint_avoiding_resources(pond: res.Pond, bushes: list[res.FoodBush]):
    m = cfg.SENSING["WAYPOINT_MARGIN"]
    avoid_pad = 60.0  # how far away from pond/bush blobs the waypoint must be

    for _ in range(160):
        x = random.uniform(m, cfg.WIDTH - m)
        y = random.uniform(m, cfg.HEIGHT - m)

        # avoid pond blobs
        bad = False
        for (cx, cy, cr) in pond.circles:
            if _dist(x, y, cx, cy) < (cr + avoid_pad):
                bad = True
                break
        if bad:
            continue

        # avoid bush blobs
        for b in bushes:
            for (cx, cy, cr) in b.blob_circles:
                if _dist(x, y, cx, cy) < (cr + avoid_pad):
                    bad = True
                    break
            if bad:
                break
        if bad:
            continue

        return (x, y)

    # fallback
    return (random.uniform(m, cfg.WIDTH - m), random.uniform(m, cfg.HEIGHT - m))


# =========================================================
# STABILITY HELPERS
# =========================================================

def _apply_bounce(a: ag.Agent, hit_tuple) -> None:
    cx, cy, cr, dist, overlap = hit_tuple
    a.x, a.y, a.velocityX, a.velocityY = res.bounce_off_circle(
        a.x, a.y, a.velocityX, a.velocityY, cx, cy, cr, dist, overlap
    )
    a.velocityX *= BOUNCE_DAMP
    a.velocityY *= BOUNCE_DAMP

    # Apply opposite vector to push away from collision center
    if dist > 1e-2:
        # Calculate unit vector pointing away from collision center
        away_x = (a.x - cx) / dist
        away_y = (a.y - cy) / dist
        # Push velocity in the away direction with stronger force
        push_strength = 6.0  # Increased from 3.0
        a.velocityX += away_x * push_strength
        a.velocityY += away_y * push_strength
    else:
        # Agent is at collision center - pick random direction away
        angle = random.uniform(0, 6.28318)
        a.velocityX = math.cos(angle) * 6.0
        a.velocityY = math.sin(angle) * 6.0

    _clamp_speed(a)
    _safe_pos(a)


def _nudge_velocity(a: ag.Agent) -> None:
    a.velocityX += random.choice([-1, 1]) * 0.6
    a.velocityY += random.choice([-1, 1]) * 0.6


def _clamp_speed(a: ag.Agent) -> None:
    vx, vy = a.velocityX, a.velocityY
    if not (math.isfinite(vx) and math.isfinite(vy)):
        a.velocityX = random.choice([-1.2, -1.0, 1.0, 1.2])
        a.velocityY = random.choice([-1.2, -1.0, 1.0, 1.2])
        return

    speed = math.hypot(vx, vy)
    if speed < 1e-6:
        a.velocityX = random.choice([-1.0, 1.0])
        a.velocityY = random.choice([-1.0, 1.0])
        return

    if speed > MAX_SPEED:
        s = MAX_SPEED / speed
        a.velocityX *= s
        a.velocityY *= s


def _safe_pos(a: ag.Agent) -> None:
    if not (math.isfinite(a.x) and math.isfinite(a.y)):
        a.x = random.uniform(cfg.AGENT_RADIUS, cfg.WIDTH - cfg.AGENT_RADIUS)
        a.y = random.uniform(cfg.AGENT_RADIUS, cfg.HEIGHT - cfg.AGENT_RADIUS)
        _nudge_velocity(a)


def _dist(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)
