# streamlit_app/pages/2_⚠️_decision_queue.py

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add utils to path
utils_path = Path(__file__).parent.parent / 'utils'
if str(utils_path) not in sys.path:
    sys.path.insert(0, str(utils_path))

from stage_executors import (
    execute_stage0_to_stage1,
    execute_stage1_to_stage2a,
    execute_stage2a_to_stage2b,
    execute_stage2b_to_stage3,
    add_pipeline_alert
)

from ui_components import (
    render_enhanced_sidebar,
    render_why_recommendation,
    render_wafermap_visualization,
    render_sem_image,
    render_cost_breakdown
)

from learning_system import (
    save_engineer_feedback,
    get_ai_performance_summary
)

from wafer_processor import (
    process_wafer_stage,
    complete_wafer,
    get_stage_options,
    process_next_wafer_in_lot,
    add_to_decision_queue
)

import time

st.set_page_config(page_title="Decision Queue", page_icon="⚠️", layout="wide")

def main():
    # Enhanced Sidebar
    render_enhanced_sidebar()

    st.title("DECISION QUEUE")
    st.caption("AI recommendations awaiting engineer approval")

    # ==========================================
    # 간소화된 필터
    # ==========================================
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])

    with filter_col1:
        # Priority 필터
        priority_options = ["🔴 HIGH", "🟡 MEDIUM", "🟢 LOW"]

        # Session state 초기화
        if 'priority_filter' not in st.session_state:
            st.session_state['priority_filter'] = ["🔴 HIGH", "🟡 MEDIUM"]

        priority_filter = st.multiselect(
            "Priority:",
            priority_options,
            default=st.session_state['priority_filter'],
            key='priority_select'
        )
        st.session_state['priority_filter'] = priority_filter

    with filter_col2:
        # Stage 필터
        stage_options = ["Stage 0", "Stage 1", "Stage 2A", "Stage 2B", "Stage 3"]

        # Session state 초기화
        if 'stage_filter' not in st.session_state:
            st.session_state['stage_filter'] = stage_options  # 전체 선택

        stage_filter = st.multiselect(
            "Stage:",
            stage_options,
            default=st.session_state['stage_filter'],
            key='stage_select'
        )
        st.session_state['stage_filter'] = stage_filter

    with filter_col3:
        # Reset 버튼
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state['priority_filter'] = ["🔴 HIGH", "🟡 MEDIUM"]
            st.session_state['stage_filter'] = stage_options
            st.rerun()

    # LOT 필터
    lots = get_lot_list()
    if lots:
        lot_filter = st.selectbox("LOT:", ["All"] + lots)
    else:
        lot_filter = "All"

    # ==========================================
    # Pending Decisions
    # ==========================================

    # DEBUG: Show all pending decisions by stage
    all_pending = st.session_state.get('pending_decisions', [])
    if all_pending:
        stage_breakdown = {}
        for d in all_pending:
            stage = d.get('stage', 'Unknown')
            stage_breakdown[stage] = stage_breakdown.get(stage, 0) + 1

        with st.expander("🔍 DEBUG: All Pending Decisions", expanded=False):
            st.write(f"**Total in session_state:** {len(all_pending)}")
            st.write("**By Stage:**")
            for stage, count in sorted(stage_breakdown.items()):
                st.write(f"  - {stage}: {count}")

    pending = get_pending_decisions(priority_filter, stage_filter, lot_filter)

    if not pending:
        st.info("✅ No pending decisions matching your filters!")
        st.write("**Tips:**")
        st.write("- Try resetting filters with the 🔄 Reset button")
        st.write("- Check if there are decisions in other stages")
        st.write("- Start a new LOT from Production Monitor")
        st.write("- **Check DEBUG section above for all pending decisions**")
        return

    # 개수 표시
    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("Pending Decisions", len(pending))
    metric_col2.metric("Filtered", f"{len(pending)} / {len(st.session_state.get('pending_decisions', []))}")

    st.markdown("---")

    # ==========================================
    # Decision Cards
    # ==========================================
    for decision in pending:
        render_decision_card(decision)

    # Hold Queue Section removed - Hold feature no longer needed


