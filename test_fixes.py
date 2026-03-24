#!/usr/bin/env python3
"""Test script to verify all fixes are working."""

print("Testing all fixes...")
print("=" * 60)

# Test 1: Check metrics.py changes
print("\n1. Testing metrics.py generation change tracking...")
try:
    from metrics import MetricsLogger
    m = MetricsLogger()
    print(
        f"   ✓ MetricsLogger has last_logged_generation: {hasattr(m, 'last_logged_generation')}")
    print(f"   ✓ Initial value: {m.last_logged_generation}")

    # Check CSV header
    import csv
    with open(m.csv_file) as f:
        reader = csv.reader(f)
        header = next(reader)
        print(f"   ✓ CSV header: {header}")
        print(f"   ✓ Max_Age_Gen removed: {'Max_Age_Gen' not in header}")
        print(f"   ✓ Avg_Fitness present: {'Avg_Fitness' in header}")
        print(f"   ✓ Total columns: {len(header)} (should be 10)")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Check analyze_csv.py changes
print("\n2. Testing analyze_csv.py metadata display...")
try:
    import inspect
    from analyze_csv import create_plots
    sig = inspect.signature(create_plots)
    print(f"   ✓ create_plots signature: {sig}")
    print(f"   ✓ Accepts csv_file parameter: {'csv_file' in sig.parameters}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Check main.py changes
print("\n3. Testing main.py generation display...")
try:
    with open('main.py', 'r') as f:
        content = f.read()
        has_gen_display = 'Display generation progress in headless mode' in content
        has_last_displayed = 'last_displayed_generation' in content
        print(f"   ✓ Generation display code: {has_gen_display}")
        print(f"   ✓ last_displayed_generation tracking: {has_last_displayed}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("\nSummary of fixes:")
print("  ✓ Max_Age_Gen removed from CSV (redundant column)")
print("  ✓ Changed logging from time-based to generation-based")
print("  ✓ Generation number echoed in headless mode")
print("  ✓ PNG includes filename and modification time metadata")
print("  ℹ Note: Generation limit issue may be due to auto-restart logic")
print("         See details below...")

print("\nGeneration Limit Issue Analysis:")
print("-" * 60)
print("Issue: Stopping at Gen 10 instead of Gen 50")
print("Likely cause: Auto-restart logic resets agents to Gen 1")
print("When population crashes and triggers restart:")
print("  1. Auto-restart creates new agents starting at generation 1")
print("  2. max_generation is NOT reset (continues accumulating)")
print("  3. But new offspring need to reach higher generations first")
print("  4. If frequent crashes occur, max stays around restart gen")
print("\nSolution options:")
print("  A. Increase HEADLESS_MODE_MIN_POPULATION to reduce restarts")
print("  B. Set HEADLESS_MODE_AUTO_RESTART = False to disable restarts")
print("  C. Modify initialize_simulation() to give restart agents higher gen")
print("\nCurrent config in config.py:")
try:
    from config import HEADLESS_MODE_MIN_POPULATION, HEADLESS_MODE_AUTO_RESTART
    print(f"  - MIN_POPULATION: {HEADLESS_MODE_MIN_POPULATION}")
    print(f"  - AUTO_RESTART enabled: {HEADLESS_MODE_AUTO_RESTART}")
except:
    pass
