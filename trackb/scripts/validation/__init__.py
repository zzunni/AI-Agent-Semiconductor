"""
Track B Validation
검증 모듈
"""

from .ground_truth_validator import GroundTruthValidator
from .proxy_validator import ProxyValidator

__all__ = [
    'GroundTruthValidator',
    'ProxyValidator'
]

# run_full_validation은 필요할 때 직접 임포트
# from validation.statistical_validator import run_full_validation
