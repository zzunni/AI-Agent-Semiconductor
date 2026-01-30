"""
Track B Decision Explainer
결정 설명 및 추적
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExplanationRecord:
    """설명 기록"""
    wafer_id: str
    stage: int
    decision: str
    risk_score: float
    threshold: float
    top_reasons: List[str]
    scheduler_reason: str
    confidence: float = 0.0


class DecisionExplainer:
    """
    결정 설명기
    각 웨이퍼에 대한 결정 이유를 추적하고 설명
    """
    
    def __init__(self, top_k_reasons: int = 3):
        """
        Args:
            top_k_reasons: 기록할 상위 이유 개수
        """
        self.top_k_reasons = top_k_reasons
        self.traces: List[ExplanationRecord] = []
        
        logger.info(f"DecisionExplainer 초기화: top_k={top_k_reasons}")
    
    def reset(self) -> None:
        """추적 기록 초기화"""
        self.traces = []
    
    def add_trace(
        self,
        wafer_id: str,
        stage: int,
        decision: str,
        risk_score: float,
        threshold: float,
        top_features: Optional[List[str]] = None,
        scheduler_reason: str = '',
        confidence: float = 0.0
    ) -> None:
        """
        결정 추적 기록 추가
        
        Args:
            wafer_id: 웨이퍼 ID
            stage: 현재 스테이지
            decision: 결정 ('inspect', 'pass', 'sem')
            risk_score: risk score
            threshold: 사용된 임계값
            top_features: 상위 기여 피처 리스트
            scheduler_reason: 스케줄러 조정 이유
            confidence: 결정 신뢰도
        """
        top_features = top_features or []
        
        # top_k로 제한
        top_features = top_features[:self.top_k_reasons]
        
        record = ExplanationRecord(
            wafer_id=wafer_id,
            stage=stage,
            decision=decision,
            risk_score=risk_score,
            threshold=threshold,
            top_reasons=top_features,
            scheduler_reason=scheduler_reason,
            confidence=confidence
        )
        
        self.traces.append(record)
    
    def add_traces_from_df(
        self,
        df: pd.DataFrame,
        wafer_id_col: str = 'wafer_id',
        decision_col: str = 'decision',
        risk_col: str = 'riskscore',
        threshold_col: str = 'threshold',
        reason_col: str = 'scheduler_reason'
    ) -> None:
        """
        DataFrame에서 추적 기록 일괄 추가
        
        Args:
            df: 결정이 포함된 DataFrame
        """
        for idx, row in df.iterrows():
            self.add_trace(
                wafer_id=str(row.get(wafer_id_col, idx)),
                stage=0,
                decision=row.get(decision_col, 'unknown'),
                risk_score=row.get(risk_col, 0),
                threshold=row.get(threshold_col, 0),
                top_features=[],  # Feature importance는 별도로 추가 필요
                scheduler_reason=row.get(reason_col, '')
            )
    
    def export(self, output_path: Optional[str] = None) -> pd.DataFrame:
        """
        추적 기록 내보내기
        
        Args:
            output_path: 저장 경로 (None이면 저장 안 함)
        
        Returns:
            추적 기록 DataFrame
        """
        if not self.traces:
            logger.warning("추적 기록이 없습니다")
            return pd.DataFrame()
        
        rows = []
        for trace in self.traces:
            row = {
                'wafer_id': trace.wafer_id,
                'stage': trace.stage,
                'decision': trace.decision,
                'risk_score': trace.risk_score,
                'threshold': trace.threshold,
                'scheduler_reason': trace.scheduler_reason,
                'confidence': trace.confidence
            }
            
            # 상위 이유 컬럼 추가
            for i, reason in enumerate(trace.top_reasons):
                row[f'top_reason_{i+1}'] = reason
            
            # 빈 이유 컬럼 채우기
            for i in range(len(trace.top_reasons), self.top_k_reasons):
                row[f'top_reason_{i+1}'] = None
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        if output_path:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"결정 추적 저장: {output_path} ({len(df)}개)")
        
        return df
    
    def get_summary(self) -> Dict[str, Any]:
        """설명 요약"""
        if not self.traces:
            return {'error': 'No traces recorded'}
        
        df = self.export()
        
        decision_counts = df['decision'].value_counts().to_dict()
        reason_counts = df['scheduler_reason'].value_counts().to_dict()
        
        return {
            'total_decisions': len(self.traces),
            'decision_counts': decision_counts,
            'scheduler_reason_counts': reason_counts,
            'avg_risk_score': float(df['risk_score'].mean()),
            'avg_threshold': float(df['threshold'].mean()),
            'inspect_rate': float(decision_counts.get('inspect', 0) / len(df)) if len(df) > 0 else 0
        }
    
    def generate_explanation_text(
        self,
        wafer_id: str
    ) -> str:
        """
        특정 웨이퍼에 대한 설명 텍스트 생성
        
        Args:
            wafer_id: 웨이퍼 ID
        
        Returns:
            설명 텍스트
        """
        matching = [t for t in self.traces if t.wafer_id == wafer_id]
        
        if not matching:
            return f"웨이퍼 {wafer_id}에 대한 기록이 없습니다."
        
        trace = matching[-1]  # 가장 최근 기록
        
        explanation = f"""