def render_decision_card(decision):
    """의사결정 카드"""
    with st.container():
        st.markdown("---")

        # Header
        severity_icon = decision['priority'].split()[0]

        # Check if wafer has been reworked
        wafer_id = decision['wafer_id']
        lot_id = decision['lot_id']
        rework_badge = ""

        # Find wafer to check rework status
        for lot in st.session_state.get('active_lots', []):
            if lot['lot_id'] == lot_id:
                for wafer in lot['wafers']:
                    if wafer['wafer_id'] == wafer_id:
                        rework_count = wafer.get('rework_count', 0)
                        if rework_count > 0:
                            rework_badge = f" 🔄 **REWORK x{rework_count}**"
                        break
                break

        header_col1, header_col2, header_col3, header_col4 = st.columns([2, 1, 1, 1])

        header_col1.markdown(f"### {severity_icon} {decision['stage']}: {decision['wafer_id']}{rework_badge}")
        header_col2.write(f"**LOT:** {decision['lot_id']}")
        header_col3.write(f"**Time:** {decision['time_elapsed']}")
        header_col4.write(f"**Priority:** {decision['priority']}")

        # AI Recommendation
        st.info(f"🤖 **AI Recommendation:** `{decision['ai_recommendation']}`")

        ai_col1, ai_col2 = st.columns(2)
        confidence_val = decision.get('ai_confidence', 0.0)
        if confidence_val is None:
            confidence_val = 0.0
        ai_col1.metric("Confidence", f"{confidence_val:.2f}")
        ai_col2.metric("Model", "v1.0")

        # Details
        with st.expander("📊 Details & Analysis", expanded=False):
            # Create tabs for organized information
            tab1, tab2, tab3, tab4 = st.tabs(["📝 AI Analysis", "🤔 Why This?", "🗺️ Visualization", "💰 Economics"])

            with tab1:
                st.write("**AI Reasoning:**")
                st.markdown(f"> {decision['ai_reasoning']}")

                # LLM Analysis (if exists)
                if 'llm_analysis' in decision and decision['llm_analysis']:
                    st.markdown("---")
                    st.write("**🧠 LLM Analysis (Korean):**")
                    st.info(decision['llm_analysis'])

                # Additional details based on stage
                if 'yield_pred' in decision and decision['yield_pred'] is not None:
                    st.markdown("---")
                    st.metric("Predicted Yield", f"{decision['yield_pred']:.1%}")

                if 'key_features' in decision:
                    st.markdown("---")
                    st.write("**Key Features:**")
                    for feature in decision['key_features']:
                        st.markdown(f"• {feature}")

            with tab2:
                # Why This Recommendation
                render_why_recommendation(decision)

            with tab3:
                # Visualizations
                viz_col1, viz_col2 = st.columns(2)

                with viz_col1:
                    # Wafermap for all stages
                    render_wafermap_visualization(decision)

                with viz_col2:
                    # SEM image for Stage 2B and Stage 3
                    stage = decision.get('stage', '')
                    if stage in ['Stage 2B', 'Stage 3']:
                        render_sem_image(decision)
                    else:
                        st.info("📷 SEM imaging available in Stage 2B and Stage 3")

            with tab4:
                # Economics with visualization
                if 'economics' in decision:
                    render_cost_breakdown(decision['economics'], decision.get('id', 'default'))

                    st.markdown("---")
                    st.write("**💰 Economic Summary:**")
                    econ_col1, econ_col2, econ_col3 = st.columns(3)
                    econ_col1.metric("Cost", f"${decision['economics']['cost']:,}")

                    if 'loss' in decision['economics']:
                        econ_col2.metric("Expected Loss", f"${decision['economics']['loss']:,}")
                    if 'benefit' in decision['economics']:
                        econ_col3.metric("Net Benefit", f"${decision['economics']['benefit']:,}")
                else:
                    st.info("No economic data available for this decision")

        # Decision Buttons - Stage별로 직접 버튼 표시 (Selectbox 제거)
        st.write("**👨‍🔧 Your Decision:**")

        decision_id = decision['id']
        available_options = decision.get('available_options', [])
        stage = decision.get('stage', '')

        # Stage별 버튼 아이콘 매핑
        button_icons = {
            'INLINE': '🔍',
            'SKIP': '⏭️',
            'PROCEED': '⏩',
            'REWORK': '🔄',
            'SCRAP': '❌',
            'COMPLETE': '✅',
            'INVESTIGATE': '🔬'
        }

        # Stage별 버튼 설명
        button_tooltips = {
            'INLINE': 'Send to inline inspection (Stage 1)',
            'SKIP': 'False positive / Normal - Complete wafer',
            'PROCEED': 'Proceed to next stage for further analysis',
            'REWORK': 'Send to rework (generates new sensor data)',
            'SCRAP': 'Discard wafer',
            'COMPLETE': 'Analysis complete - Mark as done',
            'INVESTIGATE': 'Needs further investigation'
        }

        # 버튼을 가로로 배열
        num_options = len(available_options)
        cols = st.columns(num_options)

        for i, option in enumerate(available_options):
            with cols[i]:
                icon = button_icons.get(option, '▶️')
                tooltip = button_tooltips.get(option, option)
                button_type = "primary" if option == decision.get('ai_recommendation') else "secondary"

                if st.button(
                    f"{icon} {option}",
                    key=f"btn_{option}_{decision_id}",
                    type=button_type,
                    use_container_width=True,
                    help=tooltip
                ):
                    approve_decision(decision_id, option)
                    st.rerun()


