import random
from dataclasses import dataclass


@dataclass
class Agent:
    x: float
    y: float
    velocityX: float
    velocityY: float

    # internal state
    age: int = 0
    hunger: float = 0.0
    thirst: float = 0.0
    energy: float = 100.0
    health: float = 100.0
    
    alive: bool = True
    dying: bool = False
    dying_progress: float = 0.0


def create_agent(width: int, height: int, radius: int) -> Agent:
    return Agent(
        x=float(random.randint(radius, width - radius)),
        y=float(random.randint(radius, height - radius)),
        velocityX=float(random.choice([-2, -1, 1, 2])),
        velocityY=float(random.choice([-2, -1, 1, 2]))
    )


def update_internal_state(agent, dt: float):
    if not agent.alive:
        return

    #If dying
    if agent.dying:
        DYING_SECONDS = 1.5
        agent.dying_progress += dt / DYING_SECONDS

        if agent.dying_progress >= 1.0:
            agent.dying_progress = 1.0
            agent.alive = False
            agent.dying = False
            agent.velocityX = 0
            agent.velocityY = 0
        return

    # Normal living updates
    agent.age += 1
    agent.hunger += 0.07
    agent.thirst += 0.05
    agent.energy -= 0.02

    if agent.energy <= 0:
        agent.energy = 0
        agent.alive = False
        
    if agent.health <= 0 or agent.hunger >= 100 or agent.thirst >= 100 or agent.energy <= 0:
        start_dying(agent)
        
def start_dying(agent):
    if agent.dying or not agent.alive:
        return
    agent.dying = True
    agent.dying_progress = 0.0

