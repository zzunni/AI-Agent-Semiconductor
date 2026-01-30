"""
Create Mock Model for Stage 2A: WAT Analyzer

Generates a RandomForestClassifier for LOT-level electrical quality prediction
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import os


def generate_mock_wat_data(n_lots: int = 500) -> tuple:
    """
    Generate mock WAT (Wafer Acceptance Test) data

    Args:
        n_lots: Number of LOTs to generate

    Returns:
        (X_features, y_labels)
    """
    np.random.seed(42)

    # WAT parameters (15 parameters)
    wat_params = [
        'vth_nmos', 'vth_pmos',
        'idsat_nmos', 'idsat_pmos',
        'ioff_nmos', 'ioff_pmos',
        'contact_resistance', 'sheet_resistance',
        'breakdown_voltage', 'gate_oxide_integrity',
        'dielectric_thickness', 'metal_resistance',
        'via_resistance', 'capacitance',
        'leakage_current'
    ]

    # Spec limits for each parameter (mean, std for normal operation)
    spec_params = {
        'vth_nmos': (0.45, 0.05),       # Threshold voltage
        'vth_pmos': (-0.45, 0.05),
        'idsat_nmos': (500, 50),        # Saturation current (uA)
        'idsat_pmos': (250, 25),
        'ioff_nmos': (0.1, 0.05),       # Off current (nA)
        'ioff_pmos': (0.05, 0.02),
        'contact_resistance': (50, 5),   # Ohms
        'sheet_resistance': (100, 10),
        'breakdown_voltage': (5.5, 0.3), # Volts
        'gate_oxide_integrity': (8.0, 0.5),
        'dielectric_thickness': (3.5, 0.2),
        'metal_resistance': (0.05, 0.01),
        'via_resistance': (2.0, 0.3),
        'capacitance': (10, 1),          # fF
        'leakage_current': (0.5, 0.1)    # pA
    }

    X_features = []
    y_labels = []

    for lot_idx in range(n_lots):
        # Randomly determine if this LOT is PASS or FAIL
        # 80% PASS, 20% FAIL
        is_pass = np.random.random() > 0.2

        # Generate LOT-level features (mean, std, min, max for each parameter)
        lot_features = []

        for param in wat_params:
            mean_spec, std_spec = spec_params[param]

            if is_pass:
                # Good LOT: values close to spec
                param_mean = np.random.normal(mean_spec, std_spec * 0.5)
                param_std = np.random.uniform(0, std_spec * 0.3)
            else:
                # Bad LOT: values far from spec or high variation
                if np.random.random() > 0.5:
                    # Out of spec
                    param_mean = np.random.normal(
                        mean_spec + np.random.choice([-1, 1]) * std_spec * 3,
                        std_spec
                    )
                else:
                    # High variation
                    param_mean = np.random.normal(mean_spec, std_spec * 0.7)
                param_std = np.random.uniform(std_spec * 0.5, std_spec * 2)

            # Generate min/max based on mean and std
            param_min = param_mean - 2 * param_std
            param_max = param_mean + 2 * param_std

            # Features: mean, std, min, max
            lot_features.extend([param_mean, param_std, param_min, param_max])

        X_features.append(lot_features)
        y_labels.append(1 if is_pass else 0)

    return np.array(X_features), np.array(y_labels)


def create_stage2a_model():
    """Create and save mock Stage 2A model"""

    print("=" * 60)
    print("Creating Mock Model for Stage 2A: WAT Analyzer")
    print("=" * 60)

    # Generate training data
    print("\n1. Generating mock WAT data...")
    X, y = generate_mock_wat_data(n_lots=500)

    print(f"   Generated {len(X)} LOT samples")
    print(f"   Features: {X.shape[1]} (15 params × 4 statistics)")
    print(f"   PASS LOTs: {sum(y == 1)} ({sum(y == 1)/len(y)*100:.1f}%)")
    print(f"   FAIL LOTs: {sum(y == 0)} ({sum(y == 0)/len(y)*100:.1f}%)")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    print("\n2. Training RandomForestClassifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    )

    model.fit(X_train, y_train)

    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)

    print(f"   Training accuracy: {train_score:.3f}")
    print(f"   Test accuracy: {test_score:.3f}")

    # Feature importance (top 10)
    feature_names = []
    param_names = [
        'vth_nmos', 'vth_pmos', 'idsat_nmos', 'idsat_pmos',
        'ioff_nmos', 'ioff_pmos', 'contact_resistance', 'sheet_resistance',
        'breakdown_voltage', 'gate_oxide_integrity', 'dielectric_thickness',
        'metal_resistance', 'via_resistance', 'capacitance', 'leakage_current'
    ]
    stat_names = ['mean', 'std', 'min', 'max']

    for param in param_names:
        for stat in stat_names:
            feature_names.append(f"{param}_{stat}")

    importances = model.feature_importances_
    top_features = sorted(
        zip(feature_names, importances),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    print("\n   Top 10 important features:")
    for feat, imp in top_features:
        print(f"     {feat}: {imp:.4f}")

    # Save model
    print("\n3. Saving model...")
    os.makedirs('models', exist_ok=True)
    model_path = 'models/stage2a_wat_classifier.pkl'

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    print(f"   ✓ Model saved to: {model_path}")
    print(f"   ✓ Model size: {os.path.getsize(model_path) / 1024:.1f} KB")

    print("\n" + "=" * 60)
    print("✅ Stage 2A Mock Model Created Successfully!")
    print("=" * 60)
    print("\nModel Details:")
    print(f"  Type: RandomForestClassifier")
    print(f"  Trees: 100")
    print(f"  Input: 60 features (15 WAT params × 4 statistics)")
    print(f"  Output: Binary classification (PASS/FAIL)")
    print(f"  Accuracy: {test_score:.1%}")
    print("\nNext Steps:")
    print("  1. Run: python scripts/test_stage2a_agent.py")
    print("  2. Integrate Stage 2A into pipeline")
    print("=" * 60)


if __name__ == "__main__":
    create_stage2a_model()
