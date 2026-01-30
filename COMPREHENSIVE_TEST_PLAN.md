# 종합 테스트 계획 - Sequential Wafer Processing

**Date:** 2026-01-29
**Purpose:** Stage 0부터 Stage 3까지 모든 경우의 수 테스트

---

## 테스트 환경 설정

```bash
# 1. Streamlit 앱 시작
streamlit run streamlit_app/app.py --server.port 8502

# 2. 브라우저 열기
http://localhost:8502
```

---

## 테스트 케이스 매트릭스

### Stage 0 (Sensor Monitoring)
| 케이스 | 액션 | 기대 결과 | 검증 항목 |
|--------|------|-----------|----------|
| S0-1 | INLINE | Stage 1로 즉시 이동 | ✅ Wafer가 Stage 1에서 재처리<br>✅ 비용 +$150<br>✅ Decision Queue에 Stage 1 decision 나타남 |
| S0-2 | SKIP | 웨이퍼 완료 | ✅ Wafer status = COMPLETED<br>✅ Completion stage = Stage 0<br>✅ 추가 비용 없음<br>✅ 다음 wafer로 진행 |

### Stage 1 (Inline Inspection)
| 케이스 | 액션 | 기대 결과 | 검증 항목 |
|--------|------|-----------|----------|
| S1-1 | SKIP | 웨이퍼 완료 (false positive) | ✅ Wafer status = COMPLETED<br>✅ Completion stage = Stage 1<br>✅ 추가 비용 없음 |
| S1-2 | PROCEED | Stage 2A로 즉시 이동 | ✅ Wafer가 Stage 2A에서 재처리<br>✅ 비용 +$100<br>✅ Decision Queue에 Stage 2A decision 나타남 |
| S1-3 | REWORK (70% 개선) | 새 센서 데이터 생성 후 완료 | ✅ 새로운 센서 데이터 생성 (is_rework=True)<br>✅ Rework count +1<br>✅ 비용 +$200<br>✅ Wafer status = COMPLETED<br>✅ **리워크 뱃지 표시: "🔄 REWORK x1"** |
| S1-4 | REWORK (30% 여전히 불량) | 새 센서 데이터 생성 후 재검토 | ✅ 새로운 센서 데이터 생성<br>✅ Rework count +1<br>✅ 비용 +$200<br>✅ Decision Queue에 새 Stage 1 decision<br>✅ **리워크 뱃지 표시: "🔄 REWORK x1"** |
| S1-5 | SCRAP | 웨이퍼 폐기 | ✅ Wafer status = SCRAPPED<br>✅ LOT stats: scrapped +1<br>✅ 다음 wafer로 진행 |

### Stage 2A (WAT Analysis)
| 케이스 | 액션 | 기대 결과 | 검증 항목 |
|--------|------|-----------|----------|
| S2A-1 | SKIP | 웨이퍼 완료 | ✅ Wafer status = COMPLETED<br>✅ Completion stage = Stage 2A<br>✅ 추가 비용 없음 |
| S2A-2 | PROCEED | Stage 2B로 즉시 이동 | ✅ Wafer가 Stage 2B에서 재처리<br>✅ 비용 +$80<br>✅ Decision Queue에 Stage 2B decision |

### Stage 2B (Wafermap Pattern)
| 케이스 | 액션 | 기대 결과 | 검증 항목 |
|--------|------|-----------|----------|
| S2B-1 | SKIP | 웨이퍼 완료 | ✅ Wafer status = COMPLETED<br>✅ Completion stage = Stage 2B<br>✅ 추가 비용 없음 |
| S2B-2 | PROCEED | Stage 3로 즉시 이동 | ✅ Wafer가 Stage 3에서 재처리<br>✅ 비용 +$300<br>✅ Decision Queue에 Stage 3 decision |

### Stage 3 (SEM/Root Cause)
| 케이스 | 액션 | 기대 결과 | 검증 항목 |
|--------|------|-----------|----------|
| S3-1 | COMPLETE | 웨이퍼 완료 | ✅ Wafer status = COMPLETED<br>✅ Completion stage = Stage 3<br>✅ Root cause analysis 완료 |
| S3-2 | INVESTIGATE | 웨이퍼 완료 (추가 조사 필요) | ✅ Wafer status = COMPLETED<br>✅ Completion stage = Stage 3<br>✅ 추가 조사 플래그 설정 |

---

## 복합 시나리오 테스트

