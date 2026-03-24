"""
Interaction and visualization utilities.
Handles agent state display via chatbox-style tooltips.
"""
import pygame
import config as cfg
import agent as ag
import traits as tr

# Cache loaded icon images
_icon_cache = {}

# Global state for following an agent
_followed_agent_id = None


def _load_icon(icon_key: str) -> pygame.Surface | None:
    """
    Load and cache an icon image. Returns None if icon fails to load.
    """
    if icon_key in _icon_cache:
        return _icon_cache[icon_key]

    try:
        if icon_key not in cfg.ICONS:
            return None

        icon_path = cfg.ICONS[icon_key]
        img = pygame.image.load(icon_path)
        _icon_cache[icon_key] = img
        return img
    except Exception as e:
        print(f"Failed to load icon {icon_key}: {e}")
        _icon_cache[icon_key] = None
        return None


def get_agent_at_mouse(agents: list[ag.Agent], mouse_pos: tuple) -> ag.Agent | None:
    """
    Check if mouse is hovering over any agent.
    Returns the agent if found, None otherwise.
    Extended radius for easier detection.
    """
    mx, my = mouse_pos
    hover_radius = cfg.AGENT_RADIUS + 15
    for a in agents:
        dx = a.x - mx
        dy = a.y - my
        dist = (dx * dx + dy * dy) ** 0.5
        if dist <= hover_radius:
            return a
    return None


def toggle_follow(agent: ag.Agent) -> None:
    """
    Toggle following an agent. If already following, unfollow.
    """
    global _followed_agent_id
    if _followed_agent_id == agent.id:
        _followed_agent_id = None  # Unfollow
    else:
        _followed_agent_id = agent.id  # Follow this agent


def get_followed_agent(agents: list[ag.Agent]) -> ag.Agent | None:
    """
    Get the currently followed agent, if any.
    """
    if _followed_agent_id is None:
        return None
    for a in agents:
        if a.id == _followed_agent_id:
            return a
    return None


def get_agent_state_color(agent: ag.Agent) -> tuple:
    """
    Determine chatbox color based on agent's hunger/thirst state.
    Light grey (base) -> Red (critical)
    """
    is_critical = (agent.thirst >= cfg.THRESHOLDS["THIRST_CRIT"] or
                   agent.hunger >= cfg.THRESHOLDS["HUNGER_CRIT"])

    if is_critical:
        return cfg.COLOURS["CHATBOX_CRITICAL"]  # Red
    else:
        return cfg.COLOURS["CHATBOX_BASE"]  # Light grey


def get_agent_state_value(agent: ag.Agent) -> tuple[str | None, str]:
    """
    Get icon key and value for agent's current state.
    Returns (icon_key, value_string) or (None, "OK")
    """
    # Check for SEEK_MATE first
    if getattr(agent, "action", "WANDER") == "SEEK_MATE":
        return ("LOVE", "♥")

    thirsty = agent.thirst >= cfg.THRESHOLDS["THIRST_SEEK"]
    hungry = agent.hunger >= cfg.THRESHOLDS["HUNGER_SEEK"]

    if thirsty and hungry:
        # Both thirsty and hungry - show the more urgent one
        if agent.thirst >= agent.hunger:
            return ("THIRST", f"{agent.thirst:.0f}")
        else:
            return ("HUNGER", f"{agent.hunger:.0f}")
    elif thirsty:
        return ("THIRST", f"{agent.thirst:.0f}")
    elif hungry:
        return ("HUNGER", f"{agent.hunger:.0f}")
    else:
        return (None, "OK")


