import math
import random

import config as cfg
import resources as res
import agent as ag

# ---------------------------------------------------------
# Stability / feel tuning
# ---------------------------------------------------------
INTERACT_COOLDOWN = 0.8     # seconds after eat/drink before interacting again
MAX_SPEED = 3.5             # clamp velocity so it can't explode
BOUNCE_DAMP = 0.92          # damp bounce so energy doesn't grow


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
            _nudge_velocity(a)
            _clamp_speed(a)

            # pick a new waypoint away from resources so they move off nicely
            a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
            a.waypoint_timer = random.uniform(0.0, cfg.SENSING["WAYPOINT_TIMEOUT"])
            return True

        a.drink_timer += dt
        while a.drink_timer >= cfg.RESOURCES["DRINK_INTERVAL"]:
            a.drink_timer -= cfg.RESOURCES["DRINK_INTERVAL"]
            a.thirst = max(0.0, a.thirst - cfg.RESOURCES["DRINK_AMOUNT"])

            # optional simplified energy boost
            if "ENERGY_FROM_DRINK" in cfg.RESOURCES:
                a.energy = min(100.0, a.energy + cfg.RESOURCES["ENERGY_FROM_DRINK"])

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
    # BUSH INTERACTION (eat one dot if hungry; otherwise bounce)
    # ---------------------------------------------------------
    for b in bushes:
        touching = res.touch_bush(nx, ny, cfg.AGENT_RADIUS, b, eps=4.0)
        if touching is None:
            continue

        # hungry & can interact -> try eat ONE food dot
        if a.interact_cooldown <= 0.0 and a.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]:
            ate = res.pick_food_from_bush(b)

            if ate:
                a.hunger = max(0.0, a.hunger - cfg.RESOURCES["EAT_AMOUNT"])
                if "ENERGY_FROM_EAT" in cfg.RESOURCES:
                    a.energy = min(100.0, a.energy + cfg.RESOURCES["ENERGY_FROM_EAT"])

                a.eat_pause = cfg.RESOURCES["EAT_PAUSE"]
                a.interact_cooldown = INTERACT_COOLDOWN
                _nudge_velocity(a)
                _clamp_speed(a)
                return True  # pause handled next frames

            # no food -> bounce away (prevents sticking)
            hit = res.collide_with_bush(nx, ny, cfg.AGENT_RADIUS, b)
            if hit is not None:
                _apply_bounce(a, hit)

                # IMPORTANT: if wandering, pick a new waypoint
                if a.action == "WANDER":
                    a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
                    a.waypoint_timer = 0.0
                return True

        # not hungry OR on cooldown -> solid bounce
        hit = res.collide_with_bush(nx, ny, cfg.AGENT_RADIUS, b)
        if hit is not None:
            _apply_bounce(a, hit)

            if a.action == "WANDER":
                a.waypoint = _random_waypoint_avoiding_resources(pond, bushes)
                a.waypoint_timer = 0.0
            return True

    # ---------------------------------------------------------
    # SOLID POND COLLISION (when not drinking)
    # ---------------------------------------------------------
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

    # 1) thirst priority
    if a.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]:
        pcx, pcy = _pond_center(pond)
        if _dist(a.x, a.y, pcx, pcy) <= vision:
            return (pcx, pcy)

    # 2) hunger next
    if a.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]:
        food = _nearest_food_in_vision(a, bushes, vision)
        if food is not None:
            return food

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
