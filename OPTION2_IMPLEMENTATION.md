# Option 2 구현: 모든 Stage Transition → Decision Queue

**Date:** 2026-01-29
**Status:** ✅ 완료

---

## 변경사항

### Before (Option 1 - 자동 처리)
```
Stage 0 → INLINE 선택
  ↓
Stage 1로 이동 + AI 분석
  ↓
anomaly_detected = True → Decision Queue ⚠️
anomaly_detected = False → 자동 COMPLETE ✅ (Decision Queue에 안나타남)
```

**문제점:**
- 엔지니어가 INLINE을 선택했는데 Decision Queue에 나타나지 않음
- 대부분의 wafer가 자동으로 complete되어 추적 불가
- 사용자가 혼란스러워함

### After (Option 2 - 모든 검토)
```
Stage 0 → INLINE 선택
  ↓
Stage 1로 이동 + AI 분석
  ↓
결과와 무관하게 무조건 Decision Queue에 추가 ⚠️
  ↓
엔지니어가 검토:
  - SKIP → 완료 (false positive)
  - PROCEED → Stage 2A로 이동
  - REWORK → 재처리
  - SCRAP → 폐기
```

**장점:**
- ✅ 모든 stage transition 후 엔지니어 검토
- ✅ 완전한 추적성 (모든 wafer의 decision history)
- ✅ 엔지니어가 모든 결정 제어
- ✅ 직관적인 workflow

---

## 수정된 파일

### 1. [streamlit_app/utils/wafer_processor.py](streamlit_app/utils/wafer_processor.py:148-163)

**변경 내용:**
```python
# Before
else:
    # Normal - no decision needed
    return {
        'needs_decision': False,  # ← Auto-complete
        'outcome': 'PASS',
        'decision_data': None
    }

# After
else:
    # Normal - but still need engineer review (Option 2)
    return {
        'needs_decision': True,  # ← Always show in queue
        'outcome': 'PASS',
        'decision_data': {
            'stage': stage,
            'ai_recommendation': ai_result['recommendation'],
            'ai_confidence': ai_result['confidence'],
            'ai_reasoning': ai_result['reasoning'],
            'sensor_data': sensor_data,
            'available_options': get_stage_options(stage),
            'economics': ai_result.get('economics', {}),
            'wafer_data': sensor_data,
            'yield_pred': ai_result.get('yield_pred')
        }
    }
```

**효과:**
- 모든 wafer가 Decision Queue에 추가됨
- AI recommendation은 "PASS"이지만 엔지니어가 최종 결정
- available_options에 모든 선택지 포함

---

## Phase별 동작

### Phase 1 (Stage 0, 1) - Rework 가능

#### Stage 0
**AI Recommendation:** INLINE (anomaly detected) 또는 PASS (normal)

**Engineer Options:**
- ✅ **INLINE**: Stage 1로 이동 → Decision Queue에 추가
- ✅ **SKIP**: 완료 (false positive, 정상 wafer)

#### Stage 1
**AI Recommendation:**
- REWORK (yield_pred < 0.85, value_rework > value_proceed)
- SCRAP (yield_pred < 0.5)
- PROCEED (yield_pred < 0.85 but value_proceed > value_rework)
- PASS (yield_pred >= 0.85, normal)

**Engineer Options:**
- ✅ **SKIP**: 완료 (false positive)
- ✅ **PROCEED**: Stage 2A로 이동 → Decision Queue에 추가
- ✅ **REWORK**: 재처리 with new sensor data
- ✅ **SCRAP**: 폐기

### Phase 2 (Stage 2A, 2B, 3) - Rework 불가

#### Stage 2A (WAT Analysis)
**AI Recommendation:**
- PROCEED (50% chance, needs pattern analysis)
- PASS (50% chance, normal)

**Engineer Options:**
- ✅ **SKIP**: 완료 (팹아웃, 추가 분석 불필요)
- ✅ **PROCEED**: Stage 2B로 이동 → Decision Queue에 추가

**Note:** 수율이 안좋아도 rework 불가 → SKIP으로 팹아웃하거나 PROCEED로 원인 분석

#### Stage 2B (Wafermap Pattern)
**AI Recommendation:**
- PROCEED (40% chance, needs SEM analysis)
- PASS (60% chance, no significant pattern)

**Engineer Options:**
- ✅ **SKIP**: 완료 (팹아웃, 추가 분석 불필요)
- ✅ **PROCEED**: Stage 3로 이동 → Decision Queue에 추가

#### Stage 3 (SEM/Root Cause)
**AI Recommendation:** COMPLETE (always, root cause identified)