웨이퍼 ID: {trace.wafer_id}
스테이지: {trace.stage}
결정: {trace.decision.upper()}

Risk Score: {trace.risk_score:.4f}
임계값: {trace.threshold:.4f}
스케줄러 조정: {trace.scheduler_reason}
"""
        
        if trace.top_reasons:
            explanation += "\n주요 기여 요인:\n"
            for i, reason in enumerate(trace.top_reasons, 1):
                explanation += f"  {i}. {reason}\n"
        
        if trace.decision == 'inspect':
            explanation += f"\n결정 근거: Risk score ({trace.risk_score:.4f}) >= 임계값 ({trace.threshold:.4f})"
        else:
            explanation += f"\n결정 근거: Risk score ({trace.risk_score:.4f}) < 임계값 ({trace.threshold:.4f})"
        
        return explanation


def generate_decision_trace_report(
    explainer: DecisionExplainer,
    df: pd.DataFrame,
    yield_col: str = 'yield_true',
    high_risk_threshold: float = 0.6
) -> str:
    """
    결정 추적 보고서 생성
    
    Args:
        explainer: DecisionExplainer 객체
        df: 결과 DataFrame (yield_true 포함)
        yield_col: yield 컬럼명
        high_risk_threshold: 고위험 임계값
    
    Returns:
        보고서 텍스트
    """
    trace_df = explainer.export()
    summary = explainer.get_summary()
    
    if trace_df.empty:
        return "결정 추적 기록이 없습니다."
    
    # 결과 병합
    if 'wafer_id' in df.columns and 'wafer_id' in trace_df.columns:
        merged = trace_df.merge(
            df[['wafer_id', yield_col]],
            on='wafer_id',
            how='left'
        )
    else:
        merged = trace_df.copy()
        merged[yield_col] = df[yield_col].values
    
    # 분석
    inspected = merged[merged['decision'] == 'inspect']
    passed = merged[merged['decision'] != 'inspect']
    
    report = f"""
## 결정 추적 보고서

### 요약
- 총 결정 수: {summary['total_decisions']}
- 검사 대상: {summary['decision_counts'].get('inspect', 0)}
- 통과: {summary['decision_counts'].get('pass', 0)}
- 검사율: {summary['inspect_rate']:.1%}

### 스케줄러 조정 현황
"""
    
    for reason, count in summary['scheduler_reason_counts'].items():
        report += f"- {reason}: {count}회\n"
    
    # 검사 대상 중 고위험 비율
    if len(inspected) > 0 and yield_col in inspected.columns:
        inspected_high_risk = (inspected[yield_col] < high_risk_threshold).sum()
        report += f"""
### 검사 대상 분석
- 검사 대상 중 고위험: {inspected_high_risk}/{len(inspected)} ({inspected_high_risk/len(inspected):.1%})
- 검사 대상 평균 yield: {inspected[yield_col].mean():.4f}
"""
    
    # 통과 중 고위험 (놓친 것)
    if len(passed) > 0 and yield_col in passed.columns:
        passed_high_risk = (passed[yield_col] < high_risk_threshold).sum()
        report += f"""
### 통과 웨이퍼 분석
- 통과 중 고위험 (놓침): {passed_high_risk}/{len(passed)} ({passed_high_risk/len(passed):.1%})
- 통과 평균 yield: {passed[yield_col].mean():.4f}
"""
    
    return report
