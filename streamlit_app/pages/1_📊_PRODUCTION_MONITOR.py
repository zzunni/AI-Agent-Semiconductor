# streamlit_app/pages/1_🏭_production_monitor.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# Add utils to path
utils_path = Path(__file__).parent.parent / 'utils'
if str(utils_path) not in sys.path:
    sys.path.insert(0, str(utils_path))

from ui_components import render_enhanced_sidebar

st.set_page_config(page_title="Production Monitor", page_icon="🏭", layout="wide")

def main():
    # Enhanced Sidebar
    render_enhanced_sidebar()

    st.title("PRODUCTION MONITOR")
    st.caption("Real-time LOT monitoring and sensor streams")

    # ==========================================
    # Section 1: Control Panel
    # ==========================================
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("🚀 Start New LOT", type="primary"):
            start_new_lot()
            st.rerun()

    with col2:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)

    # ==========================================
    # Section 2: Metrics
    # ==========================================
    active_lots = get_active_lots()

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.metric("🔄 Active LOTs", len(active_lots))

    with metric_col2:
        total_wafers = sum(lot['wafer_count'] for lot in active_lots)
        st.metric("📦 Wafers In-Process", total_wafers)

    with metric_col3:
        pending = get_pending_decision_count()
        st.metric("⚠️ Pending Decisions", pending, delta=f"+{pending}" if pending > 0 else "0")

    with metric_col4:
        alerts = get_alert_count()
        st.metric("🚨 Alerts", alerts, delta=f"+{alerts}" if alerts > 0 else "0")

    # ==========================================
    # Section 3: LOT Cards
    # ==========================================
    st.markdown("---")
    st.subheader("📦 Active LOTs")

    if not active_lots:
        st.info("No active LOTs. Click 'Start New LOT' to begin.")
        return

    for lot in active_lots:
        render_lot_card(lot)

    # ==========================================
    # Section 4: Real-time Sensor Stream
    # ==========================================
    st.markdown("---")
    st.subheader("📊 Real-time Sensor Stream")

    sensor_select = st.multiselect(
        "Select sensors:",
        ["etch_rate", "pressure", "temperature", "rf_power", "gas_flow"],
        default=["etch_rate", "pressure"]
    )

    if sensor_select:
        sensor_data = get_realtime_sensor_data(sensor_select)
        fig = create_realtime_sensor_chart(sensor_data, sensor_select)
        st.plotly_chart(fig, use_container_width=True, key="sensor_chart")

    # ==========================================
    # Section 5: Recent Alerts
    # ==========================================
    st.markdown("---")
    st.subheader("🚨 Recent Alerts")

    alerts = get_recent_alerts(limit=10)

    if not alerts:
        st.success("✅ No alerts")
    else:
        for alert in alerts:
            severity_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[alert['severity']]

            alert_col1, alert_col2 = st.columns([4, 1])

            with alert_col1:
                st.write(f"{severity_icon} **{alert['wafer_id']}** - {alert['message']}")
                st.caption(f"{alert['timestamp']} - Stage {alert['stage']}")

            with alert_col2:
                if st.button("View", key=f"alert_{alert['id']}"):
                    st.session_state['decision_queue_filter'] = alert['wafer_id']
                    st.switch_page("pages/2_📋_DECISION_QUEUE.py")

    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


