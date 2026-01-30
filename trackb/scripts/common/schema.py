"""
Track B Schema Validation
데이터프레임 스키마 검증 유틸리티
"""

from typing import List, Set, Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """스키마 검증 실패 예외"""
    pass


# 필수 컬럼 정의
REQUIRED_COLUMNS: Dict[str, List[str]] = {
    # Step 1 관련
    'stage0_test': [
        'lot_id', 'wafer_id', 'yield'
    ],
    'stage0_pred': [
        'lot_id', 'wafer_id', 'yield', 'yield_true', 'yield_pred'
    ],
    'stage0_risk_scores': [
        'lot_id', 'wafer_id', 'yield_true', 'riskscore'
    ],
    'stage1_pred': [
        'lot_id', 'wafer_id', 'yield', 'yield_true', 'yield_pred'
    ],
    'stage2a_pred': [
        'lot_id', 'wafer_id', 'yield', 'yield_true', 'yield_pred'
    ],
    
    # Baseline 결과
    'baseline_results': [
        'wafer_id', 'lot_id', 'yield_true', 'selected'
    ],
    
    # Stage 1 통합 출력
    'stage1_risk_scores': [
        'wafer_id', 'lot_id', 'risk_score', 'yield_true'
    ],
    'stage1_selected': [
        'wafer_id', 'lot_id', 'risk_score', 'selected'
    ],
    
    # Stage 2B 관련
    'stage2b_results': [
        'orig_idx', 'pred_label', 'severity', 'sem_selected'
    ],
    
    # Stage 3 관련
    'stage3_results': [
        'wafer_id', 'pattern', 'pred_class', 'triage', 'recommendation'
    ],
    
    # 검증 결과
    'validation_results': [
        'wafer_id', 'yield_true', 'is_high_risk', 'selected', 'method'
    ],
    
    # Agent 출력
    'autotune_history': [
        'tau0', 'tau1', 'tau2a', 'cost', 'recall', 'within_budget'
    ],
    'scheduler_log': [
        'wafer_id', 'stage', 'budget_remaining', 'decision', 'reason'
    ],
    'decision_trace': [
        'wafer_id', 'stage', 'decision', 'risk_score', 'threshold'
    ]
}

# 데이터 타입 검증 규칙
COLUMN_DTYPES: Dict[str, Dict[str, str]] = {
    'stage0_risk_scores': {
        'lot_id': 'object',
        'wafer_id': 'object',
        'yield_true': 'float64',
        'riskscore': 'float64'
    },
    'baseline_results': {
        'wafer_id': 'object',
        'lot_id': 'object',
        'yield_true': 'float64',
        'selected': 'bool'
    }
}


def validate_schema(
    df: pd.DataFrame,
    schema_name: str,
    strict: bool = False
) -> bool:
    """
    DataFrame 스키마 검증
    
    Args:
        df: 검증할 DataFrame
        schema_name: 스키마 이름 (REQUIRED_COLUMNS의 키)
        strict: True면 필수 컬럼만 있어야 함
    
    Returns:
        검증 성공 시 True
    
    Raises:
        ValidationError: 검증 실패 시
    """
    required = REQUIRED_COLUMNS.get(schema_name)
    
    if required is None:
        logger.warning(f"알 수 없는 스키마: {schema_name}")
        return True
    
    available = set(df.columns)
    required_set = set(required)
    missing = required_set - available
    
    if missing:
        raise ValidationError(
            f"스키마 검증 실패: {schema_name}\n"
            f"누락된 컬럼: {missing}\n"
            f"사용 가능한 컬럼: {list(df.columns)}"
        )
    
    if strict:
        extra = available - required_set
        if extra:
            logger.warning(
                f"추가 컬럼 발견 (strict 모드): {extra}"
            )
    
    logger.debug(f"스키마 검증 성공: {schema_name}")
    return True


