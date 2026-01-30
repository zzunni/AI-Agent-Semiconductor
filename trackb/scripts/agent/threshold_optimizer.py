"""
Track B Threshold Optimizer
자율 임계값 최적화 (Grid Search on Validation Set)
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import itertools
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """최적화 결과"""
    best_tau0: float
    best_tau1: float
    best_tau2a: float
    best_score: float
    validation_cost: float
    iterations_evaluated: int
    within_budget_count: int
    history_df: pd.DataFrame


class ThresholdOptimizer:
    """
    Threshold 최적화기
    Validation set에서 grid search로 최적 임계값 탐색
    
    두 가지 모드 지원:
    1. Absolute threshold: riskscore >= tau
    2. Percentile threshold: riskscore >= percentile(tau)
    """
    
    def __init__(
        self,
        budget: float = 30000.0,
        target_metric: str = 'recall',
        cost_inline: float = 150.0,
        tau_space: Optional[List[float]] = None,
        use_percentile: bool = True,
        target_selection_rate: float = 0.10
    ):
        """
        Args:
            budget: 총 예산 제약
            target_metric: 최적화 대상 ('recall', 'f1', 'cost_per_catch')
            cost_inline: 인라인 검사 비용
            tau_space: 탐색할 임계값 공간 (percentile 모드에서는 0.0~1.0)
            use_percentile: True면 percentile 기반 threshold
            target_selection_rate: 목표 선택 비율 (percentile 모드에서 사용)
        """
        self.budget = budget
        self.target_metric = target_metric
        self.cost_inline = cost_inline
        self.use_percentile = use_percentile
        self.target_selection_rate = target_selection_rate
        
        if use_percentile:
            # Percentile 기반: 0.85 = 상위 15% 선택
            self.tau_space = tau_space or [0.85, 0.88, 0.90, 0.92, 0.95]
        else:
            self.tau_space = tau_space or [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        self.history: List[Dict] = []
        
        logger.info(
            f"ThresholdOptimizer 초기화: "
            f"budget=${budget:,.0f}, target={target_metric}, "
            f"percentile_mode={use_percentile}"
        )
    
    def optimize(
        self,
        val_df: pd.DataFrame,
        risk_col: str = 'riskscore',
        yield_col: str = 'yield_true',
        high_risk_threshold: float = 0.6
    ) -> OptimizationResult:
        """
        Validation set에서 grid search 실행
        
        Args:
            val_df: Validation 데이터프레임
            risk_col: risk score 컬럼명
            yield_col: yield 컬럼명
            high_risk_threshold: 고위험 웨이퍼 임계값
        
        Returns:
            OptimizationResult 객체
        """
        self.history = []
        best_config = None
        best_score = -np.inf if self.target_metric != 'cost_per_catch' else np.inf
        
        # 고위험 마스크
        high_risk_mask = val_df[yield_col] < high_risk_threshold
        n_high_risk = high_risk_mask.sum()
        
        logger.info(
            f"최적화 시작: val_size={len(val_df)}, "
            f"high_risk={n_high_risk} ({n_high_risk/len(val_df):.1%})"
        )
        
        # Grid search
        # 단일 stage에서는 tau0만 사용 (multi-stage 시뮬레이션)
        # 여기서는 간단화하여 tau0 하나로 최적화
        for tau0 in self.tau_space:
            for tau1 in self.tau_space:
                for tau2a in self.tau_space:
                    result = self._simulate(
                        val_df, tau0, tau1, tau2a,
                        risk_col, yield_col, high_risk_threshold
                    )
                    
                    # 예산 제약 확인
                    within_budget = result['total_cost'] <= self.budget
                    
                    # 기록
                    self.history.append({
                        'tau0': tau0,
                        'tau1': tau1,
                        'tau2a': tau2a,
                        'cost': result['total_cost'],
                        'recall': result['recall'],
                        'precision': result['precision'],
                        'f1': result['f1'],
                        'n_selected': result['n_selected'],
                        'tp': result['tp'],
                        'cost_per_catch': result['cost_per_catch'],
                        'within_budget': within_budget
                    })
                    
                    # 예산 내에서만 최적화
                    if within_budget:
                        if self.target_metric == 'recall':
                            score = result['recall']
                            is_better = score > best_score
                        elif self.target_metric == 'f1':
                            score = result['f1']
                            is_better = score > best_score
                        else:  # cost_per_catch
                            score = result['cost_per_catch']
                            is_better = score < best_score
                        
                        if is_better:
                            best_score = score
                            best_config = (tau0, tau1, tau2a)
                            best_cost = result['total_cost']
        
        if best_config is None:
            logger.warning("예산 내 설정을 찾을 수 없음, 가장 낮은 비용 설정 사용")
            # 예산 초과해도 가장 낮은 비용 선택
            history_df = pd.DataFrame(self.history)
            min_cost_idx = history_df['cost'].idxmin()
            row = history_df.iloc[min_cost_idx]
            best_config = (row['tau0'], row['tau1'], row['tau2a'])
            best_score = row['recall'] if self.target_metric == 'recall' else row['f1']
            best_cost = row['cost']
        
        history_df = pd.DataFrame(self.history)
        within_budget_count = history_df['within_budget'].sum()
        
        logger.info(
            f"최적화 완료: tau0={best_config[0]}, tau1={best_config[1]}, "
            f"tau2a={best_config[2]}, score={best_score:.4f}"
        )
        
        return OptimizationResult(
            best_tau0=best_config[0],
            best_tau1=best_config[1],
            best_tau2a=best_config[2],
            best_score=best_score,
            validation_cost=best_cost,
            iterations_evaluated=len(self.history),
            within_budget_count=int(within_budget_count),
            history_df=history_df
        )
    
    def _simulate(
        self,
        df: pd.DataFrame,
        tau0: float,
        tau1: float,
        tau2a: float,
        risk_col: str,
        yield_col: str,
        high_risk_threshold: float
    ) -> Dict[str, Any]:
        """
        주어진 임계값으로 시뮬레이션
        
        Percentile 모드: tau는 percentile (0.9 = 상위 10% 선택)
        Absolute 모드: tau는 절대값 (riskscore >= tau)
        """
        risk_scores = df[risk_col].values
        yields = df[yield_col].values
        high_risk_mask = yields < high_risk_threshold
        
        if self.use_percentile:
            # Percentile 기반: tau0이 0.9면 상위 10% 선택
            # 즉, riskscore >= percentile(tau0)
            threshold0 = np.percentile(risk_scores, tau0 * 100)
            threshold1 = np.percentile(risk_scores, tau1 * 100)
            threshold2a = np.percentile(risk_scores, tau2a * 100)
        else:
            threshold0 = tau0
            threshold1 = tau1
            threshold2a = tau2a
        
        # Stage 0 필터링
        passed_stage0 = risk_scores >= threshold0
        
        # Stage 1 필터링 (간소화: 동일 score 사용)
        passed_stage1 = passed_stage0 & (risk_scores >= threshold1)
        
        # Stage 2A 필터링
        selected = passed_stage1 & (risk_scores >= threshold2a)
        
        n_selected = selected.sum()
        
        # 선택된 것 중 고위험
        tp = (selected & high_risk_mask).sum()
        fn = (~selected & high_risk_mask).sum()
        fp = (selected & ~high_risk_mask).sum()
        
        # 메트릭
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        total_cost = n_selected * self.cost_inline
        cost_per_catch = total_cost / tp if tp > 0 else float('inf')
        
        return {
            'n_selected': int(n_selected),
            'selection_rate': float(n_selected / len(df)),
            'tp': int(tp),
            'fn': int(fn),
            'fp': int(fp),
            'recall': float(recall),
            'precision': float(precision),
            'f1': float(f1),
            'total_cost': float(total_cost),
            'cost_per_catch': float(cost_per_catch),
            'threshold_actual': float(threshold0) if self.use_percentile else float(tau0)
        }
    
    def get_summary(self, result: OptimizationResult) -> Dict[str, Any]:
        """최적화 요약 생성"""
        return {
            'method': 'grid_search',
            'search_space': {
                'tau0': self.tau_space,
                'tau1': self.tau_space,
                'tau2a': self.tau_space
            },
            'budget_constraint': self.budget,
            'target_metric': self.target_metric,
            'best_config': {
                'tau0': result.best_tau0,
                'tau1': result.best_tau1,
                'tau2a': result.best_tau2a
            },
            'best_score': result.best_score,
            'validation_cost': result.validation_cost,
            'iterations_evaluated': result.iterations_evaluated,
            'within_budget_count': result.within_budget_count
        }


def run_threshold_optimization(
    val_df: pd.DataFrame,
    budget: float = 30000.0,
    target_metric: str = 'recall',
    risk_col: str = 'riskscore',
    yield_col: str = 'yield_true',
    high_risk_threshold: float = 0.6,
    tau_space: Optional[List[float]] = None
) -> Tuple[OptimizationResult, Dict[str, Any]]:
    """
    Threshold 최적화 실행 헬퍼 함수
    
    Returns:
        (OptimizationResult, summary_dict)
    """
    optimizer = ThresholdOptimizer(
        budget=budget,
        target_metric=target_metric,
        tau_space=tau_space
    )
    
    result = optimizer.optimize(
        val_df,
        risk_col=risk_col,
        yield_col=yield_col,
        high_risk_threshold=high_risk_threshold
    )
    
    summary = optimizer.get_summary(result)
    
    return result, summary
