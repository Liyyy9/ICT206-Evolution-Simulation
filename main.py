import pygame
import config as cfg
import agent as ag
import resources as res

pygame.init()

screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
clock = pygame.time.Clock()
running = True

agents = [ag.create_agent(
    cfg.WIDTH, cfg.HEIGHT, cfg.AGENT_RADIUS) for _ in range(cfg.NUM_AGENTS)]

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

    # update + move
    alive_agents = []
    for a in agents:
        ag.update_internal_state(a, dt)

        if not a.alive:
            continue

        # movement
        mult = ag.movement_multiplier(a)
        a.x += a.velocityX * mult
        a.y += a.velocityY * mult

        # bounce off edges
        if a.x - cfg.AGENT_RADIUS < 0 or a.x + cfg.AGENT_RADIUS > cfg.WIDTH:
            a.velocityX *= -1
        if a.y - cfg.AGENT_RADIUS < 0 or a.y + cfg.AGENT_RADIUS > cfg.HEIGHT:
            a.velocityY *= -1

        alive_agents.append(a)

        # Draw agent
        pygame.draw.circle(screen, cfg.COLOURS["OUTLINE"],
                           (int(a.x), int(a.y)), cfg.AGENT_RADIUS + 1)
        pygame.draw.circle(
            screen, a.colour, (int(a.x), int(a.y)), cfg.AGENT_RADIUS)

    agents = alive_agents

    pygame.display.flip()

pygame.quit()