# Removed: render_reject_interface, render_modify_interface, render_hold_interface
# Now using direct button approach


def get_pending_decisions(priority_filter, stage_filter, lot_filter):
    """대기 중인 결정 가져오기"""
    if 'pending_decisions' not in st.session_state:
        st.session_state['pending_decisions'] = []

    decisions = st.session_state['pending_decisions']

    # Apply filters
    filtered = decisions

    if priority_filter:
        filtered = [d for d in filtered if d['priority'] in priority_filter]

    if stage_filter:
        filtered = [d for d in filtered if d['stage'] in stage_filter]

    if lot_filter != "All":
        filtered = [d for d in filtered if d['lot_id'] == lot_filter]

    # Sort by Stage order (Stage 0 → Stage 1 → Stage 2A → Stage 2B → Stage 3)
    # Then by created_at timestamp (oldest first within same stage)
    stage_order = {
        'Stage 0': 0,
        'Stage 1': 1,
        'Stage 2A': 2,
        'Stage 2B': 3,
        'Stage 3': 4
    }

    # Sort by: 1) Stage order, 2) created_at (oldest first)
    filtered.sort(key=lambda x: (
        stage_order.get(x['stage'], 999),  # Stage order (공정 순서)
        x.get('created_at', datetime.now())  # created_at (오래된 것부터)
    ))

    return filtered