def draw_agent_state_box(screen: pygame.Surface, agent: ag.Agent) -> None:
    """
    Draw a chatbox-style indicator above the agent showing their state,
    with additional info: food memory, water location, and age.
    """
    # Get state-based color
    box_color = get_agent_state_color(agent)
    icon_key, value_text = get_agent_state_value(agent)

    # Load icon if available
    icon_img = None
    if icon_key:
        icon_img = _load_icon(icon_key)

    # Build text lines for the info box
    lines = []

    # Top line: state icon + value (already handled by icon_img and value_text)
    # Will render this separately as icon + text

    # Food memory section
    lines.append("Food:")
    if hasattr(agent, 'food_memory') and agent.food_memory:
        # Filter non-expired memories (adjusted by agent traits)
        traits_obj = getattr(agent, "traits", None) or tr.Traits()
        effective_timeout = tr.effective_memory_ttl(
            cfg.MEMORY["TIMEOUT"], traits_obj)
        timeout_ms = effective_timeout * 1000
        current_time_ms = pygame.time.get_ticks()
        valid_memories = [
            (x, y, ts) for x, y, ts in agent.food_memory
            if (current_time_ms - ts) <= timeout_ms
        ]
        for x, y, _ in valid_memories[:3]:
            lines.append(f"  {int(x)}, {int(y)}")
        if not valid_memories:
            lines.append("  --")
    else:
        lines.append("  --")

    # Water memory section
    if agent.last_water_pos:
        # Check if water memory is expired (adjusted by agent traits)
        traits_obj = getattr(agent, "traits", None) or tr.Traits()
        effective_timeout = tr.effective_memory_ttl(
            cfg.MEMORY["TIMEOUT"], traits_obj)
        timeout_ms = effective_timeout * 1000
        current_time_ms = pygame.time.get_ticks()
        if hasattr(agent, 'last_water_time_ms') and agent.last_water_time_ms >= 0:
            if (current_time_ms - agent.last_water_time_ms) <= timeout_ms:
                wx, wy = agent.last_water_pos
                lines.append(f"Water: {int(wx)}, {int(wy)}")
            else:
                lines.append("Water: --")
        else:
            wx, wy = agent.last_water_pos
            lines.append(f"Water: {int(wx)}, {int(wy)}")
    else:
        lines.append("Water: --")

    # Age section
    lines.append(f"Age: {int(agent.age)}")

    # Render all info lines with larger font
    font_info = pygame.font.Font(None, 16)
    rendered_lines = [font_info.render(
        line, True, (0, 0, 0)) for line in lines]

    # Calculate box size
    padding_x = 8
    padding_y = 6
    icon_size = 24
    gap = 6

    # Top row height (icon + value)
    top_height = max(icon_size, 18)

    # Info lines height
    info_height = sum(line.get_height()
                      for line in rendered_lines) + (len(rendered_lines) - 1) * 2

    # Total dimensions
    info_width = max(line.get_width()
                     for line in rendered_lines) if rendered_lines else 0
    box_width = max(icon_size + gap + 30, info_width) + padding_x * 2
    box_height = top_height + 8 + info_height + padding_y * 2

    box_x = int(agent.x) - box_width // 2
    box_y = int(agent.y) - cfg.AGENT_RADIUS - box_height - 15

    # Draw rounded box
    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, box_color, box_rect, border_radius=4)
    pygame.draw.rect(screen, (0, 0, 0), box_rect, 2, border_radius=4)  # Border

    # Draw top row (icon + value)
    current_y = box_y + padding_y

    if icon_img and value_text != "OK":
        # Draw icon (scaled to icon_size)
        scaled_icon = pygame.transform.scale(icon_img, (icon_size, icon_size))
        icon_x = box_x + padding_x
        icon_y = current_y + (top_height - icon_size) // 2
        screen.blit(scaled_icon, (icon_x, icon_y))

        # Draw value
        font_value = pygame.font.Font(None, 18)
        text_surface = font_value.render(value_text, True, (0, 0, 0))
        text_x = icon_x + icon_size + gap
        text_y = current_y + (top_height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))
    else:
        # Draw "OK" text
        font_value = pygame.font.Font(None, 18)
        text_surface = font_value.render(value_text, True, (0, 0, 0))
        text_x = box_x + padding_x
        text_y = current_y
        screen.blit(text_surface, (text_x, text_y))

    # Draw info lines
    current_y += top_height + 8
    for line_surface in rendered_lines:
        text_x = box_x + padding_x
        screen.blit(line_surface, (text_x, current_y))
        current_y += line_surface.get_height() + 2

    # Draw small arrow pointing to agent (chatbox tail)
    arrow_x = int(agent.x)
    arrow_y = int(agent.y) - cfg.AGENT_RADIUS - 8
    pygame.draw.polygon(
        screen,
        box_color,
        [(arrow_x - 4, arrow_y), (arrow_x + 4, arrow_y), (arrow_x, arrow_y + 6)]
    )
    pygame.draw.polygon(
        screen,
        (0, 0, 0),
        [(arrow_x - 4, arrow_y), (arrow_x + 4, arrow_y), (arrow_x, arrow_y + 6)],
        1
    )