def render_lot_card(lot):
    """Enhanced LOT card with real-time wafer processing status"""
    with st.expander(f"📦 {lot['lot_id']} - {lot['status']}", expanded=True):
        # Basic info
        info_col1, info_col2, info_col3 = st.columns(3)
        info_col1.write(f"**Chamber:** {lot['chamber']}")
        info_col2.write(f"**Recipe:** {lot['recipe']}")
        info_col3.write(f"**Total:** {lot['wafer_count']} wafers")

        # Progress bar
        stats = lot.get('stats', {})
        completed = stats.get('completed', 0)
        scrapped = stats.get('scrapped', 0)
        progress = (completed + scrapped) / lot['wafer_count']
        st.progress(progress)

        # Real-time stats
        st.write("**📊 Real-Time Status:**")
        stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)

        stat_col1.metric("⏳ Queued", stats.get('queued', 0))
        stat_col2.metric("⚙️ Processing", stats.get('processing', 0))
        stat_col3.metric("⏸️ Waiting", stats.get('waiting', 0))

        yield_info = lot.get('yield', {})
        yield_rate = yield_info.get('yield_rate', 0)
        stat_col4.metric("✅ Completed", completed, delta=f"{yield_rate:.1f}%")
        stat_col5.metric("❌ Scrapped", scrapped)

        # Current wafer being processed
        if lot['status'] == 'PROCESSING':
            processing_wafers = [w for w in lot['wafers'] if w['status'] == 'PROCESSING']
            waiting_wafers = [w for w in lot['wafers'] if w['status'] == 'WAITING_DECISION']

            if processing_wafers:
                w = processing_wafers[0]
                st.info(f"⚙️ Currently Processing: Wafer #{w['wafer_number']} at {w['current_stage']}")
            elif waiting_wafers:
                w = waiting_wafers[0]
                st.warning(f"⏸️ Waiting for Decision: Wafer #{w['wafer_number']} at {w['current_stage']}")

        # Wafer list with status icons
        st.write("**📋 Wafer Status List:**")
        with st.expander("View All Wafers", expanded=False):
            for wafer in lot['wafers']:
                status_icons = {
                    'QUEUED': '⏳',
                    'PROCESSING': '⚙️',
                    'WAITING_DECISION': '⏸️',
                    'COMPLETED': '✅',
                    'SCRAPPED': '❌'
                }
                icon = status_icons.get(wafer['status'], '❓')

                rework_badge = f" 🔄x{wafer['rework_count']}" if wafer.get('rework_count', 0) > 0 else ""
                stage_info = f" at {wafer['current_stage']}" if wafer['status'] not in ['COMPLETED', 'SCRAPPED'] else ""

                completion_info = ""
                if wafer['status'] == 'COMPLETED':
                    completion_info = f" (finished at {wafer.get('completion_stage', 'Stage 0')})"

                st.write(f"{icon} Wafer #{wafer['wafer_number']}: "
                        f"{wafer['status']}{stage_info}{completion_info}{rework_badge}")

        # Yield Summary (if LOT completed)
        if lot['status'] == 'COMPLETED':
            st.write("**🎯 Final Yield:**")
            yield_col1, yield_col2, yield_col3 = st.columns(3)

            yield_col1.metric("Stage 0 Complete", yield_info.get('completed_at_stage0', 0))
            yield_col2.metric("Stage 1 Complete", yield_info.get('completed_at_stage1', 0))
            yield_col3.metric("After Rework", yield_info.get('completed_after_rework', 0))


def create_wafer_heatmap(lot):
    """웨이퍼 상태 히트맵 (5x5 grid)"""
    # 25개 웨이퍼를 5x5 grid로 배치
    wafer_status = np.zeros((5, 5))
    wafer_ids = []

    for i, wafer in enumerate(lot['wafers']):
        row = i // 5
        col = i % 5

        # 상태에 따라 값 할당
        status_map = {
            'NORMAL': 1,
            'WARNING': 2,
            'ALERT': 3,
            'COMPLETED': 0
        }
        wafer_status[row, col] = status_map.get(wafer.get('status', 'NORMAL'), 1)
        wafer_ids.append(wafer['wafer_id'])

    wafer_ids_grid = np.array(wafer_ids).reshape(5, 5)

    fig = go.Figure(data=go.Heatmap(
        z=wafer_status,
        text=wafer_ids_grid,
        texttemplate="%{text}",
        textfont={"size": 10},
        colorscale=[
            [0, 'lightgray'],     # COMPLETED
            [0.33, 'lightgreen'], # NORMAL
            [0.67, 'yellow'],     # WARNING
            [1, 'red']            # ALERT
        ],
        showscale=False,
        hovertemplate='%{text}<br>Status: %{z}<extra></extra>'
    ))

    fig.update_layout(
        height=300,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        margin=dict(l=10, r=10, t=10, b=10)
    )

    return fig


def create_realtime_sensor_chart(sensor_data, sensors):
    """실시간 센서 라인 차트"""
    fig = go.Figure()

    for sensor in sensors:
        fig.add_trace(go.Scatter(
            x=sensor_data['timestamp'],
            y=sensor_data[sensor],
            mode='lines',
            name=sensor,
            line=dict(width=2)
        ))

    fig.update_layout(
        height=400,
        xaxis_title="Time",
        yaxis_title="Value",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )

    return fig


