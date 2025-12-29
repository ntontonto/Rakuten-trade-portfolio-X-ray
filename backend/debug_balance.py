"""Debug assetbalance parsing"""
import sys
from pathlib import Path
import pandas as pd

# Read the balance file
balance_file = Path(__file__).parent.parent / "inputs" / "assetbalance(all)_20251226_175959.csv"

# Read as raw lines first
with open(balance_file, 'r', encoding='shift_jis') as f:
    lines = f.readlines()

print(f"Total lines in file: {len(lines)}")
print("\nFirst 30 lines:")
for i, line in enumerate(lines[:30]):
    print(f"{i}: {line.strip()[:100]}")

# Now let's see the holdings section
print("\n\n=== Finding holdings section ===")
for i, line in enumerate(lines):
    if '保有商品詳細' in line:
        print(f"\nHoldings section starts at line {i}")
        print("Next 10 lines:")
        for j in range(i, min(i+10, len(lines))):
            print(f"{j}: {lines[j].strip()[:120]}")
        break