def draw_timer(screen: pygame.Surface, elapsed_time: float) -> None:
    """
    Draw elapsed time in top-left corner.
    Format: 0:23 (minutes:seconds)
    """
    font = pygame.font.Font(None, 36)
    minutes = int(elapsed_time) // 60
    seconds = int(elapsed_time) % 60
    time_text = f"{minutes}:{seconds:02d}"
    text_surface = font.render(time_text, True, (255, 255, 255))

    # Position at top-left with padding
    x, y = 15, 10

    # Draw semi-transparent background
    bg_rect = pygame.Rect(
        x - 5, y - 5, text_surface.get_width() + 10, text_surface.get_height() + 10)
    bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
    bg_surface.set_alpha(180)
    bg_surface.fill((0, 0, 0))
    screen.blit(bg_surface, (bg_rect.x, bg_rect.y))

    screen.blit(text_surface, (x, y))


def draw_population_counter(screen: pygame.Surface, population: int, max_population: int, max_generation: int = 1) -> None:
    """
    Draw population counter and max generation at top-right corner.
    Format: 20 / 20 (large font)
    Generation: 3 (smaller font below)
    """
    font_large = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 32)

    text_pop = f"{population} / {max_population}"
    text_gen = f"Gen: {max_generation}"

    text_pop_surface = font_large.render(text_pop, True, (255, 255, 255))
    text_gen_surface = font_small.render(text_gen, True, (200, 200, 200))

    # Position at top-right with padding
    x = cfg.WIDTH - max(text_pop_surface.get_width(),
                        text_gen_surface.get_width()) - 15
    y = 10

    # Calculate background height for both lines
    total_height = text_pop_surface.get_height() + text_gen_surface.get_height() + 15
    bg_width = max(text_pop_surface.get_width(),
                   text_gen_surface.get_width()) + 10

    # Draw semi-transparent background
    bg_rect = pygame.Rect(x - 5, y - 5, bg_width, total_height)
    bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
    bg_surface.set_alpha(180)
    bg_surface.fill((0, 0, 0))
    screen.blit(bg_surface, (bg_rect.x, bg_rect.y))

    # Draw population text
    screen.blit(text_pop_surface, (x, y))

    # Draw generation text beneath
    screen.blit(text_gen_surface, (x, y + text_pop_surface.get_height() + 5))


def draw_visualization_toggle_button(screen: pygame.Surface, visualization_enabled: bool) -> pygame.Rect:
    """
    Draw a toggle button for visualization mode (ON/OFF).
    Returns the button rect for click detection.
    Position: bottom-left corner
    """
    font = pygame.font.Font(None, 28)
    status = "VIS: ON" if visualization_enabled else "VIS: OFF"
    color = (100, 200, 100) if visualization_enabled else (200, 100, 100)

    text_surface = font.render(status, True, (255, 255, 255))

    # Button dimensions
    padding = 10
    button_width = text_surface.get_width() + padding * 2
    button_height = text_surface.get_height() + padding * 2

    # Position at bottom-left
    button_x = 15
    button_y = cfg.HEIGHT - button_height - 15
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Draw button background
    pygame.draw.rect(screen, color, button_rect)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)  # Border

    # Draw text
    text_x = button_x + padding
    text_y = button_y + padding
    screen.blit(text_surface, (text_x, text_y))

    return button_rect


