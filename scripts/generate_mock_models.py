"""
Generate mock models for development
These will be replaced with real models from STEP teams later
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from src.models.mock_models import MockXGBoostModel, MockCNNModel, MockResNetModel


def generate_mock_models():
    """Generate all mock models"""
    os.makedirs('models', exist_ok=True)

    # Stage 0: Isolation Forest (can use real sklearn)
    print("Generating Stage 0 model (Isolation Forest)...")
    iso_forest = IsolationForest(contamination=0.15, random_state=42)

    # Fit on random data just to have a trained model
    # 10 features to match sensor data
    X_dummy = np.random.randn(1000, 10)
    iso_forest.fit(X_dummy)

    with open('models/stage0_isolation_forest.pkl', 'wb') as f:
        pickle.dump(iso_forest, f)
    print("✅ Stage 0 model saved (Isolation Forest)")

    # Also save scaler
    scaler = StandardScaler()
    scaler.fit(X_dummy)
    with open('models/stage0_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print("✅ Stage 0 scaler saved")

    # Stage 1: XGBoost
    print("Generating Stage 1 model (XGBoost mock)...")
    xgb_mock = MockXGBoostModel()
    with open('models/stage1_xgboost.pkl', 'wb') as f:
        pickle.dump(xgb_mock, f)
    print("✅ Stage 1 model saved (Mock XGBoost)")

    # Stage 2B: CNN
    print("Generating Stage 2B model (CNN mock)...")
    cnn_mock = MockCNNModel()
    with open('models/stage2b_cnn.pkl', 'wb') as f:
        pickle.dump(cnn_mock, f)
    print("✅ Stage 2B model saved (Mock CNN)")

    # Stage 3: ResNet
    print("Generating Stage 3 model (ResNet mock)...")
    resnet_mock = MockResNetModel()
    with open('models/stage3_resnet.pkl', 'wb') as f:
        pickle.dump(resnet_mock, f)
    print("✅ Stage 3 model saved (Mock ResNet)")


def verify_models():
    """Verify that models can be loaded and used"""
    print("\n📋 Verifying models...")

    # Test Stage 0
    with open('models/stage0_isolation_forest.pkl', 'rb') as f:
        iso_forest = pickle.load(f)
    X_test = np.random.randn(10, 10)
    predictions = iso_forest.predict(X_test)
    scores = iso_forest.score_samples(X_test)
    print(f"  Stage 0: {sum(predictions == -1)}/10 anomalies detected")

    # Test Stage 1
    with open('models/stage1_xgboost.pkl', 'rb') as f:
        xgb = pickle.load(f)
    yields = xgb.predict(X_test)
    print(f"  Stage 1: Yield predictions range {yields.min():.2f} - {yields.max():.2f}")

    # Test Stage 2B
    with open('models/stage2b_cnn.pkl', 'rb') as f:
        cnn = pickle.load(f)
    patterns = cnn.predict(X_test)
    print(f"  Stage 2B: Pattern predictions {list(patterns[:3])}")

    # Test Stage 3
    with open('models/stage3_resnet.pkl', 'rb') as f:
        resnet = pickle.load(f)
    defects = resnet.predict(X_test)
    print(f"  Stage 3: Defect predictions {list(defects[:3])}")

    print("✅ All models verified")


if __name__ == "__main__":
    print("🔧 Generating mock models for development...")
    print("⚠️  These will be replaced with real models from STEP teams later\n")

    generate_mock_models()

    print("\n✅ All mock models generated!")
    print("📁 Files created in models/")
    print("   - stage0_isolation_forest.pkl")
    print("   - stage0_scaler.pkl")
    print("   - stage1_xgboost.pkl")
    print("   - stage2b_cnn.pkl")
    print("   - stage3_resnet.pkl")

    # Verify models work
    verify_models()

    print("\n💡 When STEP teams provide real models:")
    print("   1. Backup these mock models")
    print("   2. Replace .pkl files with real ones")
    print("   3. Update agent inference code if needed")
    print("   4. Test with real data")
