"""
Track B Statistical Validator
종합 통계 검증 실행
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path

# 상대 임포트 문제 해결
SCRIPT_DIR = Path(__file__).parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common.stats import (
    StatisticalValidator,
    t_test_yields,
    chi_square_detection,
    bootstrap_cost_ci
)

logger = logging.getLogger(__name__)


def run_full_validation(
    baseline_results: Dict[str, Dict[str, Any]],
    framework_results: Dict[str, Any],
    yield_col: str = 'yield_true',
    selected_col: str = 'selected',
    high_risk_threshold: float = 0.6,
    cost_inline: float = 150.0
) -> Dict[str, Any]:
    """
    종합 통계 검증 실행
    
    Args:
        baseline_results: 베이스라인 결과 {'random': {...}, 'rulebased': {...}}
        framework_results: 프레임워크 결과
        yield_col: yield 컬럼명
        selected_col: 선택 여부 컬럼명
        high_risk_threshold: 고위험 임계값
        cost_inline: 인라인 비용
    
    Returns:
        검증 결과 딕셔너리
    """
    logger.info("종합 통계 검증 시작")
    
    results = {
        'comparisons': {},
        'summary': {}
    }
    
    framework_df = framework_results.get('framework_results_df')
    if framework_df is None:
        logger.error("프레임워크 결과 DataFrame이 없습니다")
        return results
    
    # 각 베이스라인과 비교
    for baseline_name, baseline_data in baseline_results.items():
        baseline_df = baseline_data.get('results_df')
        if baseline_df is None:
            continue
        
        comparison = _compare_methods(
            baseline_df,
            framework_df,
            yield_col,
            selected_col,
            high_risk_threshold,
            cost_inline
        )
        
        results['comparisons'][f'{baseline_name}_vs_framework'] = comparison
        
        logger.info(
            f"✅ {baseline_name} vs framework: "
            f"t-test p={comparison['t_test'].get('p_value', 'N/A'):.4f}, "
            f"chi2 p={comparison['chi_square'].get('p_value', 'N/A'):.4f}"
        )
    
    # 전체 요약
    results['summary'] = _create_validation_summary(results['comparisons'])
    
    return results


def _compare_methods(
    baseline_df: pd.DataFrame,
    framework_df: pd.DataFrame,
    yield_col: str,
    selected_col: str,
    high_risk_threshold: float,
    cost_inline: float
) -> Dict[str, Any]:
    """두 방법 비교"""
    comparison = {}
    
    # 고위험 마스크
    high_risk = baseline_df[yield_col] < high_risk_threshold
    
    # 선택 상태
    baseline_selected = baseline_df[selected_col].astype(bool)
    framework_selected = framework_df[selected_col].astype(bool)
    
    # 1. T-test (선택된 웨이퍼의 yield)
    if baseline_selected.sum() > 0 and framework_selected.sum() > 0:
        baseline_yields = baseline_df.loc[baseline_selected, yield_col].values
        framework_yields = framework_df.loc[framework_selected, yield_col].values
        
        comparison['t_test'] = t_test_yields(baseline_yields, framework_yields)
    else:
        comparison['t_test'] = {'error': 'Insufficient samples'}
    
    # 2. Chi-square (검출률)
    baseline_tp = (high_risk & baseline_selected).sum()
    baseline_fn = (high_risk & ~baseline_selected).sum()
    framework_tp = (high_risk & framework_selected).sum()
    framework_fn = (high_risk & ~framework_selected).sum()
    
    comparison['chi_square'] = chi_square_detection(
        int(baseline_tp), int(baseline_fn),
        int(framework_tp), int(framework_fn)
    )
    
    # 3. Bootstrap (비용 절감)
    baseline_costs = baseline_selected.astype(float) * cost_inline
    framework_costs = framework_selected.astype(float) * cost_inline
    
    comparison['bootstrap'] = bootstrap_cost_ci(
        baseline_costs.values,
        framework_costs.values
    )
    
    # 메트릭 요약
    comparison['metrics_comparison'] = {
        'baseline_selected': int(baseline_selected.sum()),
        'framework_selected': int(framework_selected.sum()),
        'baseline_tp': int(baseline_tp),
        'framework_tp': int(framework_tp),
        'baseline_recall': float(baseline_tp / (baseline_tp + baseline_fn)) if (baseline_tp + baseline_fn) > 0 else 0,
        'framework_recall': float(framework_tp / (framework_tp + framework_fn)) if (framework_tp + framework_fn) > 0 else 0,
        'cost_reduction': float(baseline_costs.sum() - framework_costs.sum()),
        'cost_reduction_pct': float((baseline_costs.sum() - framework_costs.sum()) / baseline_costs.sum() * 100) if baseline_costs.sum() > 0 else 0
    }
    
    return comparison


def _create_validation_summary(comparisons: Dict[str, Dict]) -> Dict[str, Any]:
    """검증 요약 생성"""
    summary = {
        'total_comparisons': len(comparisons),
        'significant_tests': [],
        'overall_conclusion': ''
    }
    
    all_significant = True
    
    for comp_name, comp_data in comparisons.items():
        tests_passed = []
        
        # T-test
        t_test = comp_data.get('t_test', {})
        if t_test.get('significant_005'):
            tests_passed.append(f"{comp_name}: t-test")
        else:
            all_significant = False
        
        # Chi-square
        chi_sq = comp_data.get('chi_square', {})
        if chi_sq.get('significant_005'):
            tests_passed.append(f"{comp_name}: chi-square")
        else:
            all_significant = False
        
        # Bootstrap
        bootstrap = comp_data.get('bootstrap', {})
        if bootstrap.get('significant_005'):
            tests_passed.append(f"{comp_name}: bootstrap")
        else:
            all_significant = False
        
        summary['significant_tests'].extend(tests_passed)
    
    if all_significant:
        summary['overall_conclusion'] = "모든 통계 검정에서 유의한 차이 확인"
    elif len(summary['significant_tests']) > 0:
        summary['overall_conclusion'] = f"일부 검정에서 유의한 차이 확인 ({len(summary['significant_tests'])}개)"
    else:
        summary['overall_conclusion'] = "유의한 차이 없음"
    
    return summary


def format_validation_report(results: Dict[str, Any]) -> str:
    """검증 결과 보고서 포맷팅"""
    report = """