def draw_graph_toggle_button(screen: pygame.Surface, graph_enabled: bool) -> pygame.Rect:
    """
    Draw a toggle button for graph panel (ON/OFF).
    Returns the button rect for click detection.
    Position: bottom-left, right of VIS button
    """
    font = pygame.font.Font(None, 28)
    status = "GRAPH: ON" if graph_enabled else "GRAPH: OFF"
    color = (100, 200, 100) if graph_enabled else (200, 100, 100)

    text_surface = font.render(status, True, (255, 255, 255))

    # Button dimensions
    padding = 10
    button_width = text_surface.get_width() + padding * 2
    button_height = text_surface.get_height() + padding * 2

    # Position at bottom-left, offset from VIS button
    button_x = 15 + 125  # VIS button width + gap
    button_y = cfg.HEIGHT - button_height - 15
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Draw button background
    pygame.draw.rect(screen, color, button_rect)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)  # Border

    # Draw text
    text_x = button_x + padding
    text_y = button_y + padding
    screen.blit(text_surface, (text_x, text_y))

    return button_rect


def draw_graph_panel(screen: pygame.Surface, graph_data: dict) -> None:
    """
    Draw live evolutionary graph panel on the right side.
    Displays trait evolution and population trends.
    """
    if not graph_data["times"]:
        # Show empty panel with "Collecting data..." message
        panel_width = 350
        panel_height = cfg.HEIGHT - 100
        panel_x = cfg.WIDTH - panel_width - 10
        panel_y = 10
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        bg_surface = pygame.Surface((panel_width, panel_height))
        bg_surface.set_alpha(200)
        bg_surface.fill((20, 20, 20))
        screen.blit(bg_surface, (panel_x, panel_y))
        pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)

        font_title = pygame.font.Font(None, 28)
        title_surface = font_title.render(
            "Evolution Metrics", True, (255, 255, 255))
        screen.blit(title_surface, (panel_x + 10, panel_y + 10))

        font_msg = pygame.font.Font(None, 24)
        msg = font_msg.render("Collecting data...", True, (150, 150, 150))
        msg_x = panel_x + (panel_width - msg.get_width()) // 2
        msg_y = panel_y + (panel_height - msg.get_height()) // 2
        screen.blit(msg, (msg_x, msg_y))
        return

    # Panel dimensions
    panel_width = 350
    panel_height = cfg.HEIGHT - 100
    panel_x = cfg.WIDTH - panel_width - 10
    panel_y = 10

    # Draw panel background
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    bg_surface = pygame.Surface((panel_width, panel_height))
    bg_surface.set_alpha(200)
    bg_surface.fill((20, 20, 20))
    screen.blit(bg_surface, (panel_x, panel_y))
    pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)  # Border

    # Title
    font_title = pygame.font.Font(None, 24)
    title_surface = font_title.render(
        "Evolution Metrics", True, (255, 255, 255))
    screen.blit(title_surface, (panel_x + 10, panel_y + 10))

    # Normalize data for graphing (scale to panel size)
    graph_area_height = panel_height - 60
    graph_area_width = panel_width - 20
    graph_area_x = panel_x + 10
    graph_area_y = panel_y + 35

    # Get data ranges
    times = graph_data["times"]
    if not times:
        return

    time_min, time_max = times[0], times[-1]
    time_range = time_max - time_min if time_max > time_min else 1

    # Helper function to draw a line graph
    def draw_line_graph(data_list, color, label_text, label_idx):
        if len(data_list) < 1:
            return

        # Handle single data point or constant values
        if len(data_list) == 1:
            data_min = data_list[0] * 0.9
            data_max = data_list[0] * 1.1 if data_list[0] != 0 else 1.0
        else:
            data_min = min(data_list)
            data_max = max(data_list)

        data_range = data_max - \
            data_min if (data_max - data_min) > 0.001 else 1.0

        # Draw line
        points = []
        for i, val in enumerate(data_list):
            if len(data_list) == 1:
                x = graph_area_x + graph_area_width / 2
            else:
                x = graph_area_x + (i / (len(data_list) - 1)
                                    ) * graph_area_width
            y = graph_area_y + graph_area_height - \
                ((val - data_min) / data_range * graph_area_height)
            # Ensure coordinates are integers and valid
            x_int = int(max(0, min(cfg.WIDTH, x)))
            y_int = int(max(0, min(cfg.HEIGHT, y)))
            points.append([x_int, y_int])

        # Validate and draw
        if len(points) < 1:
            return

        if len(points) >= 2:
            # Draw line by connecting consecutive points
            for i in range(len(points) - 1):
                try:
                    p1 = (int(points[i][0]), int(points[i][1]))
                    p2 = (int(points[i+1][0]), int(points[i+1][1]))
                    pygame.draw.line(screen, color, p1, p2, 3)
                except Exception as e:
                    print(f"Error drawing line segment {i}: {e}")
        elif len(points) == 1:
            # Draw a single point
            pygame.draw.circle(screen, color, tuple(points[0]), 3)
    colors = {
        "vision": (100, 200, 255),      # Blue
        "speed": (255, 200, 100),       # Orange
        "metabolism": (100, 255, 100),  # Green
        "memory": (255, 100, 200),      # Pink
        "age": (200, 150, 255)          # Light Purple
    }

    idx = 0
    for trait, color in colors.items():
        if trait in graph_data and graph_data[trait]:
            draw_line_graph(graph_data[trait], color,
                            f"Avg {trait.capitalize()}", idx)
            idx += 1

    # Draw axes (subtle, so data lines are clearly visible)
    pygame.draw.line(screen, (100, 100, 100), (graph_area_x, graph_area_y + graph_area_height),
                     # X-axis
                     (graph_area_x + graph_area_width, graph_area_y + graph_area_height), 1)
    pygame.draw.line(screen, (100, 100, 100), (graph_area_x, graph_area_y),
                     (graph_area_x, graph_area_y + graph_area_height), 1)  # Y-axis

    # Draw legend (color-coded trait names)
    legend_y = panel_y + 40
    legend_x = panel_x + 10
    font_legend = pygame.font.Font(None, 11)

    for trait, color in colors.items():
        # Draw colored square
        square_size = 8
        pygame.draw.rect(
            screen, color, (legend_x, legend_y, square_size, square_size))

        # Draw trait name next to square
        trait_text = font_legend.render(
            trait.capitalize(), True, (200, 200, 200))
        screen.blit(trait_text, (legend_x + square_size + 5, legend_y - 1))

        legend_y += 12

    # Draw population indicator (small text)
    if graph_data["population"]:
        pop = graph_data["population"][-1]
        gen = graph_data["generation"][-1] if graph_data["generation"] else 1
        font_info = pygame.font.Font(None, 14)
        pop_text = font_info.render(
            f"Pop: {int(pop)} Gen: {int(gen)}", True, (200, 200, 200))
        screen.blit(pop_text, (panel_x + 10, panel_y + panel_height - 25))


