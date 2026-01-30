# Pipeline Progression Test Guide

**Status:** ✅ Implementation Complete - Ready to Test
**Access URL:** http://localhost:8502

---

## 🧪 Quick Test Procedure

### Step 1: Start a New LOT
1. Open http://localhost:8502
2. Navigate to **🏭 Production Monitor** (sidebar or home page button)
3. Click **"🚀 Start New LOT"** button
4. Observe:
   - LOT card appears with LOT-YYYYMMDD-HHMMSS format
   - 25 wafers generated
   - 5x5 wafer heatmap displayed (some red/yellow for anomalies)
   - Flagged wafers table shows wafers with issues
   - Recent Alerts section shows alerts for flagged wafers
   - Metrics updated: Pending Decisions increased

### Step 2: Review Stage 0 Decision
1. Navigate to **⚠️ Decision Queue** (sidebar or home page button)
2. Observe:
   - One or more Stage 0 decisions appear
   - Each card shows:
     - Wafer ID and LOT ID
     - Priority (🔴 HIGH or 🟡 MEDIUM)
     - AI Recommendation: "INLINE"
     - AI Confidence: ~0.87
     - Economics: Cost $150, Expected Loss $12,000, Benefit $11,850
   - Expandable "Details & Analysis" section

### Step 3: Approve Stage 0 → Triggers Stage 1
1. Click **"✅ Approve"** on a HIGH priority Stage 0 decision
2. Observe the progression:
   ```
   [Spinner appears]
   ⏳ Performing Inline measurement...

   [Success message appears]
   ✅ Stage 1 Decision created for LOT-xxx-W01

   [Card disappears from queue]
   ```
3. Scroll down - NEW Stage 1 decision card appears!

### Step 4: Review Stage 1 Decision
1. Expand the new Stage 1 decision card
2. Observe:
   - **Stage:** Stage 1
   - **AI Recommendation:** REWORK, MONITOR, or PROCEED (depends on yield)
   - **AI Reasoning:** "Predicted yield: 87.3%. Risk score: 0.13. Within acceptable limits."
   - **Economics:** Different costs (rework vs. expected loss)
   - **Priority:** Based on risk score (HIGH if >0.3, MEDIUM if >0.15, LOW otherwise)

### Step 5: Approve Stage 1 → Triggers Stage 2A
1. Click **"✅ Approve"** on the Stage 1 decision
2. Observe:
   ```
   ⏳ Running LOT electrical analysis...
   ✅ Stage 2A Decision created for LOT-xxx-W01
   ```
3. NEW Stage 2A decision appears!

### Step 6: Review Stage 2A Decision (LOT-level)
1. Expand Stage 2A decision
2. Observe:
   - **AI Recommendation:** SEM_REQUIRED or PASS
   - **AI Reasoning:** "LOT yield: 82.4%, Uniformity: 88.1%. Pattern irregularities detected."
   - This is LOT-level analysis (all 25 wafers)
   - Economics shows LOT review cost

### Step 7: Approve Stage 2A → Triggers Stage 2B
1. Click **"✅ Approve"**
2. Observe:
   ```
   ⏳ Analyzing wafermap patterns...
   ✅ Stage 2B Decision created for LOT-xxx-W01
   ```
3. NEW Stage 2B decision appears!

### Step 8: Review Stage 2B Decision (Pattern Analysis)
1. Expand Stage 2B decision
2. Observe:
   - **AI Recommendation:** SEM_ANALYSIS, SKIP_SEM, or REVIEW
   - **AI Reasoning:** "Pattern detected: Edge-Ring, Severity: 0.82. SEM inspection recommended for root cause."
   - **Economics:** SEM cost ($800) vs. expected benefit
   - Pattern types: Edge-Ring, Center-Bull, Radial, Scratch, None

### Step 9: Approve Stage 2B → Triggers Stage 3 (CRITICAL!)
1. Click **"✅ Approve"**
2. Observe:
   ```
   ⏳ Performing SEM analysis with LLM...
   ✅ Stage 3 Decision created for LOT-xxx-W01
   ```
