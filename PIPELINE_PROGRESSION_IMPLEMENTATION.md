# Pipeline Progression Implementation

**Date:** 2026-01-29
**Status:** ✅ COMPLETE

---

## 🎯 Objective

Implement automatic pipeline progression so that approving a decision triggers the next stage execution and creates a new decision automatically.

**Before:**
```
Stage 0 Decision → [✅ Approve] → Decision disappears (끝)
```

**After:**
```
Stage 0 → [✅ Approve] → Inline measurement → Stage 1 Decision created
   ↓
Stage 1 → [✅ Approve] → LOT analysis → Stage 2A Decision created
   ↓
Stage 2A → [✅ Approve] → Pattern analysis → Stage 2B Decision created
   ↓
Stage 2B → [✅ Approve] → SEM analysis → Stage 3 Decision created
   ↓
Stage 3 → [✅ Approve] → 🎉 Pipeline completed!
```

---

## 📁 Files Created/Modified

### 1. Created: `streamlit_app/utils/stage_executors.py` (~500 lines)

**Purpose:** Stage execution functions for pipeline progression

**Key Functions:**

#### `execute_stage0_to_stage1(wafer_id, lot_id, wafer_data)`
- Simulates inline measurement
- Calculates yield prediction using sensor data
- Determines risk score and AI recommendation (REWORK/MONITOR/PROCEED)
- Creates Stage 1 decision with economic analysis
- Returns decision object

**Logic:**
```python
yield_pred = calculate_yield_prediction(wafer_data)
risk_score = 1 - yield_pred

if risk_score > 0.3:
    recommendation = 'REWORK'
elif risk_score > 0.15:
    recommendation = 'MONITOR'
else:
    recommendation = 'PROCEED'
```

#### `execute_stage1_to_stage2a(wafer_id, lot_id, wafer_data, stage1_results)`
- Performs LOT-level electrical analysis
- Calculates LOT yield and uniformity
- Determines if SEM is required
- Creates Stage 2A decision

**Logic:**
```python
lot_yield = calculate_lot_yield(lot_wafers)
uniformity = calculate_lot_uniformity(lot_wafers)

if lot_yield < 0.85 or uniformity < 0.9:
    recommendation = 'SEM_REQUIRED'
else:
    recommendation = 'PASS'
```

#### `execute_stage2a_to_stage2b(wafer_id, lot_id, wafer_data, stage2a_results)`
- Analyzes wafermap patterns using CNN (simulated)
- Detects pattern types: Edge-Ring, Center-Bull, Radial, Scratch
- Calculates severity score
- Recommends SEM analysis if needed
- Creates Stage 2B decision

**Logic:**
```python
pattern_type = detect_pattern()  # Edge-Ring, Center-Bull, etc.
severity = calculate_severity()

if severity > 0.7 or pattern_type in ['Edge-Ring', 'Scratch']:
    recommendation = 'SEM_ANALYSIS'
else:
    recommendation = 'SKIP_SEM'
```

#### `execute_stage2b_to_stage3(wafer_id, lot_id, wafer_data, stage2b_results)`
- Simulates SEM imaging and defect classification
- Uses ResNet model (simulated) to detect defect types: Pit, Particle, Scratch, Residue, Void
- **Generates LLM root cause analysis in Korean**
- Recommends process improvement actions
- Creates Stage 3 decision (final stage)

**Key Feature: LLM Korean Analysis**
```python
llm_analysis = generate_llm_root_cause(wafer_data, stage2b_results, defect_type, defect_count)

# Example output:
"""
센서 데이터와 결함 패턴 분석:

1. 높은 etch rate (3.89 μm/min)와 압력(162 mTorr) 조합이 Pit 형성 유발
2. Edge-Ring 패턴과의 상관관계: 과도한 플라즈마 밀도로 인한 국부적 과식각
3. 유사 패턴이 최근 5 LOT에서 18 건 이상 반복 발생

권장 조치:
- 단기: Etch rate를 3.4-3.6 범위로 제한
- 중기: Chamber PM 및 샤워헤드 세정
- 장기: Recipe 최적화 (압력 -5%, Power -3%)
"""
```

**Helper Functions:**
- `calculate_yield_prediction()`: Sensor-based yield prediction
- `calculate_stage1_economics()`: Rework vs. loss analysis
- `calculate_lot_yield()`: LOT-level yield simulation
- `calculate_lot_uniformity()`: Uniformity calculation
- `calculate_stage2a_economics()`: LOT review cost analysis
- `calculate_stage2b_economics()`: SEM cost vs. benefit
- `calculate_stage3_economics()`: Process improvement ROI
- `generate_llm_root_cause()`: Korean LLM analysis (mock)
- `generate_process_actions()`: Recommended actions by defect type
- `get_lot_wafers()`: Retrieve all wafers in a LOT
- `add_pipeline_alert()`: Add progress alerts

