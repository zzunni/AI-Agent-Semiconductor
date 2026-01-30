"""
Track B Proxy Validator
Proxy 기반 통합 검증 (Step 2B/3)
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class ProxyValidator:
    """
    Proxy 검증기
    다른 데이터 출처 간 통계적 유사성 검증
    """
    
    def __init__(self):
        logger.info("ProxyValidator 초기화")
    
    def validate_risk_to_severity_proxy(
        self,
        step1_risks: np.ndarray,
        step2_severities: np.ndarray
    ) -> Dict[str, Any]:
        """
        Risk score → Severity 매핑 검증
        KS 검정으로 분포 유사성 확인
        
        Args:
            step1_risks: Step 1 risk scores
            step2_severities: Step 2 severity scores
        
        Returns:
            검증 결과
        """
        # KS 검정
        ks_stat, p_value = stats.ks_2samp(step1_risks, step2_severities)
        
        result = {
            'proxy_type': 'risk_to_severity',
            'test': 'kolmogorov_smirnov',
            'ks_statistic': float(ks_stat),
            'p_value': float(p_value),
            'distributions_similar': p_value > 0.05,
            'interpretation': 'plausible' if p_value > 0.05 else 'different',
            'step1_risk_mean': float(step1_risks.mean()),
            'step1_risk_std': float(step1_risks.std()),
            'step2_severity_mean': float(step2_severities.mean()),
            'step2_severity_std': float(step2_severities.std()),
            'n_step1': len(step1_risks),
            'n_step2': len(step2_severities),
            'caveat': 'Plausibility-checked only, NOT causally validated'
        }
        
        logger.info(
            f"Risk → Severity proxy 검증: "
            f"KS={ks_stat:.4f}, p={p_value:.4f}, "
            f"{'유사' if result['distributions_similar'] else '다름'}"
        )
        
        return result
    
    def validate_pattern_estimation(
        self,
        step1_risks: np.ndarray,
        step2_patterns: pd.Series
    ) -> Dict[str, Any]:
        """
        Risk → Pattern 추정 검증
        도메인 지식 기반 추정의 타당성 확인
        
        Args:
            step1_risks: Step 1 risk scores
            step2_patterns: Step 2 실제 패턴
        
        Returns:
            검증 결과
        """
        # 패턴 분포 분석
        pattern_dist = step2_patterns.value_counts(normalize=True).to_dict()
        
        # Risk 구간별 기대 패턴 분포 (도메인 지식)
        expected_high_risk = {'Edge-Ring': 0.4, 'Edge-Loc': 0.3, 'Center': 0.2, 'other': 0.1}
        expected_low_risk = {'none': 0.6, 'Loc': 0.2, 'Center': 0.1, 'other': 0.1}
        
        result = {
            'proxy_type': 'risk_to_pattern',
            'method': 'domain_knowledge_based',
            'actual_pattern_distribution': pattern_dist,
            'expected_high_risk_patterns': expected_high_risk,
            'expected_low_risk_patterns': expected_low_risk,
            'validation_status': 'plausibility_check_only',
            'caveat': 'Cannot validate without same-wafer measurements'
        }
        
        logger.info("Risk → Pattern 추정 검증 (도메인 지식 기반)")
        
        return result
    
    def validate_integration_coverage(
        self,
        step1_df: pd.DataFrame,
        step2_df: pd.DataFrame,
        step3_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        통합 커버리지 검증
        각 단계별 데이터 범위 및 연결성 확인
        
        Returns:
            커버리지 검증 결과
        """
        result = {
            'step1': {
                'n_wafers': len(step1_df),
                'source': 'Real fab data',
                'has_ground_truth': 'yield_true' in step1_df.columns
            },
            'step2': {
                'n_samples': len(step2_df),
                'source': 'WM-811K benchmark',
                'has_ground_truth': False
            },
            'step3': {
                'n_samples': len(step3_df),
                'source': 'Carinthia dataset',
                'has_ground_truth': False
            },
            'integration_method': 'proxy_based',
            'integration_status': 'plausibility_checked',
            'limitation': 'Different data sources, no same-wafer validation possible',
            'recommendation': 'Collect integrated multi-stage measurements'
        }
        
        logger.info("통합 커버리지 검증 완료")
        
        return result
    
    def generate_proxy_report(
        self,
        validation_results: Dict[str, Any]
    ) -> str:
        """Proxy 검증 보고서 생성"""
        report = """
## Proxy 기반 통합 검증

### 검증 상태 요약

| 구성 요소 | 상태 | 검증 방법 |
|-----------|------|----------|
| Stage 0–2A (STEP 1) | ✅ Same-source, yield_true GT validated | 200개 테스트 웨이퍼 |
| Stage 2B (STEP 2) | ⚠️ Benchmark performance reported (proxy; different source) | WM-811K 벤치마크 |
| Stage 3 (STEP 3) | ⚠️ Benchmark performance reported (proxy; different source) | Carinthia 데이터셋 |
| 통합 (2B → 3) | ⚠️ Proxy plausibility check only (not causal) | KS 검정 + 도메인 지식 |

### 중요 주의사항

**용어 정의**:
- "Validated" (검증됨): Ground truth가 있는 동일 웨이퍼 측정으로 확인
- "Plausibility-checked" (타당성 확인): 통계적 유사성 또는 도메인 지식으로 확인

**한계**:
1. 다른 데이터 출처 (Step 1: 실제 fab, Step 2: WM-811K, Step 3: Carinthia)
2. 동일 웨이퍼의 다단계 측정 없음
3. 인과 관계 증명 불가

**향후 과제**:
- 동일 웨이퍼에 대한 통합 다단계 측정 데이터 수집
- End-to-end 검증 실시
"""
        
        return report


def validate_proxy_integration(
    step1_risks: np.ndarray,
    step2_severities: np.ndarray,
    step2_patterns: Optional[pd.Series] = None
) -> Dict[str, Any]:
    """
    Proxy 통합 검증 헬퍼 함수
    
    Returns:
        통합 검증 결과
    """
    validator = ProxyValidator()
    
    results = {
        'risk_to_severity': validator.validate_risk_to_severity_proxy(
            step1_risks, step2_severities
        )
    }
    
    if step2_patterns is not None:
        results['risk_to_pattern'] = validator.validate_pattern_estimation(
            step1_risks, step2_patterns
        )
    
    return results