**Engineer Options:**
- ✅ **COMPLETE**: 완료 (root cause analysis 완료)
- ✅ **INVESTIGATE**: 완료 (추가 조사 필요 플래그)

---

## 동작 예시

### 시나리오 1: 정상 Wafer (Fast Track)
```
Wafer #1:
  Stage 0 → AI: PASS → Decision Queue
    → Engineer: SKIP → ✅ COMPLETED at Stage 0

총 비용: $0
Decision 수: 1
완료 단계: Stage 0
```

### 시나리오 2: 경미한 Anomaly (Inline 검증)
```
Wafer #2:
  Stage 0 → AI: INLINE → Decision Queue
    → Engineer: INLINE ($150)
  Stage 1 → AI: PASS (yield_pred = 0.92) → Decision Queue
    → Engineer: SKIP → ✅ COMPLETED at Stage 1

총 비용: $150
Decision 수: 2
완료 단계: Stage 1 (false positive)
```

### 시나리오 3: Rework 성공
```
Wafer #3:
  Stage 0 → AI: INLINE → Decision Queue
    → Engineer: INLINE ($150)
  Stage 1 → AI: REWORK (yield_pred = 0.78) → Decision Queue
    → Engineer: REWORK ($200)
  Stage 1 (rework) → AI: PASS (yield_pred = 0.91) → Decision Queue
    → Engineer: SKIP → ✅ COMPLETED at Stage 1

총 비용: $350
Decision 수: 3
완료 단계: Stage 1
리워크 횟수: 1 🔄
```

### 시나리오 4: 전체 파이프라인 (원인 분석)
```
Wafer #4:
  Stage 0 → AI: INLINE → Decision Queue
    → Engineer: INLINE ($150)
  Stage 1 → AI: PROCEED (yield_pred = 0.80) → Decision Queue
    → Engineer: PROCEED ($100)
  Stage 2A → AI: PROCEED (pattern detected) → Decision Queue
    → Engineer: PROCEED ($80)
  Stage 2B → AI: PROCEED (Edge-Ring pattern) → Decision Queue
    → Engineer: PROCEED ($300)
  Stage 3 → AI: COMPLETE (root cause found) → Decision Queue
    → Engineer: COMPLETE → ✅ COMPLETED at Stage 3

총 비용: $630
Decision 수: 5
완료 단계: Stage 3
원인: Chamber temperature drift
```

### 시나리오 5: Phase 2에서 팹아웃 (Rework 불가)
```
Wafer #5:
  Stage 0 → AI: INLINE → Decision Queue
    → Engineer: INLINE ($150)
  Stage 1 → AI: PROCEED (yield_pred = 0.75) → Decision Queue
    → Engineer: PROCEED ($100)  # Phase 1 끝, rework 불가
  Stage 2A → AI: PASS (normal) → Decision Queue
    → Engineer: SKIP → ✅ COMPLETED at Stage 2A (팹아웃)

총 비용: $250
Decision 수: 3
완료 단계: Stage 2A
Note: 수율 낮지만 Phase 2라서 rework 불가 → 팹아웃
```

---

## Decision Queue 표시

### 모든 wafer가 Decision Queue에 나타남

**Stage 0 - AI: PASS (normal)**
```
🟢 Stage 0: LOT-001-W01
AI Recommendation: PASS (0.90 confidence)
Reasoning: "All sensors within normal range"

Options: [🔍 INLINE] [⏭️ SKIP]
```

**Stage 1 - AI: PASS (good yield)**
```
🟢 Stage 1: LOT-001-W02
AI Recommendation: PASS (0.88 confidence)
Reasoning: "Good predicted yield: 92.3%"
Predicted Yield: 92.3%

Options: [⏭️ SKIP] [⏩ PROCEED] [🔄 REWORK] [❌ SCRAP]
```

**Stage 1 - AI: REWORK (low yield)**
```
🔴 Stage 1: LOT-001-W03
AI Recommendation: REWORK (0.82 confidence)
Reasoning: "Predicted yield: 78.5%. Economic analysis suggests REWORK."
Predicted Yield: 78.5%

Options: [⏭️ SKIP] [⏩ PROCEED] [🔄 REWORK] [❌ SCRAP]
```

**Stage 2A - AI: PASS (normal, but in Phase 2)**
```
🟡 Stage 2A: LOT-001-W04
AI Recommendation: PASS (0.90 confidence)
Reasoning: "WAT results normal"

Options: [⏩ PROCEED] [⏭️ SKIP]
Note: Phase 2 - Rework NOT possible. SKIP to fab-out or PROCEED for root cause.
```

---

## 테스트 방법

### 1. Start New LOT
```bash
streamlit run streamlit_app/app.py --server.port 8502
```

1. Production Monitor → "Start New LOT"
2. 25개 wafer 생성 확인