def start_new_lot():
    """새 LOT 시작 - 순차적 웨이퍼 처리 (새 구조)"""
    import random
    import sys
    from pathlib import Path

    # Import wafer processor
    utils_path = Path(__file__).parent.parent / 'utils'
    if str(utils_path) not in sys.path:
        sys.path.insert(0, str(utils_path))

    from wafer_processor import initialize_wafer, process_next_wafer_in_lot

    lot_id = f"LOT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Create LOT with new structure
    lot_data = {
        'lot_id': lot_id,
        'wafer_count': 25,
        'chamber': f"A-{random.randint(1, 5):02d}",
        'recipe': f"ETCH-V{random.randint(1, 3)}.{random.randint(0, 9)}",
        'status': 'PROCESSING',
        'current_wafer_number': 1,
        'started_at': datetime.now(),
        'wafers': [],

        # Real-time stats
        'stats': {
            'queued': 25,
            'processing': 0,
            'waiting': 0,
            'completed': 0,
            'scrapped': 0,
            'total_cost': 0.0
        },

        # Yield tracking
        'yield': {
            'total_wafers': 25,
            'completed_wafers': 0,
            'scrapped_wafers': 0,
            'yield_rate': 0.0,
            'completed_at_stage0': 0,
            'completed_at_stage1': 0,
            'completed_after_rework': 0,
            'stage0_cost': 0.0,
            'stage1_cost': 0.0,
            'rework_cost': 0.0,
            'sem_cost': 0.0
        }
    }

    # Initialize all 25 wafers in QUEUED state
    for i in range(25):
        wafer = initialize_wafer(lot_id, i + 1)
        lot_data['wafers'].append(wafer)

    # Session state에 LOT 추가
    if 'active_lots' not in st.session_state:
        st.session_state['active_lots'] = []
    st.session_state['active_lots'].append(lot_data)

    st.success(f"🚀 LOT Created: {lot_id}")
    st.info(f"📦 25 wafers queued for processing. Wafers will be processed one at a time through the pipeline.")

    # Start processing first wafer
    st.write("⚙️ Starting processing of Wafer #1...")

    # Process wafers automatically until first decision needed
    max_iterations = 50  # Safety limit
    for _ in range(max_iterations):
        result = process_next_wafer_in_lot(lot_id)

        if result == 'WAITING':
            st.info("⏸️ Wafer needs engineer decision. Check Decision Queue.")
            break
        elif result == 'COMPLETE':
            st.success("✅ All wafers processed!")
            break
        elif result == 'CONTINUE':
            # Keep processing next wafer
            continue
        elif result == 'ERROR':
            st.error("❌ Processing error")
            break


def generate_wafer_sequentially(lot_id, wafer_num, sensor_status_display):
    """
    웨이퍼 데이터를 실제 fab 공정 순서에 따라 순차적으로 생성
    실제 반도체 공정에서는 센서 데이터가 순차적으로 수집됨
    """
    wafer_id = f"{lot_id[-8:]}-W{wafer_num:02d}"

    # 1. Chamber 준비 단계 (1-2초)
    sensor_status_display.text(f"🔧 Chamber loading for {wafer_id}...")
    time.sleep(0.2)

    # 2. Etch Rate 측정 (첫 번째 센서, 가장 중요)
    sensor_status_display.text(f"📊 Measuring Etch Rate...")
    time.sleep(0.15)
    etch_rate = np.random.normal(3.5, 0.3)

    # 3. Pressure 측정 (두 번째 센서)
    sensor_status_display.text(f"📊 Measuring Pressure...")
    time.sleep(0.15)
    pressure = np.random.normal(150, 10)

    # 4. Temperature 측정 (세 번째 센서)
    sensor_status_display.text(f"📊 Measuring Temperature...")
    time.sleep(0.15)
    temperature = np.random.normal(65, 3)

    # 5. RF Power 측정 (네 번째 센서)
    sensor_status_display.text(f"📊 Measuring RF Power...")
    time.sleep(0.15)
    rf_power = np.random.normal(500, 30)

    # 6. Gas Flow 측정 (다섯 번째 센서)
    sensor_status_display.text(f"📊 Measuring Gas Flow...")
    time.sleep(0.15)
    gas_flow = np.random.normal(50, 5)

    # 7. 데이터 분석 단계
    sensor_status_display.text(f"🧠 Analyzing sensor data for {wafer_id}...")
    time.sleep(0.2)

    sensor_data = {
        'etch_rate': etch_rate,
        'pressure': pressure,
        'temperature': temperature,
        'rf_power': rf_power,
        'gas_flow': gas_flow,
    }

    # 이상 판단 (실제 fab의 anomaly detection 시뮬레이션)
    is_anomaly = (etch_rate > 3.8 or pressure > 160)
    anomaly_score = min(1.0, (abs(etch_rate - 3.5) / 0.5 + abs(pressure - 150) / 20) / 2)

    status = 'ALERT' if is_anomaly else 'NORMAL'
    risk_level = 'HIGH' if anomaly_score > 0.7 else 'MEDIUM' if anomaly_score > 0.4 else 'LOW'

    key_issue = []
    if etch_rate > 3.8:
        key_issue.append(f"High etch_rate: {etch_rate:.2f}")
    if pressure > 160:
        key_issue.append(f"High pressure: {pressure:.1f}")

    return {
        'wafer_id': wafer_id,
        'lot_id': lot_id,
        'status': status,
        'risk_level': risk_level,
        'anomaly_score': anomaly_score,
        'key_issue': ', '.join(key_issue) if key_issue else 'Normal',
        **sensor_data
    }