### 시나리오 1: 전체 파이프라인 통과 (최악의 경우)
```
Wafer #1:
Stage 0 → Anomaly detected → INLINE
  ↓ 비용: $150
Stage 1 → Low yield → REWORK (1차)
  ↓ 비용: $200
Stage 1 → Still low → REWORK (2차)
  ↓ 비용: $200
Stage 1 → Improved → PROCEED
  ↓ 비용: $100
Stage 2A → Pattern detected → PROCEED
  ↓ 비용: $80
Stage 2B → Edge-Ring pattern → PROCEED
  ↓ 비용: $300
Stage 3 → Root cause found → COMPLETE

총 비용: $1,030
리워크 횟수: 2
완료 Stage: Stage 3
```

**검증 항목:**
- ✅ Total cost = $1,030
- ✅ Rework count = 2
- ✅ **Decision Queue에서 "🔄 REWORK x2" 표시**
- ✅ Completion stage = Stage 3
- ✅ 모든 stage transition이 즉시 처리됨 (wafer 손실 없음)

### 시나리오 2: 조기 완료 (정상 웨이퍼)
```
Wafer #2:
Stage 0 → Normal → AUTO COMPLETE (no decision)

총 비용: $0
리워크 횟수: 0
완료 Stage: Stage 0
```

**검증 항목:**
- ✅ Total cost = $0
- ✅ Rework count = 0
- ✅ Completion stage = Stage 0
- ✅ Decision Queue에 나타나지 않음
- ✅ 즉시 다음 wafer로 진행

### 시나리오 3: False Positive Path
```
Wafer #3:
Stage 0 → Anomaly detected → INLINE
  ↓ 비용: $150
Stage 1 → Actually good → SKIP

총 비용: $150
리워크 횟수: 0
완료 Stage: Stage 1
```

**검증 항목:**
- ✅ Total cost = $150
- ✅ Completion stage = Stage 1
- ✅ False positive 처리 성공

### 시나리오 4: Rework Success
```
Wafer #4:
Stage 0 → Anomaly detected → INLINE
  ↓ 비용: $150
Stage 1 → Low yield → REWORK
  ↓ 비용: $200
Stage 1 → Improved (70% chance) → AUTO COMPLETE

총 비용: $350
리워크 횟수: 1
완료 Stage: Stage 1
```

**검증 항목:**
- ✅ Total cost = $350
- ✅ Rework count = 1
- ✅ **Decision Queue에서 "🔄 REWORK x1" 표시**
- ✅ Completion stage = Stage 1
- ✅ 새로운 센서 데이터 생성 (is_rework=True)

### 시나리오 5: Scrap Path
```
Wafer #5:
Stage 0 → Anomaly detected → INLINE
  ↓ 비용: $150
Stage 1 → Very low yield → SCRAP

총 비용: $150
리워크 횟수: 0
Status: SCRAPPED
```

**검증 항목:**
- ✅ Total cost = $150
- ✅ Wafer status = SCRAPPED
- ✅ LOT stats: scrapped count +1

---

## 자동화된 테스트 절차

### 테스트 1: Start New LOT
```
1. Production Monitor 페이지로 이동
2. "Start New LOT" 버튼 클릭
3. 확인:
   - ✅ 25개 wafer 생성
   - ✅ LOT status = PROCESSING
   - ✅ 첫 번째 wafer가 Stage 0에서 처리 시작
   - ✅ Decision Queue에 decisions 나타남 (anomaly 있는 경우)
```

### 테스트 2: Stage 0 → Stage 1 (INLINE)
```
1. Decision Queue 페이지로 이동
2. Stage 0 decision 찾기
3. "🔍 INLINE" 버튼 클릭
4. 확인:
   - ✅ "Moving to Stage 1 for inline inspection..." 메시지
   - ✅ Wafer cost = $150
   - ✅ LOT yield['stage1_cost'] = $150
   - ✅ Stage 1 decision이 즉시 나타남 (anomaly 있는 경우)
   - ✅ Wafer가 Decision Queue에서 사라지지 않음 (Stage 1에서 재등록)
```

### 테스트 3: Stage 1 → REWORK
```
1. Stage 1 decision 찾기 (yield_pred < 0.85인 경우)
2. "🔄 REWORK" 버튼 클릭
3. 확인:
   - ✅ "Re-processing with new sensor data..." 메시지
   - ✅ Wafer rework_count = 1
   - ✅ Wafer cost = 기존 cost + $200
   - ✅ LOT yield['rework_cost'] = $200
   - ✅ **Decision card header에 "🔄 REWORK x1" 표시**
   - ✅ 70% 확률: "Rework successful! Wafer improved." → COMPLETED
   - ✅ 30% 확률: "Rework complete, but still shows defects." → 새 Stage 1 decision
```

