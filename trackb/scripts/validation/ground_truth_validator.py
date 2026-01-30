"""
Track B Ground Truth Validator
200개 테스트 웨이퍼 Ground Truth 검증
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class GroundTruthValidator:
    """
    Ground Truth 검증기
    yield_true를 사용한 실제 성능 검증
    """
    
    def __init__(
        self,
        high_risk_threshold: float = 0.6,
        cost_inline: float = 150.0,
        cost_sem: float = 500.0
    ):
        """
        Args:
            high_risk_threshold: 고위험 웨이퍼 yield 임계값
            cost_inline: 인라인 검사 비용
            cost_sem: SEM 검사 비용
        """
        self.high_risk_threshold = high_risk_threshold
        self.cost_inline = cost_inline
        self.cost_sem = cost_sem
        
        logger.info(
            f"GroundTruthValidator 초기화: "
            f"threshold={high_risk_threshold}, "
            f"inline=${cost_inline}, sem=${cost_sem}"
        )
    
    def validate(
        self,
        df: pd.DataFrame,
        yield_col: str = 'yield_true',
        selected_col: str = 'selected',
        method_name: str = 'unknown'
    ) -> Dict[str, Any]:
        """
        Ground Truth 기반 검증
        
        Args:
            df: 결과 DataFrame (yield_true, selected 포함)
            yield_col: yield 컬럼명
            selected_col: 선택 여부 컬럼명
            method_name: 방법 이름
        
        Returns:
            검증 결과 딕셔너리
        """
        if yield_col not in df.columns:
            raise ValueError(f"'{yield_col}' 컬럼이 필요합니다")
        if selected_col not in df.columns:
            raise ValueError(f"'{selected_col}' 컬럼이 필요합니다")
        
        # 기본 통계
        n_total = len(df)
        high_risk_mask = df[yield_col] < self.high_risk_threshold
        n_high_risk = high_risk_mask.sum()
        
        selected = df[selected_col].astype(bool)
        n_selected = selected.sum()
        
        # Confusion matrix
        tp = (high_risk_mask & selected).sum()
        fn = (high_risk_mask & ~selected).sum()
        fp = (~high_risk_mask & selected).sum()
        tn = (~high_risk_mask & ~selected).sum()
        
        # 메트릭
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        # 비용
        total_cost = n_selected * self.cost_inline
        cost_per_catch = total_cost / tp if tp > 0 else float('inf')
        cost_per_wafer = total_cost / n_total
        
        # Yield 분석
        avg_yield_all = df[yield_col].mean()
        avg_yield_selected = df.loc[selected, yield_col].mean() if n_selected > 0 else 0.0
        avg_yield_not_selected = df.loc[~selected, yield_col].mean() if (~selected).sum() > 0 else 0.0
        
        result = {
            'method': method_name,
            'validation_type': 'ground_truth',
            'high_risk_threshold': self.high_risk_threshold,
            
            # 기본 수치
            'n_total': int(n_total),
            'n_high_risk': int(n_high_risk),
            'high_risk_rate': float(n_high_risk / n_total),
            'n_selected': int(n_selected),
            'selection_rate': float(n_selected / n_total),
            
            # Confusion matrix
            'true_positive': int(tp),
            'false_negative': int(fn),
            'false_positive': int(fp),
            'true_negative': int(tn),
            
            # 검출 메트릭
            'high_risk_recall': float(recall),
            'high_risk_precision': float(precision),
            'high_risk_f1': float(f1),
            'specificity': float(specificity),
            'false_positive_rate': float(fpr),
            'missed_high_risk': int(fn),
            
            # 비용 메트릭
            'total_cost': float(total_cost),
            'cost_per_catch': float(cost_per_catch),
            'cost_per_wafer': float(cost_per_wafer),
            
            # Yield 분석
            'avg_yield_all': float(avg_yield_all),
            'avg_yield_selected': float(avg_yield_selected),
            'avg_yield_not_selected': float(avg_yield_not_selected),
            'yield_difference': float(avg_yield_all - avg_yield_selected)
        }
        
        logger.info(
            f"✅ Ground Truth 검증 ({method_name}): "
            f"recall={recall:.1%}, precision={precision:.1%}, "
            f"cost=${total_cost:,.0f}"
        )
        
        return result
    
    def validate_multiple(
        self,
        results: Dict[str, pd.DataFrame],
        yield_col: str = 'yield_true',
        selected_col: str = 'selected'
    ) -> pd.DataFrame:
        """
        여러 방법 검증 및 비교
        
        Args:
            results: 방법명 -> DataFrame 딕셔너리
            yield_col: yield 컬럼명
            selected_col: 선택 여부 컬럼명
        
        Returns:
            비교 테이블 DataFrame
        """
        comparison = []
        
        for method, df in results.items():
            validation = self.validate(df, yield_col, selected_col, method)
            comparison.append(validation)
        
        comparison_df = pd.DataFrame(comparison)
        
        # 델타 계산 (첫 번째 방법 기준)
        if len(comparison_df) > 1:
            baseline = comparison_df.iloc[0]
            
            comparison_df['delta_cost'] = comparison_df['total_cost'] - baseline['total_cost']
            comparison_df['delta_cost_pct'] = (
                comparison_df['delta_cost'] / baseline['total_cost'] * 100
            ).round(1)
            comparison_df['delta_recall'] = (
                comparison_df['high_risk_recall'] - baseline['high_risk_recall']
            ).round(4)
            comparison_df['delta_missed'] = (
                baseline['missed_high_risk'] - comparison_df['missed_high_risk']
            )
        
        logger.info(f"✅ {len(results)}개 방법 비교 완료")
        
        return comparison_df
    
    def generate_report(
        self,
        validation_result: Dict[str, Any]
    ) -> str:
        """검증 결과 보고서 생성"""
        r = validation_result
        
        report = f"""
## Ground Truth 검증 결과: {r['method']}

### 데이터 요약
- 총 웨이퍼: {r['n_total']}개
- 고위험 웨이퍼 (yield < {r['high_risk_threshold']}): {r['n_high_risk']}개 ({r['high_risk_rate']:.1%})
- 선택된 웨이퍼: {r['n_selected']}개 ({r['selection_rate']:.1%})

### Confusion Matrix
|  | 실제 고위험 | 실제 저위험 |
|--|------------|------------|
| 선택 | {r['true_positive']} (TP) | {r['false_positive']} (FP) |
| 미선택 | {r['false_negative']} (FN) | {r['true_negative']} (TN) |

### 검출 성능
- 고위험 재현율 (Recall): **{r['high_risk_recall']:.1%}**
- 고위험 정밀도 (Precision): **{r['high_risk_precision']:.1%}**
- 고위험 F1: **{r['high_risk_f1']:.1%}**
- 특이도 (Specificity): {r['specificity']:.1%}
- 위양성률 (FPR): {r['false_positive_rate']:.1%}
- 누락된 고위험: **{r['missed_high_risk']}개**

### 비용 효율
- 총 비용: **${r['total_cost']:,.0f}**
- 검출당 비용: **${r['cost_per_catch']:,.0f}**
- 웨이퍼당 비용: ${r['cost_per_wafer']:.1f}

### Yield 분석
- 전체 평균 yield: {r['avg_yield_all']:.4f}
- 선택된 웨이퍼 평균 yield: {r['avg_yield_selected']:.4f}
- 미선택 웨이퍼 평균 yield: {r['avg_yield_not_selected']:.4f}
"""
        
        return report
