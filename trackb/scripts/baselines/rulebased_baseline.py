"""
Track B Rule-based Baseline
규칙 기반 (임계값) 베이스라인 구현
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RuleBasedBaseline:
    """
    Rule-based 베이스라인
    단순 임계값 기반 방법: risk score 상위 k% 선택
    """
    
    def __init__(
        self,
        rate: float = 0.10,
        risk_column: str = 'riskscore',
        cost_inline: float = 150.0
    ):
        """
        Args:
            rate: 선택 비율 (기본 10%)
            risk_column: risk score 컬럼명
            cost_inline: 인라인 검사 비용
        """
        self.rate = rate
        self.risk_column = risk_column
        self.cost_inline = cost_inline
        
        logger.info(
            f"RuleBasedBaseline 초기화: rate={rate}, "
            f"risk_column={risk_column}"
        )
    
    def select(
        self,
        df: pd.DataFrame,
        risk_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        risk score 상위 rate% 웨이퍼 선택
        
        Args:
            df: 테스트 데이터프레임
            risk_col: risk score 컬럼명 (None이면 기본값 사용)
        
        Returns:
            선택된 웨이퍼 데이터프레임
        """
        risk_col = risk_col or self.risk_column
        
        if risk_col not in df.columns:
            raise ValueError(f"Risk 컬럼 '{risk_col}'이 존재하지 않습니다")
        
        n_total = len(df)
        n_select = int(n_total * self.rate)
        
        # Risk score 기준 상위 선택
        selected = df.nlargest(n_select, risk_col)
        
        logger.info(
            f"Rule-based 선택: {n_select}/{n_total} ({self.rate:.1%}), "
            f"risk_col={risk_col}"
        )
        
        return selected
    
    def evaluate(
        self,
        df: pd.DataFrame,
        yield_col: str = 'yield_true',
        risk_col: Optional[str] = None,
        high_risk_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        베이스라인 성능 평가
        
        Args:
            df: 테스트 데이터프레임
            yield_col: yield 컬럼명
            risk_col: risk score 컬럼명
            high_risk_threshold: 고위험 임계값
        
        Returns:
            평가 메트릭 딕셔너리
        """
        risk_col = risk_col or self.risk_column
        
        # 전체 고위험 마스크
        high_risk_mask = df[yield_col] < high_risk_threshold
        n_high_risk = high_risk_mask.sum()
        n_total = len(df)
        
        # 선택
        selected = self.select(df, risk_col)
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
        
        # Risk score 통계
        risk_threshold = selected[risk_col].min()
        
        return {
            'method': 'rulebased',
            'rate': self.rate,
            'risk_column': risk_col,
            'risk_threshold': float(risk_threshold),
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
            'avg_yield_all': float(df[yield_col].mean()),
            'avg_risk_selected': float(selected[risk_col].mean()),
            'avg_risk_all': float(df[risk_col].mean())
        }
    
    def generate_results_df(
        self,
        df: pd.DataFrame,
        yield_col: str = 'yield_true',
        risk_col: Optional[str] = None,
        high_risk_threshold: float = 0.6
    ) -> pd.DataFrame:
        """
        결과 데이터프레임 생성
        
        Args:
            df: 테스트 데이터프레임
            yield_col: yield 컬럼명
            risk_col: risk score 컬럼명
            high_risk_threshold: 고위험 임계값
        
        Returns:
            결과 데이터프레임 (selected 컬럼 포함)
        """
        risk_col = risk_col or self.risk_column
        
        # 원본 복사
        result_df = df.copy()
        
        # 선택된 인덱스
        selected = self.select(df, risk_col)
        
        # selected 컬럼 추가
        result_df['selected'] = result_df.index.isin(selected.index)
        
        # 고위험 여부
        result_df['is_high_risk'] = result_df[yield_col] < high_risk_threshold
        
        # 비용 (선택되면 cost_inline)
        result_df['cost'] = result_df['selected'].astype(float) * self.cost_inline
        
        # risk score 복사 (일관성)
        if 'risk_score' not in result_df.columns:
            result_df['risk_score'] = result_df[risk_col]
        
        # 방법 표시
        result_df['method'] = 'rulebased'
        
        return result_df


def run_rulebased_baseline(
    test_df: pd.DataFrame,
    rate: float = 0.10,
    risk_column: str = 'riskscore',
    yield_col: str = 'yield_true',
    high_risk_threshold: float = 0.6,
    cost_inline: float = 150.0,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Rule-based baseline 실행 헬퍼 함수
    
    Args:
        test_df: 테스트 데이터
        rate: 선택 비율
        risk_column: risk score 컬럼명
        yield_col: yield 컬럼명
        high_risk_threshold: 고위험 임계값
        cost_inline: 인라인 비용
        output_path: 결과 CSV 저장 경로
    
    Returns:
        메트릭 및 결과 딕셔너리
    """
    baseline = RuleBasedBaseline(
        rate=rate,
        risk_column=risk_column,
        cost_inline=cost_inline
    )
    
    # 평가
    metrics = baseline.evaluate(
        test_df,
        yield_col=yield_col,
        risk_col=risk_column,
        high_risk_threshold=high_risk_threshold
    )
    
    # 결과 DataFrame
    results_df = baseline.generate_results_df(
        test_df,
        yield_col=yield_col,
        risk_col=risk_column,
        high_risk_threshold=high_risk_threshold
    )
    
    # 저장
    if output_path:
        results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"Rule-based baseline 결과 저장: {output_path}")
    
    return {
        'metrics': metrics,
        'results_df': results_df
    }


def compare_baselines(
    test_df: pd.DataFrame,
    yield_col: str = 'yield_true',
    risk_column: str = 'riskscore',
    high_risk_threshold: float = 0.6,
    rate: float = 0.10,
    seed: int = 42,
    cost_inline: float = 150.0
) -> pd.DataFrame:
    """
    두 베이스라인 비교
    
    Returns:
        비교 테이블 DataFrame
    """
    from .random_baseline import RandomBaseline
    
    # Random
    random_bl = RandomBaseline(rate=rate, seed=seed, cost_inline=cost_inline)
    random_metrics = random_bl.evaluate(
        test_df,
        yield_col=yield_col,
        high_risk_threshold=high_risk_threshold
    )
    
    # Rule-based
    rulebased_bl = RuleBasedBaseline(
        rate=rate,
        risk_column=risk_column,
        cost_inline=cost_inline
    )
    rulebased_metrics = rulebased_bl.evaluate(
        test_df,
        yield_col=yield_col,
        risk_col=risk_column,
        high_risk_threshold=high_risk_threshold
    )
    
    # 비교 테이블 생성
    metrics_to_compare = [
        'n_selected', 'inline_rate', 'total_cost',
        'high_risk_recall', 'high_risk_precision', 'high_risk_f1',
        'cost_per_catch', 'false_positive_rate', 'missed_high_risk'
    ]
    
    rows = []
    for metric in metrics_to_compare:
        row = {
            'metric': metric,
            'random': random_metrics.get(metric),
            'rulebased': rulebased_metrics.get(metric)
        }
        
        # 델타 계산
        if random_metrics.get(metric) is not None and rulebased_metrics.get(metric) is not None:
            if metric in ['cost_per_catch', 'false_positive_rate', 'missed_high_risk']:
                # 낮을수록 좋음
                row['delta'] = random_metrics[metric] - rulebased_metrics[metric]
            else:
                # 높을수록 좋음
                row['delta'] = rulebased_metrics[metric] - random_metrics[metric]
        
        rows.append(row)
    
    return pd.DataFrame(rows)
