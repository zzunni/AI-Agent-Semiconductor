"""
Streamlit Dashboard for AI-Driven Semiconductor QC

Real-time LOT monitoring with Human-AI Collaboration
"""

import streamlit as st
import yaml
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import datetime

# Add parent directory to path for imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Load environment variables from .env file
load_dotenv(root_dir / '.env')

# Try to import src modules (optional - dashboard works without them)
try:
    from src.pipeline.controller import PipelineController
    from src.utils.data_loader import DataLoader
    from src.utils.metrics import MetricsCalculator
    SRC_AVAILABLE = True
except ImportError:
    SRC_AVAILABLE = False
    PipelineController = None
    DataLoader = None
    MetricsCalculator = None

# Page config
st.set_page_config(
    page_title="AI Semiconductor QC",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load config
@st.cache_resource
def load_config():
    config_path = root_dir / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Initialize components
@st.cache_resource
def init_pipeline():
    if SRC_AVAILABLE and PipelineController:
        return PipelineController()
    return None

@st.cache_resource
def init_data_loader():
    if SRC_AVAILABLE and DataLoader:
        return DataLoader()
    return None

# Try to initialize (optional - dashboard works without src modules)
try:
    pipeline = init_pipeline()
    data_loader = init_data_loader()
    metrics_calc = MetricsCalculator() if SRC_AVAILABLE and MetricsCalculator else None
    init_success = True
    init_error = None
except Exception as e:
    init_success = True  # Continue anyway - dashboard works independently
    init_error = None
    pipeline = None
    data_loader = None
    metrics_calc = None

# Custom CSS
st.markdown("""
    <style>
    /* Reduce overall font size */
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1 {
        font-size: 1.8rem !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    h2 {
        font-size: 1.3rem !important;
        font-weight: 500;
    }

    h3 {
        font-size: 1.1rem !important;
        font-weight: 500;
    }

    p, div, span {
        font-size: 0.9rem;
    }

    .stButton button {
        font-size: 0.9rem;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }

    .big-metric {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
    }

    .feature-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        cursor: pointer;
        transition: transform 0.2s;
    }

    .feature-card:hover {
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# Enhanced Sidebar
sys.path.insert(0, str(Path(__file__).parent / 'utils'))
from ui_components import render_enhanced_sidebar
render_enhanced_sidebar()

# Check initialization
if not init_success:
    st.error(f"❌ Failed to initialize system: {init_error}")
    st.stop()

# Main page
st.title("AI-DRIVEN SEMICONDUCTOR QUALITY CONTROL")
st.markdown("**Real-time LOT monitoring with Human-AI collaboration**")

# Quick Stats
st.markdown("---")
st.subheader("📊 System Status")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

# Get current stats
active_lots = st.session_state.get('active_lots', [])
pending_decisions = st.session_state.get('pending_decisions', [])
decision_log = st.session_state.get('decision_log', [])

with metric_col1:
    st.metric("🔄 Active LOTs", len(active_lots))

with metric_col2:
    total_wafers = sum(lot['wafer_count'] for lot in active_lots)
    st.metric("📦 Wafers In-Process", total_wafers)

with metric_col3:
    st.metric("⚠️ Pending Decisions", len(pending_decisions))

with metric_col4:
    if decision_log:
        agreements = sum(1 for d in decision_log if d.get('agreement', False))
        agreement_rate = agreements / len(decision_log) * 100
        st.metric("🤝 AI-Engineer Agreement", f"{agreement_rate:.1f}%")
    else:
        st.metric("🤝 AI-Engineer Agreement", "N/A")

# Feature Cards
st.markdown("---")
st.subheader("🚀 Quick Access")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 PRODUCTION MONITOR")
    st.caption("Real-time LOT monitoring")
    st.write("• Start new LOT (25 wafers)")
    st.write("• Wafer status heatmap")
    st.write("• Sensor streams")
    st.write("• Real-time alerts")

    if st.button("📊  PRODUCTION MONITOR", key="btn_production", type="primary", use_container_width=True):
        st.switch_page("pages/1_📊_PRODUCTION_MONITOR.py")

    st.markdown("---")

    st.markdown("### 💡 AI INSIGHTS")
    st.caption("LLM analysis and learning")
    st.write("• Pattern discovery (Korean)")
    st.write("• Root cause analysis")
    st.write("• Learning from feedback")
    st.write("• Process recommendations")

    if st.button("💡  AI INSIGHTS", key="btn_insights", use_container_width=True):
        st.switch_page("pages/3_💡_AI_INSIGHTS.py")

with col2:
    st.markdown("### 📋 DECISION QUEUE")
    st.caption("Human-AI collaboration")
    st.write("• Review AI recommendations")
    st.write("• Approve/Reject/Modify")
    st.write("• Economic analysis")
    st.write("• Priority filtering")

    if st.button("📋  DECISION QUEUE", key="btn_decisions", use_container_width=True):
        st.switch_page("pages/2_📋_DECISION_QUEUE.py")

# Recent Activity
st.markdown("---")
st.subheader("📋 Recent Activity")

if decision_log:
    # Show last 5 decisions
    recent = decision_log[-5:]

    for decision in reversed(recent):
        action_icon = {
            'APPROVED': '✅',
            'REJECTED': '❌',
            'MODIFIED': '📝',
            'HOLD': '⏸️'
        }.get(decision['engineer_action'], '❓')

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"{action_icon} **{decision['wafer_id']}** - {decision['stage']}")

        with col2:
            st.write(f"AI: {decision['ai_recommendation']}")

        with col3:
            agreement = "✅ Agreed" if decision['agreement'] else "❌ Disagreed"
            st.write(agreement)
else:
    st.info("No decisions logged yet. Start a LOT in Production Monitor!")

# System Info
st.markdown("---")
st.subheader("ℹ️ System Information")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    st.write("**Pipeline Status**")
    if pipeline:
        budget_status = pipeline.check_budget()
        st.write(f"• Inline Budget: ${budget_status['inline']['spent']:.0f} / ${budget_status['inline']['budget']:.0f}")
        st.write(f"• SEM Budget: ${budget_status['sem']['spent']:.0f} / ${budget_status['sem']['budget']:.0f}")
    else:
        st.write("• Inline Budget: $0 / $50,000")
        st.write("• SEM Budget: $0 / $30,000")

with info_col2:
    st.write("**Models**")
    st.write("• Stage 0: Isolation Forest")
    st.write("• Stage 1: XGBoost")
    st.write("• Stage 2B: CNN")
    st.write("• Stage 3: ResNet + LLM")

with info_col3:
    st.write("**LLM Integration**")
    st.write("• Model: Claude Sonnet 4.5")
    st.write("• Language: Korean")
    st.write("• Functions: Root cause, Patterns")

# Footer
st.markdown("---")
st.caption("🔬 AI-Driven Semiconductor QC | Powered by Anthropic Claude | Multi-Stage Pipeline v2.0")
