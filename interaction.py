"""
Interaction and visualization utilities.
Handles agent state display via chatbox-style tooltips.
"""
import pygame
import config as cfg
import agent as ag

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
    Draw a chatbox-style indicator above the agent showing their state.
    Displays icon + value or "OK" text.
    """
    # Get state-based color
    box_color = get_agent_state_color(agent)
    icon_key, value_text = get_agent_state_value(agent)

    # Load icon if available
    icon_img = None
    if icon_key:
        icon_img = _load_icon(icon_key)

    # Calculate box size
    padding_x = 8
    padding_y = 6
    icon_size = 24
    text_height = 10
    gap = 6

    if icon_img and value_text != "OK":
        # Icon + value layout
        box_width = icon_size + gap + 30 + padding_x * 2  # icon + gap + value + padding
        box_height = max(icon_size, text_height) + padding_y * 2
    else:
        # Text-only layout ("OK")
        font = pygame.font.Font(None, 20)
        text_surface = font.render(value_text, True, (0, 0, 0))
        box_width = text_surface.get_width() + padding_x * 2
        box_height = text_surface.get_height() + padding_y * 2

    box_x = int(agent.x) - box_width // 2
    box_y = int(agent.y) - cfg.AGENT_RADIUS - 50

    # Draw rounded box
    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, box_color, box_rect, border_radius=4)
    pygame.draw.rect(screen, (0, 0, 0), box_rect, 2, border_radius=4)  # Border

    # Draw content
    if icon_img and value_text != "OK":
        # Draw icon (scaled to icon_size)
        scaled_icon = pygame.transform.scale(icon_img, (icon_size, icon_size))
        icon_x = box_x + padding_x
        icon_y = box_y + (box_height - icon_size) // 2
        screen.blit(scaled_icon, (icon_x, icon_y))

        # Draw value (vertically centered)
        font = pygame.font.Font(None, 20)
        text_surface = font.render(value_text, True, (0, 0, 0))
        text_x = icon_x + icon_size + gap
        text_y = box_y + (box_height - text_height) // 2
        screen.blit(text_surface, (text_x, text_y))
    else:
        # Draw "OK" text centered
        font = pygame.font.Font(None, 20)
        text_surface = font.render(value_text, True, (0, 0, 0))
        text_x = box_x + padding_x
        text_y = box_y + padding_y
        screen.blit(text_surface, (text_x, text_y))

    # Draw small arrow pointing to agent (chatbox tail)
    arrow_x = int(agent.x)
    arrow_y = int(agent.y) - cfg.AGENT_RADIUS - 12
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