3. NEW Stage 3 decision appears!

### Step 10: Review Stage 3 Decision (Final Stage with LLM!)
1. Expand Stage 3 decision
2. Click **"📊 Details & Analysis"** expander
3. **KEY FEATURE:** Observe the **🧠 LLM Analysis (Korean)** section:
   ```
   센서 데이터와 결함 패턴 분석:

   1. 높은 etch rate (3.89 μm/min)와 압력(162 mTorr) 조합이 Pit 형성 유발
   2. Edge-Ring 패턴과의 상관관계: 과도한 플라즈마 밀도로 인한 국부적 과식각
   3. 유사 패턴이 최근 5 LOT에서 18 건 이상 반복 발생

   권장 조치:
   - 단기: Etch rate를 3.4-3.6 범위로 제한
   - 중기: Chamber PM 및 샤워헤드 세정
   - 장기: Recipe 최적화 (압력 -5%, Power -3%)
   ```

4. Observe defect information:
   - Defect Type: Pit, Particle, Scratch, Residue, or Void
   - Defect Count: 5-30 defects
   - Confidence: ~0.75-0.95

5. Observe economics:
   - Cost: $5,000-$10,000 (PM or recipe adjustment)
   - Benefit: Monthly savings estimate

### Step 11: Final Approval → Pipeline Complete! 🎉
1. Click **"✅ Approve"** on Stage 3 decision
2. Observe:
   ```
   [Balloons animation appears! 🎈]
   🎉 Pipeline completed for LOT-xxx-W01!
   ```
3. Card disappears - pipeline is complete!

### Step 12: Check Results
1. **Go to Home Page**
   - Observe "Recent Activity" feed shows all 4 stages
   - Each with ✅ icon and agreement status
   - AI-Engineer Agreement rate updated

2. **Go to Production Monitor**
   - Check "Recent Alerts" section
   - Should see all pipeline progress alerts:
     - "Stage 1 analysis complete - Yield: 87.3%"
     - "Stage 2A (LOT) complete - Yield: 82.4%"
     - "Stage 2B pattern analysis - Edge-Ring detected"
     - "Stage 3 SEM analysis - 18 Pit defects found"

3. **Go to AI Insights → Root Cause Analysis tab**
   - Should see the Stage 3 analysis saved (if implemented)

---

## 🎯 What to Look For

### ✅ Success Indicators

1. **Automatic Progression:**
   - Approving Stage 0 creates Stage 1 decision ✅
   - Approving Stage 1 creates Stage 2A decision ✅
   - Approving Stage 2A creates Stage 2B decision ✅
   - Approving Stage 2B creates Stage 3 decision ✅
   - Approving Stage 3 shows completion message ✅

2. **Progress Messages:**
   - Spinner with stage-specific messages ✅
   - Success notifications after each stage ✅
   - Balloons on final completion ✅

3. **Data Flow:**
   - Yield predictions change based on sensor data ✅
   - Pattern types vary (Edge-Ring, Center-Bull, etc.) ✅
   - LLM analysis matches defect type ✅
   - Economics update at each stage ✅

4. **Alert Generation:**
   - Each stage creates an alert ✅
   - Alerts visible in Production Monitor ✅
   - Severity levels appropriate (HIGH/MEDIUM) ✅

5. **LLM Korean Analysis:**
   - Appears in Stage 3 Details section ✅
   - Specific to defect type (Pit, Particle, etc.) ✅
   - Includes sensor data references ✅
   - Provides 3-tier recommendations (단기/중기/장기) ✅

### ⚠️ Potential Issues

1. **Import Errors:**
   - If you see module import errors, check sys.path setup
   - Solution: Already handled in Decision Queue imports

2. **Missing wafer_data:**
   - If Stage 1+ fails with KeyError on sensor data
   - Solution: Already added wafer_data to Stage 0 decisions

3. **Session State Loss:**
   - If decisions disappear unexpectedly
   - Solution: Check Streamlit session state persistence