def generate_wafer_data(lot_id, wafer_num):
    """웨이퍼 데이터 생성 (레거시 - 빠른 생성용)"""
    wafer_id = f"{lot_id[-8:]}-W{wafer_num:02d}"

    # 센서 데이터
    etch_rate = np.random.normal(3.5, 0.3)
    pressure = np.random.normal(150, 10)
    temperature = np.random.normal(65, 3)

    sensor_data = {
        'etch_rate': etch_rate,
        'pressure': pressure,
        'temperature': temperature,
        'rf_power': np.random.normal(500, 30),
        'gas_flow': np.random.normal(50, 5),
    }

    # 이상 판단
    is_anomaly = (etch_rate > 3.8 or pressure > 160)
    anomaly_score = min(1.0, (abs(etch_rate - 3.5) / 0.5 + abs(pressure - 150) / 20) / 2)

    status = 'ALERT' if is_anomaly else 'NORMAL'
    risk_level = 'HIGH' if anomaly_score > 0.7 else 'MEDIUM' if anomaly_score > 0.4 else 'LOW'

    key_issue = []
    if etch_rate > 3.8:
        key_issue.append(f"High etch_rate: {etch_rate:.2f}")
    if pressure > 160:
        key_issue.append(f"High pressure: {pressure:.1f}")

    return {
        'wafer_id': wafer_id,
        'lot_id': lot_id,
        'status': status,
        'risk_level': risk_level,
        'anomaly_score': anomaly_score,
        'key_issue': ', '.join(key_issue) if key_issue else 'Normal',
        **sensor_data
    }


def add_pending_decisions(flagged_wafers, lot_id):
    """Decision queue에 추가"""
    if 'pending_decisions' not in st.session_state:
        st.session_state['pending_decisions'] = []

    added_count = 0

    for wafer in flagged_wafers:
        decision = {
            'id': f"{wafer['wafer_id']}-stage0",
            'wafer_id': wafer['wafer_id'],
            'lot_id': lot_id,
            'stage': 'Stage 0',
            'priority': f"🔴 HIGH" if wafer['risk_level'] == 'HIGH' else "🟡 MEDIUM",
            'ai_recommendation': 'INLINE',
            'ai_confidence': 0.87,
            'ai_reasoning': f"{wafer['key_issue']}로 인한 edge uniformity 이슈 예상",
            'economics': {
                'cost': 150,
                'loss': 12000,
                'benefit': 11850
            },
            'available_options': ['INLINE', 'SKIP', 'HOLD'],
            'time_elapsed': '< 1 min',
            'created_at': datetime.now(),
            'wafer_data': {
                'etch_rate': wafer.get('etch_rate'),
                'pressure': wafer.get('pressure'),
                'temperature': wafer.get('temperature'),
                'rf_power': wafer.get('rf_power'),
                'gas_flow': wafer.get('gas_flow')
            }
        }

        st.session_state['pending_decisions'].append(decision)
        added_count += 1
        print(f"[DEBUG] Decision added: {decision['id']}")

    print(f"[DEBUG] Total decisions added: {added_count}")
    print(f"[DEBUG] Total pending decisions: {len(st.session_state['pending_decisions'])}")


def add_alerts(flagged_wafers):
    """알림 추가"""
    if 'recent_alerts' not in st.session_state:
        st.session_state['recent_alerts'] = []

    for wafer in flagged_wafers:
        alert = {
            'id': f"{wafer['wafer_id']}-alert",
            'wafer_id': wafer['wafer_id'],
            'message': wafer['key_issue'],
            'severity': wafer['risk_level'],
            'stage': 'Stage 0',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        st.session_state['recent_alerts'].insert(0, alert)


def get_active_lots():
    """활성 LOT 목록"""
    if 'active_lots' not in st.session_state:
        st.session_state['active_lots'] = []
    return st.session_state['active_lots']


def get_pending_decision_count():
    """대기 중인 결정 개수"""
    if 'pending_decisions' not in st.session_state:
        return 0
    return len(st.session_state['pending_decisions'])


def get_alert_count():
    """알림 개수"""
    if 'recent_alerts' not in st.session_state:
        return 0
    return len(st.session_state['recent_alerts'])


def get_realtime_sensor_data(sensors):
    """실시간 센서 데이터"""
    timestamps = [datetime.now() - timedelta(seconds=i) for i in range(60, 0, -1)]

    data = {'timestamp': timestamps}

    base_values = {
        'etch_rate': 3.5,
        'pressure': 150,
        'temperature': 65,
        'rf_power': 500,
        'gas_flow': 50
    }

    for sensor in sensors:
        base = base_values.get(sensor, 100)
        noise = np.random.normal(0, base * 0.05, 60)
        data[sensor] = base + noise

    return pd.DataFrame(data)


def get_recent_alerts(limit=10):
    """최근 알림"""
    if 'recent_alerts' not in st.session_state:
        st.session_state['recent_alerts'] = []
    return st.session_state['recent_alerts'][:limit]


if __name__ == "__main__":
    main()
