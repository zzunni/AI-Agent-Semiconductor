"""
Stage Executors: AI 분석 실행 및 다음 Decision 생성
"""

import numpy as np
import streamlit as st
from datetime import datetime


# ==========================================
# Stage 0 → Stage 1
# ==========================================

def execute_stage0_to_stage1(wafer_id, lot_id):
    """
    Stage 0 승인 → Inline 측정 → Stage 1 분석

    Returns:
        dict: Stage 1 Decision
    """
    print(f"[DEBUG] execute_stage0_to_stage1 called: {wafer_id}, {lot_id}")

    # 1. 웨이퍼 데이터 가져오기
    wafer_data = get_wafer_data(wafer_id)

    if not wafer_data:
        print(f"[ERROR] Wafer data not found: {wafer_id}")
        return None

    # 2. Inline 측정 (Mock)
    inline_data = {
        'critical_dimension': np.random.normal(21, 1),
        'overlay_error': np.random.normal(5, 1.5),
        'defect_density': np.random.uniform(0.3, 1.2),
        'film_thickness': np.random.normal(100, 5)
    }

    # 3. Yield 예측
    yield_pred = calculate_yield_prediction(wafer_data, inline_data)

    # 4. 경제성 분석
    wafer_value = 20000
    rework_cost = 5000

    proceed_value = yield_pred * wafer_value
    rework_value = min(0.85, yield_pred + 0.15) * wafer_value - rework_cost
    net_benefit = max(0, rework_value - proceed_value)

    # 5. AI 제안
    if yield_pred < 0.4:
        ai_recommendation = 'REWORK'
        reasoning = f"Very low yield ({yield_pred:.1%}), rework strongly recommended"
    elif net_benefit > 1000:
        ai_recommendation = 'REWORK'
        reasoning = f"Rework economically beneficial (+${net_benefit:.0f})"
    else:
        ai_recommendation = 'PROCEED'
        reasoning = f"Acceptable yield ({yield_pred:.1%}), proceed to next stage"

    # 6. Decision 생성
    decision = {
        'id': f"{wafer_id}-stage1",
        'wafer_id': wafer_id,
        'lot_id': lot_id,
        'stage': 'Stage 1',
        'priority': '🔴 HIGH' if yield_pred < 0.5 else '🟡 MEDIUM',
        'ai_recommendation': ai_recommendation,
        'ai_confidence': 0.72,
        'ai_reasoning': reasoning,
        'yield_pred': yield_pred,
        'inline_data': inline_data,
        'economics': {
            'cost': rework_cost,
            'proceed_value': proceed_value,
            'rework_value': rework_value,
            'benefit': net_benefit
        },
        'key_features': [
            f"CD: {inline_data['critical_dimension']:.1f}nm",
            f"Overlay: {inline_data['overlay_error']:.1f}nm",
            f"Defect density: {inline_data['defect_density']:.2f}"
        ],
        'available_options': ['REWORK', 'PROCEED', 'SCRAP', 'HOLD'],
        'time_elapsed': '< 1 min',
        'created_at': datetime.now()
    }

    print(f"[DEBUG] Stage 1 decision created: {decision['id']}")
    return decision


def calculate_yield_prediction(wafer_data, inline_data):
    """Yield 예측"""
    yield_pred = 1.0

    # 센서 데이터 체크
    if wafer_data.get('etch_rate', 3.5) > 3.8:
        yield_pred -= 0.2
    if wafer_data.get('pressure', 150) > 160:
        yield_pred -= 0.15

    # Inline 데이터 체크
    if inline_data['critical_dimension'] > 22:
        yield_pred -= 0.15
    if inline_data['defect_density'] > 0.8:
        yield_pred -= 0.1
    if inline_data['overlay_error'] > 6:
        yield_pred -= 0.1

    return max(0.3, min(1.0, yield_pred))


# ==========================================
# Stage 1 → Stage 2A
# ==========================================

def execute_stage1_to_stage2a(wafer_id, lot_id):
    """Stage 1 → Stage 2A (LOT 분석)"""
    print(f"[DEBUG] execute_stage1_to_stage2a called: {wafer_id}, {lot_id}")

    # Mock WAT 데이터
    wat_data = {
        'vth_nmos': np.random.normal(0.45, 0.02),
        'vth_pmos': np.random.normal(-0.45, 0.02),
        'contact_resistance': np.random.normal(48, 3),
        'idsat_nmos': np.random.normal(650, 20)
    }

    electrical_quality = 'PASS'
    uniformity_score = np.random.uniform(0.7, 0.9)

    spec_violations = []
    if wat_data['contact_resistance'] > 50:
        spec_violations.append({
            'parameter': 'contact_resistance',
            'value': wat_data['contact_resistance'],
            'spec_upper': 50
        })

    if electrical_quality == 'PASS' and uniformity_score > 0.75:
        ai_recommendation = 'TO_EDS'
        reasoning = f"Good electrical quality (uniformity: {uniformity_score:.2f})"
    else:
        ai_recommendation = 'TO_EDS'
        reasoning = f"Marginal quality but acceptable (uniformity: {uniformity_score:.2f})"

    decision = {
        'id': f"{lot_id}-stage2a",
        'wafer_id': f"{lot_id} (LOT)",
        'lot_id': lot_id,
        'stage': 'Stage 2A',
        'priority': '🟡 MEDIUM',
        'ai_recommendation': ai_recommendation,
        'ai_confidence': 0.85,
        'ai_reasoning': reasoning,
        'electrical_quality': electrical_quality,
        'uniformity_score': uniformity_score,
        'spec_violations': spec_violations,
        'economics': {
            'cost': 500000,
            'loss': 0,
            'benefit': 0
        },
        'available_options': ['TO_EDS', 'LOT_SCRAP', 'REWORK_ATTEMPT'],
        'time_elapsed': '< 1 min',
        'created_at': datetime.now()
    }

    print(f"[DEBUG] Stage 2A decision created: {decision['id']}")
    return decision


