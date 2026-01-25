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

    # Position in top-right
    panel_x = cfg.WIDTH - panel_width - 10
    panel_y = 10

    # Draw panel background
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, (0, 0, 0), panel_rect)  # Black background
    pygame.draw.rect(screen, (100, 255, 100), panel_rect, 2)  # Green border

    # Draw text lines
    current_y = panel_y + padding
    for line_surface in rendered_lines:
        screen.blit(line_surface, (panel_x + padding, current_y))
        current_y += line_surface.get_height() + 2
