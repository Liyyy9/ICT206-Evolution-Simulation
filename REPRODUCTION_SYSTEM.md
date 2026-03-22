# Reproduction System Implementation

## Overview
A complete partner-seeking and reproduction system has been integrated into the agent-based evolution simulator. Agents can now form pairs, reproduce, and pass inherited traits to their offspring.

## Features Implemented

### 1. **Mate-Seeking State (SEEK_MATE)**
- Agents enter `SEEK_MATE` state when:
  - Age ≥ 25 seconds
  - Hunger < HUNGER_SEEK threshold
  - Thirst < THIRST_SEEK threshold
  - Not on reproduction cooldown
  
- Agents abort `SEEK_MATE` if:
  - Hunger rises above HUNGER_SEEK
  - Thirst rises above THIRST_SEEK
  - 5-second timeout expires with no successful mating

### 2. **Mate Finding & Reproduction**
- **Mate Search**: Agents find the closest other agent also in SEEK_MATE state
- **Proximity Check**: Reproduction attempt when agents within 50px
- **Success Rate**: 70% probability of successful reproduction (configurable)
- **Cooldown**: Both parents enter 15-second cooldown after reproduction
- **Energy Cost**: 20 energy points drained from each parent

### 3. **Offspring Creation**
- **Trait Inheritance**: Child inherits averaged trait multipliers from both parents:
  - `vision_mult`: Average of both parents' vision_mult
  - `speed_mult`: Average of both parents' speed_mult
  - `metabolism_mult`: Average of both parents' metabolism_mult
  - `memory_mult`: Average of both parents' memory_mult
  - All inherited traits clamped to valid ranges
  
- **Color Inheritance**: Child color is RGB average of parents (0-255 per channel)
- **Spawn Location**: Spawned within 30px of parent midpoint
- **Starting Stats**: Inherits all default agent values

## Configuration
Settings in `config.py` under `REPRODUCTION` dict:
```python
REPRODUCTION = {
    "MIN_MATE_AGE": 25.0,                    # seconds
    "REPRODUCTION_PROBABILITY": 0.7,         # 70% success rate
    "MATE_RADIUS": 50.0,                     # pixels
    "MATE_SEEK_TIMEOUT": 5.0,                # seconds before giving up
    "REPRO_COOLDOWN": 15.0,                  # seconds before mating again
    "REPRO_ENERGY_COST": 20.0,               # energy per parent
    "SPAWN_OFFSET_RANGE": 30.0,              # pixels from midpoint
}
```

## Module Structure

### `reproduction.py` (New)
Core reproduction logic:
- `is_eligible_for_mate_seeking(agent)` - Checks eligibility criteria
- `should_abort_mate_seeking(agent)` - Checks abort conditions
- `find_closest_mate(agent, agents)` - Locates nearest seeking agent
- `attempt_reproduction(parent_a, parent_b)` - Handles reproduction roll & outcome
- `make_child(parent_a, parent_b)` - Creates offspring with inheritance

### `agent.py` (Modified)
Added fields to `Agent` dataclass:
- `mate_seek_timer: float = 0.0` - Countdown for SEEK_MATE timeout
- `repro_cooldown: float = 0.0` - Cooldown after reproduction

### `simulation.py` (Modified)
Integration points:
- Import reproduction module
- Update cooldown timers each frame:
  - `repro_cooldown` decrements each frame
  - `mate_seek_timer` decrements each frame
- SEEK_MATE state management:
  - Check eligibility each frame
  - Abort if survival needs become critical
  - Timeout if no mate found
- Mate-seeking movement: Agents wander (not targeted steering) while SEEK_MATE
- `process_reproduction(agents)` function:
  - Called after all agents update
  - Returns list of newborn children
  - Automatically appended to agent population

### `config.py` (Modified)
Added `REPRODUCTION` configuration dict with 7 tunable parameters.

### `traits.py` (Modified)
Added trait range constants used by inheritance:
- `VISION_MULT_RANGE = (0.7, 1.4)`
- `SPEED_MULT_RANGE = (0.7, 1.4)`
- `METABOLISM_MULT_RANGE = (0.7, 1.3)`
- `MEMORY_MULT_RANGE = (0.7, 1.5)`

Added `clamp_trait(value, range_tuple)` utility function.

### `interaction.py` (Modified)
UI enhancement:
- Updated `get_agent_state_value()` to detect SEEK_MATE action
- Shows love icon (♥) in chatbox when agent is seeking mate
- Icon displays ahead of hunger/thirst indicators

### `main.py` (Modified)
Reproduction integration:
- Call `sim.process_reproduction(agents)` after all agents update
- Extends agent list with newborns each frame
- Newborns automatically spawn and begin first frame of life

## Behavior Flow

```
Agent Life Cycle (with reproduction):
    ↓
    Survival Phase (eating, drinking, wandering)
    ↓
    [If age >= 25s AND hunger/thirst below SEEK thresholds]
    ↓
    Enter SEEK_MATE state
    ↓
    [If hunger/thirst rises above SEEK → abort, return to survival]
    ↓
    Wander while seeking nearby agents also in SEEK_MATE
    ↓
    [If mate found within 50px and within 5 seconds]
    ↓
    Reproduction Attempt (70% success rate)
    ↓
    [Success] → Spawn child, apply cooldowns + energy cost
    [Failure] → Continue seeking (no penalty)
    ↓
    [If 5 seconds pass without mate] → Return to WANDER
    ↓
    Repeat from survival phase
```

## Game Mechanics

### Trait Evolution
- **No Mutation**: Children are exact averages, no randomization
- **Blending Inheritance**: Traits blend smoothly from parents
- **Natural Selection**: Only agents that survive long enough reproduce
- **Color Gradient**: Visual representation of genetic lineage

### Population Dynamics
- **Birth**: Increases population when mating successful
- **Selective Reproduction**: Only well-fed, adequately hydrated agents mate
- **Cooldown Spacing**: Prevents population explosion; 15s between matings
- **Energy Investment**: Reproduction costs energy, pressures survival balance

## Testing & Validation

✅ **All Syntax Checks Pass**
- reproduction.py: Clean
- agent.py: Clean
- simulation.py: Clean
- config.py: Clean
- interaction.py: Clean
- traits.py: Clean
- main.py: Clean

✅ **Functional Testing**
- Mate eligibility checks work correctly
- Child creation produces proper trait averaging
- Color inheritance blends RGB channels
- Spawn location offset applies properly
- Cooldown timers decrement each frame

## Next Steps (Future Enhancements)

1. **Mutation System**: Add small random variations during inheritance
2. **Fitness Tracking**: Track traits and survival success per lineage
3. **Sexual Dimorphism**: Add male/female mechanics
4. **Genetic Analysis**: Display population trait statistics
5. **Inheritance Visualization**: Show family trees or genetic maps
6. **Mating Displays**: Add visual indicators of mating pairs
7. **Reproduction Strategy**: Evolve mate-seeking behavior itself

## Configuration Tuning Tips

- **Lower MIN_MATE_AGE**: More population turnover, shorter generations
- **Increase REPRODUCTION_PROBABILITY**: More births, faster population growth
- **Increase MATE_RADIUS**: Easier to find mates, more births
- **Decrease MATE_SEEK_TIMEOUT**: Agents give up faster, more wandering
- **Decrease REPRO_COOLDOWN**: More frequent reproduction
- **Increase REPRO_ENERGY_COST**: Reproduction more expensive, harder to reproduce quickly
