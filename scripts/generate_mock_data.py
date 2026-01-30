"""
Generate mock data for development
This will be replaced with real data from STEP teams later
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def generate_step1_data(n_wafers=1252):
    """
    Generate mock step1_data.csv
    Simulates 1,252 wafers with 10 sensors
    """
    np.random.seed(42)

    data = []
    start_date = datetime(2026, 1, 10, 8, 0, 0)

    for i in range(n_wafers):
        wafer_id = f"W{i+1:04d}"
        lot_id = f"L{(i // 25) + 1:03d}"  # 25 wafers per lot

        # Simulate sensor values with some anomalies
        is_anomaly = np.random.random() < 0.15  # 15% anomalies

        if is_anomaly:
            etch_rate = np.random.uniform(3.7, 4.2)  # High
            pressure = np.random.uniform(158, 165)   # High
        else:
            etch_rate = np.random.uniform(3.2, 3.6)  # Normal
            pressure = np.random.uniform(145, 155)   # Normal

        data.append({
            'wafer_id': wafer_id,
            'lot_id': lot_id,
            'recipe': 'Etch_v3.2',
            'chamber': np.random.choice(['A', 'B', 'C']),
            'timestamp': (start_date + timedelta(minutes=i*15)).isoformat(),
            'etch_rate': etch_rate,
            'pressure': pressure,
            'temperature': np.random.uniform(58, 63),
            'rf_power': np.random.uniform(1800, 1900),
            'gas_flow': np.random.uniform(235, 255),
            'sensor6': np.random.uniform(10, 15),
            'sensor7': np.random.uniform(0.8, 0.95),
            'sensor8': np.random.uniform(40, 45),
            'sensor9': np.random.uniform(17, 20),
            'sensor10': np.random.uniform(3.0, 3.5)
        })

    df = pd.DataFrame(data)
    os.makedirs('data/inputs', exist_ok=True)
    df.to_csv('data/inputs/step1_data.csv', index=False)
    print(f"✅ Generated step1_data.csv: {len(df)} wafers")
    return df


def generate_wm811k_proxy(step1_df):
    """
    Generate mock wm811k_proxy.csv
    Maps wafers to wafermap patterns
    """
    data = []

    for _, row in step1_df.iterrows():
        # Rule-based pattern assignment
        if row['etch_rate'] > 3.7:
            pattern_type = 'Edge-Ring'
            severity = np.random.uniform(0.7, 0.9)
        elif row['etch_rate'] < 3.3:
            pattern_type = 'Center'
            severity = np.random.uniform(0.5, 0.7)
        else:
            pattern_type = 'Random'
            severity = np.random.uniform(0.3, 0.6)

        data.append({
            'wafer_id': row['wafer_id'],
            'matched_wm811k_id': f"WM_{np.random.randint(10000, 99999)}",
            'pattern_type': pattern_type,
            'severity': severity,
            'defect_density': int(100 + severity * 300),
            'confidence': np.random.uniform(0.65, 0.85)
        })

    df = pd.DataFrame(data)
    df.to_csv('data/inputs/wm811k_proxy.csv', index=False)
    print(f"✅ Generated wm811k_proxy.csv: {len(df)} mappings")
    return df


def generate_carinthia_proxy(step1_df):
    """
    Generate mock carinthia_proxy.csv
    Maps wafers to SEM defect types
    """
    data = []

    for _, row in step1_df.iterrows():
        # Rule-based defect assignment
        if row['pressure'] > 158:
            defect_type = 'Particle'
            location_pattern = 'edge'
        elif row['temperature'] > 62:
            defect_type = 'Residue'
            location_pattern = 'center'
        else:
            defect_type = np.random.choice(['Particle', 'Scratch', 'Residue'])
            location_pattern = np.random.choice(['edge', 'center', 'random'])

        data.append({
            'wafer_id': row['wafer_id'],
            'matched_carinthia_id': f"CARIN_{np.random.randint(100, 999):03d}",
            'defect_type': defect_type,
            'defect_count': np.random.randint(5, 30),
            'location_pattern': location_pattern,
            'confidence': np.random.uniform(0.7, 0.9)
        })

    df = pd.DataFrame(data)
    df.to_csv('data/inputs/carinthia_proxy.csv', index=False)
    print(f"✅ Generated carinthia_proxy.csv: {len(df)} mappings")
    return df


if __name__ == "__main__":
    print("🔧 Generating mock data for development...")
    print("⚠️  This will be replaced with real data from STEP teams later\n")

    step1_df = generate_step1_data()
    wm811k_df = generate_wm811k_proxy(step1_df)
    carinthia_df = generate_carinthia_proxy(step1_df)

    print("\n✅ All mock data generated!")
    print("📁 Files created in data/inputs/")
    print("   - step1_data.csv")
    print("   - wm811k_proxy.csv")
    print("   - carinthia_proxy.csv")