---

### 2. Modified: `streamlit_app/pages/2_⚠️_decision_queue.py`

**Changes:**

#### Added imports:
```python
from stage_executors import (
    execute_stage0_to_stage1,
    execute_stage1_to_stage2a,
    execute_stage2a_to_stage2b,
    execute_stage2b_to_stage3
)
```

#### Replaced `approve_decision()` function:

**Before:**
```python
def approve_decision(decision_id, recommendation):
    """승인"""
    log_decision(d, 'APPROVED', recommendation)
    st.session_state['pending_decisions'].pop(i)
```

**After:**
```python
def approve_decision(decision_id, recommendation):
    """승인 및 다음 단계 실행"""
    log_decision(d, 'APPROVED', recommendation)
    st.session_state['pending_decisions'].pop(i)

    # Execute next stage based on current stage
    if current_stage == 'Stage 0':
        with st.spinner("⏳ Performing Inline measurement..."):
            next_decision = execute_stage0_to_stage1(wafer_id, lot_id, wafer_data)
        st.success(f"✅ Stage 1 Decision created for {wafer_id}")

    elif current_stage == 'Stage 1':
        with st.spinner("⏳ Running LOT electrical analysis..."):
            next_decision = execute_stage1_to_stage2a(...)
        st.success(f"✅ Stage 2A Decision created for {wafer_id}")

    # ... (Stage 2A → 2B, Stage 2B → 3)

    elif current_stage == 'Stage 3':
        st.balloons()
        st.success(f"🎉 Pipeline completed for {wafer_id}!")
```

**Key Features:**
- Stage-specific branching logic
- Progress spinner messages
- Success notifications
- Error handling
- Final stage celebration with balloons

---

### 3. Modified: `streamlit_app/pages/1_🏭_production_monitor.py`

**Changes:**

Added `wafer_data` field to Stage 0 decisions so sensor data can be passed through the pipeline:

```python
decision = {
    # ... existing fields ...
    'wafer_data': {
        'etch_rate': wafer.get('etch_rate'),
        'pressure': wafer.get('pressure'),
        'temperature': wafer.get('temperature'),
        'rf_power': wafer.get('rf_power'),
        'gas_flow': wafer.get('gas_flow')
    }
}
```

**Why Important:**
- Stage executors need sensor data to calculate yield predictions
- Data flows through all stages: Stage 0 → 1 → 2A → 2B → 3
- Enables real sensor-based analysis

---

## 🧪 Testing Scenario

### Test Flow:

1. **Go to Production Monitor**
   - Click "🚀 Start New LOT"
   - 25 wafers generated
   - Some wafers flagged (red/yellow in heatmap)
   - Alerts appear in Recent Alerts section

2. **Go to Decision Queue**
   - See pending Stage 0 decisions for flagged wafers
   - Click "✅ Approve" on a HIGH priority decision

3. **Observe Pipeline Progression:**
   ```
   ⏳ Performing Inline measurement...
   ✅ Stage 1 Decision created for LOT-xxx-W01
   ```

4. **Review Stage 1 Decision:**
   - See yield prediction (e.g., 87%)
   - See risk score and AI recommendation (REWORK/MONITOR/PROCEED)
   - See economics: cost vs. expected loss
   - Click "✅ Approve"

5. **Continue Through Pipeline:**
   ```
   Stage 1 → ⏳ Running LOT electrical analysis...
            ✅ Stage 2A Decision created

   Stage 2A → ⏳ Analyzing wafermap patterns...
             ✅ Stage 2B Decision created

   Stage 2B → ⏳ Performing SEM analysis with LLM...
             ✅ Stage 3 Decision created
   ```

6. **Stage 3 Final Review:**
   - See defect type (Pit/Particle/Scratch/Residue/Void)
   - See defect count
   - **See LLM 근본 원인 분석 (Korean)** in expandable details
   - See process improvement recommendations
   - Click "✅ Approve"

7. **Pipeline Completion:**
   ```
   🎉 Pipeline completed for LOT-xxx-W01!
   [Balloons animation]
   ```

8. **Check Progress:**
   - Go to Home page
   - See updated agreement rate
   - See recent activity feed showing all stages
   - Go to Production Monitor → Recent Alerts
   - See all pipeline progress alerts

---