def approve_decision(decision_id, recommendation):
    """
    승인 및 다음 Stage 자동 실행 (NEW: Sequential processing)
    """
    import sys
    from pathlib import Path

    # Import wafer processor
    utils_path = Path(__file__).parent.parent / 'utils'
    if str(utils_path) not in sys.path:
        sys.path.insert(0, str(utils_path))

    from wafer_processor import process_next_wafer_in_lot, process_wafer_stage, complete_wafer, get_stage_options
    import time

    print(f"\n[DEBUG] ========== APPROVE DECISION (NEW) ==========")
    print(f"[DEBUG] Decision ID: {decision_id}")
    print(f"[DEBUG] Recommendation: {recommendation}")

    if 'pending_decisions' not in st.session_state:
        st.error("No pending decisions in session state")
        return

    # 1. Find decision
    decision = None
    decision_index = None

    for i, d in enumerate(st.session_state['pending_decisions']):
        if d['id'] == decision_id:
            decision = d
            decision_index = i
            break

    if not decision:
        st.error(f"Decision not found: {decision_id}")
        return

    wafer_id = decision['wafer_id']
    lot_id = decision['lot_id']
    stage = decision['stage']

    print(f"[DEBUG] Found decision: {stage}, wafer: {wafer_id}")

    # 2. Find LOT and wafer
    lot = None
    for l in st.session_state.get('active_lots', []):
        if l['lot_id'] == lot_id:
            lot = l
            break

    if not lot:
        st.error(f"LOT not found: {lot_id}")
        return

    wafer = None
    for w in lot['wafers']:
        if w['wafer_id'] == wafer_id:
            wafer = w
            break

    if not wafer:
        st.error(f"Wafer not found: {wafer_id}")
        return

    # 3. Save decision log
    log_decision(decision, 'APPROVED', recommendation)

    # 4. Remove from pending
    st.session_state['pending_decisions'].pop(decision_index)
    st.success(f"✅ {stage} approved with {recommendation}!")

    # 5. Initialize cost tracking
    if 'total_cost' not in wafer:
        wafer['total_cost'] = 0

    # 6. Route based on stage and decision
    try:
        if stage == 'Stage 0':
            if recommendation == 'INLINE':
                # Move to Stage 1 for inline inspection
                st.info("⏳ Moving to Stage 1 for inline inspection...")
                wafer['current_stage'] = 'Stage 1'

                # Add cost
                wafer['total_cost'] += 150
                lot['yield']['stage1_cost'] = lot['yield'].get('stage1_cost', 0) + 150

                add_pipeline_alert(wafer_id, 'Stage 1', 'Proceeding to inline inspection')

                # CRITICAL FIX: Immediately process THIS wafer at Stage 1
                wafer['status'] = 'PROCESSING'
                result = process_wafer_stage(wafer, 'Stage 1')

                if result['needs_decision']:
                    wafer['status'] = 'WAITING_DECISION'
                    add_to_decision_queue(wafer, result['decision_data'])
                else:
                    complete_wafer(wafer, lot)

            elif recommendation == 'SKIP':
                # False positive - complete wafer (no additional cost)
                st.info(f"⏭️ {wafer_id} SKIPPED - Marking as COMPLETED")
                complete_wafer(wafer, lot)
                add_pipeline_alert(wafer_id, 'Completed', 'False positive - completed at Stage 0')

        elif stage == 'Stage 1':
            if recommendation == 'SKIP':
                # False positive - complete wafer (no additional cost)
                st.info(f"⏭️ {wafer_id} SKIPPED - False positive, marking as COMPLETED")
                complete_wafer(wafer, lot)
                add_pipeline_alert(wafer_id, 'Completed', 'False positive - completed at Stage 1')

            elif recommendation == 'PROCEED':
                # Move to Stage 2A for post-fab analysis
                st.info(f"⏩ {wafer_id} → Stage 2A for WAT analysis")
                wafer['current_stage'] = 'Stage 2A'

                # Add cost for post-fab analysis
                wafer['total_cost'] += 100
                lot['yield']['stage2_cost'] = lot['yield'].get('stage2_cost', 0) + 100

                add_pipeline_alert(wafer_id, 'Stage 2A', 'Proceeding to post-fab WAT analysis')

                # CRITICAL FIX: Immediately process THIS wafer at Stage 2A
                wafer['status'] = 'PROCESSING'
                result = process_wafer_stage(wafer, 'Stage 2A')

                if result['needs_decision']:
                    wafer['status'] = 'WAITING_DECISION'
                    add_to_decision_queue(wafer, result['decision_data'])
                else:
                    complete_wafer(wafer, lot)

            elif recommendation == 'REWORK':
                # Stay at Stage 1 but mark as rework
                st.warning(f"🔄 {wafer_id} sent to REWORK")
                wafer['rework_count'] = wafer.get('rework_count', 0) + 1

                if 'rework_history' not in wafer:
                    wafer['rework_history'] = []

                wafer['rework_history'].append({
                    'stage': 'Stage 1',
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'Engineer decision: REWORK'
                })

                # Add rework cost
                wafer['total_cost'] += 200
                lot['yield']['rework_cost'] = lot['yield'].get('rework_cost', 0) + 200
                add_pipeline_alert(wafer_id, 'Rework', f'Rework attempt #{wafer["rework_count"]}')

                # Re-process Stage 1 with NEW sensor data
                st.info("⚙️ Re-processing with new sensor data...")
                time.sleep(1)  # Simulate rework delay

                wafer['status'] = 'PROCESSING'
                result = process_wafer_stage(wafer, 'Stage 1', is_rework=True)

                if result['needs_decision']:
                    # Still needs decision after rework
                    wafer['status'] = 'WAITING_DECISION'
                    add_to_decision_queue(wafer, result['decision_data'])
                    st.warning("⚠️ Rework complete, but still shows defects. Please review again.")
                else:
                    # Rework successful!
                    st.success("✅ Rework successful! Wafer improved.")
                    complete_wafer(wafer, lot)

            elif recommendation == 'SCRAP':
                st.error(f"❌ {wafer_id} SCRAPPED")
                wafer['status'] = 'SCRAPPED'
                wafer['final_status'] = 'SCRAPPED'
                wafer['completed_at'] = datetime.now().isoformat()
                lot['stats']['scrapped'] += 1
                lot['stats']['queued'] = sum(1 for w in lot['wafers'] if w['status'] == 'QUEUED')
                lot['stats']['waiting'] = sum(1 for w in lot['wafers'] if w['status'] == 'WAITING_DECISION')
                add_pipeline_alert(wafer_id, 'Scrapped', 'Wafer scrapped')

        elif stage == 'Stage 2A':
            # Post-fab WAT analysis
            if recommendation == 'SKIP':
                # No further analysis needed - complete
                st.info(f"⏭️ {wafer_id} SKIPPED - Post-fab analysis not needed, COMPLETED")
                complete_wafer(wafer, lot)
                add_pipeline_alert(wafer_id, 'Completed', 'WAT analysis skipped - completed')

            elif recommendation == 'PROCEED':
                # Move to Stage 2B for wafermap pattern analysis
                st.info(f"⏩ {wafer_id} → Stage 2B for pattern analysis")
                wafer['current_stage'] = 'Stage 2B'

                # Add cost for wafermap pattern analysis
                wafer['total_cost'] += 80
                lot['yield']['pattern_cost'] = lot['yield'].get('pattern_cost', 0) + 80

                add_pipeline_alert(wafer_id, 'Stage 2B', 'Proceeding to wafermap pattern analysis')

                # CRITICAL FIX: Immediately process THIS wafer at Stage 2B
                wafer['status'] = 'PROCESSING'
                result = process_wafer_stage(wafer, 'Stage 2B')

                if result['needs_decision']:
                    wafer['status'] = 'WAITING_DECISION'
                    add_to_decision_queue(wafer, result['decision_data'])
                else:
                    complete_wafer(wafer, lot)

        elif stage == 'Stage 2B':
            # Wafermap pattern analysis
            if recommendation == 'SKIP':
                # Pattern analysis not needed - complete
                st.info(f"⏭️ {wafer_id} SKIPPED - Pattern analysis not needed, COMPLETED")
                complete_wafer(wafer, lot)
                add_pipeline_alert(wafer_id, 'Completed', 'Pattern analysis skipped - completed')

            elif recommendation == 'PROCEED':
                # Move to Stage 3 for root cause analysis
                st.info(f"⏩ {wafer_id} → Stage 3 for SEM/root cause analysis")
                wafer['current_stage'] = 'Stage 3'

                # Add cost for SEM analysis
                wafer['total_cost'] += 300
                lot['yield']['sem_cost'] = lot['yield'].get('sem_cost', 0) + 300

                add_pipeline_alert(wafer_id, 'Stage 3', 'Proceeding to root cause analysis')

                # CRITICAL FIX: Immediately process THIS wafer at Stage 3
                wafer['status'] = 'PROCESSING'
                result = process_wafer_stage(wafer, 'Stage 3')

                if result['needs_decision']:
                    wafer['status'] = 'WAITING_DECISION'
                    add_to_decision_queue(wafer, result['decision_data'])
                else:
                    complete_wafer(wafer, lot)

        elif stage == 'Stage 3':
            # Root cause analysis with SEM (DESTRUCTIVE TESTING)
            # SEM destroys the wafer during measurement → must SCRAP
            if recommendation == 'COMPLETE':
                # Analysis complete - but wafer is SCRAPPED (SEM is destructive)
                st.info(f"✅ {wafer_id} Root cause analysis COMPLETE (SEM measurement - wafer scrapped)")
                wafer['status'] = 'SCRAPPED'
                wafer['final_status'] = 'SCRAPPED'
                wafer['completion_stage'] = 'Stage 3'
                wafer['scrap_reason'] = 'SEM measurement (destructive testing)'
                wafer['completed_at'] = datetime.now().isoformat()
                lot['stats']['scrapped'] += 1
                lot['stats']['queued'] = sum(1 for w in lot['wafers'] if w['status'] == 'QUEUED')
                lot['stats']['waiting'] = sum(1 for w in lot['wafers'] if w['status'] == 'WAITING_DECISION')
                add_pipeline_alert(wafer_id, 'Scrapped', 'SEM measurement complete (destructive)')

            elif recommendation == 'INVESTIGATE':
                # Need more investigation - but wafer is still SCRAPPED (SEM already done)
                st.warning(f"🔍 {wafer_id} Needs further investigation (wafer already scrapped by SEM)")
                wafer['status'] = 'SCRAPPED'
                wafer['final_status'] = 'SCRAPPED'
                wafer['completion_stage'] = 'Stage 3'
                wafer['scrap_reason'] = 'SEM measurement (destructive testing) - needs further investigation'
                wafer['completed_at'] = datetime.now().isoformat()
                lot['stats']['scrapped'] += 1
                lot['stats']['queued'] = sum(1 for w in lot['wafers'] if w['status'] == 'QUEUED')
                lot['stats']['waiting'] = sum(1 for w in lot['wafers'] if w['status'] == 'WAITING_DECISION')
                add_pipeline_alert(wafer_id, 'Scrapped', 'SEM measurement - further investigation needed')

        # Unknown stage
        else:
            st.warning(f"⚠️ Unknown stage: {stage}, marking as COMPLETED")
            complete_wafer(wafer, lot)
            add_pipeline_alert(wafer_id, 'Completed', f'Unknown stage {stage} - completed')

    except Exception as e:
        st.error(f"❌ Error in stage routing: {e}")
        import traceback
        st.code(traceback.format_exc())
        print(f"[ERROR] Exception in approve_decision: {e}")
        traceback.print_exc()
        return

    # 6. Continue processing next wafer
    st.write("⚙️ Processing next wafer...")

    # Process wafers automatically until next decision needed
    max_iterations = 10
    for _ in range(max_iterations):
        result = process_next_wafer_in_lot(lot_id)

        if result == 'WAITING':
            st.info("⏸️ Next wafer needs engineer decision")
            break
        elif result == 'COMPLETE':
            st.success(f"🎉 LOT {lot_id} processing complete!")
            st.balloons()
            break
        elif result == 'CONTINUE':
            # Keep processing
            continue
        elif result == 'ERROR':
            st.error("❌ Processing error")
            break


