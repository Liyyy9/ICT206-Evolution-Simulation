import pygame
import math
import sys
import time

import config as cfg
import agent as ag
import resources as res
import simulation as sim
import interaction
import metrics
import traits as tr


def format_elapsed_time(seconds: float) -> str:
    """Convert elapsed seconds to hh:mm:ss format."""
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    secs = int(seconds) % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# Conditional pygame initialization based on headless mode
if not cfg.HEADLESS_MODE:
    pygame.init()
    screen = pygame.display.set_mode((cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT))
    clock = pygame.time.Clock()
else:
    screen = None
    clock = None


def initialize_simulation():
    """Create fresh agents, pond, and bushes for a new simulation cycle."""
    agents = [
        ag.create_agent(i, cfg.WIDTH, cfg.HEIGHT, cfg.AGENT_RADIUS)
        for i in range(cfg.NUM_AGENTS)
    ]
    pond = res.create_pond()
    bushes = res.create_bushes(pond)
    return agents, pond, bushes


def trigger_disaster(agents, current_generation, elapsed_time, override_mortality=None, silent=False, disaster_type_override=None):
    """
    Trigger a natural disaster that culls population.
    If TARGET_WEAK is True, preferentially kills weaker agents.
    Args:
        override_mortality: Optional mortality rate (0-1). If None, uses cfg.DISASTER_MORTALITY_RATE
        silent: If True, skip the disaster description line (used for critical overpopulation)
        disaster_type_override: Optional disaster type string. If None, selects random from DISASTER_TYPES
    Returns tuple of (updated_agent_list, death_count, disaster_type).
    """
    import random
    disaster_type = disaster_type_override if disaster_type_override else random.choice(cfg.DISASTER_TYPES)
    # Use override mortality if provided, otherwise use configured rate
    mortality_rate = override_mortality if override_mortality is not None else cfg.DISASTER_MORTALITY_RATE
    mortality_count = max(1, int(len(agents) * mortality_rate))

    if cfg.DISASTER_TARGET_WEAK:
        # Sort by health (weakest first) and kill the weakest
        agents_sorted = sorted(agents, key=lambda a: a.health)
        agents_to_keep = agents_sorted[mortality_count:]
    else:
        # Random culling
        agents_to_keep = random.sample(agents, len(agents) - mortality_count)

    # Only print disaster description if not silent
    if not silent:
        print(
            f"\n🌪️  DISASTER: {disaster_type} strikes! {mortality_count} agents perished.")

    print(
        f"   Population: {len(agents)} → {len(agents_to_keep)} | Gen {current_generation} | Elapsed: {format_elapsed_time(elapsed_time)}\n")

    # Add to chat if in visualization mode
    if not cfg.HEADLESS_MODE:
        chat_messages.append(
            # type: ignore
            [f"DISASTER: {disaster_type} strikes! {mortality_count} perished", elapsed_time])

    return agents_to_keep, mortality_count, disaster_type


agents, pond, bushes = initialize_simulation()
max_population = len(agents)  # Track max population ever reached
max_generation = 1  # Track current generation
start_time = time.time()  # Track simulation start time (real wall-clock)
metrics_logger = metrics.MetricsLogger()  # Initialize metrics tracking
last_log_time = 0.0  # Last time we logged gen metrics
last_displayed_generation = 0  # Track last generation displayed in headless mode
LOG_INTERVAL = 10.0  # Log every 10 seconds
last_disaster_generation = -999  # Track when last disaster occurred
# Prevent disaster triggering multiple times per frame
disaster_triggered_this_frame = False

# Visualization-only variables (not used in headless mode)
if not cfg.HEADLESS_MODE:
    population_history = []  # Track population over time to detect decline
    visualization_enabled = True  # Toggle visualization on/off
    graph_enabled = False  # Toggle graph panel on/off
    chat_box_enabled = True  # Toggle chatbox visibility on/off
    chat_messages = []  # Store chat messages with timestamps [[message, time], ...]
    chat_fade_time = 5.0  # How long messages stay visible (seconds)
    graph_data = {  # Historical data for graphing (keep last 60 points)
        "times": [],
        "vision": [],
        "speed": [],
        "metabolism": [],
        "memory": [],
        "age": [],
        "population": [],
        "generation": []
    }
    last_restart_time = -float('inf')
    last_population_sample_time = 0.0
    max_pop_since_restart = len(agents)
