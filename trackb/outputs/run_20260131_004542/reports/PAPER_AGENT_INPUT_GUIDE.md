# Paper AI Agent Input Guide

**Run ID:** `run_20260131_004542`  
**Date:** 2026-01-31  
**Purpose:** Guide for paper-generating AI Agent

---

## 📋 Quick Start: Essential Files (Read These First)

논문 작성 AI Agent는 아래 **4개 핵심 파일**을 우선 읽고, 필요시 추가 파일을 참조하세요.

### 🔴 **MUST READ (Priority 1 - Core Evidence)**

1. **`trackB_report_core_validated.md`** (143 lines)
   - **내용:** Step1 (Stage 0+1) 검증 결과 (same-wafer ground truth)
   - **핵심 지표:**
     - Recall: Random 5.0% → AI 15.0% (ΔRecall observed, but 95% CI includes 0)
     - Cost: Normalized units (inline_cost_norm, NOT currency)
     - Primary Endpoint: Bootstrap CI-based conclusion only
     - Validation: Hold-out test (wafer_id-based split)
   - **Why Essential:** 이 파일만이 "정량 성능 주장"을 할 수 있는 유일한 근거입니다. 논문의 메인 클레임은 여기서만 가져와야 합니다.
   - **Key Sections:**
     - Section 3: Core Primary Results (Comparison Table)
     - Section 4: Statistical Validation (Bootstrap CI, Random Seed Sweeps)
     - Section 5: Limitations (Lot leakage, Class imbalance 20%, CI interpretation)

2. **`trackB_report_appendix_proxy.md`** (73 lines)
   - **내용:** Step2 (Pattern) + Step3 (SEM) Proxy 검증 결과
   - **핵심 지표:**
     - WM-811K: Accuracy 86.4%, Macro-F1 0.69 (external wafermap dataset)
     - Carinthia: AI vs Random severity/triage ratios (external SEM dataset)
   - **Why Essential:** Step2/3의 존재 이유와 검증 범위를 명확히 합니다. **주의: 이 결과는 Core 결론에 포함하면 안 됩니다 (different source).**
   - **Key Sections:**
     - Section B: Validation Scope (Proxy plausibility check only)
     - Section C: "FAILED" 해석 (정책 위반 검출, 기술 실패 아님)
     - Section D: 책임감 있게 주장할 수 있는 내용
     - Section E: Future Plan (same-wafer GT 확보 후 end-to-end 검증)

3. **`trackA_report.md`** (975 lines)
   - **내용:** 운영 워크플로우 & Web UI 시스템 (Human-in-the-Loop)
   - **핵심 기능:**
     - Sequential wafer processing (25 wafers/LOT)
     - Multi-stage pipeline (Stage 0 → 1 → 2A → 2B → 3)
     - Rework logic (Phase 1, 70% improvement probability)
     - SEM destructive testing (Stage 3 scraps wafer)
     - Economic transparency (cost/benefit at each stage)
     - Audit trail (all decisions logged)
   - **Why Essential:** 시스템이 "실제로 어떻게 작동하는지" (운영 관점)를 보여줍니다. 하지만 **정량 성능은 Track B Core에만 의존**합니다.
   - **Key Sections:**
     - Section 1: Executive Summary
     - Section 2: System Architecture & Operational Flow
     - Section 3: Web UI Features (Decision Queue, Production Monitor)
     - Section 7: Connection to Track B (Core vs Proxy 구분)
     - Section 8: Validation Status (Track A는 운영 워크플로우만 검증)

4. **`paper_bundle.json`** (structured metadata)
   - **내용:** 전체 파이프라인 입출력 정의, 스펙, 파일 경로
   - **Why Essential:** 논문 AI Agent가 데이터 파일 위치, 스펙 준수 여부, 입출력 계약을 확인할 수 있습니다.
   - **Key Fields:**
     - `spec_version`: 파이프라인 스펙 버전
     - `inputs`: 각 Step별 입력 파일 경로
     - `outputs`: 각 Step별 출력 파일 경로
     - `validation_status`: Core (validated) vs Proxy (benchmark)
     - `primary_claims`: 주장 가능한 결론 (Core만)

---

## 📚 Supporting Files (Optional - Read If Needed)

### 🟡 **SHOULD READ (Priority 2 - Validation Details)**

5. **`FINAL_VALIDATION.md`**
   - **내용:** 전체 검증 요약 (Core + Proxy + 정책 준수)
   - **When to read:** 검증 절차, 정책 위반 검사 방법을 상세히 알고 싶을 때

6. **`PAPER_IO_TRACE.md`**
   - **내용:** 논문 제출용 입출력 추적 (각 보고서가 어떤 데이터에서 생성되었는지)
   - **When to read:** 재현성 확보, 데이터 계보(lineage) 설명이 필요할 때

