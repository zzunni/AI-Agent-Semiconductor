"""
Learning System: Engineer feedback 저장 및 AI 개선
"""

import streamlit as st
from datetime import datetime
import json
from pathlib import Path


def init_learning_system():
    """학습 시스템 초기화"""
    if 'engineer_feedbacks' not in st.session_state:
        st.session_state['engineer_feedbacks'] = []

    if 'ai_performance_metrics' not in st.session_state:
        st.session_state['ai_performance_metrics'] = {
            'total_decisions': 0,
            'agreements': 0,
            'disagreements': 0,
            'modifications': 0,
            'stage_performance': {
                'Stage 0': {'agreements': 0, 'total': 0},
                'Stage 1': {'agreements': 0, 'total': 0},
                'Stage 2A': {'agreements': 0, 'total': 0},
                'Stage 2B': {'agreements': 0, 'total': 0},
                'Stage 3': {'agreements': 0, 'total': 0}
            }
        }


def save_engineer_feedback(decision, action, engineer_decision, reasoning=None, note=None):
    """
    엔지니어 피드백 저장 (학습용)

    Args:
        decision: 원래 AI decision
        action: 'APPROVED', 'REJECTED', 'MODIFIED', 'HOLD'
        engineer_decision: 엔지니어가 선택한 최종 결정
        reasoning: 이유/근거 (Reject/Modify/Hold 시 필수)
        note: 추가 메모
    """
    init_learning_system()

    # Agreement 여부 판단
    ai_recommendation = decision.get('ai_recommendation', '')
    agreement = (action == 'APPROVED' and engineer_decision == ai_recommendation)

    # Feedback 객체 생성
    feedback = {
        'id': f"feedback-{datetime.now().timestamp()}",
        'timestamp': datetime.now().isoformat(),
        'decision_id': decision.get('id', ''),
        'wafer_id': decision.get('wafer_id', ''),
        'lot_id': decision.get('lot_id', ''),
        'stage': decision.get('stage', ''),

        # AI 제안
        'ai_recommendation': ai_recommendation,
        'ai_confidence': decision.get('ai_confidence', 0),
        'ai_reasoning': decision.get('ai_reasoning', ''),

        # 엔지니어 결정
        'engineer_action': action,
        'engineer_decision': engineer_decision,
        'engineer_reasoning': reasoning,
        'engineer_note': note,

        # Agreement
        'agreement': agreement,

        # 컨텍스트 데이터
        'economics': decision.get('economics', {}),
        'sensor_data': decision.get('wafer_data', {}),
        'inline_data': decision.get('inline_data', {}),
        'priority': decision.get('priority', ''),

        # 학습용 메타데이터
        'yield_pred': decision.get('yield_pred', None),
        'risk_score': decision.get('anomaly_score', None),
        'pattern': decision.get('sem_candidates', [{}])[0].get('pattern', None) if decision.get('sem_candidates') else None,
        'defect_type': decision.get('defect_type', None),
    }

    # 피드백 저장
    st.session_state['engineer_feedbacks'].append(feedback)

    # 성능 메트릭 업데이트
    update_ai_performance_metrics(feedback)

    # 파일로 저장 (optional - 영구 저장용)
    save_feedback_to_file(feedback)

    return feedback


def update_ai_performance_metrics(feedback):
    """AI 성능 메트릭 업데이트"""
    metrics = st.session_state['ai_performance_metrics']

    metrics['total_decisions'] += 1

    if feedback['agreement']:
        metrics['agreements'] += 1
    else:
        metrics['disagreements'] += 1

    if feedback['engineer_action'] == 'MODIFIED':
        metrics['modifications'] += 1

    # Stage별 성능
    stage = feedback['stage']
    if stage in metrics['stage_performance']:
        metrics['stage_performance'][stage]['total'] += 1
        if feedback['agreement']:
            metrics['stage_performance'][stage]['agreements'] += 1