# Removed: reject_decision_with_reason, modify_and_execute_with_reason, hold_decision_with_reason
# Now using direct button approach with simplified workflow


def log_decision(decision, action, final_rec, note=None):
    """
    결정 로그 저장 (Backward compatibility)
    Approve는 learning_system을 통해 저장, 나머지는 이미 처리됨
    """
    if action == 'APPROVED':
        # Approve는 이유가 필요없으므로 바로 저장
        save_engineer_feedback(
            decision=decision,
            action=action,
            engineer_decision=final_rec,
            reasoning=None,  # Approve는 이유 불필요
            note=note
        )

    # Legacy decision_log도 유지 (기존 코드 호환성)
    if 'decision_log' not in st.session_state:
        st.session_state['decision_log'] = []

    log_entry = {
        'decision_id': decision['id'],
        'wafer_id': decision['wafer_id'],
        'lot_id': decision['lot_id'],
        'stage': decision['stage'],
        'ai_recommendation': decision['ai_recommendation'],
        'ai_confidence': decision['ai_confidence'],
        'engineer_action': action,
        'final_recommendation': final_rec,
        'engineer_note': note,
        'timestamp': datetime.now(),
        'agreement': action == 'APPROVED' and final_rec == decision['ai_recommendation'],
        'economics': decision.get('economics', {})
    }

    st.session_state['decision_log'].append(log_entry)
    print(f"[DEBUG] Logged decision: {action} for {decision['wafer_id']}")


def get_lot_list():
    """LOT 목록"""
    if 'active_lots' in st.session_state:
        return [lot['lot_id'] for lot in st.session_state['active_lots']]
    return []


# Removed: All Hold Queue related functions (render_hold_queue_section, render_held_decision_card,
# resume_held_decision, remove_held_decision, update_held_decision)
# Hold feature completely removed as requested


if __name__ == "__main__":
    main()