7. **`methodology.md`**
   - **내용:** 검증 방법론 (Bootstrap CI, Hold-out test, Random seed sweep)
   - **When to read:** Methods section 작성 시

8. **`limitations.md`**
   - **내용:** 시스템 한계 (Lot leakage, Class imbalance, Proxy 검증 범위)
   - **When to read:** Limitations section 작성 시

### 🟢 **MAY READ (Priority 3 - Background)**

9. **`executive_summary.md`**
   - **내용:** 전체 시스템 요약 (비기술 관점)
   - **When to read:** Abstract/Introduction 작성 시

10. **`results_detailed.md`**
    - **내용:** 상세 결과 (Core 테이블의 확장 버전)
    - **When to read:** Results section에 추가 지표 필요 시

11. **`SPEC_COMPLIANCE.md`**
    - **내용:** 파이프라인 스펙 준수 여부 체크리스트
    - **When to read:** 스펙 준수 증명이 필요할 때

12. **`PIPELINE_IO_TRACE.md`**
    - **内容:** 파이프라인 실행 추적 (내부 디버깅용)
    - **When to read:** 기술 상세가 필요할 때 (논문에는 보통 불필요)

---

## 🚨 Critical Rules for Paper Writing

### ✅ DO (Safe to Claim)

1. **Core 결과 (Step1 Stage 0+1):**
   - ✅ "Recall improved from 5.0% (random) to 15.0% (AI) in same-wafer ground truth experiment"
   - ✅ "ΔRecall signal observed, but 95% bootstrap CI includes 0 → cautious interpretation required"
   - ✅ "Cost expressed in normalized units (not currency)"
   - ✅ "Validation via hold-out test (wafer_id-based split)"

2. **Track A 운영 워크플로우:**
   - ✅ "System demonstrates Human-in-the-Loop workflow with explainable AI recommendations"
   - ✅ "Rework capability in Phase 1 with new sensor data generation"
   - ✅ "SEM destructive testing correctly reflected in yield tracking"
   - ✅ "Budget tracking and audit trail for all decisions"

3. **Proxy 벤치마크 (Step2/3):**
   - ✅ "Pattern classification achieved 86.4% accuracy on WM-811K (external benchmark, proxy only)"
   - ✅ "SEM triage ratios on Carinthia dataset (external benchmark, proxy only)"
   - ✅ "These results are reported as capability benchmarks, not validated for this fab environment"

### ❌ DON'T (Forbidden)

1. **절대 하지 말아야 할 주장:**
   - ❌ "Recall improved **significantly** from 5.0% to 15.0%" (CI includes 0 → cannot claim statistical significance)
   - ❌ "Total cost is $3,000" (절대 통화 단위 사용 금지, normalized units만 허용)
   - ❌ "End-to-end pipeline achieved 15.0% recall and 86.4% accuracy" (Core + Proxy 혼합 금지)
   - ❌ "System validated across Stages 0-3" (Stage 0-1만 validated, 2-3은 proxy)

2. **과장 표현:**
   - ❌ "입증하였습니다", "statistically proven", "확인되었습니다"
   - ✅ 대신 사용: "observed signal", "suggests improvement", "preliminary evidence"

3. **Proxy를 Core처럼 주장:**
   - ❌ "Our system achieved 86.4% accuracy" (WM-811K는 external dataset)
   - ✅ 대신 사용: "Pattern classifier shows 86.4% accuracy on WM-811K benchmark (proxy, different source)"

---

## 📊 Key Numbers Reference (Quick Copy-Paste for Paper)

### Core Results (Step1 - Validated)
```
- Random Framework: Recall 5.0%, inline_cost_norm X, total_cost_norm Y
- AI Framework: Recall 15.0%, inline_cost_norm X', total_cost_norm Y'
- ΔRecall: +10.0 percentage points (signal observed)
- 95% Bootstrap CI: [lower, upper] (includes 0 → no statistical significance claim)
- Hold-out test: wafer_id-based split, N_train / N_test wafers
- Random seed sweep: 10 seeds, std(Recall) reported
```

### Proxy Benchmarks (Step2/3 - NOT Validated for Primary Claims)
```
- WM-811K: Accuracy 86.4%, Macro-F1 0.69, Precision 0.74, Recall 0.67
- Carinthia: AI vs Random severity mean, triage ratio (different source)
- Label: "Proxy benchmark only, not validated for this fab"
```

