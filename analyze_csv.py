"""
Post-simulation analysis script.
Reads CSV logs from csv_logs folder and generates matplotlib plots
showing evolutionary trends over time.
"""
import csv
import os
import sys
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def load_csv_data(csv_file):
    """Load data from a CSV file."""
    data = defaultdict(list)

    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse numeric values
                data["generation"].append(int(row.get("Generation", 0)))
                data["population"].append(int(row.get("Population", 0)))
                data["births"].append(int(row.get("Births", 0)))
                data["deaths"].append(int(row.get("Deaths", 0)))

                # Trait data
                avg_vision = float(row.get("Avg_Vision", 0))
                avg_speed = float(row.get("Avg_Speed", 0))
                avg_metabolism = float(row.get("Avg_Metabolism", 0))
                avg_memory = float(row.get("Avg_Memory", 0))

                data["avg_vision"].append(avg_vision)
                data["avg_speed"].append(avg_speed)
                data["avg_metabolism"].append(avg_metabolism)
                data["avg_memory"].append(avg_memory)

                # Trait variance data (population genetic diversity)
                var_vision = float(row.get("Var_Vision", 0))
                var_speed = float(row.get("Var_Speed", 0))
                var_metabolism = float(row.get("Var_Metabolism", 0))
                var_memory = float(row.get("Var_Memory", 0))

                data["var_vision"].append(var_vision)
                data["var_speed"].append(var_speed)
                data["var_metabolism"].append(var_metabolism)
                data["var_memory"].append(var_memory)

                # Fitness score: use from CSV if available, else calculate from traits
                if "Avg_Fitness" in reader.fieldnames:
                    avg_fitness = float(row.get("Avg_Fitness", 0))
                else:
                    # Backward compatibility: calculate fitness from traits
                    avg_fitness = (avg_vision + avg_speed +
                                   avg_metabolism + avg_memory) / 4

                data["avg_fitness"].append(avg_fitness)

                # Age data
                data["avg_age"].append(float(row.get("Avg_Age", 0)))

        return data
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None


