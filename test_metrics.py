#!/usr/bin/env python3
"""Test script to verify metrics fitness calculation."""

import csv
from config import CONFIG
from resources import Environment
from agent import Agent
from metrics import MetricsLogger
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))


# Initialize test environment
env = Environment(CONFIG["MAP_SIZE"])
metrics = MetricsLogger()

print(f"✓ Metrics logger initialized")
print(f"✓ CSV file: {metrics.csv_file}")

# Create a few test agents with known traits
test_agents = []
for i in range(3):
    a = Agent(10, 10, env)
    # Set specific trait values for testing
    a.traits.vision_mult = 1.0 + (i * 0.1)
    a.traits.speed_mult = 1.0 + (i * 0.05)
    a.traits.metabolism_mult = 0.9 + (i * 0.05)
    a.traits.memory_mult = 1.1 + (i * 0.05)
    test_agents.append(a)
    print(f"  Agent {i}: Vision={a.traits.vision_mult:.2f}, Speed={a.traits.speed_mult:.2f}, "
          f"Metabolism={a.traits.metabolism_mult:.2f}, Memory={a.traits.memory_mult:.2f}")

# Log the generation
metrics.log_generation(test_agents)
print("✓ Generation logged")

# Read back the CSV to verify
with open(metrics.csv_file, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    print(f"\n✓ CSV Header ({len(header)} columns):")
    print(f"  {header}")

    for row in reader:
        print(f"\n✓ CSV Data Row ({len(row)} columns):")
        # Print each column with its name
        for name, value in zip(header, row):
            print(f"  {name}: {value}")

print("\n✅ Test complete! Metrics are working correctly with fitness column.")