### Track A Operational (Workflow Demonstration)
```
- LOT size: 25 wafers
- Stages: 5 (Stage 0, 1, 2A, 2B, 3)
- Rework: Phase 1 only, 70% improvement probability
- SEM: Destructive testing, wafer scrapped at Stage 3
- Budget: Inline (normalized), SEM (normalized), Rework (normalized)
```

---

## 🎯 Recommended Paper Structure

### Abstract
- **Sources:** `trackB_report_core_validated.md` (Core results ONLY)
- **Avoid:** Proxy 수치, Track A 정량 클레임

### Introduction
- **Sources:** `trackA_report.md` Section 1, `executive_summary.md`
- **Focus:** Problem statement, fab constraints, Human-in-the-Loop motivation

### Related Work
- **Sources:** Not in reports (논문 AI Agent가 외부 검색 필요)

### Methodology
- **Sources:** `methodology.md`, `trackB_report_core_validated.md` Section 2
- **Focus:** Bootstrap CI, Hold-out test, Random seed sweep

### System Design (Track A)
- **Sources:** `trackA_report.md` Sections 2-3
- **Focus:** Multi-stage pipeline, Rework logic, SEM destructive testing, UI/UX

### Validation (Track B Core)
- **Sources:** `trackB_report_core_validated.md` Sections 3-5
- **Focus:** Core results, Statistical tests, Limitations

### Proxy Benchmarks (Optional Section)
- **Sources:** `trackB_report_appendix_proxy.md`
- **Focus:** Step2/3 capability demonstration, Future work

### Limitations
- **Sources:** `limitations.md`, `trackB_report_core_validated.md` Section 5
- **Focus:** Lot leakage, Class imbalance, Proxy scope, CI interpretation

### Conclusion
- **Sources:** `trackB_report_core_validated.md` Section 6 (if exists), `executive_summary.md`
- **Focus:** Core 결과 요약 (cautious tone), Future work

---

## 🔍 How to Use This Guide

### Step 1: Read Priority 1 Files (30 min)
```bash
# In order:
1. trackB_report_core_validated.md    # Core evidence
2. trackB_report_appendix_proxy.md    # Proxy benchmarks
3. trackA_report.md                    # System design
4. paper_bundle.json                   # Metadata
```

### Step 2: Understand Validation Boundaries
- **Core (validated):** Step1 Stage 0+1 ONLY
- **Proxy (benchmark):** Step2/3 on external datasets
- **Track A (operational):** Workflow demonstration, no quantitative claims

### Step 3: Draft Paper Sections
- Use Core results for **Abstract, Results, Conclusion**
- Use Track A for **System Design section**
- Use Proxy for **Optional appendix or Future Work**
- **Never mix Core + Proxy in same claim**

### Step 4: Apply Critical Rules
- Search paper draft for: `$`, `3000`, `150`, `500` → Replace with `normalized units` or remove
- Search for: `statistically significant`, `proven`, `입증` → Replace with cautious language
- Search for: `Stage 2`, `Stage 3`, `86.4%`, `WM-811K` → Check labeled as "Proxy"
- Search for: `15.0%` → Check includes "ΔRecall signal observed, CI includes 0"

### Step 5: Verify Against Evidence Gate
```python
# Pseudo-check:
for claim in paper:
    if "recall" in claim or "cost" in claim or "performance" in claim:
        assert source == "trackB_report_core_validated.md"
        assert "Proxy" not in source_context
        assert "$" not in claim
```

---

## 📞 Contact & Support

**Questions About:**
- Core validation → Read `trackB_report_core_validated.md` Section 5 (Limitations)
- Proxy scope → Read `trackB_report_appendix_proxy.md` Section B
- Track A features → Read `trackA_report.md` Section 8 (Validation Status)
- File locations → Check `paper_bundle.json`

**Report Issues:**
- Validation errors → Check `FINAL_VALIDATION.md`
- Policy violations → Check `SPEC_COMPLIANCE.md`
- Missing data → Check `PAPER_IO_TRACE.md`

---

## ✅ Final Checklist Before Submission

- [ ] Abstract uses Core results ONLY (no Proxy)
- [ ] All cost values in "normalized units" (no $, no 3000/150/500)
- [ ] "15.0% recall" always accompanied by "ΔRecall CI includes 0"
- [ ] Step2/3 results labeled "Proxy benchmark (different source)"
- [ ] Track A claims limited to "workflow demonstration" (no quantitative)
- [ ] No mixing of Core + Proxy in same sentence/paragraph
- [ ] Limitations section includes: Lot leakage, Class imbalance 20%, CI interpretation
- [ ] References cite: `run_20260131_004542` as evidence binding

---

**Guide Version:** 1.0  
**Last Updated:** 2026-01-31  
**Run Binding:** `run_20260131_004542`  
**Total Report Files:** 14 (4 essential + 10 supporting)
