# 🧪 Complete Pipeline Test Guide - 유기적 동작 검증

**Date:** 2026-01-29
**Status:** ✅ ALL FUNCTIONS IMPLEMENTED

---

## 📋 구현 완료 항목

### ✅ Phase 1 (In-Line) - COMPLETE
- **Stage 0**: INLINE / SKIP / HOLD ✅
- **Stage 1**: REWORK / PROCEED / SCRAP / HOLD ✅

### ✅ Phase 2 (Post-Fab) - COMPLETE
- **Stage 2A**: TO_EDS / LOT_SCRAP / REWORK_ATTEMPT ✅
- **Stage 2B**: APPROVE_ALL / APPROVE_PARTIAL / SKIP_SEM / REVISE_LIST ✅
- **Stage 3**: IMPLEMENT / MODIFY / INVESTIGATE / DEFER ✅

### ✅ 모든 액션 버튼 - COMPLETE
- **✅ Approve**: 선택한 옵션으로 다음 stage 실행
- **❌ Reject**: 파이프라인 종료, 로그 기록
- **📝 Modify**: 커스텀 추천 + 노트, 다음 stage 실행
- **⏸️ Hold**: Hold 리스트로 이동

---

## 🧪 테스트 시나리오

### 시나리오 1: 정상 플로우 (전체 파이프라인 완주)

```
1. Production Monitor
   └─ "Start New LOT" 클릭
       └─ 25 wafers 생성
           └─ 일부 flagged (red/yellow)

2. Decision Queue
   └─ Stage 0 Decision 확인
       ├─ Select: INLINE
       └─ [✅ Approve] 클릭
           └─ ⏳ "Performing Inline measurement..."
               └─ ✅ "Stage 1 Decision created"

3. Stage 1 Decision 자동 생성
   ├─ Yield prediction 확인
   ├─ Select: PROCEED
   └─ [✅ Approve] 클릭
       └─ ⏳ "Processing to Stage 2A..."
           └─ ✅ "Stage 2A Decision created"

4. Stage 2A Decision 자동 생성 (LOT-level)
   ├─ Electrical quality 확인
   ├─ Select: TO_EDS
   └─ [✅ Approve] 클릭
       └─ ⏳ "Analyzing wafermap patterns..."
           └─ ✅ "Stage 2B Decision created"

5. Stage 2B Decision 자동 생성 (SEM candidates)
   ├─ SEM 후보 리스트 확인
   ├─ Select: APPROVE_ALL
   └─ [✅ Approve] 클릭
       └─ ⏳ "Performing SEM analysis..."
           └─ ✅ "Stage 3 Decision created"

6. Stage 3 Decision 자동 생성
   ├─ 🧠 LLM 한국어 분석 확인
   ├─ Defect type, count 확인
   ├─ Select: IMPLEMENT
   └─ [✅ Approve] 클릭
       └─ 🎉 "Pipeline completed!"
           └─ 🎈 Balloons!
```

**예상 결과:**
- ✅ 모든 stage가 순차적으로 생성됨
- ✅ 각 stage에서 데이터가 전달됨
- ✅ 최종 완료 시 풍선 애니메이션
- ✅ 터미널에 DEBUG 로그 출력

---

### 시나리오 2: Stage 0에서 SKIP

```
1. Stage 0 Decision
   ├─ Select: SKIP
   └─ [✅ Approve] 클릭
       └─ ⏭️ "SKIPPED inline measurement"
           └─ Alert 생성
               └─ 파이프라인 종료 (정상 공정 진행)
```

**예상 결과:**
- ✅ Skip 메시지 표시
- ✅ Alert 생성됨
- ✅ 다음 stage 생성 안 됨 (정상)

---

### 시나리오 3: Stage 1에서 REWORK

```
1. Stage 1 Decision
   ├─ Select: REWORK
   └─ [✅ Approve] 클릭
       └─ 🔄 "Sent to REWORK"
           └─ Alert 생성
               └─ 파이프라인 일시 중단
```

**예상 결과:**
- ✅ Rework 메시지 표시
- ✅ Alert 생성됨
- ✅ Decision log에 기록됨

---

### 시나리오 4: Stage 1에서 SCRAP

```
1. Stage 1 Decision
   ├─ Select: SCRAP
   └─ [✅ Approve] 클릭
       └─ ❌ "SCRAPPED"
           └─ Alert 생성
               └─ 파이프라인 종료
```

**예상 결과:**
- ✅ Scrap 에러 메시지 표시
- ✅ Alert 생성됨
- ✅ Decision log에 기록됨

---

### 시나리오 5: REJECT 버튼 테스트

```
1. 아무 Stage Decision
   └─ [❌ Reject] 클릭
       └─ ❌ "Decision REJECTED"
           └─ ⚠️ "Pipeline terminated"
               └─ Alert 생성
                   └─ Decision log 기록
```

**예상 결과:**
- ✅ Reject 에러 메시지
- ✅ Pipeline 종료 경고
- ✅ Alert 생성됨
- ✅ Decision log에 'REJECTED' 기록

---

### 시나리오 6: MODIFY 버튼 테스트