def draw_restart_button(screen: pygame.Surface) -> pygame.Rect:
    """
    Draw a manual restart button.
    Position: bottom-center
    """
    font = pygame.font.Font(None, 28)
    text_surface = font.render("RESTART", True, (255, 255, 255))

    # Button dimensions
    padding = 10
    button_width = text_surface.get_width() + padding * 2
    button_height = text_surface.get_height() + padding * 2

    # Position at bottom-center
    button_x = (cfg.WIDTH - button_width) // 2
    button_y = cfg.HEIGHT - button_height - 15
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Draw button background (red)
    pygame.draw.rect(screen, (200, 50, 50), button_rect)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)  # Border

    # Draw text
    text_x = button_x + padding
    text_y = button_y + padding
    screen.blit(text_surface, (text_x, text_y))

    return button_rect


def draw_disaster_button(screen: pygame.Surface) -> pygame.Rect:
    """
    Draw a manual disaster button.
    Position: bottom-center-right (to the right of restart button)
    """
    font = pygame.font.Font(None, 28)
    text_surface = font.render("DISASTER", True, (255, 255, 255))

    # Button dimensions
    padding = 10
    button_width = text_surface.get_width() + padding * 2
    button_height = text_surface.get_height() + padding * 2

    # Position at bottom-center-right (next to restart button)
    restart_button_x = (cfg.WIDTH - 115) // 2
    button_x = restart_button_x + 130
    button_y = cfg.HEIGHT - button_height - 15
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Draw button background (orange/yellow for disaster)
    pygame.draw.rect(screen, (200, 120, 40), button_rect)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)  # Border

    # Draw text
    text_x = button_x + padding
    text_y = button_y + padding
    screen.blit(text_surface, (text_x, text_y))

    return button_rect


