# Integration Guide: STEP Team Model Integration

**Version:** 1.0
**Last Updated:** 2026-01-29
**Purpose:** Guide for integrating production ML models from STEP teams

---

## 📋 Overview

This guide provides step-by-step instructions for STEP teams to integrate their production models into the AI-Driven Semiconductor QC system, replacing the current mock models.

### Current Mock Models (to be replaced)

| Stage | Model Type | File | Team Responsible |
|-------|------------|------|------------------|
| Stage 0 | Isolation Forest | `models/stage0_isolation_forest.pkl` | STEP 1 Team |
| Stage 0 | StandardScaler | `models/stage0_scaler.pkl` | STEP 1 Team |
| Stage 1 | XGBoost | `models/stage1_xgboost.pkl` | STEP 2 Team |
| Stage 2B | CNN | `models/stage2b_cnn.pkl` | STEP 3 Team |
| Stage 3 | ResNet | `models/stage3_resnet.pkl` | STEP 3 Team |

---

## 🎯 General Integration Process

### Prerequisites

1. **Python Environment:**
   ```bash
   python --version  # Should be 3.11.x
   pip list | grep -E "scikit-learn|xgboost|torch|tensorflow"
   ```

2. **Required Libraries:**
   - scikit-learn >= 1.3.0
   - xgboost >= 2.0.0
   - pytorch/tensorflow (for CNN/ResNet)

3. **Backup Current System:**
   ```bash
   # Create backup directory
   mkdir -p models/backup_$(date +%Y%m%d)

   # Backup all current models
   cp models/*.pkl models/backup_$(date +%Y%m%d)/

   # Backup configuration
   cp config.yaml config.yaml.backup
   ```

### Integration Workflow

```
1. Receive model from STEP team
   ↓
2. Validate model format and requirements
   ↓
3. Backup existing mock model
   ↓
4. Install new model
   ↓
5. Run unit tests
   ↓
6. Run integration tests
   ↓
7. Update configuration (if needed)
   ↓
8. Deploy to staging
   ↓
9. Validation in staging
   ↓
10. Deploy to production
```

---

## 🔵 Stage 0: Anomaly Detection (STEP 1 Team)

### Model Requirements

**Input:**
- 10 sensor readings (float): `etch_rate`, `pressure`, `temperature`, `rf_power`, `gas_flow`, `sensor6-10`
- Shape: `(1, 10)` for single wafer or `(n, 10)` for batch

**Output:**
- Anomaly score: float (0-1, higher = more anomalous)
- Decision score: float (raw model output)

**Expected Files from STEP 1:**
```
isolation_forest.pkl        # Main model
scaler.pkl                 # StandardScaler (optional but recommended)
preprocess.py             # Preprocessing code (optional)
inference.py              # Custom inference logic (optional)
model_card.md            # Model documentation
test_samples.csv         # Test samples with expected outputs
```

### Integration Steps

#### 1. Validate Received Model

```bash
# Create validation script
python scripts/validate_step1_model.py --model /path/to/isolation_forest.pkl
```

Create `scripts/validate_step1_model.py`:
```python
"""Validate STEP 1 model before integration"""
import pickle
import numpy as np

def validate_model(model_path):
    # Load model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Check model type
    print(f"Model type: {type(model)}")

    # Test inference
    test_input = np.random.randn(1, 10)
    try:
        output = model.decision_function(test_input)
        print(f"✓ decision_function works: {output}")
    except Exception as e:
        print(f"✗ decision_function failed: {e}")

    # Check required methods
    required_methods = ['decision_function', 'predict']
    for method in required_methods:
        if hasattr(model, method):
            print(f"✓ Has method: {method}")
        else:
            print(f"✗ Missing method: {method}")

if __name__ == "__main__":
    import sys
    validate_model(sys.argv[1])
```

#### 2. Backup Mock Models

```bash
# Backup with timestamp
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p models/backup/stage0_${timestamp}
cp models/stage0_*.pkl models/backup/stage0_${timestamp}/

echo "Backed up to: models/backup/stage0_${timestamp}/"
```

#### 3. Install New Model