else:
    population_history = []
    visualization_enabled = False
    graph_enabled = False
    graph_data = None
    # Initialize to very old time to prevent initial restart
    last_restart_time = -float('inf')
    last_population_sample_time = 0.0  # Track when we last sampled population
    # Track max population reached in this cycle
    max_pop_since_restart = len(agents)


running = True
try:
    while running:
        if not cfg.HEADLESS_MODE:
            dt = clock.tick(cfg.FPS) / 1000.0  # type: ignore
        else:
            # In headless mode, run as fast as possible
            dt = 1.0 / cfg.FPS  # Fixed timestep

        # Calculate real elapsed time from wall-clock
        elapsed_time = time.time() - start_time

        # Reset disaster flag each frame
        disaster_triggered_this_frame = False

        # Handle pygame events (only in visualization mode)
        if not cfg.HEADLESS_MODE:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()

                        # Check if visualization toggle button was clicked
                        button_height = 48  # Approx height of button
                        button_width = 110  # Approx width of button
                        button_x = 15
                        button_y = cfg.DISPLAY_HEIGHT - button_height - 15
                        vis_button_rect = pygame.Rect(
                            button_x, button_y, button_width, button_height)

                        # Graph button rect
                        graph_button_x = button_x + 125
                        graph_button_rect = pygame.Rect(
                            graph_button_x, button_y, 180, button_height)

                        # Chat button rect (top-left, right of VIS)
                        chat_button_x = button_x + 275
                        chat_button_rect = pygame.Rect(
                            chat_button_x, cfg.DISPLAY_HEIGHT - button_height - 15, 110, button_height)

                        # Restart button rect (bottom center)
                        restart_button_x = (cfg.DISPLAY_WIDTH - 115) // 2
                        restart_button_rect = pygame.Rect(
                            restart_button_x, button_y, 115, button_height)

                        # Disaster button rect (bottom center-right)
                        disaster_button_x = restart_button_x + 130
                        disaster_button_rect = pygame.Rect(
                            disaster_button_x, button_y, 120, button_height)

                        if vis_button_rect.collidepoint(mouse_pos):
                            visualization_enabled = not visualization_enabled
                        # Check graph button separately (drawn later, so check its rect)
                        elif graph_button_rect.collidepoint(mouse_pos):
                            graph_enabled = not graph_enabled
                        elif chat_button_rect.collidepoint(mouse_pos):
                            chat_box_enabled = not chat_box_enabled  # type: ignore
                        elif restart_button_rect.collidepoint(mouse_pos):
                            # Manual restart
                            agents, pond, bushes = initialize_simulation()
                            max_population = len(agents)
                            max_generation = 1
                            start_time = time.time()  # Reset timer to real wall-clock
                            population_history = []
                            last_log_time = 0.0
                            metrics_logger.reset_for_restart()
                            chat_messages = []
                            chat_messages.append(
                                ["RESTART: Simulation reset", 0.0])
                            graph_data["times"] = []
                            graph_data["vision"] = []
                            graph_data["speed"] = []
                            graph_data["metabolism"] = []
                            graph_data["memory"] = []
                            graph_data["age"] = []
                            graph_data["population"] = []
                            graph_data["generation"] = []
                        elif disaster_button_rect.collidepoint(mouse_pos):
                            # Manual disaster trigger
                            if len(agents) > 0 and not disaster_triggered_this_frame:
                                agents, death_count, disaster_type = trigger_disaster(
                                    agents, max_generation, elapsed_time)
                                last_disaster_generation = max_generation
                                for _ in range(death_count):
                                    metrics_logger.record_death()
                                metrics_logger.record_disaster(disaster_type)
                                disaster_triggered_this_frame = True
                                test_msg = f"Population: {len(agents)}"
                                if len(chat_messages) > 0:  # type: ignore
                                    pass
                        else:
                            # Try to click on agent instead
                            clicked_agent = interaction.get_agent_at_mouse(
                                agents, mouse_pos)
                            if clicked_agent is not None:
                                interaction.toggle_follow(clicked_agent)

        # Draw scene (only in visualization mode)
        if not cfg.HEADLESS_MODE:
            screen.fill(cfg.COLOURS["GRASS"])  # type: ignore

            # resources
            res.update_resources(bushes, dt)
            res.draw_resources(screen, pond, bushes)  # type: ignore
        else:
            # Still update resources in headless mode, just don't draw
            res.update_resources(bushes, dt)

        alive = []
        for a in agents:
            if not sim.update_agent(a, dt, pond, bushes):
                continue

            alive.append(a)

            # Draw agents only if visualization is enabled
            if not cfg.HEADLESS_MODE and visualization_enabled:
                # --- Safe draw guard (prevents pygame crash) ---
                if not (math.isfinite(a.x) and math.isfinite(a.y)):  # type: ignore
                    continue

                cx, cy = int(a.x * cfg.ZOOM_SCALE), int(a.y * cfg.ZOOM_SCALE)
                scaled_radius = max(2, int(cfg.AGENT_RADIUS * cfg.ZOOM_SCALE))
                generation = getattr(a, "generation", 1)

                # Draw filled circle
                pygame.draw.circle(
                    screen,  # type: ignore
                    cfg.COLOURS["OUTLINE"],
                    (cx, cy),
                    scaled_radius + 1
                )
                pygame.draw.circle(
                    screen,  # type: ignore
                    a.colour,
                    (cx, cy),
                    scaled_radius
                )

        # Track deaths for metrics
        deaths_this_frame = len(agents) - len(alive)
        for _ in range(deaths_this_frame):
            metrics_logger.record_death()

        agents = alive

        # Handle reproduction: spawn newborns from mating pairs
        newborns = sim.process_reproduction(agents)
        agents.extend(newborns)

        # Track births for metrics
        for _ in range(len(newborns)):
            metrics_logger.record_birth()

        # DO NOT hard-cap population - let natural selection control it
        # With aggressive health drain, death rate should scale with births

        # Update max population tracker
        if len(agents) > max_population:
            max_population = len(agents)

        # Calculate max generation (highest generation alive)
        max_generation = max((getattr(a, "generation", 1)
                             for a in agents), default=1)

        # Log metrics immediately when we detect generation change (BEFORE exit check)
        metrics_logger.log_generation(agents)

        # Display generation progress in headless mode
        if cfg.HEADLESS_MODE and max_generation > last_displayed_generation:
            print(
                f"Generation: {max_generation} | Population: {len(agents)} | Elapsed: {format_elapsed_time(elapsed_time)}")
            last_displayed_generation = max_generation

        # DISASTER SYSTEM - Check if population exceeds threshold (headless mode only)
        if cfg.HEADLESS_MODE and cfg.DISASTER_ENABLED and not disaster_triggered_this_frame:
            # HARD SAFETY CAP: If population exceeds 10,000, trigger immediate 90% mortality disaster
            if len(agents) >= 10000:
                print("🚨 CRITICAL OVERPOPULATION: Ecological Collapse Triggered!")
                agents, death_count, disaster_type = trigger_disaster(
                    agents, max_generation, elapsed_time, override_mortality=0.90, silent=True, disaster_type_override="CRITICAL_OVERPOPULATION")
                last_disaster_generation = max_generation
                for _ in range(death_count):
                    metrics_logger.record_death()
                metrics_logger.record_disaster(disaster_type)
                disaster_triggered_this_frame = True
            # Standard threshold check: 85% mortality after waiting min_generations_apart
            elif len(agents) > cfg.DISASTER_POPULATION_THRESHOLD:
                # Check if enough generations have passed since last disaster
                if max_generation - last_disaster_generation >= cfg.DISASTER_MIN_GENERATIONS_APART:
                    agents, death_count, disaster_type = trigger_disaster(
                        agents, max_generation, elapsed_time)
                    last_disaster_generation = max_generation
                    for _ in range(death_count):
                        metrics_logger.record_death()
                    metrics_logger.record_disaster(disaster_type)
                    disaster_triggered_this_frame = True

        # Check headless mode exit conditions (AFTER max_generation is calculated and logged)
        if cfg.HEADLESS_MODE:
            if cfg.HEADLESS_MODE_DURATION > 0 and elapsed_time >= cfg.HEADLESS_MODE_DURATION:
                print(
                    f"\n⏱ Headless mode duration limit reached ({cfg.HEADLESS_MODE_DURATION}s)")
                running = False
                break
            if cfg.HEADLESS_MODE_MAX_GENERATION > 0 and max_generation >= cfg.HEADLESS_MODE_MAX_GENERATION:
                print(f"\n🎯 Max generation reached (Gen {max_generation})")
                running = False
                break

        # HEADLESS MODE AUTO-RESTART LOGIC
        # Restart if population crashes, but respect duration/generation limits
        if cfg.HEADLESS_MODE and cfg.HEADLESS_MODE_AUTO_RESTART:
            # Check for immediate extinction (population hit 0)
            if len(agents) == 0:
                time_since_restart = elapsed_time - last_restart_time
                if time_since_restart >= cfg.HEADLESS_MODE_MIN_TIME_BETWEEN_RESTARTS:
                    can_restart = True
                    if cfg.HEADLESS_MODE_DURATION > 0 and elapsed_time >= cfg.HEADLESS_MODE_DURATION * 0.9:
                        can_restart = False
                    if cfg.HEADLESS_MODE_MAX_GENERATION > 0 and max_generation >= cfg.HEADLESS_MODE_MAX_GENERATION * 0.9:
                        can_restart = False

                    if can_restart:
                        print(
                            f"\n🔄 AUTO-RESTART: Population extinct at Gen {max_generation} (Elapsed: {format_elapsed_time(elapsed_time)})")
                        agents, pond, bushes = initialize_simulation()
                        max_population = len(agents)
                        population_history = []
                        last_population_sample_time = elapsed_time
                        last_restart_time = elapsed_time
                        last_log_time = elapsed_time
                        last_displayed_generation = 0
                        max_pop_since_restart = len(agents)
                        metrics_logger.reset_for_restart()

            # Sample population every 10 seconds for gradual crash detection
            elif elapsed_time - last_population_sample_time >= 10.0:
                population_history.append((elapsed_time, len(agents)))
                last_population_sample_time = elapsed_time

                # Update maximum population reached in this cycle
                current_pop = len(agents)
                max_pop_since_restart = max(max_pop_since_restart, current_pop)

                # Check if population has crashed and enough time passed since last restart
                time_since_restart = elapsed_time - last_restart_time
                # Restart if:
                # 1. Population is 0 (extinction) OR population declined 50% AND below threshold
                # 2. Enough time since last restart
                pop_decline_threshold = max_pop_since_restart * 0.5  # 50% of peak
                is_extinct = current_pop == 0
                is_crashed = current_pop < pop_decline_threshold and current_pop <= cfg.HEADLESS_MODE_MIN_POPULATION

                if (is_extinct or is_crashed) and time_since_restart >= cfg.HEADLESS_MODE_MIN_TIME_BETWEEN_RESTARTS:
                    # Check if we have time/generation budget left to restart
                    can_restart = True

                    # If duration limit set, only restart if we have significant time left
                    if cfg.HEADLESS_MODE_DURATION > 0:
                        if elapsed_time >= cfg.HEADLESS_MODE_DURATION * 0.9:  # Don't restart in last 10% of time
                            can_restart = False

                    # If generation limit set, only restart if we have room to grow
                    if cfg.HEADLESS_MODE_MAX_GENERATION > 0:
                        if max_generation >= cfg.HEADLESS_MODE_MAX_GENERATION * 0.9:  # Don't restart in last gen
                            can_restart = False

                    if can_restart:
                        print(
                            f"\n🔄 AUTO-RESTART: Population crashed to {len(agents)} at Gen {max_generation} (Elapsed: {format_elapsed_time(elapsed_time)})")
                        agents, pond, bushes = initialize_simulation()
                        max_population = len(agents)
                        # DO NOT reset max_generation or elapsed_time - they continue accumulating
                        population_history = []
                        last_population_sample_time = elapsed_time
                        last_restart_time = elapsed_time
                        last_log_time = elapsed_time
                        last_displayed_generation = 0  # Reset echo tracker so generation display continues
                        # Reset max population tracker for this cycle
                        max_pop_since_restart = len(agents)
                        metrics_logger.reset_for_restart()
                        # Keep graph data to show restart point
                        continue  # Skip to next iteration

        # Draw timer in top-left
        if not cfg.HEADLESS_MODE:
            interaction.draw_timer(screen, elapsed_time)  # type: ignore

            # Draw population counter (always visible)
            interaction.draw_population_counter(
                # type: ignore
                screen, len(agents), max_population, max_generation)

            # Draw visualization toggle button
            interaction.draw_visualization_toggle_button(
                screen, visualization_enabled)  # type: ignore

            # Draw graph toggle button
            interaction.draw_graph_toggle_button(
                screen, graph_enabled)  # type: ignore

            # Draw chat toggle button
            interaction.draw_chat_toggle_button(
                screen, chat_box_enabled)  # type: ignore

            # Draw restart button
            interaction.draw_restart_button(screen)  # type: ignore

            # Draw disaster button
            interaction.draw_disaster_button(screen)  # type: ignore

            # Draw graph panel AFTER love icons so UI stays on top
            if graph_enabled:
                interaction.draw_graph_panel(
                    screen, graph_data)  # type: ignore

        # Update graph data (only if visualization mode) - log every 10 seconds
        if not cfg.HEADLESS_MODE and agents and graph_data is not None and elapsed_time - last_log_time >= LOG_INTERVAL:
            traits_list = [getattr(a, "traits", tr.Traits())
                           for a in agents]
            visions = [t.vision_mult for t in traits_list]
            speeds = [t.speed_mult for t in traits_list]
            metabolisms = [t.metabolism_mult for t in traits_list]
            memories = [t.memory_mult for t in traits_list]
            ages = [a.age for a in agents]

            graph_data["times"].append(elapsed_time)
            graph_data["vision"].append(
                sum(visions) / len(visions) if visions else 0)
            graph_data["speed"].append(
                sum(speeds) / len(speeds) if speeds else 0)
            graph_data["metabolism"].append(
                sum(metabolisms) / len(metabolisms) if metabolisms else 0)
            graph_data["memory"].append(
                sum(memories) / len(memories) if memories else 0)
            graph_data["age"].append(
                sum(ages) / len(ages) if ages else 0)
            graph_data["population"].append(len(agents))
            graph_data["generation"].append(max_generation)

            # Keep only last 60 points (5 minutes at 10s intervals)
            for key in graph_data:
                if len(graph_data[key]) > 60:
                    graph_data[key] = graph_data[key][-60:]

            last_log_time = elapsed_time

        # Drawing code (only in visualization mode)
        if not cfg.HEADLESS_MODE:
            # Draw love icons only if visualization enabled
            if visualization_enabled:
                interaction.draw_reproduction_icon(
                    screen, agents)  # type: ignore

            mouse_pos = pygame.mouse.get_pos()
            hovered_agent = interaction.get_agent_at_mouse(agents, mouse_pos)
            followed_agent = interaction.get_followed_agent(agents)

            # Show chatbox for hovered agent
            if hovered_agent is not None:
                interaction.draw_agent_state_box(
                    screen, hovered_agent)  # type: ignore
            # Or show chatbox for followed agent if they exist
            elif followed_agent is not None:
                interaction.draw_agent_state_box(
                    screen, followed_agent)  # type: ignore

            # Show debug traits panel for followed agent
            if followed_agent is not None:
                interaction.draw_agent_debug_panel(
                    screen, followed_agent)  # type: ignore

            # Draw event chat log (RESTART, DISASTER messages) if enabled
            if chat_box_enabled:   # type: ignore
                interaction.draw_chatbox(
                    screen, chat_messages, elapsed_time, chat_fade_time)  # type: ignore

            pygame.display.flip()  # type: ignore

except KeyboardInterrupt:
    print("\n\n⏹ Simulation interrupted by user (Ctrl+C)")

    # Print final summary
    if agents:
        final_gen = max((getattr(a, "generation", 1)
                        for a in agents), default=1)
    else:
        final_gen = max_generation

    print("\n" + "="*50)
    print("FINAL SUMMARY")
    print("="*50)
    print(f"Simulation Duration:  {elapsed_time:.1f}s")
    print(f"Final Generation:     {final_gen}")
    print(f"Final Population:     {len(agents)}")
    print(f"Max Population:       {max_population}")
    print(
        # type: ignore
        f"Metrics Logged:       {len(metrics_logger.entries) if hasattr(metrics_logger, 'entries') else 'N/A'}")
    print("="*50 + "\n")
    sys.exit(0)

if not cfg.HEADLESS_MODE:
    pygame.quit()
