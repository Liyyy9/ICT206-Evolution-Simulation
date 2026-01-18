import pygame
import config as cfg
import agent as ag
import utils

pygame.init()

screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
clock = pygame.time.Clock()
running = True

agents = [ag.create_agent(
    cfg.WIDTH, cfg.HEIGHT, cfg.AGENT_RADIUS) for _ in range(cfg.NUM_AGENTS)]

OUTLINE_COLOUR = (20, 20, 20)

while running:

    dt = clock.tick(cfg.FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(cfg.COLOURS["GRASS"])

    for a in agents:
        ag.update_internal_state(a, dt)

        # movement
        if a.alive:

            if a.dying:
                FRICTION = 0.92
                a.velocityX *= FRICTION
                a.velocityY *= FRICTION

                # snap tiny speeds to 0 to avoid endless drifting
                if abs(a.velocityX) < 0.05:
                    a.velocityX = 0.0
                if abs(a.velocityY) < 0.05:
                    a.velocityY = 0.0

            a.x += a.velocityX
            a.y += a.velocityY

            # bounce only if not dying
            if not a.dying:
                if a.x - cfg.AGENT_RADIUS < 0 or a.x + cfg.AGENT_RADIUS > cfg.WIDTH:
                    a.velocityX *= -1
                if a.y - cfg.AGENT_RADIUS < 0 or a.y + cfg.AGENT_RADIUS > cfg.HEIGHT:
                    a.velocityY *= -1

        # Colour logic
        base = cfg.COLOURS["AGENT"]

        if not a.alive:
            colour = cfg.COLOURS["DEAD"]

        else:
            h_sev = utils.severity(a.hunger, cfg.THRESHOLDS["HUNGER"], span=40)
            t_sev = utils.severity(a.thirst, cfg.THRESHOLDS["THIRST"], span=40)

            # Energy is reversed: lower energy => higher severity
            e_sev = utils.severity(
                cfg.THRESHOLDS["ENERGY_LOW"] - a.energy, start=0, span=30)
            e_sev = min(e_sev, 0.9)

            if e_sev > 0:
                # tired overrides everything else
                colour = utils.lerp_colour(base, cfg.COLOURS["TIRED"], e_sev)

            else:
                need_total = h_sev + t_sev

                if need_total > 0:
                    hunger_w = h_sev / need_total
                    thirst_w = t_sev / need_total

                    need_colour = (
                        int(cfg.COLOURS["HUNGRY"][0] * hunger_w +
                            cfg.COLOURS["THIRSTY"][0] * thirst_w),
                        int(cfg.COLOURS["HUNGRY"][1] * hunger_w +
                            cfg.COLOURS["THIRSTY"][1] * thirst_w),
                        int(cfg.COLOURS["HUNGRY"][2] * hunger_w +
                            cfg.COLOURS["THIRSTY"][2] * thirst_w),
                    )

                    intensity = max(h_sev, t_sev)

                    colour = utils.lerp_colour(base, need_colour, intensity)

                else:
                    colour = base

            if getattr(a, "dying", False):
                colour = utils.lerp_colour(
                    colour, cfg.COLOURS["DEAD"], getattr(a, "dying_progress", 0.0))

        # Draw agent
        pygame.draw.circle(screen, OUTLINE_COLOUR,
                           (int(a.x), int(a.y)), cfg.AGENT_RADIUS + 1)
        pygame.draw.circle(
            screen, colour, (int(a.x), int(a.y)), cfg.AGENT_RADIUS)

    pygame.display.flip()
    clock.tick(cfg.FPS)

pygame.quit()
