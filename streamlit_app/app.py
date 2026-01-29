"""
AI-Driven Semiconductor Quality Control System
Main Streamlit Application Entry Point
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def main():
    """Main application entry point"""

    # Page configuration
    st.set_page_config(
        page_title="AI Semiconductor QC",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["Home", "Upload Data", "Pattern Discovery", "Root Cause Analysis",
         "Defect Classification", "Predictive Maintenance", "Process Optimization",
         "Learning & Feedback", "Settings"]
    )

    # Main content
    if page == "Home":
        show_home_page()
    elif page == "Upload Data":
        st.title("Upload Data")
        st.info("Data upload functionality will be implemented here.")
    elif page == "Pattern Discovery":
        st.title("Pattern Discovery")
        st.info("Pattern discovery analysis will be implemented here.")
    elif page == "Root Cause Analysis":
        st.title("Root Cause Analysis")
        st.info("Root cause analysis will be implemented here.")
    elif page == "Defect Classification":
        st.title("Defect Classification")
        st.info("Defect classification will be implemented here.")
    elif page == "Predictive Maintenance":
        st.title("Predictive Maintenance")
        st.info("Predictive maintenance forecasting will be implemented here.")
    elif page == "Process Optimization":
        st.title("Process Optimization")
        st.info("Process optimization recommendations will be implemented here.")
    elif page == "Learning & Feedback":
        st.title("Learning & Feedback")
        st.info("Learning and feedback system will be implemented here.")
    elif page == "Settings":
        st.title("Settings")
        st.info("Application settings will be implemented here.")


def show_home_page():
    """Display the home page"""

    st.markdown('<div class="main-header">AI-Driven Semiconductor Quality Control System</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-stage decision support using 6 AI models for real-time wafer inspection optimization</div>',
                unsafe_allow_html=True)

    # Overview section
    st.header("Overview")
    st.write("""
    This system leverages advanced AI models to provide comprehensive quality control
    for semiconductor manufacturing. It analyzes wafer defects, identifies patterns,
    performs root cause analysis, and optimizes inspection processes in real-time.
    """)

    # Features grid
    st.header("Key Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🔍 Pattern Discovery")
        st.write("Identifies recurring defect patterns across wafer batches")

        st.subheader("🔧 Predictive Maintenance")
        st.write("Forecasts equipment issues before they occur")

    with col2:
        st.subheader("🧪 Root Cause Analysis")
        st.write("Analyzes defects to determine underlying causes")

        st.subheader("⚙️ Process Optimization")
        st.write("Recommends process improvements")

    with col3:
        st.subheader("🏷️ Defect Classification")
        st.write("Categorizes defects by type and severity")

        st.subheader("📚 Learning & Feedback")
        st.write("Continuously improves from inspection results")

    # Quick stats (placeholder)
    st.header("System Status")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Models Active", "6 / 6", "100%")
    with col2:
        st.metric("Wafers Analyzed", "0", "0")
    with col3:
        st.metric("Defects Detected", "0", "0")
    with col4:
        st.metric("Accuracy", "N/A", "0%")

    # Getting started
    st.header("Getting Started")
    st.info("""
    **To begin using the system:**
    1. Configure your API key in `.env` file
    2. Upload wafer inspection data using the "Upload Data" page
    3. Select an analysis type from the sidebar
    4. Review results and recommendations
    """)

    # Footer
    st.divider()
    st.caption("Powered by Anthropic Claude | Built with Streamlit")


if __name__ == "__main__":
    main()
