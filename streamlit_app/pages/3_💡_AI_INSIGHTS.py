# streamlit_app/pages/3_🧠_ai_insights.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Insights", page_icon="🧠", layout="wide")

def main():
    st.title("🧠 AI Insights")

    tab1, tab2, tab3 = st.tabs([
        "🔍 Pattern Discovery",
        "🔬 Root Cause Analysis",
        "📚 Learning Insights"
    ])

    with tab1:
        page_pattern_discovery()

    with tab2:
        page_root_cause()

    with tab3:
        page_learning_insights()


def page_pattern_discovery():
    """Pattern Discovery 탭"""
    st.subheader("🔍 Discovered Patterns")

    if st.button("🔄 Run Pattern Discovery"):
        with st.spinner("Discovering patterns..."):
            # Mock patterns
            patterns = get_mock_patterns()

        st.session_state['discovered_patterns'] = patterns
        st.success(f"Found {len(patterns)} significant patterns!")

    if 'discovered_patterns' in st.session_state:
        patterns = st.session_state['discovered_patterns']

        for i, pattern in enumerate(patterns):
            with st.expander(f"Pattern {i+1}: {pattern['name']}", expanded=True):
                # Stats
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                stat_col1.metric("Correlation", f"{pattern['correlation']:.3f}")
                stat_col2.metric("p-value", f"{pattern['p_value']:.6f}")
                stat_col3.metric("Sample Size", pattern['n'])

                # Evidence
                st.write("**Evidence:**")
                st.write(pattern['evidence'])

                # LLM Interpretation (Korean)
                if pattern.get('llm_interpretation'):
                    st.write("**🧠 LLM 해석 (한국어):**")
                    st.info(pattern['llm_interpretation'])


def page_root_cause():
    """Root Cause Analysis 탭"""
    st.subheader("🔬 Root Cause Analysis")

    # Mock Stage 3 analyses
    analyses = get_mock_stage3_analyses()

    if not analyses:
        st.info("No SEM analyses available yet. Run wafers through Stage 3 first.")
        return

    for analysis in analyses:
        with st.expander(f"{analysis['wafer_id']} - {analysis['defect_type']}", expanded=False):
            # Basic info
            st.write(f"**Defect Type:** {analysis['defect_type']}")
            st.write(f"**Count:** {analysis['defect_count']}")
            st.write(f"**Confidence:** {analysis['confidence']:.2f}")

            # LLM Root Cause (Korean)
            st.markdown("### 🧠 근본 원인 분석")
            st.info(analysis['llm_root_cause'])

            # Actions
            st.markdown("### 💡 권장 조치")
            st.write("**Process Improvement:**")
            st.write(analysis['process_improvement_action'])

            st.write("**Recipe Adjustment:**")
            st.json(analysis['recipe_adjustment'])

            # Impact
            impact_col1, impact_col2, impact_col3 = st.columns(3)
            impact_col1.metric("Yield ↑", f"+{analysis['yield_improvement']*100:.1f}%p")
            impact_col2.metric("Cost Saving", f"${analysis['cost_saving']:,}/mo")
            impact_col3.metric("Payback", f"{analysis['payback']:.1f} months")


def page_learning_insights():
    """Learning Insights 탭"""
    st.subheader("📚 Learning from Engineer Feedback")

    # Check if we have decision log
    if 'decision_log' not in st.session_state or len(st.session_state['decision_log']) == 0:
        st.info("No engineer decisions logged yet. Make some decisions in the Decision Queue first!")
        return

    if st.button("🔄 Analyze Feedback"):
        with st.spinner("Analyzing..."):
            insights = analyze_decision_log()

        st.session_state['learning_insights'] = insights
        st.success("Analysis complete!")

    if 'learning_insights' in st.session_state:
        insights = st.session_state['learning_insights']

        # Agreement rate
        st.metric("AI-Engineer Agreement", f"{insights['agreement_rate']*100:.1f}%")

        # Patterns
        st.write("**Discovered Decision Patterns:**")

        for pattern in insights['patterns']:
            with st.expander(pattern['name'], expanded=True):
                st.write(pattern['description'])
                st.write("**Evidence:**", pattern['evidence'])

                # LLM Insight (Korean)
                if pattern.get('llm_insight'):
                    st.write("**🧠 LLM Insight (한국어):**")
                    st.info(pattern['llm_insight'])


