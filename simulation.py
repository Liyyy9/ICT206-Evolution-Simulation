import config as cfg
import resources as res
import agent as ag
import random
import math

# --- Stability / feel tuning ---
INTERACT_COOLDOWN = 0.8   # seconds after drink/eat before interacting again
MAX_SPEED = 3.5           # caps velocity so physics can't explode
BOUNCE_DAMP = 0.92        # slight damping to prevent runaway bounce energy


def update_agent(a: ag.Agent, dt: float, pond: res.Pond, bushes: list[res.FoodBush]) -> bool:
    """
    Updates one agent for one frame. Returns True if agent still exists (alive),
    False if dead (main should remove).
    """
    ag.update_internal_state(a, dt)
    if not a.alive:
        return False

    # --- safety guard in case something goes invalid ---
    _safe_pos(a)
    _clamp_speed(a)

    # cooldown timer
    if a.interact_cooldown > 0.0:
        a.interact_cooldown = max(0.0, a.interact_cooldown - dt)

    # ---------------------------------------------------
    # 0) Eat pause: freeze for a short time (visual "bite")
    # ---------------------------------------------------
    if a.eat_pause > 0.0:
        a.eat_pause = max(0.0, a.eat_pause - dt)
        return True

    # -------------------------
    # 1) DRINK STATE
    # -------------------------
    if a.action == "DRINK":
        touching = res.touch_pond(a.x, a.y, cfg.AGENT_RADIUS, pond, eps=6.0)

        # Release condition: stop drinking if no longer touching OR thirst low enough
        if touching is None or a.thirst <= cfg.THRESHOLDS["THIRST_OK"]:
            a.action = "WANDER"
            a.drink_timer = 0.0
            a.interact_cooldown = INTERACT_COOLDOWN
            _nudge_velocity(a)   # ensures they actually leave the rim
            _clamp_speed(a)
            return True

        # Sip over time
        a.drink_timer += dt
        while a.drink_timer >= cfg.RESOURCES["DRINK_INTERVAL"]:
            a.drink_timer -= cfg.RESOURCES["DRINK_INTERVAL"]
            a.thirst = max(0.0, a.thirst - cfg.RESOURCES["DRINK_AMOUNT"])

        # Freeze position while drinking (IMPORTANT: do NOT zero velocity)
        return True

    # -------------------------
    # 2) PROPOSED MOVE (WANDER)
    # -------------------------
    move_scale = 60.0 * dt
    mult = ag.movement_multiplier(a)

    nx = a.x + a.velocityX * mult * move_scale
    ny = a.y + a.velocityY * mult * move_scale

    # -------------------------
    # 3) START DRINK (only if cooldown is over)
    # -------------------------
    if (
        a.interact_cooldown <= 0.0
        and a.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]
        and res.touch_pond(nx, ny, cfg.AGENT_RADIUS, pond, eps=6.0) is not None
    ):
        a.action = "DRINK"
        a.drink_timer = 0.0
        return True  # freeze this frame

    # -------------------------
    # 4) BUSH INTERACTION
    #    - If hungry AND food exists -> eat one food dot
    #    - If hungry BUT no food -> bounce off (solid)
    #    - If not hungry -> bounce off (solid)
    # -------------------------
    for b in bushes:
        touching = res.touch_bush(nx, ny, cfg.AGENT_RADIUS, b, eps=4.0)
        if touching is None:
            continue

        # hungry & cooldown over -> try eat
        if a.interact_cooldown <= 0.0 and a.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]:
            ate = res.pick_food_from_bush(b)

            if ate:
                a.hunger = max(0.0, a.hunger - cfg.RESOURCES["EAT_AMOUNT"])
                a.eat_pause = cfg.RESOURCES["EAT_PAUSE"]
                a.interact_cooldown = INTERACT_COOLDOWN
                _nudge_velocity(a)
                _clamp_speed(a)
                return True  # freeze this frame (pause handled next frame)

            # no food available -> bounce (prevents camping)
            hit = res.collide_with_bush(nx, ny, cfg.AGENT_RADIUS, b)
            if hit is not None:
                _apply_bounce(a, hit)
                return True

        # not hungry OR still on cooldown -> solid bounce
        hit = res.collide_with_bush(nx, ny, cfg.AGENT_RADIUS, b)
        if hit is not None:
            _apply_bounce(a, hit)
            return True

    # -------------------------
    # 5) SOLID POND COLLISION (not drinking)
    # -------------------------
    hit = res.collide_with_pond(nx, ny, cfg.AGENT_RADIUS, pond)
    if hit is not None:
        _apply_bounce(a, hit)
        return True

    # -------------------------
    # 6) SCREEN BOUNDS
    # -------------------------
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

    # Apply final position
    a.x, a.y = nx, ny

    _safe_pos(a)
    _clamp_speed(a)
    return True


# -------------------------
# Helpers
# -------------------------

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
    # small random nudge so agents don't re-stick to rims after release
    a.velocityX += random.choice([-1, 1]) * 0.6
    a.velocityY += random.choice([-1, 1]) * 0.6


def _clamp_speed(a: ag.Agent) -> None:
    vx, vy = a.velocityX, a.velocityY
    if not (math.isfinite(vx) and math.isfinite(vy)):
        a.velocityX = random.choice([-2.0, -1.5, 1.5, 2.0])
        a.velocityY = random.choice([-2.0, -1.5, 1.5, 2.0])
        return

    speed = math.hypot(vx, vy)
    if speed > MAX_SPEED:
        s = MAX_SPEED / speed
        a.velocityX *= s
        a.velocityY *= s


def _safe_pos(a: ag.Agent) -> None:
    if not (math.isfinite(a.x) and math.isfinite(a.y)):
        a.x = random.uniform(cfg.AGENT_RADIUS, cfg.WIDTH - cfg.AGENT_RADIUS)
        a.y = random.uniform(cfg.AGENT_RADIUS, cfg.HEIGHT - cfg.AGENT_RADIUS)
        _nudge_velocity(a)