# ==========================================
# Stage 2A → Stage 2B
# ==========================================

def execute_stage2a_to_stage2b(lot_id):
    """Stage 2A → Stage 2B (Pattern 분석)"""
    print(f"[DEBUG] execute_stage2a_to_stage2b called: {lot_id}")

    sem_candidates = []
    patterns = ['Edge-Ring', 'Random', 'Center', 'Loc', 'Edge-Ring']
    severities = [85, 78, 65, 62, 58]

    for i, (pattern, severity) in enumerate(zip(patterns, severities)):
        wafer_id = f"{lot_id}-W{np.random.randint(1, 26):03d}"
        sem_candidates.append({
            'wafer_id': wafer_id,
            'pattern': pattern,
            'severity': severity
        })

    decision = {
        'id': f"{lot_id}-stage2b",
        'wafer_id': f"{lot_id} (SEM Selection)",
        'lot_id': lot_id,
        'stage': 'Stage 2B',
        'priority': '🟡 MEDIUM',
        'ai_recommendation': 'APPROVE_TOP_3',
        'ai_confidence': 0.80,
        'ai_reasoning': "Top 3 candidates provide 85% pattern coverage",
        'sem_candidates': sem_candidates,
        'total_sem_cost': len(sem_candidates) * 800,
        'available_options': ['APPROVE_ALL', 'APPROVE_PARTIAL', 'SKIP_SEM', 'REVISE_LIST'],
        'time_elapsed': '< 1 min',
        'created_at': datetime.now()
    }

    print(f"[DEBUG] Stage 2B decision created: {decision['id']}")
    return decision


# ==========================================
# Stage 2B → Stage 3
# ==========================================

def execute_stage2b_to_stage3(wafer_id, lot_id):
    """Stage 2B → Stage 3 (SEM 분석)"""
    print(f"[DEBUG] execute_stage2b_to_stage3 called: {wafer_id}, {lot_id}")

    wafer_data = get_wafer_data(wafer_id)
    etch_rate = wafer_data.get('etch_rate', 3.5) if wafer_data else 3.5
    pressure = wafer_data.get('pressure', 150) if wafer_data else 150

    defect_type = np.random.choice(['Pit', 'Particle', 'Residue'])
    defect_count = np.random.randint(5, 25)

    # LLM 근본 원인 분석 (한국어)
    llm_root_cause = f"""센서 데이터와 결함 패턴 분석:

1. 높은 etch rate ({etch_rate:.2f} μm/min)와 압력({pressure:.1f} mTorr) 조합이
   {defect_type} 결함을 유발하여 가장자리 과식각 발생

2. Chamber의 uniformity 저하 징후 확인 (최근 5 LOT 분석 결과)

3. 유사 패턴이 현재 Recipe 사용 시 83% 확률로 발생

권장 조치:
• 단기 (즉시): Chamber PM 수행
• 중기 (1주): Etch rate 3.6 μm/min으로 감소
• 장기 (지속): Edge uniformity 모니터링 강화

예상 효과:
• 수율 향상: +{np.random.randint(4, 8)}%p
• 비용 절감: ${np.random.randint(40, 60):,}/월
• 투자 회수: {np.random.uniform(0.8, 1.5):.1f}개월"""

    ai_recommendation = 'APPLY_NEXT_LOT' if defect_count < 15 else 'INVESTIGATE'

    decision = {
        'id': f"{wafer_id}-stage3",
        'wafer_id': wafer_id,
        'lot_id': lot_id,
        'stage': 'Stage 3',
        'priority': '🔴 HIGH' if defect_count > 15 else '🟡 MEDIUM',
        'ai_recommendation': ai_recommendation,
        'ai_confidence': 0.91,
        'ai_reasoning': f"{defect_type} defects detected ({defect_count} count)",
        'llm_analysis': llm_root_cause,
        'defect_type': defect_type,
        'defect_count': defect_count,
        'available_options': ['APPLY_NEXT_LOT', 'MODIFY', 'DEFER'],
        'time_elapsed': '< 1 min',
        'created_at': datetime.now()
    }

    print(f"[DEBUG] Stage 3 decision created: {decision['id']}")
    return decision


# ==========================================
# Helper Functions
# ==========================================

def get_wafer_data(wafer_id):
    """웨이퍼 데이터 가져오기"""
    if 'active_lots' not in st.session_state:
        print(f"[ERROR] active_lots not in session_state")
        return None

    for lot in st.session_state['active_lots']:
        for wafer in lot['wafers']:
            if wafer['wafer_id'] == wafer_id:
                print(f"[DEBUG] Found wafer data: {wafer_id}")
                return wafer

    print(f"[ERROR] Wafer not found: {wafer_id}")
    return None


def add_pipeline_alert(wafer_id, stage, message):
    """파이프라인 알림 추가"""
    if 'recent_alerts' not in st.session_state:
        st.session_state['recent_alerts'] = []

    alert = {
        'id': f"alert-{datetime.now().timestamp()}",
        'wafer_id': wafer_id,
        'message': message,
        'severity': 'MEDIUM',
        'stage': stage,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }

    st.session_state['recent_alerts'].insert(0, alert)

    if len(st.session_state['recent_alerts']) > 100:
        st.session_state['recent_alerts'] = st.session_state['recent_alerts'][:100]

    print(f"[DEBUG] Alert added: {message}")