def get_mock_patterns():
    """Mock pattern data"""
    return [
        {
            'name': 'etch_rate-Edge-Ring correlation',
            'correlation': 0.529,
            'p_value': 0.000001,
            'n': 1252,
            'evidence': 'Edge-Ring: 3.95 μm/min vs Others: 3.40 μm/min (+16%)',
            'llm_interpretation': '높은 etch rate가 가장자리 영역에서 과도한 식각을 유발하여 Edge-Ring 패턴을 형성합니다. Chamber uniformity 개선이 필요합니다.'
        },
        {
            'name': 'pressure-Edge-Ring correlation',
            'correlation': 0.635,
            'p_value': 0.000001,
            'n': 1252,
            'evidence': 'Edge-Ring: 161.21 mTorr vs Others: 149.95 mTorr (+7.5%)',
            'llm_interpretation': '높은 압력이 plasma density를 증가시켜 edge 영역의 반응성을 높입니다. 압력 제어가 핵심입니다.'
        }
    ]


def get_mock_stage3_analyses():
    """Mock Stage 3 analyses"""
    return [
        {
            'wafer_id': 'W0002',
            'defect_type': 'Pit',
            'defect_count': 18,
            'confidence': 0.91,
            'llm_root_cause': '''센서 데이터와 결함 패턴 분석:

1. 높은 etch rate (3.89 μm/min)와 압력(162 mTorr) 조합이 가장자리 과식각 유발
2. Chamber A-03의 uniformity 저하 징후 (최근 5 LOT 분석)
3. 유사 패턴이 Recipe ETCH-V2.1 사용 시 83% 확률로 발생

권장 조치:
- 단기: Chamber A-03 PM
- 중기: Etch rate 3.6으로 감소
- 장기: Edge uniformity 모니터링 강화''',
            'process_improvement_action': 'Chamber A-03 PM',
            'recipe_adjustment': {'etch_rate': '-5%', 'pressure': '-3%'},
            'yield_improvement': 0.06,
            'cost_saving': 50000,
            'payback': 1.2
        }
    ]


def analyze_decision_log():
    """Analyze decision log to find patterns"""
    decision_log = st.session_state.get('decision_log', [])

    if not decision_log:
        return {
            'agreement_rate': 0.0,
            'patterns': []
        }

    # Calculate agreement rate
    agreements = sum(1 for d in decision_log if d['agreement'])
    agreement_rate = agreements / len(decision_log) if len(decision_log) > 0 else 0

    # Find patterns
    patterns = []

    # Pattern 1: Cost sensitivity
    high_cost = [d for d in decision_log if d.get('economics', {}).get('cost', 0) > 500]
    low_cost = [d for d in decision_log if d.get('economics', {}).get('cost', 0) <= 500]

    if high_cost and low_cost:
        high_cost_approval = sum(1 for d in high_cost if d['agreement']) / len(high_cost)
        low_cost_approval = sum(1 for d in low_cost if d['agreement']) / len(low_cost)

        patterns.append({
            'name': 'Cost sensitivity',
            'description': f'High cost (>$500): {high_cost_approval*100:.0f}% approval vs Low cost: {low_cost_approval*100:.0f}%',
            'evidence': f'{abs(high_cost_approval - low_cost_approval)*100:.0f}% difference in approval rate',
            'llm_insight': '엔지니어들은 고비용 제안에 더 신중하게 접근하며, 명확한 경제적 근거를 요구합니다.'
        })

    # Pattern 2: Confidence threshold
    high_conf = [d for d in decision_log if d['ai_confidence'] > 0.8]
    low_conf = [d for d in decision_log if d['ai_confidence'] <= 0.8]

    if high_conf and low_conf:
        high_conf_approval = sum(1 for d in high_conf if d['agreement']) / len(high_conf)
        low_conf_approval = sum(1 for d in low_conf if d['agreement']) / len(low_conf)

        patterns.append({
            'name': 'Confidence threshold',
            'description': f'High confidence (>0.8): {high_conf_approval*100:.1f}% vs Low confidence: {low_conf_approval*100:.1f}%',
            'evidence': f'{abs(high_conf_approval - low_conf_approval)*100:.1f}% difference',
            'llm_insight': 'AI 신뢰도가 의사결정에 미치는 영향이 제한적입니다. 근거의 품질이 더 중요합니다.'
        })

    return {
        'agreement_rate': agreement_rate,
        'patterns': patterns
    }


if __name__ == "__main__":
    main()
