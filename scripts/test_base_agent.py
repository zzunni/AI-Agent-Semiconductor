"""
Test script for BaseAgent class

Creates a mock subclass and verifies all functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import yaml
from typing import Dict, Any

from src.agents.base_agent import BaseAgent
from src.utils.logger import SystemLogger


class MockAgent(BaseAgent):
    """
    Mock agent for testing BaseAgent functionality
    """

    def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
        """
        Mock analysis: check if etch rate is high

        Args:
            wafer_data: Single wafer data

        Returns:
            Analysis results
        """
        etch_rate = wafer_data.get('etch_rate', 3.4)
        threshold = self.get_config_value('etch_rate_threshold', 3.7)

        is_anomaly = etch_rate > threshold
        anomaly_score = min((etch_rate - 3.2) / (4.2 - 3.2), 1.0)  # Normalize to 0-1

        return {
            'anomaly_score': anomaly_score,
            'is_anomaly': is_anomaly,
            'confidence': 0.85,
            'etch_rate': etch_rate,
            'threshold': threshold
        }

    def make_recommendation(
        self,
        wafer_data: pd.Series,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mock recommendation: recommend INLINE if anomaly detected

        Args:
            wafer_data: Single wafer data
            analysis_result: Output from analyze()

        Returns:
            Recommendation
        """
        if analysis_result['is_anomaly']:
            action = 'INLINE'
            cost = 150
            reasoning = f"High etch rate detected: {analysis_result['etch_rate']:.2f}"
        else:
            action = 'PASS'
            cost = 0
            reasoning = "Etch rate within normal range"

        return {
            'action': action,
            'confidence': analysis_result['confidence'],
            'estimated_cost': cost,
            'reasoning': reasoning
        }


def test_initialization():
    """Test 1: Agent initialization"""
    print("=" * 80)
    print("Test 1: Agent Initialization")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create mock agent with stage0 config
    stage0_config = config['models']['stage0']
    agent = MockAgent(
        stage_name="stage0",
        config=stage0_config
    )

    print(f"✓ Agent initialized: {agent.stage_name}")
    print(f"✓ Model loaded: {agent.model is not None}")
    print(f"✓ Logger initialized: {agent.logger is not None}")
    print(f"✓ Decision logger initialized: {agent.decision_logger is not None}")
    print()

    return agent


def test_analysis():
    """Test 2: Analysis method"""
    print("=" * 80)
    print("Test 2: Analysis Method")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create agent
    stage0_config = config['models']['stage0']
    agent = MockAgent(stage_name="stage0", config=stage0_config)

    # Create test wafer data
    normal_wafer = pd.Series({
        'wafer_id': 'W_TEST_001',
        'etch_rate': 3.4,  # Normal
        'pressure': 150,
        'temperature': 60
    })

    anomaly_wafer = pd.Series({
        'wafer_id': 'W_TEST_002',
        'etch_rate': 3.95,  # High - anomaly
        'pressure': 162,
        'temperature': 62
    })

    # Test normal wafer
    result_normal = agent.analyze(normal_wafer)
    print("Normal wafer analysis:")
    print(f"  Etch rate: {result_normal['etch_rate']:.2f}")
    print(f"  Is anomaly: {result_normal['is_anomaly']}")
    print(f"  Anomaly score: {result_normal['anomaly_score']:.2f}")
    print(f"  Confidence: {result_normal['confidence']:.2f}")
    print()

    # Test anomaly wafer
    result_anomaly = agent.analyze(anomaly_wafer)
    print("Anomaly wafer analysis:")
    print(f"  Etch rate: {result_anomaly['etch_rate']:.2f}")
    print(f"  Is anomaly: {result_anomaly['is_anomaly']}")
    print(f"  Anomaly score: {result_anomaly['anomaly_score']:.2f}")
    print(f"  Confidence: {result_anomaly['confidence']:.2f}")
    print()

    assert result_normal['is_anomaly'] == False, "Normal wafer should not be anomaly"
    assert result_anomaly['is_anomaly'] == True, "Anomaly wafer should be detected"
    print("✓ Analysis method works correctly")
    print()

    return agent, normal_wafer, anomaly_wafer


