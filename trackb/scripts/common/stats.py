"""
Track B Statistical Validation
통계 검증 유틸리티
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def t_test_yields(
    baseline_yields: np.ndarray,
    framework_yields: np.ndarray,
    alternative: str = 'two-sided'
) -> Dict[str, Any]:
    """
    두 방법의 yield 분포 T-검정
    
    Args:
        baseline_yields: 베이스라인 방법의 선택된 웨이퍼 yield
        framework_yields: 프레임워크 방법의 선택된 웨이퍼 yield
        alternative: 'two-sided', 'less', 'greater'
    
    Returns:
        검정 결과 딕셔너리
    """
    t_stat, p_value = stats.ttest_ind(
        baseline_yields,
        framework_yields,
        alternative=alternative
    )
    
    # Effect size (Cohen's d)
    pooled_std = np.sqrt(
        (baseline_yields.std()**2 + framework_yields.std()**2) / 2
    )
    cohens_d = (baseline_yields.mean() - framework_yields.mean()) / pooled_std if pooled_std > 0 else 0
    
    return {
        'test': 'independent_t_test',
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant_005': p_value < 0.05,
        'significant_001': p_value < 0.01,
        'cohens_d': float(cohens_d),
        'effect_size': _interpret_cohens_d(cohens_d),
        'baseline_mean': float(baseline_yields.mean()),
        'baseline_std': float(baseline_yields.std()),
        'framework_mean': float(framework_yields.mean()),
        'framework_std': float(framework_yields.std()),
        'n_baseline': len(baseline_yields),
        'n_framework': len(framework_yields)
    }


def _interpret_cohens_d(d: float) -> str:
    """Cohen's d 해석"""
    d = abs(d)
    if d < 0.2:
        return 'negligible'
    elif d < 0.5:
        return 'small'
    elif d < 0.8:
        return 'medium'
    else:
        return 'large'


def chi_square_detection(
    baseline_tp: int,
    baseline_fn: int,
    framework_tp: int,
    framework_fn: int
) -> Dict[str, Any]:
    """
    검출률 차이 카이제곱 검정
    
    Args:
        baseline_tp: 베이스라인 True Positive
        baseline_fn: 베이스라인 False Negative
        framework_tp: 프레임워크 True Positive
        framework_fn: 프레임워크 False Negative
    
    Returns:
        검정 결과 딕셔너리
    """
    # 2x2 분할표
    table = np.array([
        [baseline_tp, baseline_fn],
        [framework_tp, framework_fn]
    ])
    
    chi2, p_value, dof, expected = stats.chi2_contingency(table)
    
    # Odds ratio
    if baseline_fn > 0 and framework_tp > 0:
        odds_ratio = (baseline_tp * framework_fn) / (baseline_fn * framework_tp)
    else:
        odds_ratio = float('inf')
    
    return {
        'test': 'chi_square',
        'chi2_statistic': float(chi2),
        'p_value': float(p_value),
        'degrees_of_freedom': int(dof),
        'significant_005': p_value < 0.05,
        'significant_001': p_value < 0.01,
        'odds_ratio': float(odds_ratio),
        'contingency_table': table.tolist(),
        'expected_frequencies': expected.tolist(),
        'baseline_recall': baseline_tp / (baseline_tp + baseline_fn) if (baseline_tp + baseline_fn) > 0 else 0,
        'framework_recall': framework_tp / (framework_tp + framework_fn) if (framework_tp + framework_fn) > 0 else 0
    }


