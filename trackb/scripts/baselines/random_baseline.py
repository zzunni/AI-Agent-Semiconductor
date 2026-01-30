"""
Track B Random Baseline
무작위 샘플링 베이스라인 구현
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RandomBaseline:
    """
    Random Sampling 베이스라인
    업계 표준 fallback 방법: 무작위로 일정 비율 웨이퍼 선택
    """
    
    def __init__(
        self,
        rate: float = 0.10,
        seed: int = 42,
        cost_inline: float = 150.0
    ):
        """
        Args:
            rate: 선택 비율 (기본 10%)
            seed: 랜덤 시드
            cost_inline: 인라인 검사 비용
        """
        self.rate = rate
        self.seed = seed
        self.cost_inline = cost_inline
        self.rng = np.random.RandomState(seed)
        
        logger.info(f"RandomBaseline 초기화: rate={rate}, seed={seed}")
    
    def select(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        무작위로 rate% 웨이퍼 선택
        
        Args:
            df: 테스트 데이터프레임
        
        Returns:
            선택된 웨이퍼 데이터프레임
        """
        n_total = len(df)
        n_select = int(n_total * self.rate)
        
        # 무작위 인덱스 선택
        selected_idx = self.rng.choice(
            df.index,
            size=n_select,
            replace=False
        )
        
        logger.info(f"Random 선택: {n_select}/{n_total} ({self.rate:.1%})")
        
        return df.loc[selected_idx]
    
    def evaluate(
        self,
        df: pd.DataFrame,
        yield_col: str = 'yield_true',
        high_risk_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        베이스라인 성능 평가
        
        Args:
            df: 테스트 데이터프레임
            yield_col: yield 컬럼명
            high_risk_threshold: 고위험 임계값
        
        Returns:
            평가 메트릭 딕셔너리
        """
        # 전체 고위험 마스크
        high_risk_mask = df[yield_col] < high_risk_threshold
        n_high_risk = high_risk_mask.sum()
        n_total = len(df)
        
        # 선택
        selected = self.select(df)
        n_selected = len(selected)
        
        # 선택된 것 중 고위험
        selected_high_risk = selected[yield_col] < high_risk_threshold
        
        # Confusion matrix
        tp = selected_high_risk.sum()
        fn = n_high_risk - tp
        fp = n_selected - tp
        tn = n_total - n_selected - fn
        
        # 메트릭 계산
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        # 비용
        total_cost = n_selected * self.cost_inline
        cost_per_catch = total_cost / tp if tp > 0 else float('inf')
        
        return {
            'method': 'random',
            'rate': self.rate,
            'seed': self.seed,
            'n_total': int(n_total),
            'n_selected': int(n_selected),
            'n_high_risk': int(n_high_risk),
            'inline_rate': float(n_selected / n_total),
            'total_cost': float(total_cost),
            'true_positive': int(tp),
            'false_negative': int(fn),
            'false_positive': int(fp),
            'true_negative': int(tn),
            'high_risk_recall': float(recall),
            'high_risk_precision': float(precision),
            'high_risk_f1': float(f1),
            'false_positive_rate': float(fpr),
            'cost_per_catch': float(cost_per_catch),
            'missed_high_risk': int(fn),
            'avg_yield_selected': float(selected[yield_col].mean()),
            'avg_yield_all': float(df[yield_col].mean())
        }
    
    def generate_results_df(
        self,
        df: pd.DataFrame,
        yield_col: str = 'yield_true',
        high_risk_threshold: float = 0.6
    ) -> pd.DataFrame:
        """
        결과 데이터프레임 생성
        
        Args:
            df: 테스트 데이터프레임
            yield_col: yield 컬럼명
            high_risk_threshold: 고위험 임계값
        
        Returns:
            결과 데이터프레임 (selected 컬럼 포함)
        """
        # 원본 복사
        result_df = df.copy()
        
        # 선택된 인덱스
        selected = self.select(df)
        
        # selected 컬럼 추가
        result_df['selected'] = result_df.index.isin(selected.index)
        
        # 고위험 여부
        result_df['is_high_risk'] = result_df[yield_col] < high_risk_threshold
        
        # 비용 (선택되면 cost_inline)
        result_df['cost'] = result_df['selected'].astype(float) * self.cost_inline
        
        # 방법 표시
        result_df['method'] = 'random'
        
        return result_df


def run_random_baseline(
    test_df: pd.DataFrame,
    rate: float = 0.10,
    seed: int = 42,
    yield_col: str = 'yield_true',
    high_risk_threshold: float = 0.6,
    cost_inline: float = 150.0,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Random baseline 실행 헬퍼 함수
    
    FIX: 선택을 한 번만 수행하여 metrics와 results_df 일관성 보장
    
    Args:
        test_df: 테스트 데이터
        rate: 선택 비율
        seed: 랜덤 시드
        yield_col: yield 컬럼명
        high_risk_threshold: 고위험 임계값
        cost_inline: 인라인 비용
        output_path: 결과 CSV 저장 경로
    
    Returns:
        메트릭 및 결과 딕셔너리
    """
    baseline = RandomBaseline(rate=rate, seed=seed, cost_inline=cost_inline)
    
    # 선택을 한 번만 수행
    selected = baseline.select(test_df)
    selected_indices = selected.index
    
    # 결과 DataFrame 생성 (선택 결과 재사용)
    result_df = test_df.copy()
    result_df['selected'] = result_df.index.isin(selected_indices)
    result_df['is_high_risk'] = result_df[yield_col] < high_risk_threshold
    result_df['cost'] = result_df['selected'].astype(float) * cost_inline
    result_df['method'] = 'random'
    
    # 메트릭 계산 (동일한 선택 결과 사용)
    n_total = len(test_df)
    n_selected = len(selected_indices)
    
    high_risk_mask = test_df[yield_col] < high_risk_threshold
    n_high_risk = high_risk_mask.sum()
    
    selected_high_risk = selected[yield_col] < high_risk_threshold
    tp = int(selected_high_risk.sum())
    fn = int(n_high_risk - tp)
    fp = int(n_selected - tp)
    tn = int(n_total - n_selected - fn)
    
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    total_cost = n_selected * cost_inline
    cost_per_catch = total_cost / tp if tp > 0 else float('inf')
    
    metrics = {
        'method': 'random',
        'rate': rate,
        'seed': seed,
        'n_total': n_total,
        'n_selected': n_selected,
        'n_high_risk': int(n_high_risk),
        'inline_rate': float(n_selected / n_total),
        'total_cost': float(total_cost),
        'true_positive': tp,
        'false_negative': fn,
        'false_positive': fp,
        'true_negative': tn,
        'high_risk_recall': float(recall),
        'high_risk_precision': float(precision),
        'high_risk_f1': float(f1),
        'false_positive_rate': float(fpr),
        'cost_per_catch': float(cost_per_catch),
        'missed_high_risk': fn,
        'avg_yield_selected': float(selected[yield_col].mean()),
        'avg_yield_all': float(test_df[yield_col].mean())
    }
    
    # 저장
    if output_path:
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"Random baseline 결과 저장: {output_path}")
    
    return {
        'metrics': metrics,
        'results_df': result_df
    }
