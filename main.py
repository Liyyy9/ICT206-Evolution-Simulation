import pygame
import config as cfg
import agent as ag
import resources as res

pygame.init()

screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
clock = pygame.time.Clock()
running = True

agents = [ag.create_agent(i, cfg.WIDTH, cfg.HEIGHT, cfg.AGENT_RADIUS)
          for i in range(cfg.NUM_AGENTS)]

pond = res.create_pond()
bushes = res.create_bushes(pond)

while running:
    dt = clock.tick(cfg.FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(cfg.COLOURS["GRASS"])

    # resources
    res.update_resources(bushes, dt)
    res.draw_resources(screen, pond, bushes)

    alive_agents = []

    for a in agents:
        ag.update_internal_state(a, dt)
        if not a.alive:
            continue

        # -------------------------
        # 1) eat pause = true freeze
        # -------------------------
        if a.eat_pause > 0.0:
            a.eat_pause = max(0.0, a.eat_pause - dt)

            # draw + keep alive, but do NOT move this frame
            alive_agents.append(a)
            pygame.draw.circle(screen, cfg.COLOURS["OUTLINE"], (int(
                a.x), int(a.y)), cfg.AGENT_RADIUS + 1)
            pygame.draw.circle(screen, a.colour, (int(a.x),
                               int(a.y)), cfg.AGENT_RADIUS)
            continue

        # Proposed movement variables
        nx, ny = a.x, a.y
        vx, vy = a.velocityX, a.velocityY

        # -------------------------
        # 2) DRINK state (freeze + sip over time)
        # -------------------------
        if a.action == "DRINK":
            touch_now = res.touch_pond(
                a.x, a.y, cfg.AGENT_RADIUS, pond, eps=6.0)

            # leave drink state if not touching OR already full
            # NOTE: use < (not <=) because THIRST_SEEK == DRINK_FULL_LEVEL right now
            if touch_now is None or a.thirst < cfg.RESOURCES["DRINK_FULL_LEVEL"]:
                a.action = "WANDER"
                a.drink_timer = 0.0
            else:
                a.drink_timer += dt
                while a.drink_timer >= cfg.RESOURCES["DRINK_INTERVAL"]:
                    a.drink_timer -= cfg.RESOURCES["DRINK_INTERVAL"]
                    a.thirst = max(0.0, a.thirst -
                                   cfg.RESOURCES["DRINK_AMOUNT"])

                # freeze while drinking
                nx, ny = a.x, a.y
                vx, vy = 0.0, 0.0

        # -------------------------
        # 3) WANDER movement
        # -------------------------
        if a.action == "WANDER":
            move_scale = 60.0 * dt  # keeps speed consistent across FPS
            mult = ag.movement_multiplier(a)

            nx = a.x + vx * mult * move_scale
            ny = a.y + vy * mult * move_scale

            # start drinking when touching pond rim AND thirsty
            pond_touch = res.touch_pond(
                nx, ny, cfg.AGENT_RADIUS, pond, eps=6.0)
            if pond_touch is not None and a.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]:
                a.action = "DRINK"
                a.drink_timer = 0.0

                # freeze immediately this frame
                nx, ny = a.x, a.y
                vx, vy = 0.0, 0.0

        # -------------------------
        # 4) Screen edge bounce
        # -------------------------
        if nx - cfg.AGENT_RADIUS < 0 or nx + cfg.AGENT_RADIUS > cfg.WIDTH:
            vx *= -1
            nx = a.x
        if ny - cfg.AGENT_RADIUS < 0 or ny + cfg.AGENT_RADIUS > cfg.HEIGHT:
            vy *= -1
            ny = a.y

        # -------------------------
        # 5) Solid pond collision bounce (only when not drinking)
        # -------------------------
        if a.action != "DRINK":
            pond_hit = res.collide_with_pond(nx, ny, cfg.AGENT_RADIUS, pond)
            if pond_hit is not None:
                cx, cy, cr, dist, overlap = pond_hit
                nx, ny, vx, vy = res.bounce_off_circle(
                    nx, ny, vx, vy, cx, cy, cr, dist, overlap)

        # -------------------------
        # 6) Bush: eat-on-touch OR bounce-on-collision
        # (we keep this even while testing thirst; it won't trigger unless hungry)
        # -------------------------
        if a.action != "DRINK":
            for b in bushes:
                bush_touch = res.touch_bush(
                    nx, ny, cfg.AGENT_RADIUS, b, eps=4.0)

                # hungry -> pick ONE food dot, pause
                if bush_touch is not None and a.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]:
                    ate = res.pick_food_from_bush(b)
                    if ate:
                        a.hunger = max(0.0, a.hunger -
                                       cfg.RESOURCES["EAT_AMOUNT"])
                        a.eat_pause = cfg.RESOURCES["EAT_PAUSE"]

                    # stop this frame
                    nx, ny = a.x, a.y
                    vx, vy = 0.0, 0.0
                    break

                # otherwise, solid bounce
                bush_hit = res.collide_with_bush(nx, ny, cfg.AGENT_RADIUS, b)
                if bush_hit is not None:
                    cx, cy, cr, dist, overlap = bush_hit
                    nx, ny, vx, vy = res.bounce_off_circle(
                        nx, ny, vx, vy, cx, cy, cr, dist, overlap)
                    break

        # Apply final position + velocity
        a.x, a.y = nx, ny
        a.velocityX, a.velocityY = vx, vy

        alive_agents.append(a)

        # Draw agent
        pygame.draw.circle(screen, cfg.COLOURS["OUTLINE"], (int(
            a.x), int(a.y)), cfg.AGENT_RADIUS + 1)
        pygame.draw.circle(screen, a.colour, (int(a.x),
                           int(a.y)), cfg.AGENT_RADIUS)

    agents = alive_agents
    pygame.display.flip()

pygame.quit()