def test_recommendation():
    """Test 3: Recommendation method"""
    print("=" * 80)
    print("Test 3: Recommendation Method")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create agent
    stage0_config = config['models']['stage0']
    agent = MockAgent(stage_name="stage0", config=stage0_config)

    # Create test wafer
    anomaly_wafer = pd.Series({
        'wafer_id': 'W_TEST_003',
        'etch_rate': 3.95,
        'pressure': 162,
        'temperature': 62
    })

    # Analyze and recommend
    analysis = agent.analyze(anomaly_wafer)
    recommendation = agent.make_recommendation(anomaly_wafer, analysis)

    print("Recommendation for anomaly wafer:")
    print(f"  Action: {recommendation['action']}")
    print(f"  Confidence: {recommendation['confidence']:.2f}")
    print(f"  Estimated cost: ${recommendation['estimated_cost']:.2f}")
    print(f"  Reasoning: {recommendation['reasoning']}")
    print()

    assert recommendation['action'] == 'INLINE', "Should recommend INLINE for anomaly"
    assert recommendation['estimated_cost'] == 150, "INLINE cost should be $150"
    print("✓ Recommendation method works correctly")
    print()

    return agent, anomaly_wafer, analysis, recommendation


def test_logging():
    """Test 4: Decision logging"""
    print("=" * 80)
    print("Test 4: Decision Logging")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create agent
    stage0_config = config['models']['stage0']
    agent = MockAgent(stage_name="stage0", config=stage0_config)

    # Log a decision
    agent.log_decision(
        wafer_id="W_TEST_004",
        ai_recommendation="INLINE",
        ai_confidence=0.85,
        ai_reasoning="High etch rate detected: 3.95",
        engineer_decision="INLINE",
        engineer_rationale="Agree with AI assessment",
        response_time=1.5,
        cost=150
    )

    print("✓ Decision logged successfully")
    print("  Check logs/decisions.csv for the entry")
    print()


def test_config_access():
    """Test 5: Configuration access"""
    print("=" * 80)
    print("Test 5: Configuration Access")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create agent
    stage0_config = config['models']['stage0']
    agent = MockAgent(stage_name="stage0", config=stage0_config)

    # Test config value retrieval
    confidence_threshold = agent.get_config_value('confidence_threshold', 0.5)
    print(f"✓ Confidence threshold: {confidence_threshold}")

    # Test default value
    nonexistent = agent.get_config_value('nonexistent_key', 'default_value')
    print(f"✓ Default value works: {nonexistent}")
    print()


def test_model_loading():
    """Test 6: Model loading verification"""
    print("=" * 80)
    print("Test 6: Model Loading")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create agent with stage0 (Isolation Forest)
    stage0_config = config['models']['stage0']
    agent = MockAgent(stage_name="stage0", config=stage0_config)

    print(f"✓ Model type: {type(agent.model).__name__}")
    print(f"✓ Model loaded: {agent.model is not None}")

    # Verify model can be used
    if agent.model is not None:
        import numpy as np
        X_test = np.random.randn(5, 10)
        predictions = agent.model.predict(X_test)
        print(f"✓ Model predictions shape: {predictions.shape}")
        print(f"✓ Sample predictions: {predictions[:3]}")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("BaseAgent Test Suite")
    print("=" * 80)
    print()

    try:
        # Run tests
        test_initialization()
        test_analysis()
        test_recommendation()
        test_logging()
        test_config_access()
        test_model_loading()

        print("=" * 80)
        print("✅ All tests passed!")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Agent initialization works")
        print("  ✓ Abstract methods can be implemented")
        print("  ✓ Model loading works")
        print("  ✓ Decision logging works")
        print("  ✓ Configuration access works")
        print()
        print("Next steps:")
        print("  1. Implement Stage0Agent (Anomaly Detection)")
        print("  2. Implement Stage1Agent (Risk Assessment)")
        print("  3. Implement Stage2bAgent (Severity Analysis)")
        print("  4. Implement Stage3Agent (Detailed Classification)")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
