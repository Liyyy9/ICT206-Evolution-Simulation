"""
Metrics tracking and CSV logging for evolutionary data.
Logs per-generation statistics to CSV for long-term analysis.
"""

from __future__ import annotations
import csv
import os
from datetime import datetime
import traits as tr


class MetricsLogger:
    """Track and log evolutionary metrics per generation."""

    def __init__(self):
        self.csv_file = None
        self.csv_writer = None
        self.current_generation = 1
        self.generation_births = 0
        self.generation_deaths = 0
        self.generation_start_pop = 0
        self.last_logged_generation = 0  # Track last logged generation to avoid duplicates
        # Track disaster type for current generation
        self.current_generation_disaster = None
        # Theoretical maximum for efficiency formula (used for fixed 0-1 normalization)
        self.theoretical_max_fitness = 2.5
        self._initialized = False  # Guard against double initialization
        self._initialize_csv()

    def _initialize_csv(self):
        """Create CSV file with timestamp in csv_logs folder."""
        # Prevent multiple initializations on startup
        if self._initialized:
            return
        self._initialized = True

        # Create csv_logs folder if it doesn't exist
        log_dir = "csv_logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Generate filename with date
        date_str = datetime.now().strftime("%Y%m%d")

        # Find next available number (csv_logging_date_1.csv, _2.csv, etc.)
        counter = 1
        while True:
            filename = f"csv_logging_{date_str}_{counter}.csv"
            filepath = os.path.join(log_dir, filename)
            if not os.path.exists(filepath):
                self.csv_file = filepath
                break
            counter += 1

        # Write header
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Generation',
                'Population',
                'Avg_Age',
                'Births',
                'Deaths',
                'Avg_Vision',
                'Avg_Speed',
                'Avg_Metabolism',
                'Avg_Memory',
                'Var_Vision',
                'Var_Speed',
                'Var_Metabolism',
                'Var_Memory',
                'Avg_Fitness',
                'Disaster'
            ])

        print(f"Created metrics log: {self.csv_file}")

    def record_birth(self):
        """Increment birth counter for current generation."""
        self.generation_births += 1

    def record_death(self):
        """Increment death counter for current generation."""
        self.generation_deaths += 1

    def record_disaster(self, disaster_type: str):
        """Record disaster type for current generation."""
        self.current_generation_disaster = disaster_type

    def log_generation(self, agents: list):
        """
        Log metrics for the current generation.
        Only logs when generation actually changes (not on time interval).
        """
        if not agents:
            return

        # Get generation from agents
        max_gen = max((getattr(a, "generation", 1) for a in agents), default=1)

        # Only log if generation has changed since last log
        if max_gen <= self.last_logged_generation:
            return

        self.last_logged_generation = max_gen

        # Calculate trait statistics
        traits_list = [getattr(a, "traits", tr.Traits()) for a in agents]
        visions = [t.vision_mult for t in traits_list]
        speeds = [t.speed_mult for t in traits_list]
        metabolisms = [t.metabolism_mult for t in traits_list]
        memories = [t.memory_mult for t in traits_list]

        ages = [a.age for a in agents]

        # Calculate average fitness (simple average of 4 traits)
        avg_vision = sum(visions) / len(visions) if visions else 0
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        avg_metabolism = sum(metabolisms) / \
            len(metabolisms) if metabolisms else 0
        avg_memory = sum(memories) / len(memories) if memories else 0

        # Calculate trait variance (population genetic diversity)
        var_vision = self._calculate_variance(visions, avg_vision)
        var_speed = self._calculate_variance(speeds, avg_speed)
        var_metabolism = self._calculate_variance(metabolisms, avg_metabolism)
        var_memory = self._calculate_variance(memories, avg_memory)

        # Calculate fitness using efficiency formula: (vision + speed + memory) / 3 * (1 / metabolism)
        # Avoid division by zero
        if avg_metabolism > 0:
            raw_fitness = (avg_vision + avg_speed + avg_memory) / \
                3 * (1 / avg_metabolism)
        else:
            raw_fitness = 0

        # Normalize to 0-1 scale using fixed theoretical maximum
        # This allows fitness to start low and gradually improve toward 1.0
        avg_fitness = min(1.0, raw_fitness / self.theoretical_max_fitness)

        row = [
            max_gen,
            len(agents),
            sum(ages) / len(ages) if ages else 0,
            self.generation_births,
            self.generation_deaths,
            avg_vision,
            avg_speed,
            avg_metabolism,
            avg_memory,
            var_vision,
            var_speed,
            var_metabolism,
            var_memory,
            avg_fitness,
            self.current_generation_disaster or "N/A",
        ]

        # Append to CSV
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        # Reset counters for next generation
        self.generation_births = 0
        self.generation_deaths = 0
        self.current_generation_disaster = None

    def _calculate_variance(self, values: list, mean: float) -> float:
        """Calculate variance of a list of values."""
        if not values or len(values) < 2:
            return 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance

    def reset_for_restart(self):
        """Called when simulation restarts - creates a new CSV file."""
        # Reset counters
        self.generation_births = 0
        self.generation_deaths = 0
        self.last_logged_generation = 0
        self.current_generation_disaster = None

        # Allow a new CSV file to be created
        self._initialized = False

        # Create a new CSV file for the next restart cycle
        self._initialize_csv()


# Module-level singleton instance
_metrics_logger_instance = None


def get_metrics_logger():
    """Get or create the singleton MetricsLogger instance."""
    global _metrics_logger_instance
    if _metrics_logger_instance is None:
        _metrics_logger_instance = MetricsLogger()
    return _metrics_logger_instance