## 📊 Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     PRODUCTION MONITOR                       │
│                                                              │
│  [🚀 Start New LOT]                                         │
│     ↓                                                        │
│  Generate 25 wafers                                         │
│     ↓                                                        │
│  Anomaly detection (etch_rate > 3.8 or pressure > 160)     │
│     ↓                                                        │
│  Flagged wafers → Stage 0 Decisions                        │
└──────────────────────────┬───────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                      DECISION QUEUE                          │
│                                                              │
│  Stage 0 Decision: Anomaly detected                         │
│  • Wafer: LOT-xxx-W01                                       │
│  • AI Rec: INLINE                                           │
│  • Risk: HIGH                                               │
│  • [✅ Approve] ←────────────────────────┐                  │
└──────────────────────────┬───────────────┼───────────────────┘
                           ↓               │
                   execute_stage0_to_stage1│
                           ↓               │
                   • Inline measurement    │ Pipeline
                   • Yield prediction      │ Progression
                   • Create Stage 1 Decision│ (automatic)
                           ↓               │
┌─────────────────────────────────────────┼───────────────────┐
│  Stage 1 Decision: Yield Prediction     │                   │
│  • Yield: 87%                            │                   │
│  • AI Rec: MONITOR                       │                   │
│  • Risk: MEDIUM                          │                   │
│  • [✅ Approve] ←────────────────────────┤                  │
└──────────────────────────┬───────────────┘                   │
                           ↓                                   │
                   execute_stage1_to_stage2a                   │
                           ↓                                   │
                   • LOT electrical analysis                   │
                   • Yield/uniformity check                    │
                   • Create Stage 2A Decision                  │
                           ↓                                   │
┌─────────────────────────────────────────┐                   │
│  Stage 2A Decision: LOT Analysis        │                   │
│  • LOT Yield: 82%                       │                   │
│  • Uniformity: 88%                      │                   │
│  • AI Rec: SEM_REQUIRED                 │                   │
│  • [✅ Approve] ←────────────────────────┤                  │
└──────────────────────────┬───────────────┘                   │
                           ↓                                   │
                   execute_stage2a_to_stage2b                  │
                           ↓                                   │
                   • Wafermap pattern analysis                 │
                   • Severity calculation                      │
                   • Create Stage 2B Decision                  │
                           ↓                                   │
┌─────────────────────────────────────────┐                   │
│  Stage 2B Decision: Pattern Analysis    │                   │
│  • Pattern: Edge-Ring                   │                   │
│  • Severity: 0.82                       │                   │
│  • AI Rec: SEM_ANALYSIS                 │                   │
│  • [✅ Approve] ←────────────────────────┤                  │
└──────────────────────────┬───────────────┘                   │
                           ↓                                   │
                   execute_stage2b_to_stage3                   │
                           ↓                                   │
                   • SEM imaging                               │
                   • Defect classification (ResNet)            │
                   • LLM root cause analysis (Korean)          │
                   • Create Stage 3 Decision                   │
                           ↓                                   │
┌─────────────────────────────────────────┐                   │
│  Stage 3 Decision: SEM Analysis         │                   │
│  • Defect: Pit (18 counts)              │                   │
│  • 🧠 LLM 근본 원인 분석 (Korean)       │                   │
│  • AI Rec: PROCESS_IMPROVEMENT          │                   │
│  • [✅ Approve] ←────────────────────────┤                  │
└──────────────────────────┬───────────────┘                   │
                           ↓                                   │
                  🎉 Pipeline Completed! ───────────────────────┘
                  [Balloons animation]
```

---

## 🎯 Key Achievements

| Feature | Status | Notes |
|---------|--------|-------|
| Stage 0 → Stage 1 | ✅ | Inline measurement + yield prediction |
| Stage 1 → Stage 2A | ✅ | LOT electrical analysis |
| Stage 2A → Stage 2B | ✅ | Wafermap pattern analysis |
| Stage 2B → Stage 3 | ✅ | SEM + LLM root cause (Korean) |
| Progress messages | ✅ | Spinner + success notifications |
| Alert generation | ✅ | Pipeline progress tracked |
| Economic analysis | ✅ | Cost/benefit at each stage |
| LLM Korean analysis | ✅ | Defect-specific root cause |
| Final celebration | ✅ | Balloons on Stage 3 completion |
| Error handling | ✅ | Try-except with error display |

---

## 💡 Technical Details

### Session State Flow

```python
# Stage 0 Decision created in Production Monitor
st.session_state['pending_decisions'].append({
    'stage': 'Stage 0',
    'wafer_data': {...}  # Sensor data included
})

# Stage 0 Approved → Stage 1 Decision created
next_decision = execute_stage0_to_stage1(wafer_id, lot_id, wafer_data)
st.session_state['pending_decisions'].append(next_decision)

# Stage 1 Approved → Stage 2A Decision created
next_decision = execute_stage1_to_stage2a(wafer_id, lot_id, wafer_data, stage1_results)
st.session_state['pending_decisions'].append(next_decision)

