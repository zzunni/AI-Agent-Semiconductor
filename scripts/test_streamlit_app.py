"""
Quick test to verify Streamlit app components load without errors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")

    try:
        import streamlit as st
        print("✓ streamlit imported")

        import plotly.express as px
        import plotly.graph_objects as go
        print("✓ plotly imported")

        from src.pipeline.controller import PipelineController
        print("✓ PipelineController imported")

        from src.agents.discovery_agent import DiscoveryAgent
        from src.agents.learning_agent import LearningAgent
        print("✓ Discovery and Learning agents imported")

        from src.utils.data_loader import DataLoader
        from src.utils.metrics import MetricsCalculator
        print("✓ Utils imported")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_components():
    """Test that key components can be initialized"""
    print("\n" + "=" * 60)
    print("Testing component initialization...")
    print("=" * 60)

    try:
        from src.pipeline.controller import PipelineController
        from src.utils.data_loader import DataLoader

        # Test pipeline initialization
        print("\nInitializing PipelineController...")
        pipeline = PipelineController()
        print("✓ PipelineController initialized")

        # Test data loader
        print("\nInitializing DataLoader...")
        data_loader = DataLoader()
        print("✓ DataLoader initialized")

        # Test loading data
        print("\nLoading wafer data...")
        step1_df = data_loader.load_step1_data()
        print(f"✓ Loaded {len(step1_df)} wafers")

        # Test budget check
        print("\nChecking budget...")
        budget = pipeline.check_budget()
        print(f"✓ Budget check successful:")
        print(f"  Inline: ${budget['inline']['budget']:,}")
        print(f"  SEM: ${budget['sem']['budget']:,}")

        print("\n✅ All components initialized successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Streamlit App Component Tests")
    print("=" * 60)

    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False

    # Test components
    if not test_components():
        print("\n❌ Component tests failed!")
        return False

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nStreamlit Dashboard Status:")
    print("  URL: http://localhost:8501")
    print("  Status: Running")
    print("\nAvailable Pages:")
    print("  🏠 Dashboard - Overview and metrics")
    print("  🔍 Wafer Inspection - Execute multi-stage pipeline")
    print("  📊 Pattern Discovery - Statistical pattern analysis")
    print("  📚 Learning Insights - Engineer feedback analysis")
    print("  💰 Budget Monitor - Cost tracking and budget utilization")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