def draw_reproduction_icon(screen: pygame.Surface, agents: list[ag.Agent]) -> None:
    """
    Draw love icon above agents during reproduction animation.
    """
    love_icon = _load_icon("LOVE")
    if love_icon is None:
        return

    for agent in agents:
        repro_timer = getattr(agent, "repro_animation_timer", 0.0)
        if repro_timer <= 0.0:
            continue

        # Scale icon for pulsing effect
        pulse = (1.0 - (repro_timer /
                 cfg.REPRODUCTION.get("REPRO_ANIMATION_DURATION", 1.0))) * 0.3
        scale = 1.0 + pulse

        icon_size = int(24 * scale)
        try:
            scaled_icon = pygame.transform.scale(
                love_icon, (icon_size, icon_size))
        except:
            continue

        # Draw above agent
        icon_x = int(agent.x - icon_size / 2)
        icon_y = int(agent.y - cfg.AGENT_RADIUS - 35)
        screen.blit(scaled_icon, (icon_x, icon_y))


def draw_agent_debug_panel(screen: pygame.Surface, agent: ag.Agent) -> None:
    """
    Draw debug panel in top-right showing agent effective trait values.
    Shows the actual values the agent uses (after trait multipliers applied).
    Format:
    Vision: x.xx px
    Speed: x.xx
    Metabolism: x.xx
    Memory: x.xx s
    """
    traits_obj = getattr(agent, "traits", None)
    if traits_obj is None:
        return

    # Calculate effective values
    effective_vision = tr.effective_vision(
        cfg.SENSING["VISION_RADIUS"], traits_obj)
    effective_speed = tr.effective_max_speed(
        3.5, traits_obj)  # MAX_SPEED constant
    # For metabolism, show average of the three drain rates
    avg_metabolism = (
        tr.effective_drain(cfg.RATES["HUNGER_UP"], traits_obj) +
        tr.effective_drain(cfg.RATES["THIRST_UP"], traits_obj) +
        tr.effective_drain(cfg.RATES["ENERGY_DOWN"], traits_obj)
    ) / 3.0
    effective_memory_ttl = tr.effective_memory_ttl(
        cfg.MEMORY["TIMEOUT"], traits_obj)

    # Create debug lines
    lines = [
        f"Vision: {effective_vision:.1f} px",
        f"Speed: {effective_speed:.2f}",
        f"Metabolism: {avg_metabolism:.3f}",
        f"Memory: {effective_memory_ttl:.1f} s",
        f"Generation: {getattr(agent, 'generation', 1)}",
    ]

    # Render text lines
    font = pygame.font.Font(None, 14)
    rendered_lines = [font.render(line, True, (255, 255, 255))
                      for line in lines]

    # Calculate panel size
    padding = 8
    max_width = max(line.get_width() for line in rendered_lines)
    total_height = sum(line.get_height()
                       for line in rendered_lines) + (len(rendered_lines) - 1) * 2

    panel_width = max_width + padding * 2
    panel_height = total_height + padding * 2

    # Position in top-right (below population counter)
    panel_x = cfg.WIDTH - panel_width - 10
    panel_y = 90

    # Draw panel background
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, (0, 0, 0), panel_rect)  # Black background
    pygame.draw.rect(screen, (100, 255, 100), panel_rect, 2)  # Green border

    # Draw text lines
    current_y = panel_y + padding
    for line_surface in rendered_lines:
        screen.blit(line_surface, (panel_x + padding, current_y))
        current_y += line_surface.get_height() + 2