---

## 🔧 Troubleshooting

### Problem: Stage executors not found
**Error:** `ModuleNotFoundError: No module named 'stage_executors'`

**Solution:**
```python
# Check if utils/__init__.py exists
ls streamlit_app/utils/__init__.py

# Verify import path in Decision Queue
# Should have:
utils_path = Path(__file__).parent.parent / 'utils'
sys.path.insert(0, str(utils_path))
```

### Problem: No Stage 1 decision created
**Error:** Silent failure, no next stage appears

**Check:**
1. Browser console for JavaScript errors
2. Terminal running Streamlit for Python errors
3. Session state: `st.session_state['pending_decisions']`

**Debug:**
Add to approve_decision():
```python
st.write(f"DEBUG: Current stage = {current_stage}")
st.write(f"DEBUG: wafer_data = {wafer_data}")
```

### Problem: Balloons don't appear
**Note:** This is cosmetic. Verify completion message appears instead.

---

## 📊 Expected Behavior Summary

| Action | Expected Result | Time |
|--------|----------------|------|
| Start New LOT | 25 wafers, some flagged, Stage 0 decisions | Instant |
| Approve Stage 0 | Spinner → Stage 1 decision created | ~0.5s |
| Approve Stage 1 | Spinner → Stage 2A decision created | ~0.5s |
| Approve Stage 2A | Spinner → Stage 2B decision created | ~0.5s |
| Approve Stage 2B | Spinner → Stage 3 decision created | ~0.8s |
| Approve Stage 3 | Balloons → Completion message | Instant |

**Total Pipeline Time:** ~2.3 seconds from Stage 0 to completion

---

## 🎬 Demo Recording Checklist

For paper/presentation video:

- [ ] Show Home page with system overview
- [ ] Show Production Monitor empty state
- [ ] Click "Start New LOT"
- [ ] Show wafer heatmap with red/yellow alerts
- [ ] Show flagged wafers table
- [ ] Navigate to Decision Queue
- [ ] Show Stage 0 decision card (expand details)
- [ ] Click Approve → capture spinner message
- [ ] Show Stage 1 decision appears
- [ ] Expand Stage 1 details (yield prediction)
- [ ] Click Approve → Stage 2A
- [ ] Expand Stage 2A (LOT-level analysis)
- [ ] Click Approve → Stage 2B
- [ ] Expand Stage 2B (pattern: Edge-Ring)
- [ ] Click Approve → Stage 3
- [ ] **IMPORTANT:** Expand Stage 3 Details
- [ ] **CRITICAL:** Capture LLM Korean analysis section
- [ ] Show defect info and process recommendations
- [ ] Click Final Approve → Capture balloons 🎈
- [ ] Return to Home → show activity feed
- [ ] Show Production Monitor alerts
- [ ] Zoom in on LLM Korean text

**Key Screenshots:**
1. Wafer heatmap with alerts
2. Stage 1 yield prediction
3. Stage 2B pattern analysis
4. **Stage 3 LLM Korean analysis (MOST IMPORTANT)**
5. Completion balloons
6. Activity feed showing all stages

---

## ✅ Test Completion Checklist

After testing, verify:

- [ ] All 5 stages execute successfully (0 → 1 → 2A → 2B → 3)
- [ ] Progress messages appear correctly
- [ ] LLM Korean analysis displays in Stage 3
- [ ] Economics update at each stage
- [ ] Alerts generated and visible
- [ ] Home page activity feed updates
- [ ] AI-Engineer agreement rate calculates
- [ ] No Python errors in terminal
- [ ] No JavaScript errors in browser console
- [ ] Pipeline completes with balloons

**If all checked:** ✅ Pipeline Progression is WORKING!

---

**Tested By:** _______________
**Date:** _______________
**Result:** ⬜ PASS | ⬜ FAIL
**Notes:** _______________________________________

---

**Access URL:** http://localhost:8502
**Happy Testing!** 🚀