### 2. Stage 0 → 모든 wafer가 Decision Queue에 나타남
```
Decision Queue:
  - Stage 0: LOT-001-W01 (AI: INLINE or PASS)
  - Stage 0: LOT-001-W02 (AI: INLINE or PASS)
  - Stage 0: LOT-001-W03 (AI: INLINE or PASS)
  ...
  - Stage 0: LOT-001-W25 (AI: INLINE or PASS)
```

**기대:** ~20-25개의 Stage 0 decisions (anomaly 비율에 따라)

### 3. INLINE 선택 → Stage 1 Decision 나타남
```
Stage 0: LOT-001-W01 → INLINE 선택
  ↓
Decision Queue:
  - Stage 1: LOT-001-W01 (AI: PASS or REWORK or SCRAP)
```

**기대:** Stage 1 decision이 **즉시** 나타남 (사라지지 않음)

### 4. 모든 Stage에서 확인
- Stage 0 → INLINE → Stage 1 decision 나타남 ✅
- Stage 1 → PROCEED → Stage 2A decision 나타남 ✅
- Stage 2A → PROCEED → Stage 2B decision 나타남 ✅
- Stage 2B → PROCEED → Stage 3 decision 나타남 ✅

### 5. Phase 2에서 SKIP 동작 확인
```
Stage 2A: LOT-001-W05 (yield_pred = 0.75, low but in Phase 2)
  → Engineer: SKIP (팹아웃)
  ↓
✅ COMPLETED at Stage 2A
Note: 수율 낮지만 rework 불가하므로 팹아웃
```

---

## 예상 결과

### LOT 완료 후 통계
```
LOT-001 Completed:
  Total: 25 wafers

  Completed: 22 wafers (88%)
    - Stage 0 (SKIP): 5 wafers (20%)
    - Stage 1 (SKIP/after rework): 12 wafers (48%)
    - Stage 2A (SKIP): 3 wafers (12%)
    - Stage 2B (SKIP): 1 wafer (4%)
    - Stage 3 (COMPLETE): 1 wafer (4%)

  Scrapped: 3 wafers (12%)
    - Stage 1 (SCRAP): 3 wafers

  Decision Count: ~75-100 decisions
    - Stage 0: ~25 decisions
    - Stage 1: ~20 decisions
    - Stage 2A: ~10 decisions
    - Stage 2B: ~5 decisions
    - Stage 3: ~2 decisions

  Total Cost: ~$3,500-5,000
    - Stage 1 cost: ~$3,000 (20 wafers × $150)
    - Rework cost: ~$400-800 (2-4 reworks × $200)
    - Stage 2+ cost: ~$500-1,000
```

---

## 주요 개선사항

### ✅ 완전한 추적성
- 모든 wafer가 Decision Queue에 나타남
- 엔지니어가 모든 stage transition 검토
- Decision history 완벽 기록

### ✅ 직관적인 Workflow
- "INLINE 선택 → Stage 1 decision 나타남" (예상대로 동작)
- "모든 wafer 추적 가능" (누락 없음)

### ✅ Phase 2 로직 명확
- Rework 불가 명시
- SKIP (팹아웃) vs PROCEED (원인분석) 선택 명확
- 수율 낮아도 팹아웃 가능

### ✅ 학습 데이터 풍부
- 모든 decision 기록
- AI recommendation vs Engineer decision 비교
- PASS recommendation에 대한 engineer action 학습

---

## 성능 영향

### Before (Option 1)
- Decision Queue: ~10-15 decisions (anomaly만)
- Auto-complete: ~10-15 wafers (80%)
- Engineer review: ~20% wafers

### After (Option 2)
- Decision Queue: ~75-100 decisions (모든 transition)
- Auto-complete: 0 wafers (0%)
- Engineer review: 100% wafers

**Trade-off:**
- ➕ 완전한 제어와 추적성
- ➕ 풍부한 학습 데이터
- ➖ 더 많은 decision 필요 (하지만 PASS는 빠르게 SKIP 가능)

---

## 최종 상태

**✅ 모든 기능 완성:**
- Sequential wafer processing
- **모든 stage transition → Decision Queue**
- Phase 1: Rework 가능
- Phase 2: Rework 불가, SKIP (팹아웃) 또는 PROCEED (원인분석)
- Rework badge display
- Cost tracking
- No wafer loss

**✅ 테스트 준비 완료**
- 모든 wafer 추적 가능
- 직관적인 workflow
- Phase별 로직 명확

---

**Status:** ✅ **완료 및 테스트 준비 완료**
**Test:** 이제 "Start New LOT" → 모든 wafer가 Decision Queue에 나타남!
