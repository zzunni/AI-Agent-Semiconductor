"""
Track B Metrics Calculation
검출 및 비용 효율 메트릭 계산
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_detection_metrics(
    y_true: np.ndarray,
    y_selected: np.ndarray,
    high_risk_mask: np.ndarray
) -> Dict[str, float]:
    """
    고위험 웨이퍼 검출 메트릭 계산
    
    Args:
        y_true: 실제 yield 값
        y_selected: 선택 여부 (boolean)
        high_risk_mask: 고위험 웨이퍼 마스크 (boolean)
    
    Returns:
        검출 메트릭 딕셔너리
    """
    # 기본 카운트
    total = len(y_true)
    n_high_risk = high_risk_mask.sum()
    n_low_risk = total - n_high_risk
    n_selected = y_selected.sum()
    
    # Confusion matrix 요소
    # TP: 고위험이고 선택됨
    tp = (high_risk_mask & y_selected).sum()
    # FN: 고위험인데 선택 안 됨
    fn = (high_risk_mask & ~y_selected).sum()
    # FP: 저위험인데 선택됨
    fp = (~high_risk_mask & y_selected).sum()
    # TN: 저위험이고 선택 안 됨
    tn = (~high_risk_mask & ~y_selected).sum()
    
    # 메트릭 계산 (0 division 방지)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    # 선택률
    selection_rate = n_selected / total if total > 0 else 0.0
    
    return {
        'total_wafers': int(total),
        'high_risk_count': int(n_high_risk),
        'low_risk_count': int(n_low_risk),
        'selected_count': int(n_selected),
        'selection_rate': float(selection_rate),
        'true_positive': int(tp),
        'false_negative': int(fn),
        'false_positive': int(fp),
        'true_negative': int(tn),
        'high_risk_recall': float(recall),
        'high_risk_precision': float(precision),
        'high_risk_f1': float(f1),
        'specificity': float(specificity),
        'false_positive_rate': float(fpr),
        'missed_high_risk': int(fn)
    }


def calculate_cost_metrics(
    n_inline: int,
    n_sem: int,
    tp: int,
    cost_inline: float = 150.0,
    cost_sem: float = 500.0
) -> Dict[str, float]:
    """
    비용 효율 메트릭 계산
    
    Args:
        n_inline: 인라인 검사 수
        n_sem: SEM 검사 수
        tp: True Positive 수 (검출된 고위험 웨이퍼)
        cost_inline: 인라인 검사 비용 ($/wafer)
        cost_sem: SEM 검사 비용 ($/wafer)
    
    Returns:
        비용 메트릭 딕셔너리
    """
    total_cost = n_inline * cost_inline + n_sem * cost_sem
    
    # 검출당 비용 (TP가 0이면 무한대)
    cost_per_catch = total_cost / tp if tp > 0 else float('inf')
    
    # 검사당 비용
    total_inspections = n_inline + n_sem
    cost_per_inspection = total_cost / total_inspections if total_inspections > 0 else 0.0
    
    return {
        'n_inline': int(n_inline),
        'n_sem': int(n_sem),
        'total_inspections': int(total_inspections),
        'inline_cost': float(n_inline * cost_inline),
        'sem_cost': float(n_sem * cost_sem),
        'total_cost': float(total_cost),
        'cost_per_catch': float(cost_per_catch),
        'cost_per_inspection': float(cost_per_inspection),
        'cost_inline_unit': float(cost_inline),
        'cost_sem_unit': float(cost_sem)
    }


class MetricsCalculator:
    """
    종합 메트릭 계산기
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
    
    def calculate_all(
        self,
        df: pd.DataFrame,
        yield_col: str = 'yield_true',
        selected_col: str = 'selected',
        sem_col: Optional[str] = None,
        high_risk_mask: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        모든 메트릭 계산
        
        Args:
            df: 데이터프레임
            yield_col: yield 컬럼명
            selected_col: 선택 여부 컬럼명
            sem_col: SEM 선택 컬럼명 (선택)
            high_risk_mask: High-risk 마스크 (하위 20% 정의). None이면 기존 threshold 방식 사용
        
        Returns:
            종합 메트릭 딕셔너리
        """
        y_true = df[yield_col].values
        y_selected = df[selected_col].values.astype(bool)
        
        # High-risk mask: 전달받은 것을 우선 사용, 없으면 기존 방식
        if high_risk_mask is None:
            if 'is_high_risk' in df.columns:
                high_risk_mask = df['is_high_risk'].values.astype(bool)
            else:
                # Fallback to threshold (legacy)
                high_risk_mask = y_true < self.high_risk_threshold
        else:
            # Ensure it's boolean array
            high_risk_mask = np.asarray(high_risk_mask, dtype=bool)
        
        # 검출 메트릭
        detection = calculate_detection_metrics(
            y_true, y_selected, high_risk_mask
        )
        
        # 비용 메트릭
        n_inline = y_selected.sum()
        n_sem = df[sem_col].sum() if sem_col and sem_col in df.columns else 0
        tp = detection['true_positive']
        
        cost = calculate_cost_metrics(
            n_inline, n_sem, tp,
            self.cost_inline, self.cost_sem
        )
        
        # 추가 분석
        additional = self._calculate_additional_metrics(df, yield_col, y_selected)
        
        return {
            'detection': detection,
            'cost': cost,
            'additional': additional,
            'config': {
                'high_risk_threshold': self.high_risk_threshold,
                'cost_inline': self.cost_inline,
                'cost_sem': self.cost_sem
            }
        }
    
    def _calculate_additional_metrics(
        self,
        df: pd.DataFrame,
        yield_col: str,
        y_selected: np.ndarray
    ) -> Dict[str, float]:
        """추가 분석 메트릭"""
        y_true = df[yield_col].values
        
        # 선택된 웨이퍼와 전체 웨이퍼의 yield 비교
        avg_yield_all = y_true.mean()
        avg_yield_selected = y_true[y_selected].mean() if y_selected.sum() > 0 else 0.0
        avg_yield_not_selected = y_true[~y_selected].mean() if (~y_selected).sum() > 0 else 0.0
        
        # Yield 분포 통계
        yield_std = y_true.std()
        yield_q25 = np.percentile(y_true, 25)
        yield_q50 = np.percentile(y_true, 50)
        yield_q75 = np.percentile(y_true, 75)
        
        return {
            'avg_yield_all': float(avg_yield_all),
            'avg_yield_selected': float(avg_yield_selected),
            'avg_yield_not_selected': float(avg_yield_not_selected),
            'yield_difference': float(avg_yield_all - avg_yield_selected),
            'yield_std': float(yield_std),
            'yield_q25': float(yield_q25),
            'yield_q50': float(yield_q50),
            'yield_q75': float(yield_q75)
        }
    
    def compare_methods(
        self,
        results: Dict[str, pd.DataFrame],
        yield_col: str = 'yield_true',
        selected_col: str = 'selected'
    ) -> pd.DataFrame:
        """
        여러 방법 비교
        
        Args:
            results: 방법명 -> DataFrame 딕셔너리
            yield_col: yield 컬럼명
            selected_col: 선택 여부 컬럼명
        
        Returns:
            비교 테이블 DataFrame
        """
        comparison = []
        
        for method, df in results.items():
            metrics = self.calculate_all(df, yield_col, selected_col)
            
            comparison.append({
                'method': method,
                'n_selected': metrics['detection']['selected_count'],
                'selection_rate': metrics['detection']['selection_rate'],
                'total_cost': metrics['cost']['total_cost'],
                'high_risk_recall': metrics['detection']['high_risk_recall'],
                'high_risk_precision': metrics['detection']['high_risk_precision'],
                'high_risk_f1': metrics['detection']['high_risk_f1'],
                'cost_per_catch': metrics['cost']['cost_per_catch'],
                'false_positive_rate': metrics['detection']['false_positive_rate'],
                'missed_high_risk': metrics['detection']['missed_high_risk']
            })
        
        comparison_df = pd.DataFrame(comparison)
        
        # 델타 계산 (첫 번째 방법 기준)
        if len(comparison_df) > 1:
            baseline_cost = comparison_df.iloc[0]['total_cost']
            baseline_recall = comparison_df.iloc[0]['high_risk_recall']
            
            comparison_df['delta_cost'] = comparison_df['total_cost'] - baseline_cost
            comparison_df['delta_cost_pct'] = (
                comparison_df['delta_cost'] / baseline_cost * 100
            ).round(1)
            comparison_df['delta_recall'] = (
                comparison_df['high_risk_recall'] - baseline_recall
            ).round(4)
        
        return comparison_df


def create_metrics_summary(
    metrics: Dict[str, Any],
    method_name: str
) -> str:
    """메트릭 요약 문자열 생성"""
    d = metrics['detection']
    c = metrics['cost']
    
    summary = f"""
=== {method_name} 메트릭 요약 ===
검출 성능:
  - 고위험 재현율 (Recall): {d['high_risk_recall']:.1%}
  - 고위험 정밀도 (Precision): {d['high_risk_precision']:.1%}
  - 고위험 F1: {d['high_risk_f1']:.1%}
  - 위양성률 (FPR): {d['false_positive_rate']:.1%}
  - 누락된 고위험: {d['missed_high_risk']}개

선택 현황:
  - 선택된 웨이퍼: {d['selected_count']}개 / {d['total_wafers']}개 ({d['selection_rate']:.1%})
  - 고위험 웨이퍼: {d['high_risk_count']}개 ({d['high_risk_count']/d['total_wafers']:.1%})

비용:
  - 총 비용: ${c['total_cost']:,.0f}
  - 검출당 비용: ${c['cost_per_catch']:,.0f}
  - 검사당 비용: ${c['cost_per_inspection']:,.0f}
"""
    return summary