```bash
# Copy from STEP 1 team location
cp /path/from/step1/isolation_forest.pkl models/stage0_isolation_forest.pkl
cp /path/from/step1/scaler.pkl models/stage0_scaler.pkl

# Verify files
ls -lh models/stage0_*.pkl
```

#### 4. Update Agent Code (if needed)

If STEP 1 team uses different inference logic, update [src/agents/stage0_agent.py](src/agents/stage0_agent.py):

```python
def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
    """
    If STEP 1 team provides custom preprocessing or inference:
    """
    # Extract features
    X = self._extract_features(wafer_data)  # Your custom method

    # Preprocess
    if self.scaler is not None:
        X_scaled = self.scaler.transform(X)
    else:
        X_scaled = X

    # STEP 1 TEAM: Replace this if inference logic changes
    decision_score = self.model.decision_function(X_scaled)[0]

    # STEP 1 TEAM: Update score normalization if needed
    anomaly_score = 1 / (1 + np.exp(decision_score))

    # Rest of the code remains the same...
```

#### 5. Test Integration

```bash
# Run Stage 0 tests
python scripts/test_stage0_agent.py

# Expected output:
# ✅ All Stage0Agent tests passed!
```

#### 6. Verify with STEP 1 Test Samples

If STEP 1 provides `test_samples.csv`:

```python
"""Verify model outputs match STEP 1 expectations"""
import pandas as pd
from src.agents.stage0_agent import Stage0Agent

# Load test samples
test_df = pd.read_csv('/path/from/step1/test_samples.csv')

# Initialize agent
agent = Stage0Agent(config['models']['stage0'], config)

# Test each sample
for idx, row in test_df.iterrows():
    result = agent.analyze(row)
    expected = row['expected_anomaly_score']
    actual = result['anomaly_score']

    diff = abs(expected - actual)
    if diff < 0.05:  # 5% tolerance
        print(f"✓ Sample {idx}: Expected={expected:.3f}, Actual={actual:.3f}")
    else:
        print(f"✗ Sample {idx}: Expected={expected:.3f}, Actual={actual:.3f}, Diff={diff:.3f}")
```

#### 7. Pipeline Integration Test

```bash
# Test full pipeline with new Stage 0 model
python scripts/test_pipeline_controller.py

# Should show:
# ✅ All PipelineController tests passed!
```

---

## 🟢 Stage 1: Yield Prediction (STEP 2 Team)

### Model Requirements

**Input:**
- 10 sensor readings (float): same as Stage 0
- 4 inline measurements (float): `cd`, `overlay`, `thickness`, `uniformity` (optional)
- Shape: `(1, 14)` with inline or `(1, 10)` without

**Output:**
- Predicted yield: float (0-1)

**Expected Files from STEP 2:**
```
xgboost_model.pkl         # XGBoost model
feature_importance.csv    # Feature importance rankings
model_card.md            # Model documentation
test_samples.csv         # Test samples
calibration_curve.png    # Calibration plot (optional)
```

### Integration Steps

#### 1. Validate Model

```python
"""scripts/validate_step2_model.py"""
import pickle
import xgboost as xgb
import numpy as np

def validate_xgboost_model(model_path):
    # Load
    model = pickle.load(open(model_path, 'rb'))

    # Check type
    assert isinstance(model, (xgb.XGBRegressor, xgb.Booster)), \
        f"Expected XGBoost model, got {type(model)}"

    # Test inference (14 features)
    test_input = np.random.randn(1, 14)
    prediction = model.predict(test_input)

    print(f"✓ Model type: {type(model)}")
    print(f"✓ Prediction shape: {prediction.shape}")
    print(f"✓ Sample prediction: {prediction[0]:.3f}")

    # Check prediction range
    assert 0 <= prediction[0] <= 1, \
        f"Prediction out of range [0,1]: {prediction[0]}"
    print(f"✓ Prediction in valid range")

if __name__ == "__main__":
    import sys
    validate_xgboost_model(sys.argv[1])
```

#### 2. Backup and Install

```bash
# Backup
timestamp=$(date +%Y%m%d_%H%M%S)
cp models/stage1_xgboost.pkl models/backup/stage1_${timestamp}.pkl

# Install
cp /path/from/step2/xgboost_model.pkl models/stage1_xgboost.pkl

# Test
python scripts/validate_step2_model.py models/stage1_xgboost.pkl
```