def draw_chatbox(screen: pygame.Surface, chat_messages: list, elapsed_time: float, chat_fade_time: float = 5.0) -> None:
    """
    Draw collapsible chatbox on the bottom-left (Minecraft/RuneScape style).
    Uses same styling as graph panel: dark background (20,20,20) with alpha 200.
    Shows max 5 most recent messages with timestamps. No fading - messages stay until replaced.
    """
    # Panel dimensions
    panel_width = 300
    panel_height = 180
    panel_x = 15
    # Above buttons (approx 48px) with 15px gap
    panel_y = cfg.HEIGHT - panel_height - 65

    # Draw panel background
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    bg_surface = pygame.Surface((panel_width, panel_height))
    bg_surface.set_alpha(200)
    bg_surface.fill((20, 20, 20))  # Match graph panel color
    screen.blit(bg_surface, (panel_x, panel_y))
    pygame.draw.rect(screen, (200, 200, 200), panel_rect,
                     2)  # Match graph panel border

    # Title
    font_title = pygame.font.Font(None, 22)
    title_surface = font_title.render("Chatbox", True, (255, 255, 255))
    screen.blit(title_surface, (panel_x + 10, panel_y + 8))

    # Keep only the most recent 5 messages (no fading, always show)
    active_messages = chat_messages[-5:]

    if not active_messages:
        # Show empty message
        font_msg = pygame.font.Font(None, 16)
        msg = font_msg.render("No messages", True, (150, 150, 150))
        msg_x = panel_x + 10
        msg_y = panel_y + 45
        screen.blit(msg, (msg_x, msg_y))
        return

    # Draw messages from top to bottom (oldest at top, newest at bottom)
    font = pygame.font.Font(None, 15)
    content_start_y = panel_y + 35
    line_height = 28
    max_height = panel_height - 45

    y_offset = content_start_y
    for msg, spawn_time in active_messages:
        if y_offset - content_start_y >= max_height:
            break

        # Format message with timestamp
        time_str = f"[{spawn_time:.1f}s]"
        display_text = f"{time_str} {msg}"

        # Render text at full opacity (no fading)
        text_surface = font.render(display_text, True, (220, 220, 220))

        # Draw to screen
        screen.blit(text_surface, (panel_x + 10, y_offset))
        y_offset += line_height


def draw_chat_toggle_button(screen: pygame.Surface, chat_box_enabled: bool) -> None:
    """
    Draw chat toggle button (ON/OFF).
    Position: bottom-left, right of GRAPH button
    """
    font = pygame.font.Font(None, 28)
    status = "CHAT: ON" if chat_box_enabled else "CHAT: OFF"
    color = (100, 200, 100) if chat_box_enabled else (200, 100, 100)

    text_surface = font.render(status, True, (255, 255, 255))

    # Button dimensions
    padding = 10
    button_width = text_surface.get_width() + padding * 2
    button_height = text_surface.get_height() + padding * 2

    # Position at bottom-left, right of GRAPH button
    button_x = 15 + 125 + 180  # VIS + GRAPH widths
    button_y = cfg.HEIGHT - button_height - 15
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Draw button background
    pygame.draw.rect(screen, color, button_rect)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)  # Border

    # Draw text
    text_x = button_x + padding
    text_y = button_y + padding
    screen.blit(text_surface, (text_x, text_y))