def get_ai_performance_summary():
    """AI 성능 요약 반환"""
    init_learning_system()
    metrics = st.session_state['ai_performance_metrics']

    total = metrics['total_decisions']
    if total == 0:
        return {
            'agreement_rate': 0,
            'modification_rate': 0,
            'total_decisions': 0,
            'stage_performance': {}
        }

    agreement_rate = (metrics['agreements'] / total) * 100
    modification_rate = (metrics['modifications'] / total) * 100

    # Stage별 성능
    stage_perf = {}
    for stage, data in metrics['stage_performance'].items():
        if data['total'] > 0:
            stage_perf[stage] = {
                'agreement_rate': (data['agreements'] / data['total']) * 100,
                'total': data['total']
            }
        else:
            stage_perf[stage] = {'agreement_rate': 0, 'total': 0}

    return {
        'agreement_rate': agreement_rate,
        'modification_rate': modification_rate,
        'total_decisions': total,
        'stage_performance': stage_perf
    }


def save_feedback_to_file(feedback):
    """피드백을 파일로 저장 (영구 저장)"""
    try:
        # logs 디렉토리 생성
        logs_dir = Path(__file__).parent.parent.parent / 'logs'
        logs_dir.mkdir(exist_ok=True)

        # 날짜별 파일
        date_str = datetime.now().strftime('%Y%m%d')
        feedback_file = logs_dir / f'engineer_feedbacks_{date_str}.jsonl'

        # JSONL 형식으로 append
        with open(feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback, ensure_ascii=False) + '\n')

    except Exception as e:
        print(f"[WARNING] Failed to save feedback to file: {e}")


def get_recent_feedbacks(limit=50):
    """최근 피드백 가져오기"""
    init_learning_system()
    feedbacks = st.session_state['engineer_feedbacks']
    return feedbacks[-limit:] if len(feedbacks) > limit else feedbacks


def get_disagreement_patterns():
    """AI-Engineer 불일치 패턴 분석"""
    init_learning_system()
    feedbacks = st.session_state['engineer_feedbacks']

    disagreements = [f for f in feedbacks if not f['agreement']]

    if not disagreements:
        return {
            'total_disagreements': 0,
            'by_stage': {},
            'common_reasons': []
        }

    # Stage별 불일치
    by_stage = {}
    for d in disagreements:
        stage = d['stage']
        if stage not in by_stage:
            by_stage[stage] = []
        by_stage[stage].append({
            'ai_rec': d['ai_recommendation'],
            'engineer_rec': d['engineer_decision'],
            'reasoning': d['engineer_reasoning']
        })

    # 공통 이유 추출 (간단한 키워드 분석)
    all_reasons = [d['engineer_reasoning'] for d in disagreements if d['engineer_reasoning']]

    return {
        'total_disagreements': len(disagreements),
        'by_stage': by_stage,
        'all_reasons': all_reasons
    }


def should_retrain_model(stage):
    """해당 Stage 모델의 재학습 필요 여부 판단"""
    init_learning_system()
    metrics = st.session_state['ai_performance_metrics']

    stage_data = metrics['stage_performance'].get(stage, {'total': 0, 'agreements': 0})

    # 최소 피드백 개수 확인
    if stage_data['total'] < 50:
        return False, "Insufficient feedback data (need 50+)"

    # Agreement rate 확인
    agreement_rate = (stage_data['agreements'] / stage_data['total']) * 100

    if agreement_rate < 70:
        return True, f"Low agreement rate: {agreement_rate:.1f}%"

    return False, f"Performance acceptable: {agreement_rate:.1f}%"


def export_training_data(stage=None):
    """학습 데이터 export (모델 재학습용)"""
    init_learning_system()
    feedbacks = st.session_state['engineer_feedbacks']

    if stage:
        feedbacks = [f for f in feedbacks if f['stage'] == stage]

    # 학습 데이터 포맷으로 변환
    training_data = []
    for f in feedbacks:
        training_data.append({
            'features': {
                'sensor_data': f['sensor_data'],
                'inline_data': f['inline_data'],
                'economics': f['economics'],
                'ai_confidence': f['ai_confidence']
            },
            'ai_prediction': f['ai_recommendation'],
            'ground_truth': f['engineer_decision'],
            'metadata': {
                'wafer_id': f['wafer_id'],
                'timestamp': f['timestamp'],
                'reasoning': f['engineer_reasoning']
            }
        })

    return training_data