def find_latest_csv():
    """Find the most recent CSV file in csv_logs folder by modification time."""
    csv_dir = Path("csv_logs")
    if not csv_dir.exists():
        print("csv_logs folder not found!")
        return None

    csv_files = list(csv_dir.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in csv_logs folder!")
        return None

    # Sort by modification time (most recent last)
    return max(csv_files, key=lambda p: p.stat().st_mtime)


def find_all_csvs_by_date(date_str=None):
    """Find all CSV files from a specific date. If date_str is None, uses today's date."""
    from datetime import datetime as dt

    csv_dir = Path("csv_logs")
    if not csv_dir.exists():
        return []

    if date_str is None:
        date_str = dt.now().strftime("%Y%m%d")

    # Find all files matching the date pattern
    pattern = f"csv_logging_{date_str}_*.csv"
    matching_files = sorted(csv_dir.glob(pattern),
                            # Sort by numeric suffix
                            key=lambda p: int(p.stem.split('_')[-1]))
    return matching_files


def merge_csv_data(csv_files):
    """Merge data from multiple CSV files into one continuous dataset."""
    merged_data = defaultdict(list)
    generation_offset = 0

    for csv_file in csv_files:
        data = load_csv_data(csv_file)
        if not data or not data["generation"]:
            continue

        # Offset generation numbers so they don't overlap between restarts
        if merged_data["generation"]:
            generation_offset = max(merged_data["generation"])

        for key in data:
            if key == "generation":
                # Offset generations from this file
                merged_data[key].extend(
                    [g + generation_offset for g in data[key]])
            else:
                merged_data[key].extend(data[key])

    return dict(merged_data)


def create_plots(data, csv_file=None):
    """Create matplotlib plots from the data."""
    if not data or not data["generation"]:
        print("No data to plot!")
        return

    # Define output file path
    output_file = "evolution_analysis.png"

    # Use generation count as x-axis
    x = data["generation"]

    # Create a 2x3 subplot layout
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # Add metadata to title
    if csv_file:
        csv_filename = Path(csv_file).name
        title_text = f"Evolution Simulator Analysis - {csv_filename}"
    else:
        title_text = "Evolution Simulator Analysis"

    fig.suptitle(title_text, fontsize=16, fontweight='bold')

    # Plot 1: Population Growth
    ax = axes[0, 0]
    ax.plot(x, data["population"], color='blue', linewidth=2, label='Population')
    # Add carrying capacity reference line
    ax.axhline(y=10000, color='red', linestyle='--', linewidth=1.5, label='Population Ceiling (10k)')
    ax.set_ylabel("Population", fontsize=10, fontweight='bold')
    ax.set_xlabel("Generation")
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_title("Population Growth")
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Plot 2: Average Trait Evolution
    ax = axes[0, 1]
    ax.plot(x, data["avg_vision"], color='blue', linewidth=2, label='Vision')
    ax.plot(x, data["avg_speed"], color='orange', linewidth=2, label='Speed')
    ax.plot(x, data["avg_metabolism"], color='green',
            linewidth=2, label='Metabolism')
    ax.plot(x, data["avg_memory"], color='pink', linewidth=2, label='Memory')
    ax.set_ylabel("Trait Multiplier", fontsize=10, fontweight='bold')
    ax.set_xlabel("Generation")
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_title("Average Trait Evolution")
    ax.set_ylim([0.6, 1.5])
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Plot 3: Fitness Score
    ax = axes[0, 2]
    ax.plot(x, data["avg_fitness"], color='purple', linewidth=2.5)
    ax.set_ylabel("Fitness Score", fontsize=10, fontweight='bold')
    ax.set_xlabel("Generation")
    ax.grid(True, alpha=0.3)
    ax.set_title("Average Population Fitness")
    ax.set_ylim([0, 1])
    ax.fill_between(x, data["avg_fitness"], alpha=0.3, color='purple')
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Plot 4: Lifespan Evolution
    ax = axes[1, 0]
    ax.plot(x, data["avg_age"], color='red', linewidth=2)
    ax.set_ylabel("Age (seconds)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Generation")
    ax.grid(True, alpha=0.3)
    ax.set_title("Average Lifespan")
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Plot 5: Population Trait Variance (genetic diversity)
    ax = axes[1, 1]

    # Calculate combined variance (average of all trait variances)
    if len(data["var_vision"]) > 0:
        combined_var = [(v + s + me + ma) / 4 for v, s, me, ma in
                        zip(data["var_vision"], data["var_speed"], data["var_metabolism"], data["var_memory"])]

        # Plot individual trait variances
        ax.plot(x, data["var_vision"], color='blue',
                linewidth=2, label='Vision', alpha=0.7)
        ax.plot(x, data["var_speed"], color='orange',
                linewidth=2, label='Speed', alpha=0.7)
        ax.plot(x, data["var_metabolism"], color='green',
                linewidth=2, label='Metabolism', alpha=0.7)
        ax.plot(x, data["var_memory"], color='pink',
                linewidth=2, label='Memory', alpha=0.7)

        # Plot combined variance
        ax.plot(x, combined_var, color='red', linewidth=2.5,
                label='Average', linestyle='--')

    ax.set_ylabel("Trait Variance (population diversity)",
                  fontsize=10, fontweight='bold')
    ax.set_xlabel("Generation")
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_title("Population Trait Variance (Genetic Diversity)")
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Plot 6: Population vs Fitness Correlation
    ax = axes[1, 2]
    ax.plot(x, data["population"], color='blue',
            linewidth=2, label='Population')
    ax2 = ax.twinx()
    ax2.plot(x, data["avg_fitness"], color='purple',
             linewidth=2, label='Fitness', linestyle='--')
    ax.set_ylabel("Population", fontsize=10, fontweight='bold', color='blue')
    ax2.set_ylabel("Fitness Score", fontsize=10,
                   fontweight='bold', color='purple')
    ax2.set_ylim([0, 1])
    ax.set_xlabel("Generation")
    ax.grid(True, alpha=0.3)
    ax.set_title("Population vs Fitness Trend")
    ax.tick_params(axis='y', labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='purple')
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Add metadata footer with elapsed time
    if csv_file:
        csv_path = Path(csv_file)
        # Get file modification time
        import time
        mod_time = time.ctime(csv_path.stat().st_mtime)
        # Add text box with metadata
        metadata_text = f"File: {csv_path.name}\nGenerated: {mod_time}"
        fig.text(0.99, 0.01, metadata_text, ha='right', va='bottom',
                 fontsize=8, style='italic', alpha=0.7,
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Plot saved as '{output_file}'")

    # Display summary statistics
    if data["generation"]:
        print("\n" + "="*50)
        print("EVOLUTION SUMMARY")
        print("="*50)
        print(f"Final Generation: {int(data['generation'][-1])}")
        print(f"Final Population: {data['population'][-1]}")
        print(f"Max Population: {max(data['population'])}")
        print(f"\nFinal Trait Averages:")
        print(
            f"  Vision:      {data['avg_vision'][-1]:.3f} (started: {data['avg_vision'][0]:.3f})")
        print(
            f"  Speed:       {data['avg_speed'][-1]:.3f} (started: {data['avg_speed'][0]:.3f})")
        print(
            f"  Metabolism:  {data['avg_metabolism'][-1]:.3f} (started: {data['avg_metabolism'][0]:.3f})")
        print(
            f"  Memory:      {data['avg_memory'][-1]:.3f} (started: {data['avg_memory'][0]:.3f})")

        # Display fitness info
        if data["avg_fitness"]:
            fitness_final = data['avg_fitness'][-1]
            fitness_start = data['avg_fitness'][0]
            print(f"\nAverage Fitness:")
            print(
                f"  Current:     {fitness_final:.3f} (started: {fitness_start:.3f})")
            print(
                f"  Min/Max:     {min(data['avg_fitness']):.3f} / {max(data['avg_fitness']):.3f}")

        # Display lifespan info
        avg_lifespan_final = data['avg_age'][-1] if data['avg_age'] else 0
        avg_lifespan_start = data['avg_age'][0] if data['avg_age'] else 0
        print(f"\nAverage Lifespan:")
        print(
            f"  Current:     {avg_lifespan_final:.2f}s (started: {avg_lifespan_start:.2f}s)")
        if data['avg_age']:
            print(
                f"  Min/Max:     {min(data['avg_age']):.2f}s / {max(data['avg_age']):.2f}s")

        print(f"\nReproduction:")
        print(f"  Total Births: {sum(data['births'])}")
        print(f"  Total Deaths: {sum(data['deaths'])}")
        # Calculate B/D ratios
        total_births = sum(data['births'])
        total_deaths = sum(data['deaths'])
        if total_deaths > 0:
            overall_ratio = total_births / total_deaths
            print(f"  Overall B/D Ratio: {overall_ratio:.3f}")
        # Calculate per-generation ratios
        ratios = []
        for b, d in zip(data['births'], data['deaths']):
            if d > 0:
                ratios.append(b / d)
        if ratios:
            print(
                f"  Avg Gen B/D Ratio: {sum(ratios) / len(ratios):.3f} (target: 1.0)")
        print("="*50 + "\n")

    plt.show()


def main():
    """Main entry point."""
    print("Evolution Simulator CSV Analysis Tool")
    print("="*50)

    # Determine which CSV to load
    if len(sys.argv) > 1:
        # User specified a file
        csv_file = Path(sys.argv[1])
    else:
        # Auto-detect: Find the latest CSV file by modification time
        csv_file = find_latest_csv()

    if not csv_file or not csv_file.exists():
        print(f"CSV file not found: {csv_file}")
        return

    print(f"Loading data from: {csv_file.name}")
    data = load_csv_data(csv_file)

    if data and data["generation"]:
        print(f"[OK] Loaded {len(data['generation'])} time samples\n")
        create_plots(data, csv_file)
    else:
        print("[ERROR] Failed to load data or file is empty")


if __name__ == "__main__":
    main()
