# Track B Interface Specification
## 데이터 스키마 및 인터페이스 명세

## 1. 입력 데이터 스키마

### 1.1 Step 1 (Stage 0-2A)

#### _stage0_test.csv
| 컬럼 | 타입 | 설명 | 필수 |
|------|------|------|------|
| lot_id | string | 로트 ID | ✅ |
| wafer_id | string | 웨이퍼 ID | ✅ |
| product_type | string | 제품 유형 | ✅ |
| technology_node | string | 기술 노드 | ✅ |
| etch_tool | string | 식각 장비 | ✅ |
| litho_tool | string | 리소그래피 장비 | ✅ |
| deposition_tool | string | 증착 장비 | ✅ |
| implant_tool | string | 이온 주입 장비 | ✅ |
| pressure | float | 압력 | ✅ |
| temperature | float | 온도 | ✅ |
| exposure_time | float | 노광 시간 | ✅ |
| focus_offset | float | 포커스 오프셋 | ✅ |
| dose | float | 도즈 | ✅ |
| implant_energy | float | 이온 주입 에너지 | ✅ |
| tilt_angle | float | 틸트 각도 | ✅ |
| yield | float | 예측 수율 | ✅ |

#### _stage0_pred.csv
위 컬럼 + 추가:
| 컬럼 | 타입 | 설명 | 필수 |
|------|------|------|------|
| yield_true | float | 실제 수율 (Ground Truth) | ✅ |
| yield_pred | float | 모델 예측 수율 | ✅ |

#### _stage0_risk_scores_sample.csv
위 컬럼 + 추가:
| 컬럼 | 타입 | 설명 | 필수 |
|------|------|------|------|
| riskscore | float | 리스크 점수 (0-1) | ✅ |
| riskscore_binary | int | 이진 리스크 (0/1) | ✅ |

### 1.2 Step 2 (Stage 2B)

#### test_accuracy_summary.json
```json
{
  "test_accuracy": float,
  "num_test_samples": int,
  "num_classes": int,
  "model_path": string,
  "created_at": string
}
```

#### stage2b_results.csv
| 컬럼 | 타입 | 설명 | 필수 |
|------|------|------|------|
| orig_idx | int | 원본 인덱스 | ✅ |
| true_label | string | 실제 레이블 | ✅ |
| pred_label | string | 예측 레이블 | ✅ |
| severity | float | 심각도 점수 | ✅ |
| conf | float | 신뢰도 | ✅ |
| sem_selected | bool | SEM 선택 여부 | ✅ |
| sem_reason | string | SEM 선택 이유 | ❌ |
| route | string | 라우팅 결정 | ❌ |

### 1.3 Step 3

#### stage3_results_final.csv
| 컬럼 | 타입 | 설명 | 필수 |
|------|------|------|------|
| wafer_id | string | 웨이퍼 ID | ✅ |
| pattern | string | 패턴 유형 | ✅ |
| severity | float | 심각도 | ✅ |
| pred_class | int | 예측 클래스 | ✅ |
| pred_name_en | string | 예측 이름 (영문) | ❌ |
| triage | string | Triage 결정 | ✅ |
| recommendation | string | 권장 조치 | ✅ |
| engineer_decision | string | 엔지니어 결정 | ❌ |

#### efficiency_summary.json
```json
{
  "random": {
    "selected_k": int,
    "total_sem_cost": float,
    "mean_severity": float,
    "triage_A_rate": float,
    "triage_BCD_rate": float
  },
  "ai": {
    "selected_k": int,
    "total_sem_cost": float,
    "mean_severity": float,
    "triage_A_rate": float,
    "triage_BCD_rate": float
  }
}
```

## 2. 출력 데이터 스키마

### 2.1 Baseline 결과

#### baselines/random_results.csv
| 컬럼 | 타입 | 설명 |
|------|------|------|
| lot_id | string | 로트 ID |
| wafer_id | string | 웨이퍼 ID |
| yield_true | float | 실제 수율 |
| selected | bool | 선택 여부 |
| is_high_risk | bool | 고위험 여부 |
| cost | float | 비용 |
| method | string | 'random' |

#### baselines/rulebased_results.csv
위 컬럼 + 추가:
| 컬럼 | 타입 | 설명 |
|------|------|------|
| risk_score | float | 리스크 점수 |

### 2.2 Agent 결과

#### agent/autotune_summary.json
```json
{
  "method": "grid_search",
  "search_space": {
    "tau0": [float],
    "tau1": [float],
    "tau2a": [float]
  },
  "budget_constraint": float,
  "target_metric": string,
  "best_config": {
    "tau0": float,
    "tau1": float,
    "tau2a": float
  },
  "best_score": float,
  "validation_cost": float,
  "iterations_evaluated": int,
  "within_budget_count": int
}
```