# ... and so on
```

### Data Persistence

Each decision carries forward previous stage results:
- Stage 1 decision includes `wafer_data` + `stage1_results`
- Stage 2A decision includes `wafer_data` + `stage1_results` + `stage2a_results`
- Stage 2B decision includes all previous + `stage2b_results`
- Stage 3 decision includes complete history

This enables:
- Root cause analysis using full sensor history
- Economic analysis based on accumulated risk
- LLM analysis with complete context

### Mock vs. Real Implementation

**Currently Mock (Simulated):**
- Sensor measurements (random generation)
- ML model predictions (formulas, not real models)
- LLM analysis (pre-written Korean text)
- Defect detection (random selection)

**Ready for Real Integration:**
- All functions have clear interfaces
- Real model calls can replace mock calculations
- Real LLM API can replace mock text
- Data structures support real sensor data

**Integration Points:**
```python
# Replace with real model
def calculate_yield_prediction(wafer_data):
    # TODO: Load actual XGBoost model
    # model = joblib.load('models/stage1/xgboost.pkl')
    # return model.predict(features)
    pass

# Replace with real LLM call
def generate_llm_root_cause(wafer_data, stage2b_results, defect_type, defect_count):
    # TODO: Call Anthropic API
    # client = anthropic.Anthropic(api_key=...)
    # response = client.messages.create(...)
    # return response.content[0].text
    pass
```

---

## 🚀 Demo Script

**For paper/presentation:**

1. "Here's our real-time LOT monitoring system with automatic pipeline progression"
2. "Let me start a new LOT" → Click "Start New LOT"
3. "The system detected 3 anomalies and created Stage 0 decisions"
4. "Now I'll approve this high-priority decision" → Click ✅ Approve
5. "Watch as the system automatically executes Stage 1 inline measurement"
6. "A new Stage 1 decision appears with yield prediction"
7. "I approve again" → Stage 2A appears → "LOT-level analysis"
8. "Continue" → Stage 2B appears → "Pattern analysis detects Edge-Ring"
9. "Final approval triggers SEM analysis with LLM"
10. "Here's the LLM root cause analysis in Korean - see how it connects sensor data to defects"
11. "Final approval" → 🎉 Balloons → "Pipeline completed!"
12. "Check the home page - agreement rate updated, activity feed shows all stages"

**Key Message:**
> "This demonstrates seamless Human-AI collaboration with automatic pipeline progression. Engineers review AI recommendations at critical checkpoints, while the system handles execution and creates follow-up decisions automatically. The LLM provides Korean language root cause analysis at the final stage, making it ideal for Korean semiconductor fabs."

---

## 📈 Impact on Paper

**Novel Contributions:**

1. **Automatic Multi-Stage Progression**: Not just isolated ML models, but a continuous pipeline with automatic stage transitions

2. **Human-in-the-Loop at Every Stage**: Engineers approve/reject at checkpoints, system executes automatically

3. **Economic Decision Making**: Cost-benefit analysis at each stage guides recommendations

4. **LLM Integration for Root Cause**: Korean language analysis connecting sensor data → patterns → defects → process improvements

5. **LOT-level + Wafer-level Analysis**: Stage 2A analyzes entire LOT, Stage 2B/3 focus on specific wafers

6. **Continuous Learning**: Decision log tracks engineer feedback for learning insights

---

## 🔧 Maintenance Notes

**Adding New Stages:**

To add Stage 2C between 2B and 3:

1. Create `execute_stage2b_to_stage2c()` in stage_executors.py
2. Update `approve_decision()` in Decision Queue:
   ```python
   elif current_stage == 'Stage 2B':
       next_decision = execute_stage2b_to_stage2c(...)
   ```
3. Create `execute_stage2c_to_stage3()` for next transition

**Modifying Economics:**

Edit helper functions in stage_executors.py:
- `calculate_stage1_economics()`: Adjust wafer_value, rework_cost
- `calculate_stage2b_economics()`: Adjust sem_cost
- `calculate_stage3_economics()`: Adjust pm_cost, recipe_cost

**Updating LLM Analysis:**

Edit `generate_llm_root_cause()` in stage_executors.py:
- Add new defect types to `analyses` dictionary
- Modify Korean text templates
- Or replace with real LLM API call

---

**Last Updated:** 2026-01-29
**Version:** 1.0.0
**Status:** ✅ COMPLETE - Ready for Demo!

---

## 🎊 Summary

The pipeline progression feature is now fully implemented!

**What works:**
- ✅ Stage 0 → 1 → 2A → 2B → 3 automatic transitions
- ✅ Progress messages and success notifications
- ✅ LLM Korean analysis at Stage 3
- ✅ Alert generation for pipeline progress
- ✅ Balloons celebration on completion
- ✅ Economic analysis at each stage
- ✅ Error handling

**Try it now:**
```bash
streamlit run streamlit_app/app.py
```

Navigate: Production Monitor → Start LOT → Decision Queue → Approve decisions → Watch the pipeline flow! 🚀