### 테스트 4: Multiple Reworks
```
1. Stage 1 decision (REWORK 후 여전히 불량)
2. 다시 "🔄 REWORK" 버튼 클릭
3. 확인:
   - ✅ Wafer rework_count = 2
   - ✅ Wafer cost = 기존 cost + $200 (총 $700 if started from Stage 0)
   - ✅ **Decision card header에 "🔄 REWORK x2" 표시**
   - ✅ rework_history에 2개 entry
```

### 테스트 5: Stage 1 → Stage 2A (PROCEED)
```
1. Stage 1 decision 찾기
2. "⏩ PROCEED" 버튼 클릭
3. 확인:
   - ✅ "→ Stage 2A for WAT analysis" 메시지
   - ✅ Wafer cost += $100
   - ✅ LOT yield['stage2_cost'] = $100
   - ✅ Stage 2A decision이 즉시 나타남 (anomaly 있는 경우)
```

### 테스트 6: Stage 2A → Stage 2B → Stage 3
```
1. Stage 2A에서 "⏩ PROCEED" 클릭
2. 확인:
   - ✅ Wafer cost += $80
   - ✅ Stage 2B decision 나타남

3. Stage 2B에서 "⏩ PROCEED" 클릭
4. 확인:
   - ✅ Wafer cost += $300
   - ✅ Stage 3 decision 나타남

5. Stage 3에서 "✅ COMPLETE" 클릭
6. 확인:
   - ✅ Wafer status = COMPLETED
   - ✅ Completion stage = Stage 3
   - ✅ "Root cause analysis COMPLETE" 메시지
```

### 테스트 7: SKIP at各 Stages
```
Stage 0 SKIP:
  - ✅ Wafer completes at Stage 0
  - ✅ No additional cost

Stage 1 SKIP:
  - ✅ Wafer completes at Stage 1
  - ✅ Cost = Stage 0 cost ($150 if INLINE, $0 if auto-pass)

Stage 2A SKIP:
  - ✅ Wafer completes at Stage 2A
  - ✅ Cost = previous stages cost

Stage 2B SKIP:
  - ✅ Wafer completes at Stage 2B
  - ✅ Cost = previous stages cost
```

### 테스트 8: Sequential Processing (No Wafer Loss)
```
1. Start New LOT (25 wafers)
2. Process 첫 5개 wafer through Stage 0:
   - Wafer #1: INLINE → Stage 1
   - Wafer #2: AUTO COMPLETE (no anomaly)
   - Wafer #3: INLINE → Stage 1
   - Wafer #4: AUTO COMPLETE
   - Wafer #5: INLINE → Stage 1

3. 확인:
   - ✅ Decision Queue에 Wafer #1, #3, #5의 Stage 1 decisions만 있음
   - ✅ Wafer #2, #4는 COMPLETED at Stage 0
   - ✅ **모든 wafer가 추적 가능** (누락 없음)
   - ✅ LOT stats: completed = 2, waiting = 3

4. Process Wafer #1 at Stage 1: PROCEED → Stage 2A
5. 확인:
   - ✅ Wafer #1이 Stage 2A decision으로 이동
   - ✅ Wafer #3, #5는 여전히 Stage 1에 대기 중
   - ✅ **Wafer #1이 사라지지 않음**
```

---

## Production Monitor 검증

### LOT 상태 표시
```
Production Monitor 페이지에서 확인:

✅ Progress bar: (completed + scrapped) / total
✅ Real-time stats:
   - Queued: QUEUED 상태 wafer 수
   - Processing: PROCESSING 상태 wafer 수
   - Waiting: WAITING_DECISION 상태 wafer 수
   - Completed: COMPLETED 상태 wafer 수 (yield rate 표시)
   - Scrapped: SCRAPPED 상태 wafer 수

✅ Wafer list (expander 내):
   - ⏳ QUEUED
   - ⚙️ PROCESSING
   - ⏸️ WAITING_DECISION
   - ✅ COMPLETED
   - ❌ SCRAPPED
   - 🔄xN REWORK (rework_count > 0인 경우)
```

### Yield 계산
```
LOT 완료 후 확인:

✅ yield_rate = completed / (completed + scrapped) * 100
✅ completed_at_stage0 = Stage 0에서 완료된 wafer 수
✅ completed_at_stage1 = Stage 1에서 완료된 wafer 수
✅ completed_after_rework = rework_count > 0인 완료 wafer 수
✅ total_cost = 모든 wafer의 total_cost 합계
✅ cost_per_good_wafer = total_cost / completed
```