#### agent/scheduler_log.csv
| 컬럼 | 타입 | 설명 |
|------|------|------|
| wafer_id | string | 웨이퍼 ID |
| stage | int | 스테이지 |
| wafers_remaining | int | 남은 웨이퍼 수 |
| budget_remaining | float | 남은 예산 |
| budget_per_wafer | float | 웨이퍼당 예산 |
| adjustment | float | 임계값 조정량 |
| tau_adjusted | float | 조정된 임계값 |
| risk_score | float | 리스크 점수 |
| decision | string | 결정 |
| reason | string | 조정 이유 |

#### agent/decision_trace.csv
| 컬럼 | 타입 | 설명 |
|------|------|------|
| wafer_id | string | 웨이퍼 ID |
| stage | int | 스테이지 |
| decision | string | 결정 |
| risk_score | float | 리스크 점수 |
| threshold | float | 사용된 임계값 |
| top_reason_1 | string | 주요 이유 1 |
| top_reason_2 | string | 주요 이유 2 |
| top_reason_3 | string | 주요 이유 3 |
| scheduler_reason | string | 스케줄러 조정 이유 |

### 2.3 검증 결과

#### validation/framework_results.csv
| 컬럼 | 타입 | 설명 |
|------|------|------|
| method | string | 방법 이름 |
| n_selected | int | 선택 수 |
| selection_rate | float | 선택률 |
| total_cost | float | 총 비용 |
| high_risk_recall | float | 고위험 재현율 |
| high_risk_precision | float | 고위험 정밀도 |
| high_risk_f1 | float | 고위험 F1 |
| cost_per_catch | float | 검출당 비용 |
| false_positive_rate | float | 위양성률 |
| missed_high_risk | int | 누락된 고위험 수 |
| delta_cost | float | 비용 차이 |
| delta_cost_pct | float | 비용 차이 (%) |
| delta_recall | float | 재현율 차이 |

#### validation/statistical_tests.json
```json
{
  "alpha": float,
  "sample_size": int,
  "high_risk_count": int,
  "tests": {
    "t_test_yields": {
      "test": "independent_t_test",
      "t_statistic": float,
      "p_value": float,
      "significant_005": bool,
      "cohens_d": float
    },
    "chi_square_detection": {
      "test": "chi_square",
      "chi2_statistic": float,
      "p_value": float,
      "significant_005": bool,
      "odds_ratio": float
    },
    "bootstrap_cost": {
      "test": "bootstrap",
      "observed_mean_diff": float,
      "ci_lower": float,
      "ci_upper": float,
      "confidence_level": float,
      "p_value": float
    }
  },
  "summary": {
    "total_tests": int,
    "significant_tests": [string],
    "significant_count": int,
    "conclusion": string
  }
}
```

## 3. 매니페스트 스키마

#### _manifest.json
```json
{
  "version": "1.0",
  "timestamp": "ISO8601 datetime",
  "inputs": [
    {
      "path": string,
      "sha256": string,
      "size_bytes": int,
      "mtime": "ISO8601 datetime"
    }
  ],
  "outputs": [
    {
      "path": string,
      "sha256": string,
      "size_bytes": int,
      "mtime": "ISO8601 datetime",
      "row_count": int (optional),
      "columns": [string] (optional)
    }
  ],
  "config_snapshot": object
}
```

## 4. 설정 스키마

#### configs/trackb_config.json
```json
{
  "version": "1.0",
  "mode": "from_artifacts",
  "random_seed": 42,
  
  "paths": {
    "data_root": string,
    "step1_artifacts": string,
    "step2_artifacts": string,
    "step3_artifacts": string,
    "trackb_root": string,
    "trackb_outputs": string
  },
  
  "data": {
    "test_size": int,
    "train_size": int,
    "high_risk_threshold": float,
    "high_risk_percentile": float
  },
  
  "baselines": {
    "random": {
      "rate": float,
      "seed": int
    },
    "rulebased": {
      "rate": float,
      "risk_column": string
    }
  },
  
  "agent": {
    "enable_optimizer": bool,
    "enable_scheduler": bool,
    "enable_explainer": bool,
    "budget_total": float,
    "budget_per_wafer_inline": float,
    "budget_per_wafer_sem": float,
    "threshold_search_space": [float],
    "target_metric": string
  },
  
  "validation": {
    "join_coverage_threshold": float,
    "null_rate_threshold": float,
    "statistical_alpha": float
  }
}
```