def validate_null_rate(
    df: pd.DataFrame,
    critical_cols: List[str],
    max_rate: float = 0.01
) -> bool:
    """
    주요 컬럼의 null 비율 검증
    
    Args:
        df: 검증할 DataFrame
        critical_cols: 검증할 컬럼 리스트
        max_rate: 허용 최대 null 비율 (기본 1%)
    
    Returns:
        검증 성공 시 True
    
    Raises:
        ValidationError: null 비율 초과 시
    """
    errors = []
    
    for col in critical_cols:
        if col not in df.columns:
            continue
        
        null_count = df[col].isnull().sum()
        null_rate = null_count / len(df)
        
        if null_rate > max_rate:
            errors.append(
                f"컬럼 '{col}': {null_rate:.1%} null "
                f"(최대 허용: {max_rate:.1%}, {null_count}개)"
            )
    
    if errors:
        raise ValidationError(
            "Null 비율 검증 실패:\n" + "\n".join(errors)
        )
    
    logger.debug(f"Null 비율 검증 성공 (컬럼 {len(critical_cols)}개)")
    return True


def validate_row_count(
    df: pd.DataFrame,
    expected_rows: int,
    tolerance: float = 0.05
) -> bool:
    """
    행 수 검증
    
    Args:
        df: 검증할 DataFrame
        expected_rows: 예상 행 수
        tolerance: 허용 오차 비율 (기본 5%)
    
    Returns:
        검증 성공 시 True
    
    Raises:
        ValidationError: 행 수가 범위를 벗어날 때
    """
    actual_rows = len(df)
    min_rows = int(expected_rows * (1 - tolerance))
    max_rows = int(expected_rows * (1 + tolerance))
    
    if not (min_rows <= actual_rows <= max_rows):
        raise ValidationError(
            f"행 수 검증 실패: {actual_rows}행 "
            f"(예상: {expected_rows}행, 허용 범위: {min_rows}-{max_rows})"
        )
    
    logger.debug(f"행 수 검증 성공: {actual_rows}행")
    return True


def validate_value_range(
    df: pd.DataFrame,
    col: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> bool:
    """
    값 범위 검증
    
    Args:
        df: 검증할 DataFrame
        col: 검증할 컬럼
        min_val: 최소값 (None이면 검사 안 함)
        max_val: 최대값 (None이면 검사 안 함)
    
    Returns:
        검증 성공 시 True
    
    Raises:
        ValidationError: 범위를 벗어난 값이 있을 때
    """
    if col not in df.columns:
        raise ValidationError(f"컬럼 '{col}'이 존재하지 않습니다")
    
    values = df[col].dropna()
    
    if min_val is not None:
        below_min = (values < min_val).sum()
        if below_min > 0:
            raise ValidationError(
                f"컬럼 '{col}': {below_min}개 값이 최소값 {min_val} 미만"
            )
    
    if max_val is not None:
        above_max = (values > max_val).sum()
        if above_max > 0:
            raise ValidationError(
                f"컬럼 '{col}': {above_max}개 값이 최대값 {max_val} 초과"
            )
    
    logger.debug(f"값 범위 검증 성공: {col}")
    return True


def validate_unique(
    df: pd.DataFrame,
    cols: List[str]
) -> bool:
    """
    유니크 제약 검증
    
    Args:
        df: 검증할 DataFrame
        cols: 유니크해야 하는 컬럼 조합
    
    Returns:
        검증 성공 시 True
    
    Raises:
        ValidationError: 중복이 있을 때
    """
    for col in cols:
        if col not in df.columns:
            raise ValidationError(f"컬럼 '{col}'이 존재하지 않습니다")
    
    duplicates = df[df.duplicated(subset=cols, keep=False)]
    
    if len(duplicates) > 0:
        sample = duplicates.head(5)[cols].to_dict('records')
        raise ValidationError(
            f"중복 발견 (컬럼: {cols})\n"
            f"중복 수: {len(duplicates)}개\n"
            f"샘플: {sample}"
        )
    
    logger.debug(f"유니크 검증 성공: {cols}")
    return True


def get_schema_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """DataFrame 스키마 요약 생성"""
    summary = {
        'row_count': len(df),
        'column_count': len(df.columns),
        'columns': {}
    }
    
    for col in df.columns:
        col_info = {
            'dtype': str(df[col].dtype),
            'null_count': int(df[col].isnull().sum()),
            'null_rate': float(df[col].isnull().mean()),
            'unique_count': int(df[col].nunique())
        }
        
        if df[col].dtype in ['float64', 'int64']:
            col_info['min'] = float(df[col].min())
            col_info['max'] = float(df[col].max())
            col_info['mean'] = float(df[col].mean())
        
        summary['columns'][col] = col_info
    
    return summary
