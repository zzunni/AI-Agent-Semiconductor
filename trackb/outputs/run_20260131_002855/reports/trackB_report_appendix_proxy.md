# Track B Appendix (Proxy Only)
## Step2/Step3 — Plausibility Only, NOT Causal

**Executive Summary (Appendix)**  
Step2/Step3 are candidate follow-up modules reported Appendix-only; they are not promoted to Core due to lack of same-wafer linkage and failed proxy alignment. The pipeline is ready to validate end-to-end utility once linked data is secured.

**배너**: 본 부록은 Proxy(Step2/Step3) 결과만 다룹니다. Core 결론에 섞이지 않습니다.

**Appendix only — 주요 결론 제외**: Proxy validation FAILED. Step2/Step3 수치는 주요 결론에 사용하지 않습니다.

---
## A. Why Step2/Step3 Exist (Operational Design Intent)

Beyond Step1 (inline risk triage), a realistic fab pipeline needs downstream modules for triage prioritization, defect-type confirmation, and resource allocation. Step2B (wafermap pattern) and Step3 (SEM/defect classification) are **candidate follow-up modules** designed to plug into this pipeline. They are evaluated here at module-level on external benchmarks; they are not claimed to increase real defect yield in the fab unless same-wafer GT exists.

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

When same-wafer multi-stage data exists, the following will be run:
- **Enrichment metrics**: Incremental recall/precision of Step2/3 over Step1-only on the same wafer set.
- **Incremental utility under fixed budget**: Cost–utility curves comparing Step1-only vs Step1+2 vs Step1+2+3 under the same budget cap.
- **Holdout-lot / group split**: Lot-level or GroupKFold evaluation to control for leakage and support generalization claims.
- **Core extension**: If same-source Step2/Step3 GT and aligned mappings are validated, Core may be extended to include these modules; until then, all Step2/3 content remains Appendix-only.

