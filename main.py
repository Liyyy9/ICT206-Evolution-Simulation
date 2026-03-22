import pygame
import math

import config as cfg
import agent as ag
import resources as res
import simulation as sim
import interaction

pygame.init()
screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
clock = pygame.time.Clock()

agents = [
    ag.create_agent(i, cfg.WIDTH, cfg.HEIGHT, cfg.AGENT_RADIUS)
    for i in range(cfg.NUM_AGENTS)
]

pond = res.create_pond()
bushes = res.create_bushes(pond)

max_population = len(agents)  # Track max population ever reached


running = True
while running:
    dt = clock.tick(cfg.FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                clicked_agent = interaction.get_agent_at_mouse(
                    agents, mouse_pos)
                if clicked_agent is not None:
                    interaction.toggle_follow(clicked_agent)

    screen.fill(cfg.COLOURS["GRASS"])

    # resources
    res.update_resources(bushes, dt)
    res.draw_resources(screen, pond, bushes)

    alive = []
    for a in agents:
        if not sim.update_agent(a, dt, pond, bushes):
            continue

        alive.append(a)

        # --- Safe draw guard (prevents pygame crash) ---
        if not (math.isfinite(a.x) and math.isfinite(a.y)):
            continue

        cx, cy = int(a.x), int(a.y)
        generation = getattr(a, "generation", 1)

        # Draw filled circle
        pygame.draw.circle(
            screen,
            cfg.COLOURS["OUTLINE"],
            (cx, cy),
            cfg.AGENT_RADIUS + 1
        )
        pygame.draw.circle(
            screen,
            a.colour,
            (cx, cy),
            cfg.AGENT_RADIUS
        )

    agents = alive

    # Handle reproduction: spawn newborns from mating pairs
    newborns = sim.process_reproduction(agents)
    agents.extend(newborns)

    # Update max population tracker
    if len(agents) > max_population:
        max_population = len(agents)

    # Calculate max generation (highest generation alive)
    max_generation = max((getattr(a, "generation", 1)
                         for a in agents), default=1)

    # Draw population counter (always visible)
    interaction.draw_population_counter(
        screen, len(agents), max_population, max_generation)

    # Draw love icons above reproducing agents
    interaction.draw_reproduction_icon(screen, agents)

    mouse_pos = pygame.mouse.get_pos()
    hovered_agent = interaction.get_agent_at_mouse(agents, mouse_pos)
    followed_agent = interaction.get_followed_agent(agents)

    # Show chatbox for hovered agent
    if hovered_agent is not None:
        interaction.draw_agent_state_box(screen, hovered_agent)
    # Or show chatbox for followed agent if they exist
    elif followed_agent is not None:
        interaction.draw_agent_state_box(screen, followed_agent)

    # Show debug traits panel for followed agent
    if followed_agent is not None:
        interaction.draw_agent_debug_panel(screen, followed_agent)

    pygame.display.flip()

pygame.quit()
