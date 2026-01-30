# Track B Appendix (Proxy Only)
## Step2/Step3 — Plausibility Only, NOT Causal

**Executive Summary (Appendix)**  
Step2/Step3 are candidate follow-up modules reported Appendix-only; they are not promoted to Core due to lack of same-wafer linkage and failed proxy alignment. The pipeline is ready to validate end-to-end utility once linked data is secured. Step2/3는 동일 웨이퍼 GT로 효용을 주장하는 목적이 아니라, 후속검사(wafermap/SEM) 단계에서 필요한 기능 블록을 모듈 단위로 검증하고, 통합 주장은 proxy 게이트에 의해 차단되는 구조를 보이기 위한 것이다.

**배너**: 본 부록은 Proxy(Step2/Step3) 결과만 다룹니다. Core 결론에 섞이지 않습니다.

**Appendix only — 주요 결론 제외**: Proxy validation FAILED. Step2/Step3 수치는 주요 결론에 사용하지 않습니다.

---
## A. Why Step2/Step3 Exist (Operational Design Intent)

Beyond Step1 (inline risk triage), a realistic fab pipeline needs downstream modules for triage prioritization, defect-type confirmation, and resource allocation. Step2B (wafermap pattern) and Step3 (SEM/defect classification) are **candidate follow-up modules** designed to plug into this pipeline. Step1이 "누구를 추가 계측 후보로 올릴지(Top-k)"를 결정한다면, Step2/3는 "후속검사에서 어떤 결함 유형을 우선 확인할지/어떤 검사 플로우로 보낼지"를 정하는 후보 모듈이다. They are evaluated here at module-level on external benchmarks; they are not claimed to increase real defect yield in the fab unless same-wafer GT exists.

---
## B. Validation Scope Statement

Step2B was validated on WM-811K; Step3 on the Carinthia dataset. There is **no shared wafer_id** and **no same-wafer GT** across Step1, Step2, and Step3. Therefore we make **no end-to-end utility claims** (e.g., "additional inspection improved true defect rate"). Module-level performance on each benchmark is reported for functional feasibility only.

---
## Step2B (WM-811K)

- Dataset: WM-811K. Objective: wafermap pattern classification (proxy).
- Model: SmallCNN. Outputs: pattern labels, severity.
- Why proxy: Different data source; no same-wafer GT.

---
## Step3 (Carinthia)

- Dataset: Carinthia. Objective: SEM defect classification (proxy).
- Outputs: defect classes, engineer decisions.
- Why proxy: Different data source; no same-wafer GT.

---
## Integration Mapping & Plausibility Checks

- KS statistic: 0.41
- p-value: 1.99799391269964e-15
- Passed: False
- Plausibility only; 인과 증명 아님.

---
## C. Interpretation of "Proxy Validation FAILED"

The failed proxy mapping (KS test rejecting distribution alignment) is a **governance/evidence gate success**: it blocks integrated claims that would require same-wafer linkage we do not have. It does **not** mean Step2/Step3 modules are worthless—they show functional feasibility on their respective benchmarks. It means we correctly refrain from claiming end-to-end causal utility until linked data exists.

---
## D. What We Can Responsibly Claim Today

- **Functional feasibility**: Step2B and Step3 achieve their benchmark objectives (pattern/defect classification) on external datasets.
- **Evidence gate**: Failed proxy alignment prevents promotion of Step2/3 into Core; Core remains Step1-only.
- **Readiness for same-wafer upgrade**: When same-wafer multi-stage data is secured, the pipeline is ready to run enrichment metrics, incremental utility under fixed budget, and holdout-lot/group split for leakage control (see Future Work).

---
## E. Concrete Future Work (Pre-Registered Plan)

**(a) When same-wafer multi-stage data exists**, the following will be run:
- **Enrichment metrics**: Incremental recall/precision of Step2/3 over Step1-only on the same wafer set.
- **Incremental utility under fixed budget**: Cost–utility curves comparing Step1-only vs Step1+2 vs Step1+2+3 under the same budget cap.
- **Holdout-lot / group split**: Lot-level or GroupKFold evaluation to control for leakage and support generalization claims.

**(b)–(c) Core 승격 조건 (예)**
동일 wafer_id로 Stage 간 연결이 확인되고, (i) end-to-end에서 Step1-only 대비 recall@10%의 개선이 재현되며(bootstrap CI로 평가), (ii) fixed budget에서 Pareto 우위가 관측되고, (iii) holdout-lot/GroupKFold에서도 성능 저하가 허용 범위 내일 때 Core로 Step2/3를 승격할 수 있다. 그 전까지는 Step2/3 내용은 모두 Appendix 전용이다.