---

## 오류 시나리오 테스트

### 오류 1: Wafer 손실
```
문제: Stage transition 후 wafer가 사라짐
원인: get_next_queued_wafer()가 잘못된 wafer 선택
수정: ✅ approve_decision에서 즉시 process_wafer_stage() 호출

테스트:
1. Stage 0 → INLINE 선택
2. 확인: Stage 1 decision이 즉시 나타남
3. 확인: Wafer ID가 동일함
```

### 오류 2: Cost 미추적
```
문제: Wafer cost가 증가하지 않음
원인: approve_decision에서 cost 추가 누락
수정: ✅ 모든 stage transition과 rework에 cost 추가

테스트:
1. Stage 0 → INLINE ($150)
2. Production Monitor에서 wafer total_cost 확인
3. Stage 1 → REWORK ($200)
4. 확인: total_cost = $350
```

### 오류 3: Rework 센서 데이터 미생성
```
문제: Rework 후 동일한 센서 데이터 사용
원인: is_rework=False로 process_wafer_stage() 호출
수정: ✅ is_rework=True로 호출

테스트:
1. Stage 1 → REWORK
2. wafer['stage_history'] 확인
3. 마지막 entry의 sensor_data['is_rework'] = True 확인
4. 센서 값이 이전과 다른지 확인
```

### 오류 4: Import 누락
```
문제: process_wafer_stage, complete_wafer 등 함수 import 안됨
원인: wafer_processor import 누락
수정: ✅ 파일 상단에 import 추가

테스트:
1. 앱 시작
2. 오류 없이 로딩되는지 확인
3. Decision 처리 시 오류 없는지 확인
```

---

## 최종 검증 체크리스트

### ✅ 기능 완성도
- [ ] Stage 0 → Stage 1 transition 즉시 처리
- [ ] Stage 1 → Stage 2A transition 즉시 처리
- [ ] Stage 2A → Stage 2B transition 즉시 처리
- [ ] Stage 2B → Stage 3 transition 즉시 처리
- [ ] REWORK 시 새로운 센서 데이터 생성
- [ ] 모든 stage에서 SKIP 동작
- [ ] SCRAP 동작
- [ ] **리워크 뱃지 표시 (🔄 REWORK xN)**

### ✅ 비용 추적
- [ ] Stage 0 → Stage 1: +$150
- [ ] Stage 1 → Stage 2A: +$100
- [ ] Stage 1 REWORK: +$200
- [ ] Stage 2A → Stage 2B: +$80
- [ ] Stage 2B → Stage 3: +$300
- [ ] Wafer total_cost 정확히 추적
- [ ] LOT yield cost breakdown 정확

### ✅ Sequential Processing
- [ ] 한 번에 하나의 wafer만 processing
- [ ] Wafer 손실 없음 (모든 transition 추적 가능)
- [ ] Decision Queue에서 올바른 wafer 표시
- [ ] process_next_wafer_in_lot() 정상 동작

### ✅ UI/UX
- [ ] **Decision card에 리워크 뱃지 표시**
- [ ] Real-time LOT 상태 업데이트
- [ ] Progress bar 정확
- [ ] Wafer list에 아이콘 표시
- [ ] 오류 메시지 명확

### ✅ Rework 기능
- [ ] Rework count 증가
- [ ] Rework history 기록
- [ ] 새로운 센서 데이터 생성
- [ ] 70% 개선 / 30% 불량 확률 동작
- [ ] **여러 번 rework 가능 (x2, x3...)**

---

## 성공 기준

### 최소 요구사항
1. ✅ 25개 wafer LOT 시작 성공
2. ✅ 모든 stage transition이 wafer 손실 없이 동작
3. ✅ Cost tracking 정확
4. ✅ Rework 기능 완벽 동작
5. ✅ **리워크 뱃지 표시**
6. ✅ LOT 완료까지 오류 없음

### 추가 목표
1. ✅ 모든 경우의 수 (20+ 시나리오) 테스트 통과
2. ✅ 복합 시나리오 (전체 파이프라인 통과) 성공
3. ✅ UI/UX 전문적이고 직관적
4. ✅ 성능: 25 wafer LOT을 10분 내 처리

---

**테스트 담당자:** AI Agent
**테스트 완료 목표:** 모든 체크리스트 항목 ✅
**최종 목표:** 논문/발표용 데모 준비 완료