def bootstrap_cost_ci(
    baseline_costs: np.ndarray,
    framework_costs: np.ndarray,
    n_bootstrap: int = 10000,
    confidence_level: float = 0.95,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    비용 절감 부트스트랩 신뢰구간
    
    FIXED: Per-wafer 비용 벡터를 리샘플링하여 정확한 CI 계산
    
    Args:
        baseline_costs: 베이스라인 per-wafer 비용 배열 (0 or cost_inline)
        framework_costs: 프레임워크 per-wafer 비용 배열
        n_bootstrap: 부트스트랩 반복 횟수
        confidence_level: 신뢰수준
        random_seed: 랜덤 시드
    
    Returns:
        부트스트랩 결과 딕셔너리
    """
    np.random.seed(random_seed)
    
    n = len(baseline_costs)
    observed_baseline_total = baseline_costs.sum()
    observed_framework_total = framework_costs.sum()
    observed_diff = observed_baseline_total - observed_framework_total
    
    bootstrap_diffs = []
    bootstrap_baseline_totals = []
    bootstrap_framework_totals = []
    
    for _ in range(n_bootstrap):
        # Per-wafer 리샘플링 (with replacement)
        indices = np.random.choice(n, size=n, replace=True)
        boot_baseline = baseline_costs[indices].sum()
        boot_framework = framework_costs[indices].sum()
        
        bootstrap_baseline_totals.append(boot_baseline)
        bootstrap_framework_totals.append(boot_framework)
        bootstrap_diffs.append(boot_baseline - boot_framework)
    
    bootstrap_diffs = np.array(bootstrap_diffs)
    
    # 신뢰구간 계산
    alpha = (1 - confidence_level) / 2
    ci_low = np.percentile(bootstrap_diffs, alpha * 100)
    ci_high = np.percentile(bootstrap_diffs, (1 - alpha) * 100)
    
    # 표준오차
    se = bootstrap_diffs.std()
    
    # p-value (귀무가설: 차이 = 0)
    # 단측: framework가 더 저렴한지
    if observed_diff > 0:  # baseline이 더 비쌈 (좋은 결과)
        p_value = (bootstrap_diffs <= 0).mean()
    else:  # framework가 더 비쌈
        p_value = (bootstrap_diffs >= 0).mean()

    # 비율 CI: Core/보고서용 절대금액 금지 → delta_cost_pct_ci만 사용
    bootstrap_pct = np.array([
        (b - f) / b * 100 if b > 0 else 0
        for b, f in zip(bootstrap_baseline_totals, bootstrap_framework_totals)
    ])
    ci_low_pct = float(np.percentile(bootstrap_pct, alpha * 100))
    ci_high_pct = float(np.percentile(bootstrap_pct, (1 - alpha) * 100))
    
    return {
        'test': 'bootstrap_cost',
        'observed_baseline_total': float(observed_baseline_total),
        'observed_framework_total': float(observed_framework_total),
        'observed_diff': float(observed_diff),
        'bootstrap_mean_diff': float(bootstrap_diffs.mean()),
        'bootstrap_std': float(se),
        'ci_lower': float(ci_low),
        'ci_upper': float(ci_high),
        'delta_cost_pct_ci_lower': ci_low_pct,
        'delta_cost_pct_ci_upper': ci_high_pct,
        'confidence_level': confidence_level,
        'p_value': float(p_value),
        'significant_005': bool(ci_low > 0 or ci_high < 0),  # CI가 0을 포함하지 않으면 유의
        'n_bootstrap': n_bootstrap,
        'n_samples': n,
        'percent_reduction': float(observed_diff / observed_baseline_total * 100) if observed_baseline_total > 0 else 0
    }


def bootstrap_recall_ci(
    baseline_detected: np.ndarray,
    framework_detected: np.ndarray,
    high_risk_mask: np.ndarray,
    n_bootstrap: int = 10000,
    confidence_level: float = 0.95,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Recall 향상 부트스트랩 신뢰구간
    
    Args:
        baseline_detected: 베이스라인 검출 여부 (per-wafer boolean)
        framework_detected: 프레임워크 검출 여부 (per-wafer boolean)
        high_risk_mask: 실제 고위험 여부 (per-wafer boolean)
        n_bootstrap: 부트스트랩 반복 횟수
        confidence_level: 신뢰수준
        random_seed: 랜덤 시드
    
    Returns:
        부트스트랩 결과 딕셔너리
    """
    np.random.seed(random_seed)
    
    n = len(baseline_detected)
    n_high_risk = high_risk_mask.sum()
    
    def calc_recall(detected, mask):
        tp = (detected & mask).sum()
        return tp / mask.sum() if mask.sum() > 0 else 0
    
    observed_baseline_recall = calc_recall(baseline_detected, high_risk_mask)
    observed_framework_recall = calc_recall(framework_detected, high_risk_mask)
    observed_diff = observed_framework_recall - observed_baseline_recall
    
    bootstrap_diffs = []
    
    for _ in range(n_bootstrap):
        indices = np.random.choice(n, size=n, replace=True)
        boot_baseline = baseline_detected[indices]
        boot_framework = framework_detected[indices]
        boot_mask = high_risk_mask[indices]
        
        recall_baseline = calc_recall(boot_baseline, boot_mask)
        recall_framework = calc_recall(boot_framework, boot_mask)
        bootstrap_diffs.append(recall_framework - recall_baseline)
    
    bootstrap_diffs = np.array(bootstrap_diffs)
    
    alpha = (1 - confidence_level) / 2
    ci_low = np.percentile(bootstrap_diffs, alpha * 100)
    ci_high = np.percentile(bootstrap_diffs, (1 - alpha) * 100)
    
    return {
        'test': 'bootstrap_recall',
        'observed_baseline_recall': float(observed_baseline_recall),
        'observed_framework_recall': float(observed_framework_recall),
        'observed_diff': float(observed_diff),
        'ci_lower': float(ci_low),
        'ci_upper': float(ci_high),
        'confidence_level': confidence_level,
        'significant_005': bool(ci_low > 0 or ci_high < 0),
        'n_bootstrap': n_bootstrap,
        'n_high_risk': int(n_high_risk)
    }


def ks_distribution_test(
    sample1: np.ndarray,
    sample2: np.ndarray
) -> Dict[str, Any]:
    """
    두 분포의 유사성 Kolmogorov-Smirnov 검정
    (Proxy 검증용)
    
    Args:
        sample1: 첫 번째 샘플
        sample2: 두 번째 샘플
    
    Returns:
        검정 결과 딕셔너리
    """
    ks_stat, p_value = stats.ks_2samp(sample1, sample2)
    
    return {
        'test': 'kolmogorov_smirnov',
        'ks_statistic': float(ks_stat),
        'p_value': float(p_value),
        'distributions_similar': p_value > 0.05,
        'interpretation': 'similar' if p_value > 0.05 else 'different',
        'sample1_mean': float(sample1.mean()),
        'sample1_std': float(sample1.std()),
        'sample2_mean': float(sample2.mean()),
        'sample2_std': float(sample2.std()),
        'n_sample1': len(sample1),
        'n_sample2': len(sample2)
    }


def mcnemar_test(
    baseline_correct: np.ndarray,
    framework_correct: np.ndarray
) -> Dict[str, Any]:
    """
    McNemar 검정 (동일 샘플에서 두 분류기 비교)
    
    Args:
        baseline_correct: 베이스라인 정답 여부 (boolean)
        framework_correct: 프레임워크 정답 여부 (boolean)
    
    Returns:
        검정 결과 딕셔너리
    """
    # 분할표 생성
    # b: 베이스라인은 맞고, 프레임워크는 틀림
    # c: 베이스라인은 틀리고, 프레임워크는 맞음
    b = ((baseline_correct) & (~framework_correct)).sum()
    c = ((~baseline_correct) & (framework_correct)).sum()
    
    # McNemar 검정 (연속 보정 포함)
    if b + c == 0:
        return {
            'test': 'mcnemar',
            'statistic': 0,
            'p_value': 1.0,
            'significant_005': False,
            'b': int(b),
            'c': int(c),
            'note': 'No disagreements between methods'
        }
    
    statistic = (abs(b - c) - 1)**2 / (b + c)
    p_value = 1 - stats.chi2.cdf(statistic, df=1)
    
    return {
        'test': 'mcnemar',
        'statistic': float(statistic),
        'p_value': float(p_value),
        'significant_005': p_value < 0.05,
        'b': int(b),
        'c': int(c),
        'framework_improvement': int(c - b),
        'odds_ratio': float(c / b) if b > 0 else float('inf')
    }


class StatisticalValidator:
    """
    종합 통계 검증기
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        Args:
            alpha: 유의수준
        """
        self.alpha = alpha
        self.results = {}
    
    def run_all_tests(
        self,
        baseline_df: pd.DataFrame,
        framework_df: pd.DataFrame,
        yield_col: str = 'yield_true',
        selected_col: str = 'selected',
        high_risk_threshold: float = 0.6,
        cost_inline: float = 150.0,
        high_risk_mask: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        모든 통계 검정 실행
        
        Args:
            baseline_df: 베이스라인 결과 DataFrame
            framework_df: 프레임워크 결과 DataFrame
            yield_col: yield 컬럼명
            selected_col: 선택 여부 컬럼명
            high_risk_threshold: 고위험 임계값 (legacy fallback)
            cost_inline: 인라인 비용
            high_risk_mask: High-risk 마스크 (하위 20% 정의). None이면 기존 threshold 방식 사용
        
        Returns:
            모든 검정 결과 딕셔너리
        """
        # 데이터 준비: High-risk mask 우선 사용
        if high_risk_mask is None:
            # Try to get from DataFrame
            if 'is_high_risk' in baseline_df.columns:
                high_risk_mask = baseline_df['is_high_risk'].values.astype(bool)
            else:
                # Fallback to threshold (legacy)
                high_risk_mask = baseline_df[yield_col] < high_risk_threshold
        else:
            high_risk_mask = np.asarray(high_risk_mask, dtype=bool)
        
        baseline_selected = baseline_df[selected_col].astype(bool)
        framework_selected = framework_df[selected_col].astype(bool)
        
        baseline_tp = (high_risk_mask & baseline_selected).sum()
        baseline_fn = (high_risk_mask & ~baseline_selected).sum()
        framework_tp = (high_risk_mask & framework_selected).sum()
        framework_fn = (high_risk_mask & ~framework_selected).sum()
        
        # 비용 배열
        baseline_costs = baseline_selected.astype(float) * cost_inline
        framework_costs = framework_selected.astype(float) * cost_inline
        
        # 검정 실행
        self.results = {
            'alpha': self.alpha,
            'sample_size': len(baseline_df),
            'high_risk_count': int(high_risk_mask.sum()),
            'tests': {}
        }
        
        # T-검정 (선택된 웨이퍼의 yield)
        if baseline_selected.sum() > 0 and framework_selected.sum() > 0:
            baseline_yields = baseline_df.loc[baseline_selected, yield_col].values
            framework_yields = framework_df.loc[framework_selected, yield_col].values
            
            self.results['tests']['t_test_yields'] = t_test_yields(
                baseline_yields, framework_yields
            )
        
        # 카이제곱 검정 (검출률)
        self.results['tests']['chi_square_detection'] = chi_square_detection(
            baseline_tp, baseline_fn, framework_tp, framework_fn
        )
        
        # 부트스트랩 (비용 절감)
        self.results['tests']['bootstrap_cost'] = bootstrap_cost_ci(
            baseline_costs.values, framework_costs.values
        )
        
        # 부트스트랩 (Recall 차이) — Primary endpoint CI
        self.results['tests']['bootstrap_recall'] = bootstrap_recall_ci(
            baseline_selected.values,
            framework_selected.values,
            high_risk_mask,
        )
        
        # McNemar 검정 (개별 샘플 비교)
        baseline_correct = (baseline_selected == high_risk_mask)
        framework_correct = (framework_selected == high_risk_mask)
        
        self.results['tests']['mcnemar'] = mcnemar_test(
            baseline_correct.values, framework_correct.values
        )
        
        # 요약 추가
        self.results['summary'] = self._create_summary()
        
        return self.results
    
    def _create_summary(self) -> Dict[str, Any]:
        """검정 결과 요약"""
        tests = self.results.get('tests', {})
        
        significant_tests = []
        for name, result in tests.items():
            if result.get('significant_005', False):
                significant_tests.append(name)
        
        return {
            'total_tests': len(tests),
            'significant_tests': significant_tests,
            'significant_count': len(significant_tests),
            'all_significant': len(significant_tests) == len(tests),
            'conclusion': self._get_conclusion(significant_tests)
        }
    
    def _get_conclusion(self, significant_tests: List[str]) -> str:
        """결론 생성"""
        if len(significant_tests) == 0:
            return "유의한 차이 없음"
        elif len(significant_tests) == len(self.results.get('tests', {})):
            return "모든 검정에서 유의한 차이 확인"
        else:
            return f"일부 검정에서 유의한 차이 확인: {', '.join(significant_tests)}"
    
    def to_dataframe(self) -> pd.DataFrame:
        """결과를 DataFrame으로 변환"""
        rows = []
        for test_name, result in self.results.get('tests', {}).items():
            row = {
                'test': test_name,
                'statistic': result.get('t_statistic') or result.get('chi2_statistic') or result.get('statistic') or result.get('ks_statistic'),
                'p_value': result.get('p_value'),
                'significant_005': result.get('significant_005'),
                'significant_001': result.get('significant_001', False)
            }
            rows.append(row)
        
        return pd.DataFrame(rows)


def format_p_value(p: float) -> str:
    """p-value 포맷팅"""
    if p < 0.001:
        return "<0.001"
    elif p < 0.01:
        return f"{p:.3f}"
    elif p < 0.05:
        return f"{p:.3f}"
    else:
        return f"{p:.3f}"
