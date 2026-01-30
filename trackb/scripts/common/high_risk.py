"""
High-risk Definition Utility
하위 20% 기반 고위험 웨이퍼 정의
"""

from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np
import hashlib
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def define_high_risk_bottom_quantile(
    df: pd.DataFrame,
    yield_col: str = 'yield_true',
    quantile: float = 0.20,
    tie_breaker_col: str = 'wafer_id'
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    하위 quantile (예: 20%) 기반 고위험 웨이퍼 정의
    
    Args:
        df: 평가 데이터프레임
        yield_col: yield 컬럼명
        quantile: 하위 비율 (0.20 = 하위 20%)
        tie_breaker_col: 동점 처리용 컬럼
    
    Returns:
        (high_risk_mask, definition_dict)
    """
    if yield_col not in df.columns:
        raise ValueError(f"컬럼 '{yield_col}'이 존재하지 않습니다")
    
    N = len(df)
    k = int(np.floor(quantile * N))  # 정확히 k개 선택
    
    # Yield 기준 정렬 (오름차순: 낮은 yield가 위험)
    df_sorted = df.sort_values(
        by=[yield_col, tie_breaker_col],
        ascending=[True, True]  # yield 낮은 순, wafer_id 오름차순
    ).reset_index(drop=True)
    
    # 하위 k개를 high-risk로 지정
    high_risk_indices = df_sorted.index[:k]
    high_risk_mask = pd.Series(False, index=df.index)
    high_risk_mask.iloc[high_risk_indices] = True
    
    # Threshold 값 (참고용)
    if k > 0:
        threshold_yield_at_k = df_sorted.iloc[k-1][yield_col]
        # k번째와 k+1번째 사이의 값도 기록
        if k < N:
            threshold_yield_next = df_sorted.iloc[k][yield_col]
        else:
            threshold_yield_next = threshold_yield_at_k
    else:
        threshold_yield_at_k = None
        threshold_yield_next = None
    
    # 정의 정보 저장
    definition = {
        'method': 'bottom_quantile_fixed_k',
        'quantile': quantile,
        'N': int(N),
        'k': int(k),
        'actual_rate': float(k / N),
        'threshold_yield_at_k': float(threshold_yield_at_k) if threshold_yield_at_k is not None else None,
        'threshold_yield_next': float(threshold_yield_next) if threshold_yield_next is not None else None,
        'tie_breaker': f'{tie_breaker_col}_ascending',
        'yield_col': yield_col
    }
    
    logger.info(
        f"High-risk 정의: 하위 {quantile:.0%} = {k}/{N}개, "
        f"threshold_yield_at_k={threshold_yield_at_k:.4f}"
    )
    
    return high_risk_mask, definition


def save_high_risk_definition(
    definition: Dict[str, Any],
    df_source: pd.DataFrame,
    output_path: Path,
    source_file_hash: str = None
) -> None:
    """
    High-risk 정의를 JSON으로 저장
    
    Args:
        definition: 정의 딕셔너리
        df_source: 소스 데이터프레임 (해시 계산용)
        output_path: 저장 경로
        source_file_hash: 소스 파일 해시 (있으면 사용)
    """
    # 데이터프레임 해시 계산 (yield_true 컬럼만)
    if source_file_hash is None:
        if 'yield_true' in df_source.columns:
            yield_values = df_source['yield_true'].values
            yield_str = ','.join([f'{v:.6f}' for v in sorted(yield_values)])
            source_hash = hashlib.sha256(yield_str.encode()).hexdigest()
        else:
            source_hash = None
    else:
        source_hash = source_file_hash
    
    definition['source_data_hash'] = source_hash
    definition['source_row_count'] = int(len(df_source))
    # 평가 라벨 vs 운영 선별 분리 (논문/정책 명시)
    definition['evaluation_label'] = (
        f"yield_true bottom 20% with k fixed on test={definition.get('N', 200)} (k={definition.get('k', 40)})"
    )
    definition['operational_selection'] = (
        "top selection_rate by risk_score (default 10%)"
    )
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(definition, f, indent=2, ensure_ascii=False)
    
    logger.info(f"High-risk 정의 저장: {output_path}")


def load_high_risk_definition(definition_path: Path) -> Dict[str, Any]:
    """High-risk 정의 로드"""
    with open(definition_path, 'r', encoding='utf-8') as f:
        return json.load(f)