## 통계 검증 결과

### 검정 요약

"""
    
    for comp_name, comp_data in results.get('comparisons', {}).items():
        report += f"#### {comp_name}\n\n"
        
        # T-test
        t_test = comp_data.get('t_test', {})
        t_sig = "✅ 유의" if t_test.get('significant_005') else "❌ 비유의"
        t_p = t_test.get('p_value', 'N/A')
        t_p_str = f"<0.001" if isinstance(t_p, float) and t_p < 0.001 else f"{t_p:.4f}" if isinstance(t_p, float) else t_p
        report += f"- **T-test**: t={t_test.get('t_statistic', 'N/A'):.3f}, p={t_p_str} ({t_sig})\n"
        
        # Chi-square
        chi_sq = comp_data.get('chi_square', {})
        chi_sig = "✅ 유의" if chi_sq.get('significant_005') else "❌ 비유의"
        chi_p = chi_sq.get('p_value', 'N/A')
        chi_p_str = f"<0.001" if isinstance(chi_p, float) and chi_p < 0.001 else f"{chi_p:.4f}" if isinstance(chi_p, float) else chi_p
        report += f"- **Chi-square**: χ²={chi_sq.get('chi2_statistic', 'N/A'):.3f}, p={chi_p_str} ({chi_sig})\n"
        
        # Bootstrap
        bootstrap = comp_data.get('bootstrap', {})
        report += f"- **Bootstrap 95% CI**: [{bootstrap.get('ci_lower', 'N/A'):.1f}, {bootstrap.get('ci_upper', 'N/A'):.1f}]\n"
        
        # 메트릭 비교
        metrics = comp_data.get('metrics_comparison', {})
        report += f"- 비용 절감: ${metrics.get('cost_reduction', 0):,.0f} ({metrics.get('cost_reduction_pct', 0):.1f}%)\n"
        report += f"- Recall 향상: {metrics.get('framework_recall', 0) - metrics.get('baseline_recall', 0):.1%}\n"
        report += "\n"
    
    # 결론
    summary = results.get('summary', {})
    report += f"""
### 전체 결론

{summary.get('overall_conclusion', '')}

- 총 비교 수: {summary.get('total_comparisons', 0)}
- 유의한 검정 수: {len(summary.get('significant_tests', []))}
"""
    
    return report