#### 3. Update Configuration

If STEP 2 model has different economic parameters, update [config.yaml](config.yaml):

```yaml
models:
  stage1:
    path: 'models/stage1_xgboost.pkl'
    wafer_value: 1000        # Update if changed
    rework_cost: 200         # Update if changed
    rework_improvement: 0.15  # Update based on STEP 2 data
```

#### 4. Test

```bash
python scripts/test_stage1_agent.py
python scripts/test_pipeline_controller.py
```

---

## 🟡 Stage 2B: Pattern Classification (STEP 3 Team - Part 1)

### Model Requirements

**Input:**
- Wafer map image or features
- May require WM-811K proxy data integration

**Output:**
- Pattern type: str ('Edge-Ring', 'Center', 'Loc', 'Random', etc.)
- Confidence: float (0-1)
- Severity: float (0-1)

**Expected Files from STEP 3:**
```
cnn_model.pkl            # CNN model (PyTorch/TensorFlow)
preprocessing.py         # Image preprocessing code
class_names.json         # Pattern class mapping
model_card.md           # Documentation
test_images/            # Test wafer maps
```

### Integration Steps

#### 1. Validate Model

```python
"""scripts/validate_step3_cnn.py"""
import pickle
import numpy as np

def validate_cnn_model(model_path):
    # Load model
    model = pickle.load(open(model_path, 'rb'))

    print(f"Model type: {type(model)}")

    # Test with dummy wafermap features (adjust based on actual input)
    test_input = np.random.randn(1, 100)  # Example: 100 features

    try:
        output = model.predict(test_input)
        print(f"✓ Prediction works: shape={output.shape}")
        print(f"✓ Sample output: {output[0]}")
    except Exception as e:
        print(f"✗ Prediction failed: {e}")

    return True
```

#### 2. Update Agent Code

Update [src/agents/stage2b_agent.py](src/agents/stage2b_agent.py) if input/output format changes:

```python
def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
    """
    STEP 3 TEAM: Update this method if CNN input format changes
    """
    # Get WM-811K proxy data (or real wafermap)
    wm811k_data = self.data_loader.get_wm811k_by_wafer(wafer_data['wafer_id'])

    # STEP 3 TEAM: Custom preprocessing here
    wafermap_features = self._preprocess_wafermap(wm811k_data)

    # STEP 3 TEAM: Model inference
    prediction = self.model.predict(wafermap_features)

    # Parse output (update based on model output format)
    pattern_type = self._parse_pattern(prediction)
    confidence = self._get_confidence(prediction)
    severity = self._calculate_severity(prediction, wm811k_data)

    return {
        'pattern_type': pattern_type,
        'confidence': float(confidence),
        'severity': float(severity),
        # ... rest of output
    }
```

#### 3. Test

```bash
python scripts/test_stage2b_agent.py
```

---

## 🔴 Stage 3: Defect Classification (STEP 3 Team - Part 2)

### Model Requirements

**Input:**
- SEM image features or defect signatures
- Carinthia proxy data integration

**Output:**
- Defect type: str ('Particle', 'Scratch', 'Residue', etc.)
- Confidence: float (0-1)
- Defect count: int

**Expected Files from STEP 3:**
```
resnet_model.pkl         # ResNet model
preprocessing.py         # SEM image preprocessing
defect_classes.json     # Defect type mapping
model_card.md           # Documentation
test_sem_images/        # Test SEM images
```

### Integration Steps

Similar to Stage 2B, but for SEM defect classification.

#### Update Agent Code

Update [src/agents/stage3_agent.py](src/agents/stage3_agent.py):

```python
def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
    """
    STEP 3 TEAM: Update for real ResNet model
    """
    # Get Carinthia proxy (or real SEM data)
    carinthia_data = self.data_loader.get_carinthia_by_wafer(wafer_data['wafer_id'])

    # STEP 3 TEAM: Preprocess SEM image/features
    sem_features = self._preprocess_sem_data(carinthia_data)

    # STEP 3 TEAM: Model inference
    prediction = self.model.predict(sem_features)

    # Parse outputs
    defect_type = self._parse_defect_type(prediction)
    confidence = self._get_confidence(prediction)
    defect_count = self._count_defects(prediction, carinthia_data)

    return {
        'defect_type': defect_type,
        'confidence': float(confidence),
        'defect_count': int(defect_count),
        # ... rest
    }
```

