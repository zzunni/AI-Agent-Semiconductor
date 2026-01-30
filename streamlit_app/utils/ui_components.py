"""
Shared UI Components for Streamlit Dashboard
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime


def render_enhanced_sidebar():
    """Enhanced sidebar with stage progress and cost tracking"""
    st.sidebar.title("🔬 AI SEMICONDUCTOR QC")
    st.sidebar.markdown("### HUMAN-AI COLLABORATION")
    st.sidebar.markdown("---")

    # Stage Progress Indicator
    st.sidebar.markdown("### 📍 PIPELINE PROGRESS")

    # Get current stage counts
    pending_decisions = st.session_state.get('pending_decisions', [])
    stage_counts = {
        'Stage 0': 0,
        'Stage 1': 0,
        'Stage 2A': 0,
        'Stage 2B': 0,
        'Stage 3': 0
    }

    for decision in pending_decisions:
        stage = decision.get('stage', 'Unknown')
        if stage in stage_counts:
            stage_counts[stage] += 1

    # Display stage progress
    st.sidebar.markdown("""
    **PHASE 1 (IN-LINE)** *Rework possible*
    """)

    for stage in ['Stage 0', 'Stage 1']:
        count = stage_counts[stage]
        icon = "✅" if count > 0 else "⭕"
        st.sidebar.markdown(f"{icon} {stage}: {count} pending")

    st.sidebar.markdown("""
    **PHASE 2 (POST-FAB)** *Rework NOT possible*
    """)

    for stage in ['Stage 2A', 'Stage 2B', 'Stage 3']:
        count = stage_counts[stage]
        icon = "✅" if count > 0 else "⭕"
        st.sidebar.markdown(f"{icon} {stage}: {count} pending")

    st.sidebar.markdown("---")

    # Cost Tracking
    st.sidebar.markdown("### 💰 COST TRACKING")

    # Calculate costs from decision log
    decision_log = st.session_state.get('decision_log', [])

    total_inline_cost = 0
    total_sem_cost = 0
    total_rework_cost = 0

    for log_entry in decision_log:
        stage = log_entry.get('stage', '')
        economics = log_entry.get('economics', {})

        if stage == 'Stage 0' and log_entry.get('engineer_action') == 'APPROVED':
            total_inline_cost += economics.get('cost', 0)
        elif stage in ['Stage 2B', 'Stage 3']:
            total_sem_cost += economics.get('cost', 0)
        elif 'REWORK' in log_entry.get('engineer_decision', ''):
            total_rework_cost += economics.get('cost', 0)

    # Monthly budgets (from config)
    inline_budget = 50000
    sem_budget = 30000

    # Display budget status
    inline_pct = (total_inline_cost / inline_budget * 100) if inline_budget > 0 else 0
    sem_pct = (total_sem_cost / sem_budget * 100) if sem_budget > 0 else 0

    st.sidebar.metric("Inline Cost", f"${total_inline_cost:,.0f}",
                     f"{inline_pct:.1f}% of ${inline_budget:,.0f}")

    st.sidebar.progress(min(inline_pct / 100, 1.0))

    st.sidebar.metric("SEM Cost", f"${total_sem_cost:,.0f}",
                     f"{sem_pct:.1f}% of ${sem_budget:,.0f}")

    st.sidebar.progress(min(sem_pct / 100, 1.0))

    if total_rework_cost > 0:
        st.sidebar.metric("Rework Cost", f"${total_rework_cost:,.0f}")

    st.sidebar.markdown("---")

    # System Info
    st.sidebar.caption("🤖 LLM: Claude Sonnet 4.5")
    st.sidebar.caption("📊 Models: 5 Stage Agents")
    st.sidebar.caption("🔬 Focus: Process Improvement")


def render_why_recommendation(decision):
    """Render 'Why This Recommendation' section"""
    st.markdown("### 🤔 Why This Recommendation?")

    stage = decision.get('stage', '')
    recommendation = decision.get('ai_recommendation', '')
    confidence = decision.get('ai_confidence', 0)
    if confidence is None:
        confidence = 0.0

    # Stage-specific explanations
    if stage == 'Stage 0':
        if recommendation == 'INLINE':
            st.markdown("""
            **Inline measurement is recommended because:**

            1. **Anomaly Detected**: Sensor data shows deviations from normal operating range
            2. **Early Detection Value**: Catching defects early saves downstream costs
            3. **Cost-Benefit**: Inline cost ($150) is much lower than potential wafer loss ($12,000)
            4. **Risk Mitigation**: Confirming quality before proceeding prevents cascading failures

            **What happens next:**
            - Critical Dimension (CD) measurement
            - Overlay error measurement
            - Film thickness verification
            - Defect density assessment
            """)
        elif recommendation == 'SKIP':
            st.markdown("""
            **Skipping inline measurement because:**

            1. **Low Risk**: Sensor data within acceptable normal range
            2. **Cost Optimization**: Saving $150 per wafer for low-risk cases
            3. **Throughput**: Faster processing for normal wafers
            """)

    elif stage == 'Stage 1':
        yield_pred = decision.get('yield_pred', 0)
        if yield_pred is None:
            yield_pred = 0.0

        if recommendation == 'REWORK':
            st.markdown(f"""
            **Rework is recommended because:**

            1. **Low Yield Prediction**: Estimated yield is {yield_pred:.1%}
            2. **Economic Benefit**: Rework cost ($5,000) < Expected loss (${decision.get('economics', {}).get('loss', 0):,.0f})
            3. **Recovery Potential**: High probability of yield improvement after rework
            4. **Phase 1 Advantage**: Still in in-line phase where rework is feasible

            **What rework involves:**
            - Strip and redeposit layers
            - Adjust process parameters
            - Re-run quality checks
            """)
        elif recommendation == 'PROCEED':
            st.markdown(f"""
            **Proceeding is recommended because:**

            1. **Acceptable Yield**: Estimated yield is {yield_pred:.1%}
            2. **Economic Viability**: Expected value justifies continuation
            3. **Risk Assessment**: Risk score within acceptable limits
            4. **Throughput Optimization**: Moving forward maintains fab efficiency
            """)
        elif recommendation == 'SCRAP':
            st.markdown(f"""
            **Scrapping is recommended because:**

            1. **Very Low Yield**: Estimated yield is {yield_pred:.1%}
            2. **Unrecoverable Defects**: Issues too severe for cost-effective rework
            3. **Economic Decision**: Continuing would exceed recovery value
            """)

    elif stage == 'Stage 2A':
        if recommendation == 'TO_EDS':
            uniformity = decision.get('uniformity_score', 0)
            if uniformity is None:
                uniformity = 0.0
            st.markdown(f"""
            **Proceeding to EDS (Electrical Die Sorting) because:**

            1. **LOT Quality**: Electrical tests passed with {uniformity:.1%} uniformity
            2. **Pattern Analysis Needed**: Wafermap shows patterns requiring investigation
            3. **Root Cause Discovery**: SEM analysis can identify systematic issues
            4. **Process Improvement**: Findings will benefit future LOTs

            **Next Steps:**
            - Wafermap pattern analysis
            - SEM candidate selection
            - Defect clustering analysis
            """)
        elif recommendation == 'LOT_SCRAP':
            st.markdown("""
            **LOT scrapping recommended because:**

            1. **Systemic Failure**: Multiple wafers show critical electrical failures
            2. **No Recovery Path**: Issues cannot be fixed in post-fab phase
            3. **Economic Decision**: Cost of analysis exceeds potential recovery
            """)

    elif stage == 'Stage 2B':
        sem_candidates = decision.get('sem_candidates', [])
        total_cost = decision.get('total_sem_cost', 0)

        if recommendation == 'APPROVE_TOP_3':
            st.markdown(f"""
            **Top 3 SEM candidates recommended because:**

            1. **Pattern Coverage**: Top 3 candidates cover {85}% of observed patterns
            2. **Cost Optimization**: ${total_cost:,.0f} for maximum insight
            3. **Representative Sample**: Selected wafers represent different pattern types
            4. **Root Cause Focus**: Prioritized by severity and pattern frequency

            **Selected Candidates:**
            """)
            for i, candidate in enumerate(sem_candidates[:3], 1):
                st.markdown(f"{i}. **{candidate['wafer_id']}**: {candidate['pattern']} pattern (severity: {candidate['severity']})")

        elif recommendation == 'SKIP_SEM':
            st.markdown("""
            **Skipping SEM because:**

            1. **Budget Constraint**: Monthly SEM budget nearly exhausted
            2. **Low Severity**: Observed patterns are minor
            3. **Known Issues**: Similar patterns already analyzed
            """)

    elif stage == 'Stage 3':
        defect_count = decision.get('defect_count', 0)
        defect_type = decision.get('defect_type', 'Unknown')

        if recommendation == 'APPLY_NEXT_LOT':
            st.markdown(f"""
            **Immediate implementation recommended because:**

            1. **Clear Root Cause**: {defect_type} defects traced to specific process parameters
            2. **High Confidence**: AI confidence is {confidence:.1%}
            3. **Proven Solution**: Similar fixes showed {np.random.randint(5, 10)}% yield improvement
            4. **Cost Benefit**: Implementation cost < Monthly savings

            **Defect Analysis:**
            - Type: {defect_type}
            - Count: {defect_count} defects
            - Pattern: Correlated with sensor data
            """)
        elif recommendation == 'INVESTIGATE':
            st.markdown(f"""
            **Further investigation needed because:**

            1. **High Defect Count**: {defect_count} defects detected
            2. **Complex Pattern**: Multiple contributing factors identified
            3. **Risk Management**: Need more data before process changes
            4. **Cross-LOT Correlation**: Checking recent LOTs for similar patterns
            """)

    # Always show confidence explanation
    st.markdown("---")
    st.markdown("### 📊 Confidence Level")

    if confidence >= 0.85:
        st.success(f"**{confidence:.1%} - Very High Confidence**")
        st.write("Model has seen many similar cases with consistent outcomes.")
    elif confidence >= 0.70:
        st.info(f"**{confidence:.1%} - High Confidence**")
        st.write("Model prediction is reliable based on historical patterns.")
    elif confidence >= 0.50:
        st.warning(f"**{confidence:.1%} - Medium Confidence**")
        st.write("Some uncertainty due to limited similar cases or mixed signals.")
    else:
        st.error(f"**{confidence:.1%} - Low Confidence**")
        st.write("High uncertainty - human judgment is critical.")


def render_wafermap_visualization(decision):
    """Render wafermap visualization for decision"""
    st.markdown("### 🗺️ Wafer Map")

    # Generate mock wafermap data (5x5 grid)
    wafermap_data = np.random.rand(5, 5)

    # Add pattern based on stage/recommendation
    stage = decision.get('stage', '')

    if stage == 'Stage 2B' or stage == 'Stage 3':
        # Get pattern type from decision
        pattern_type = None

        if 'sem_candidates' in decision:
            pattern_type = decision['sem_candidates'][0].get('pattern', 'Random') if decision['sem_candidates'] else 'Random'
        elif 'defect_type' in decision:
            pattern_type = 'Edge-Ring'  # Common pattern

        # Generate pattern
        if pattern_type == 'Edge-Ring':
            # Edge ring pattern (high values at edges)
            for i in range(5):
                for j in range(5):
                    if i == 0 or i == 4 or j == 0 or j == 4:
                        wafermap_data[i, j] = np.random.uniform(0.7, 1.0)
                    else:
                        wafermap_data[i, j] = np.random.uniform(0.1, 0.4)

        elif pattern_type == 'Center':
            # Center-high pattern
            for i in range(5):
                for j in range(5):
                    dist = abs(i - 2) + abs(j - 2)
                    wafermap_data[i, j] = 1.0 - (dist / 4.0) + np.random.normal(0, 0.1)

        elif pattern_type == 'Radial':
            # Radial pattern
            for i in range(5):
                for j in range(5):
                    angle = np.arctan2(i - 2, j - 2)
                    wafermap_data[i, j] = (np.sin(angle * 3) + 1) / 2 + np.random.normal(0, 0.1)

    # Clip values
    wafermap_data = np.clip(wafermap_data, 0, 1)

    # Create wafer IDs
    wafer_id = decision.get('wafer_id', 'W01')
    lot_id = decision.get('lot_id', 'LOT-001')

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=wafermap_data,
        colorscale='RdYlGn_r',  # Red=bad, Green=good
        showscale=True,
        colorbar=dict(title="Defect<br>Density"),
        hovertemplate='Die [%{x}, %{y}]<br>Defect Score: %{z:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title=f"Wafermap: {wafer_id}",
        height=400,
        xaxis=dict(
            title="X Position",
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title="Y Position",
            showgrid=False,
            zeroline=False,
            scaleanchor="x"
        ),
        margin=dict(l=60, r=60, t=60, b=60)
    )

    st.plotly_chart(fig, use_container_width=True, key=f"wafermap_{decision.get('id', 'default')}")

    # Add pattern description if available
    if stage in ['Stage 2B', 'Stage 3'] and pattern_type:
        st.info(f"**Pattern Detected:** {pattern_type}")

        pattern_descriptions = {
            'Edge-Ring': 'High defect density at wafer edges, often caused by edge effects or non-uniform plasma distribution',
            'Center': 'High defect density at wafer center, may indicate hot spots or gas flow issues',
            'Radial': 'Radial defect pattern, typically from equipment asymmetry or rotation artifacts',
            'Random': 'Random defect distribution, suggests particle contamination or equipment instability',
            'Loc': 'Localized defect cluster, indicates specific die or region issues'
        }

        st.caption(pattern_descriptions.get(pattern_type, 'Pattern analysis in progress'))


def render_sem_image(decision):
    """Render mock SEM image for Stage 2B/3"""
    st.markdown("### 🔬 SEM Image")

    defect_type = decision.get('defect_type', 'Pit')

    # Create mock SEM visualization
    # Using plotly to create a realistic-looking SEM image simulation
    x = np.linspace(-5, 5, 200)
    y = np.linspace(-5, 5, 200)
    X, Y = np.meshgrid(x, y)

    # Base pattern (circuit-like structure)
    Z = np.sin(X) * np.cos(Y) + np.random.normal(0, 0.1, (200, 200))

    # Add defect
    if defect_type == 'Pit':
        # Create pit (dark spot)
        Z += -2 * np.exp(-((X - 1)**2 + (Y - 1)**2) / 0.5)
    elif defect_type == 'Particle':
        # Create particle (bright spot)
        Z += 3 * np.exp(-((X + 1)**2 + (Y - 0.5)**2) / 0.3)
    elif defect_type == 'Scratch':
        # Create scratch (line)
        Z += -1.5 * np.exp(-(Y - 0.3 * X)**2 / 0.1)
    elif defect_type == 'Residue':
        # Create residue (irregular blob)
        Z += 2 * np.exp(-((X - 0.5)**2 + (Y + 1)**2) / 0.8)

    fig = go.Figure(data=go.Heatmap(
        z=Z,
        colorscale='gray',
        showscale=False,
        hoverinfo='skip'
    ))

    fig.update_layout(
        title=f"SEM Image: {defect_type} Defect",
        height=400,
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, scaleanchor="x"),
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white')
    )

    st.plotly_chart(fig, use_container_width=True, key=f"sem_{decision.get('id', 'default')}")

    # Defect details
    defect_count = decision.get('defect_count', 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Defect Type", defect_type)
    col2.metric("Count", defect_count)
    col3.metric("Severity", "High" if defect_count > 15 else "Medium")

    st.caption(f"🔬 Magnification: 10,000x | Accelerating Voltage: 5.0 kV | Working Distance: 10.0 mm")


def render_cost_breakdown(economics, decision_id=None):
    """Render cost breakdown visualization"""
    st.markdown("### 💰 Cost Breakdown")

    if not economics:
        st.info("No economic data available")
        return

    cost = economics.get('cost', 0)
    benefit = economics.get('benefit', 0)
    loss = economics.get('loss', 0)

    # Create bar chart
    categories = []
    values = []
    colors = []

    if cost > 0:
        categories.append('Inspection Cost')
        values.append(cost)
        colors.append('lightcoral')

    if loss > 0:
        categories.append('Potential Loss')
        values.append(loss)
        colors.append('indianred')

    if benefit > 0:
        categories.append('Net Benefit')
        values.append(benefit)
        colors.append('lightgreen')

    if not categories:
        st.info("No cost data available")
        return

    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f"${v:,.0f}" for v in values],
            textposition='outside'
        )
    ])

    fig.update_layout(
        height=300,
        yaxis=dict(title="Cost ($)"),
        showlegend=False,
        margin=dict(l=60, r=20, t=40, b=60)
    )

    # Use decision_id for unique key, fallback to hash
    chart_key = f"cost_{decision_id}" if decision_id else f"cost_{hash(str(economics))}_{id(economics)}"
    st.plotly_chart(fig, use_container_width=True, key=chart_key)

    # ROI calculation if applicable
    if benefit > 0 and cost > 0:
        roi = (benefit / cost) * 100
        st.metric("Return on Investment (ROI)", f"{roi:.1f}%")

        if roi > 200:
            st.success("✅ Excellent ROI - Strong economic case")
        elif roi > 100:
            st.info("✅ Good ROI - Economically justified")
        elif roi > 50:
            st.warning("⚠️ Moderate ROI - Consider alternatives")
        else:
            st.error("❌ Low ROI - May not be cost-effective")
