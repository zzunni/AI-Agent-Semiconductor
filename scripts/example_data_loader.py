"""
Example usage of DataLoader

This script demonstrates how to use the DataLoader class to access wafer data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.data_loader import DataLoader
import pandas as pd


def main():
    print("=" * 60)
    print("DataLoader Example Usage")
    print("=" * 60)
    print()

    # Initialize the loader
    loader = DataLoader()
    print()

    # Example 1: Load all step1 data
    print("Example 1: Load all step1 data")
    print("-" * 60)
    df = loader.load_step1_data()
    print(f"Total wafers: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print()
    print("First wafer:")
    print(df.head(1).T)
    print()

    # Example 2: Get specific wafer
    print("Example 2: Get specific wafer by ID")
    print("-" * 60)
    wafer = loader.get_wafer_by_id("W0100")
    print(f"Wafer: {wafer['wafer_id']}")
    print(f"Lot: {wafer['lot_id']}")
    print(f"Etch rate: {wafer['etch_rate']:.3f}")
    print(f"Pressure: {wafer['pressure']:.2f}")
    print(f"Temperature: {wafer['temperature']:.2f}")
    print()

    # Example 3: Get wafer with all proxy mappings
    print("Example 3: Get wafer with proxy mappings")
    print("-" * 60)
    full_data = loader.get_wafer_with_proxies("W0100")

    print("Step1 data:")
    print(f"  - Etch rate: {full_data['wafer_data']['etch_rate']:.3f}")
    print(f"  - Pressure: {full_data['wafer_data']['pressure']:.2f}")

    print("\nWM-811K proxy:")
    print(f"  - Pattern: {full_data['wm811k']['pattern_type']}")
    print(f"  - Severity: {full_data['wm811k']['severity']:.3f}")
    print(f"  - Defect density: {full_data['wm811k']['defect_density']}")

    print("\nCarinthia proxy:")
    print(f"  - Defect type: {full_data['carinthia']['defect_type']}")
    print(f"  - Defect count: {full_data['carinthia']['defect_count']}")
    print(f"  - Location: {full_data['carinthia']['location_pattern']}")
    print()

    # Example 4: Get all wafers in a lot
    print("Example 4: Get all wafers in a lot")
    print("-" * 60)
    lot_wafers = loader.get_lot_wafers("L010")
    print(f"Lot L010 has {len(lot_wafers)} wafers")
    print(f"Wafer IDs: {list(lot_wafers['wafer_id'])}")
    print()

    # Example 5: Filter wafers by conditions
    print("Example 5: Filter wafers by conditions")
    print("-" * 60)
    df = loader.load_step1_data()
    high_etch = df[df['etch_rate'] > 3.7]
    print(f"Wafers with high etch rate (>3.7): {len(high_etch)}")
    print(f"Example IDs: {list(high_etch['wafer_id'].head(5))}")
    print()

    # Example 6: Join with proxy data
    print("Example 6: Join step1 with WM-811K proxy")
    print("-" * 60)
    step1_df = loader.load_step1_data()
    wm811k_df = loader.load_wm811k_proxy()

    # Merge on wafer_id
    merged = step1_df.merge(wm811k_df, on='wafer_id', how='left')
    print(f"Merged dataset shape: {merged.shape}")
    print(f"Columns: {list(merged.columns)}")

    # Analyze patterns by etch rate
    print("\nPattern distribution by etch rate:")
    for pattern in ['Edge-Ring', 'Center', 'Random']:
        pattern_df = merged[merged['pattern_type'] == pattern]
        avg_etch = pattern_df['etch_rate'].mean()
        print(f"  {pattern}: avg etch_rate = {avg_etch:.3f}")
    print()

    print("=" * 60)
    print("✅ All examples completed!")
    print()


if __name__ == "__main__":
    main()