---

## ✅ Verification Checklist

### Pre-Integration

- [ ] Received all required files from STEP team
- [ ] Model documentation reviewed (model_card.md)
- [ ] Test samples available
- [ ] Backup created for existing models
- [ ] Development environment ready

### Model Validation

- [ ] Model loads without errors
- [ ] Model type matches expected (sklearn, xgboost, torch, etc.)
- [ ] Input shape verified
- [ ] Output format verified
- [ ] Test samples pass (if provided)
- [ ] Inference time acceptable (< 1s per wafer)

### Code Integration

- [ ] Agent code updated (if needed)
- [ ] Configuration updated (if needed)
- [ ] Unit tests updated (if needed)
- [ ] Documentation updated

### Testing

- [ ] Unit tests pass (`test_stage*_agent.py`)
- [ ] Integration tests pass (`test_pipeline_controller.py`)
- [ ] Performance acceptable (latency, throughput)
- [ ] No memory leaks during batch processing
- [ ] Error handling works correctly

### Staging Deployment

- [ ] Deployed to staging environment
- [ ] Smoke tests pass
- [ ] Run on historical data (if available)
- [ ] Compare outputs with mock model baseline
- [ ] Performance metrics collected

### Production Deployment

- [ ] Rollback plan prepared
- [ ] Deploy during maintenance window
- [ ] Monitor first 100 wafers closely
- [ ] Verify results with engineers
- [ ] Update system documentation

---

## 🔄 Rollback Procedure

If issues are discovered after integration:

### Quick Rollback

```bash
# 1. Stop any running processes
pkill -f streamlit
pkill -f python

# 2. Restore from backup
timestamp=YYYYMMDD_HHMMSS  # Use your backup timestamp
cp models/backup/stage*_${timestamp}/* models/

# 3. Verify restoration
ls -lh models/

# 4. Test
python scripts/test_pipeline_controller.py

# 5. Restart services
streamlit run streamlit_app/app.py &
```

### Document Issues

Create issue report:
```markdown
## Integration Rollback Report

**Date:** YYYY-MM-DD
**Stage:** Stage X
**Team:** STEP Y Team
**Model:** model_name.pkl

**Issue:**
[Describe the problem]

**Impact:**
[Describe impact on system]

**Rollback Time:**
[Time taken to rollback]

**Root Cause:**
[If known]

**Follow-up Actions:**
- [ ] Report issue to STEP team
- [ ] Request model fix
- [ ] Update integration checklist
- [ ] Schedule re-integration
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Model Loading Error

**Error:** `ModuleNotFoundError: No module named 'sklearn'`

**Solution:**
```bash
pip install scikit-learn==1.3.2
# Or version specified by STEP team
```

#### 2. Version Mismatch

**Error:** `InconsistentVersionWarning: Trying to unpickle estimator from version X.Y when using version A.B`

**Solution:**
```bash
# Install exact version used for training
pip install scikit-learn==X.Y.Z

# Or retrain model with current version
```

#### 3. Input Shape Mismatch

**Error:** `ValueError: Expected 2D array, got 1D array instead`

**Solution:**
```python
# Reshape input
X = wafer_data[feature_cols].values.reshape(1, -1)
```

#### 4. Output Format Unexpected

**Error:** `KeyError: 'pattern_type'`

**Solution:**
- Check model output format
- Update agent's `_parse_*` methods
- Verify with STEP team's model_card.md

#### 5. Performance Degradation

**Symptom:** Inference time > 5 seconds per wafer

**Solution:**
- Profile the code: `python -m cProfile scripts/test_stage*_agent.py`
- Identify bottleneck (preprocessing, model, postprocessing)
- Optimize or parallelize
- Consider model quantization/optimization

---

## 📊 Performance Benchmarks

### Expected Performance Targets

| Stage | Metric | Target | Acceptable | Unacceptable |
|-------|--------|--------|------------|--------------|
| Stage 0 | Inference time | < 0.1s | < 0.5s | > 1s |
| Stage 1 | Inference time | < 0.1s | < 0.5s | > 1s |
| Stage 2B | Inference time | < 0.5s | < 2s | > 5s |
| Stage 3 | Inference time | < 1s | < 3s | > 10s |
| Full Pipeline | End-to-end | < 2s | < 5s | > 10s |

### Benchmark Script

```python
"""scripts/benchmark_models.py"""
import time
import numpy as np
from src.pipeline.controller import PipelineController
from src.utils.data_loader import DataLoader