```
1. Stage 1 Decision (AI: PROCEED)
   └─ [📝 Modify] 클릭
       └─ 📝 Modify UI 표시
           ├─ New recommendation: REWORK
           ├─ Engineer note: "CD out of spec"
           └─ [💾 Save] 클릭
               └─ 📝 "Decision MODIFIED: PROCEED → REWORK"
                   └─ Alert 생성
                       └─ Rework 플로우 실행
```

**예상 결과:**
- ✅ Modify UI가 표시됨
- ✅ Save 시 REWORK 실행됨
- ✅ Decision log에 'MODIFIED' + note 기록
- ✅ Agreement = False

---

### 시나리오 7: HOLD 버튼 테스트

```
1. Stage 0 Decision
   └─ [⏸️ Hold] 클릭
       └─ ⏸️ "Decision placed on HOLD"
           └─ 💡 "Unhold later from Hold Queue"
               └─ held_decisions 리스트로 이동
                   └─ pending_decisions에서 제거
```

**예상 결과:**
- ✅ Hold 메시지 표시
- ✅ held_decisions에 추가됨
- ✅ pending_decisions에서 제거됨
- ✅ Decision log에 'HOLD' 기록

---

### 시나리오 8: Stage 2A LOT SCRAP

```
1. Stage 2A Decision
   ├─ Select: LOT_SCRAP
   └─ [✅ Approve] 클릭
       └─ ❌ "SCRAPPED. Entire LOT discarded."
           └─ Alert 생성
               └─ 파이프라인 종료
```

**예상 결과:**
- ✅ LOT scrap 에러 메시지
- ✅ Alert 생성됨
- ✅ 전체 LOT 폐기 처리

---

### 시나리오 9: Stage 2B SKIP_SEM

```
1. Stage 2B Decision
   ├─ Select: SKIP_SEM
   └─ [✅ Approve] 클릭
       └─ ⏭️ "SEM analysis SKIPPED for cost savings"
           └─ Alert 생성
               └─ 파이프라인 종료
```

**예상 결과:**
- ✅ Skip 메시지 표시
- ✅ Alert 생성됨
- ✅ Stage 3 생성 안 됨 (정상)

---

## 🔍 디버깅 체크리스트

### 터미널 로그 확인

**Stage 0 Approve 시:**
```
[DEBUG] ========== APPROVE DECISION ==========
[DEBUG] Decision ID: LOT-20260129-171907-W01-stage0
[DEBUG] Recommendation: INLINE
[DEBUG] Found decision: Stage 0, wafer: LOT-20260129-171907-W01
[DEBUG] Calling execute_stage0_to_stage1(LOT-20260129-171907-W01, LOT-20260129-171907)
[DEBUG] execute_stage0_to_stage1 called: LOT-20260129-171907-W01, LOT-20260129-171907
[DEBUG] Found wafer data: LOT-20260129-171907-W01
[DEBUG] Stage 1 decision created: LOT-20260129-171907-W01-stage1
[DEBUG] Alert added: Inline measurement completed
[DEBUG] Added next decision: LOT-20260129-171907-W01-stage1
[DEBUG] Logged decision: APPROVED for LOT-20260129-171907-W01
```

**Reject 시:**
```
[DEBUG] ========== REJECT DECISION ==========
[DEBUG] Decision ID: LOT-xxx-stage0
[DEBUG] Decision rejected, pipeline terminated
[DEBUG] Logged decision: REJECTED for LOT-xxx-W01
```

**Modify 시:**
```
[DEBUG] ========== MODIFY DECISION ==========
[DEBUG] Decision ID: LOT-xxx-stage1
[DEBUG] New Recommendation: REWORK
[DEBUG] Note: CD out of spec
[DEBUG] Logged decision: MODIFIED for LOT-xxx-W01
```

**Hold 시:**
```
[DEBUG] ========== HOLD DECISION ==========
[DEBUG] Decision ID: LOT-xxx-stage0
[DEBUG] Decision moved to held list
[DEBUG] Logged decision: HOLD for LOT-xxx-W01
```

---

## ⚠️ 문제 해결

### 문제 1: Stage 1 Decision이 생성 안 됨

**원인:**
- `get_wafer_data(wafer_id)`가 웨이퍼를 못 찾음
- wafer_id 형식 불일치

**확인:**
```python
# 터미널에서 확인
[ERROR] Wafer not found: LOT-xxx-W01
```

**해결:**
- Production Monitor에서 wafer_id 형식 확인
- LOT ID와 웨이퍼 번호 매칭 확인

---

### 문제 2: Import Error

**증상:**
```
❌ Import error: No module named 'stage_executors'
```

**해결:**
1. `streamlit_app/utils/__init__.py` 존재 확인
2. `streamlit_app/utils/stage_executors.py` 존재 확인
3. Streamlit 재시작

---

### 문제 3: Modify UI가 안 닫힘

**해결:**
- Cancel 버튼 클릭
- Save 후 자동으로 닫힘 (st.rerun())

---

## 📊 성공 지표

### ✅ 모든 기능이 정상 작동하는 경우:

1. **Stage 0 → Stage 1**
   - ✅ INLINE 선택 시 Stage 1 생성됨
   - ✅ SKIP 선택 시 Skip 메시지, Stage 1 생성 안 됨
   - ✅ HOLD 선택 시 Hold 리스트로 이동

2. **Stage 1 → Stage 2A**
   - ✅ PROCEED 선택 시 Stage 2A 생성됨
   - ✅ REWORK 선택 시 Rework 메시지
   - ✅ SCRAP 선택 시 Scrap 메시지
   - ✅ HOLD 선택 시 Hold 리스트로 이동

3. **Stage 2A → Stage 2B**
   - ✅ TO_EDS 선택 시 Stage 2B 생성됨
   - ✅ LOT_SCRAP 선택 시 LOT Scrap 메시지
   - ✅ REWORK_ATTEMPT 선택 시 Special Rework 메시지

4. **Stage 2B → Stage 3**
   - ✅ APPROVE_ALL 선택 시 Stage 3 생성됨
   - ✅ APPROVE_PARTIAL 선택 시 Stage 3 생성됨
   - ✅ SKIP_SEM 선택 시 Skip 메시지
   - ✅ REVISE_LIST 선택 시 Revise 메시지

5. **Stage 3 완료**
   - ✅ IMPLEMENT 선택 시 완료 + "Process improvements will be implemented"
   - ✅ MODIFY 선택 시 완료 + "Recommendations will be modified"
   - ✅ INVESTIGATE 선택 시 완료 + "Further investigation required"
   - ✅ DEFER 선택 시 완료 + "Implementation deferred"
   - ✅ 🎈 풍선 애니메이션

6. **액션 버튼**
   - ✅ Approve: 선택한 옵션으로 실행
   - ✅ Reject: 파이프라인 종료
   - ✅ Modify: 새 추천으로 실행
   - ✅ Hold: Hold 리스트로 이동

7. **로깅**
   - ✅ 모든 decision이 decision_log에 기록됨
   - ✅ Agreement 계산 정확함
   - ✅ Engineer note 저장됨

8. **알림**
   - ✅ 모든 액션에 대해 alert 생성됨
   - ✅ Production Monitor에서 alert 확인 가능

---

## 🎯 최종 확인

### 전체 파이프라인 테스트 (5분)

1. **Start New LOT** (30초)
2. **Stage 0 INLINE** (30초)
3. **Stage 1 PROCEED** (30초)
4. **Stage 2A TO_EDS** (30초)
5. **Stage 2B APPROVE_ALL** (30초)
6. **Stage 3 IMPLEMENT** (30초)
   - 🎈 Balloons!
7. **Home Page 확인** (1분)
   - Activity feed 확인
   - Agreement rate 확인
8. **Production Monitor 확인** (1분)
   - Alerts 확인
9. **AI Insights 확인** (30초)
   - Pattern Discovery
   - Root Cause
   - Learning Insights

---

## 🚀 데모 스크립트

**5분 데모 (논문/발표용):**

```
"안녕하세요. AI 기반 반도체 품질 관리 시스템을 소개합니다.

1. [Production Monitor]
   "먼저 새로운 LOT를 시작하겠습니다. 25개 웨이퍼가 생성되고,
    일부는 이상 징후로 플래그됩니다."

2. [Decision Queue]
   "플래그된 웨이퍼에 대해 AI가 INLINE 계측을 추천합니다.
    엔지니어가 승인하면..."

3. [Stage 1]
   "자동으로 Stage 1 분석이 실행되고, 수율 예측 결과를 보여줍니다.
    PROCEED를 승인하면..."

4. [Stage 2A]
   "LOT 레벨 전기적 특성 분석이 실행됩니다.
    TO_EDS를 승인하면..."

5. [Stage 2B]
   "웨이퍼맵 패턴을 분석하고 SEM 후보를 자동 선정합니다.
    APPROVE_ALL을 승인하면..."

6. [Stage 3]
   "SEM 이미지 분석과 함께 LLM이 한국어로 근본 원인을 분석합니다.
    보시다시피, 센서 데이터와 결함 패턴의 상관관계를 설명하고,
    단기/중기/장기 조치를 제안합니다.

    IMPLEMENT를 승인하면..."

7. [완료]
   "🎉 전체 파이프라인이 완료되었습니다!

    이제 Home으로 돌아가면, 엔지니어의 의사결정 이력과
    AI와의 합의율을 확인할 수 있습니다."

8. [결론]
   "이 시스템은 센서 모니터링부터 SEM 분석까지 다단계 파이프라인을
    자동화하고, 각 단계에서 Human-AI Collaboration을 통해
    최적의 의사결정을 지원합니다.

    특히 한국어 LLM 분석으로 한국 반도체 공정 엔지니어들이
    쉽게 이해하고 활용할 수 있습니다."
```

---

**Last Updated:** 2026-01-29 17:30
**Status:** ✅ ALL FUNCTIONS IMPLEMENTED AND TESTED
**Access:** http://localhost:8502

---

## 🎊 준비 완료!

모든 기능이 유기적으로 동작합니다. 지금 바로 테스트하세요! 🚀
