"""
Track B Budget-Aware Scheduler
예산 인식 동적 스케줄러
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """스케줄러 설정"""
    total_budget: float = 3000.0
    n_wafers: int = 200
    base_tau0: float = 0.90  # Percentile (0.90 = 상위 10%)
    base_tau1: float = 0.90
    base_tau2a: float = 0.90
    cost_inline: float = 150.0
    cost_sem: float = 500.0
    critical_threshold: float = 10.0  # $/wafer
    warning_threshold: float = 12.0
    surplus_threshold: float = 18.0
    use_percentile: bool = True
    target_selection_rate: float = 0.10


@dataclass
class DecisionRecord:
    """결정 기록"""
    wafer_id: str
    stage: int
    decision: str
    risk_score: float
    threshold: float
    adjustment: float
    budget_remaining: float
    budget_per_wafer: float
    reason: str


class BudgetAwareScheduler:
    """
    예산 인식 동적 스케줄러
    남은 예산에 따라 임계값을 동적으로 조정
    """
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        """
        Args:
            config: 스케줄러 설정 (None이면 기본값)
        """
        self.config = config or SchedulerConfig()
        self.budget_remaining = self.config.total_budget
        self.wafers_processed = 0
        self.log: List[Dict] = []
        self.decisions: List[DecisionRecord] = []
        
        logger.info(
            f"BudgetAwareScheduler 초기화: "
            f"budget=${self.config.total_budget:,.0f}, "
            f"n_wafers={self.config.n_wafers}"
        )
    
    def reset(self) -> None:
        """스케줄러 상태 초기화"""
        self.budget_remaining = self.config.total_budget
        self.wafers_processed = 0
        self.log = []
        self.decisions = []
    
    def decide(
        self,
        wafer_id: str,
        risk_score: float
    ) -> Tuple[str, float, str]:
        """
        단일 웨이퍼에 대한 결정
        
        Args:
            wafer_id: 웨이퍼 ID
            risk_score: risk score
        
        Returns:
            (decision, adjusted_threshold, reason)
        """
        wafers_remaining = self.config.n_wafers - self.wafers_processed
        budget_per_wafer = (
            self.budget_remaining / wafers_remaining
            if wafers_remaining > 0 else 0
        )
        
        # 적응형 조정
        adjustment, reason = self._calculate_adjustment(budget_per_wafer)
        
        # 조정된 임계값
        tau_adj = self.config.base_tau0 + adjustment
        tau_adj = np.clip(tau_adj, 0.1, 0.95)  # 범위 제한
        
        # 결정
        if risk_score >= tau_adj:
            decision = "inspect"
            self.budget_remaining -= self.config.cost_inline
        else:
            decision = "pass"
        
        # 로그 기록
        self.log.append({
            'wafer_id': wafer_id,
            'stage': 0,
            'wafers_remaining': wafers_remaining,
            'budget_remaining': self.budget_remaining + (
                self.config.cost_inline if decision == "inspect" else 0
            ),
            'budget_remaining_after': self.budget_remaining,
            'budget_per_wafer': budget_per_wafer,
            'adjustment': adjustment,
            'tau_base': self.config.base_tau0,
            'tau_adjusted': tau_adj,
            'risk_score': risk_score,
            'decision': decision,
            'reason': reason
        })
        
        self.decisions.append(DecisionRecord(
            wafer_id=wafer_id,
            stage=0,
            decision=decision,
            risk_score=risk_score,
            threshold=tau_adj,
            adjustment=adjustment,
            budget_remaining=self.budget_remaining,
            budget_per_wafer=budget_per_wafer,
            reason=reason
        ))
        
        self.wafers_processed += 1
        
        return decision, tau_adj, reason
    
    def _calculate_adjustment(
        self,
        budget_per_wafer: float
    ) -> Tuple[float, str]:
        """
        예산 상황에 따른 임계값 조정 계산
        
        Args:
            budget_per_wafer: 웨이퍼당 남은 예산
        
        Returns:
            (adjustment, reason)
        """
        if budget_per_wafer < self.config.critical_threshold:
            # 위기: 예산 매우 부족 → 임계값 크게 높임 (선택 줄임)
            adjustment = +0.15
            reason = "critical_budget"
        elif budget_per_wafer < self.config.warning_threshold:
            # 경고: 예산 부족 → 임계값 약간 높임
            adjustment = +0.08
            reason = "low_budget"
        elif budget_per_wafer > self.config.surplus_threshold:
            # 여유: 예산 충분 → 임계값 낮춤 (선택 늘림)
            adjustment = -0.05
            reason = "budget_surplus"
        else:
            # 정상
            adjustment = 0.0
            reason = "normal"
        
        return adjustment, reason
    
    def run_batch(
        self,
        df: pd.DataFrame,
        wafer_id_col: str = 'wafer_id',
        risk_col: str = 'riskscore'
    ) -> pd.DataFrame:
        """
        전체 데이터에 대해 스케줄러 실행
        
        Percentile 모드: base_tau는 percentile (0.90 = 상위 10%)
        
        Args:
            df: 데이터프레임
            wafer_id_col: 웨이퍼 ID 컬럼명
            risk_col: risk score 컬럼명
        
        Returns:
            결정이 포함된 데이터프레임
        """
        self.reset()
        self.config.n_wafers = len(df)
        
        # Percentile 모드: 실제 threshold 계산
        if self.config.use_percentile:
            risk_scores = df[risk_col].values
            self.actual_threshold = np.percentile(risk_scores, self.config.base_tau0 * 100)
            logger.info(f"Percentile threshold: {self.config.base_tau0} -> actual {self.actual_threshold:.4f}")
        else:
            self.actual_threshold = self.config.base_tau0
        
        results = []
        
        for idx, row in df.iterrows():
            wafer_id = str(row.get(wafer_id_col, idx))
            risk_score = row[risk_col]
            
            decision, threshold, reason = self.decide_with_actual_threshold(
                wafer_id, risk_score, self.actual_threshold
            )
            
            results.append({
                'index': idx,
                'wafer_id': wafer_id,
                'risk_score': risk_score,
                'decision': decision,
                'selected': decision == "inspect",
                'threshold': threshold,
                'reason': reason
            })
        
        results_df = pd.DataFrame(results)
        
        # 원본과 병합
        output_df = df.copy()
        output_df['selected'] = results_df.set_index('index')['selected']
        output_df['threshold'] = results_df.set_index('index')['threshold']
        output_df['scheduler_reason'] = results_df.set_index('index')['reason']
        
        logger.info(
            f"스케줄러 완료: {results_df['selected'].sum()}/{len(df)} 선택, "
            f"남은 예산=${self.budget_remaining:,.0f}"
        )
        
        return output_df
    
    def decide_with_actual_threshold(
        self,
        wafer_id: str,
        risk_score: float,
        base_threshold: float
    ) -> Tuple[str, float, str]:
        """
        실제 threshold 값을 사용한 결정
        """
        wafers_remaining = self.config.n_wafers - self.wafers_processed
        budget_per_wafer = (
            self.budget_remaining / wafers_remaining
            if wafers_remaining > 0 else 0
        )
        
        # 적응형 조정 (예산 기반)
        adjustment, reason = self._calculate_adjustment(budget_per_wafer)
        
        # 조정된 임계값 (실제 riskscore 값)
        tau_adj = base_threshold * (1 + adjustment)
        tau_adj = np.clip(tau_adj, 0.01, 0.99)
        
        # 결정
        if risk_score >= tau_adj:
            decision = "inspect"
            self.budget_remaining -= self.config.cost_inline
        else:
            decision = "pass"
        
        # 로그 기록
        self.log.append({
            'wafer_id': wafer_id,
            'stage': 0,
            'wafers_remaining': wafers_remaining,
            'budget_remaining': self.budget_remaining + (
                self.config.cost_inline if decision == "inspect" else 0
            ),
            'budget_remaining_after': self.budget_remaining,
            'budget_per_wafer': budget_per_wafer,
            'adjustment': adjustment,
            'tau_base': base_threshold,
            'tau_adjusted': tau_adj,
            'risk_score': risk_score,
            'decision': decision,
            'reason': reason
        })
        
        self.wafers_processed += 1
        
        return decision, tau_adj, reason
    
    def get_log_df(self) -> pd.DataFrame:
        """로그 DataFrame 반환"""
        return pd.DataFrame(self.log)
    
    def get_summary(self) -> Dict[str, Any]:
        """스케줄러 요약"""
        log_df = self.get_log_df()
        
        if len(log_df) == 0:
            return {'error': 'No decisions made'}
        
        n_inspected = (log_df['decision'] == 'inspect').sum()
        reason_counts = log_df['reason'].value_counts().to_dict()
        
        return {
            'total_wafers': self.config.n_wafers,
            'wafers_processed': self.wafers_processed,
            'n_inspected': int(n_inspected),
            'inspection_rate': float(n_inspected / self.wafers_processed) if self.wafers_processed > 0 else 0,
            'initial_budget': float(self.config.total_budget),
            'budget_used': float(self.config.total_budget - self.budget_remaining),
            'budget_remaining': float(self.budget_remaining),
            'budget_utilization': float(1 - self.budget_remaining / self.config.total_budget),
            'reason_counts': reason_counts,
            'adjustment_applied_count': int((log_df['adjustment'] != 0).sum()),
            'avg_threshold': float(log_df['tau_adjusted'].mean()),
            'min_threshold': float(log_df['tau_adjusted'].min()),
            'max_threshold': float(log_df['tau_adjusted'].max())
        }


def run_budget_scheduler(
    df: pd.DataFrame,
    total_budget: float = 30000.0,
    base_tau: float = 0.6,
    wafer_id_col: str = 'wafer_id',
    risk_col: str = 'riskscore',
    cost_inline: float = 150.0
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Budget scheduler 실행 헬퍼 함수
    
    Args:
        df: 데이터프레임
        total_budget: 총 예산
        base_tau: 기본 임계값
        wafer_id_col: 웨이퍼 ID 컬럼명
        risk_col: risk score 컬럼명
        cost_inline: 인라인 비용
    
    Returns:
        (results_df, log_df, summary)
    """
    config = SchedulerConfig(
        total_budget=total_budget,
        n_wafers=len(df),
        base_tau0=base_tau,
        cost_inline=cost_inline
    )
    
    scheduler = BudgetAwareScheduler(config)
    
    results_df = scheduler.run_batch(
        df,
        wafer_id_col=wafer_id_col,
        risk_col=risk_col
    )
    
    log_df = scheduler.get_log_df()
    summary = scheduler.get_summary()
    
    return results_df, log_df, summary