def benchmark():
    controller = PipelineController()
    loader = DataLoader()

    # Get test wafers
    step1_df = loader.load_step1_data()
    test_wafers = step1_df.head(100)['wafer_id'].tolist()

    # Benchmark
    times = []
    for wafer_id in test_wafers:
        start = time.time()
        result = controller.process_wafer(wafer_id)
        elapsed = time.time() - start
        times.append(elapsed)

    # Report
    print(f"Average time: {np.mean(times):.3f}s")
    print(f"Median time: {np.median(times):.3f}s")
    print(f"95th percentile: {np.percentile(times, 95):.3f}s")
    print(f"Max time: {np.max(times):.3f}s")

if __name__ == "__main__":
    benchmark()
```

---

## 📞 Support Contacts

### STEP Team Contacts

**STEP 1 Team (Stage 0):**
- Email: step1-team@company.com
- Slack: #step1-anomaly-detection
- Lead: [Name]

**STEP 2 Team (Stage 1):**
- Email: step2-team@company.com
- Slack: #step2-yield-prediction
- Lead: [Name]

**STEP 3 Team (Stages 2B & 3):**
- Email: step3-team@company.com
- Slack: #step3-pattern-defect
- Lead: [Name]

### Integration Support

**System Integration Team:**
- Email: integration-team@company.com
- Slack: #ai-qc-integration
- On-call: [Phone]

---

## 📝 Integration Log Template

Keep a log of all integrations:

```markdown
# Model Integration Log

## Stage 0 Integration - [Date]

**Model Version:** v1.0
**Trained on:** [Dataset info]
**Training Date:** YYYY-MM-DD
**Integrated by:** [Name]
**Integration Date:** YYYY-MM-DD

**Files:**
- isolation_forest.pkl (5.2 MB)
- scaler.pkl (1.1 KB)

**Changes:**
- None (drop-in replacement)

**Test Results:**
- Unit tests: ✅ Pass
- Integration tests: ✅ Pass
- Performance: 0.08s avg (target: <0.1s)

**Validation:**
- Test accuracy: 94.2% (target: >90%)
- False positive rate: 5.1% (target: <10%)

**Issues:** None

**Rollback Plan:** `models/backup/stage0_20260129_140000/`

---

## Stage 1 Integration - [Date]

[Similar format]
```

---

## 🔐 Security Considerations

### Model Security

1. **Model Provenance:**
   - Verify model source (authorized STEP team only)
   - Check file hash/signature if available
   - Store model metadata (who, when, what)

2. **Access Control:**
   - Limit model file write access
   - Log all model changes
   - Require approval for production deployment

3. **Model Testing:**
   - Test for adversarial inputs
   - Verify no data leakage
   - Check for backdoors (if applicable)

### Data Security

1. **Sensitive Data:**
   - Ensure models don't expose proprietary process data
   - Check for memorization of training samples
   - Validate output doesn't leak sensitive info

2. **Compliance:**
   - Ensure GDPR/privacy compliance
   - Document data usage
   - Implement audit trails

---

## 📚 Additional Resources

- **System Documentation:** [README.md](README.md)
- **Dashboard Guide:** [streamlit_app/README.md](streamlit_app/README.md)
- **System Status:** [SYSTEM_STATUS.md](SYSTEM_STATUS.md)
- **Test Scripts:** [scripts/](scripts/) directory

---

## ✨ Best Practices

1. **Always backup before integration**
2. **Test thoroughly in staging first**
3. **Integrate one stage at a time**
4. **Monitor closely after deployment**
5. **Document everything**
6. **Communicate with STEP teams**
7. **Have rollback plan ready**
8. **Keep integration log updated**

---

**Last Updated:** 2026-01-29
**Document Version:** 1.0
**Next Review:** [Date after first integration]
