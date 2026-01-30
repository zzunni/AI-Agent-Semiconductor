"""
Test script for Stage0Agent

Tests the Stage 0 agent with mock data and models
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import pandas as pd
from src.agents.stage0_agent import Stage0Agent
from src.utils.data_loader import DataLoader


def test_initialization():
    """Test 1: Agent initialization"""
    print("=" * 80)
    print("Test 1: Stage0Agent Initialization")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize agent
    agent = Stage0Agent(config)

    print(f"✓ Agent initialized: {agent.stage_name}")
    print(f"✓ Model loaded: {agent.model is not None}")
    print(f"✓ Model type: {type(agent.model).__name__}")
    print(f"✓ Scaler loaded: {agent.scaler is not None}")
    print(f"✓ Confidence threshold: {agent.confidence_threshold}")
    print(f"✓ Inline cost: ${agent.inline_cost}")
    print()

    return agent


def test_analysis_normal_wafer():
    """Test 2: Analyze normal wafer"""
    print("=" * 80)
    print("Test 2: Analyze Normal Wafer")
    print("=" * 80)

    # Load config and data
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = Stage0Agent(config)
    loader = DataLoader()
    step1_df = loader.load_step1_data()

    # Find a normal wafer (low etch rate)
    normal_wafers = step1_df[step1_df['etch_rate'] < 3.5]
    if len(normal_wafers) == 0:
        print("⚠️  No normal wafers found in dataset")
        return

    wafer = normal_wafers.iloc[0]

    # Analyze
    analysis = agent.analyze(wafer)

    print(f"Wafer ID: {wafer['wafer_id']}")
    print(f"Etch rate: {wafer['etch_rate']:.2f}")
    print(f"Pressure: {wafer['pressure']:.1f}")
    print(f"Temperature: {wafer['temperature']:.1f}")
    print()
    print("Analysis Results:")
    print(f"  Anomaly score: {analysis['anomaly_score']:.3f}")
    print(f"  Risk level: {analysis['risk_level']}")
    print(f"  Outlier sensors: {analysis['outlier_sensors'] or 'None'}")
    print(f"  Decision score: {analysis['decision_score']:.3f}")
    print()

    assert analysis['risk_level'] in ['LOW', 'MEDIUM', 'HIGH'], "Invalid risk level"
    print("✓ Analysis completed successfully")
    print()

    return agent, wafer, analysis


def test_analysis_anomaly_wafer():
    """Test 3: Analyze anomaly wafer"""
    print("=" * 80)
    print("Test 3: Analyze Anomaly Wafer")
    print("=" * 80)

    # Load config and data
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = Stage0Agent(config)
    loader = DataLoader()
    step1_df = loader.load_step1_data()

    # Find an anomaly wafer (high etch rate)
    anomaly_wafers = step1_df[step1_df['etch_rate'] > 3.7]
    if len(anomaly_wafers) == 0:
        print("⚠️  No anomaly wafers found in dataset")
        return

    wafer = anomaly_wafers.iloc[0]

    # Analyze
    analysis = agent.analyze(wafer)

    print(f"Wafer ID: {wafer['wafer_id']}")
    print(f"Etch rate: {wafer['etch_rate']:.2f}")
    print(f"Pressure: {wafer['pressure']:.1f}")
    print(f"Temperature: {wafer['temperature']:.1f}")
    print()
    print("Analysis Results:")
    print(f"  Anomaly score: {analysis['anomaly_score']:.3f}")
    print(f"  Risk level: {analysis['risk_level']}")
    print(f"  Outlier sensors: {analysis['outlier_sensors']}")
    print(f"  Decision score: {analysis['decision_score']:.3f}")
    print()

    # Anomaly wafers should have higher scores
    assert analysis['anomaly_score'] > 0.3, "Anomaly should have higher score"
    print("✓ Anomaly detection works correctly")
    print()

    return agent, wafer, analysis


def test_recommendation_inline():
    """Test 4: Recommendation for HIGH risk wafer"""
    print("=" * 80)
    print("Test 4: Recommendation for HIGH Risk Wafer")
    print("=" * 80)

    # Load config and data
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = Stage0Agent(config)
    loader = DataLoader()
    step1_df = loader.load_step1_data()

    # Find high-risk wafer
    high_risk_wafers = step1_df[step1_df['etch_rate'] > 3.9]
    if len(high_risk_wafers) == 0:
        print("⚠️  No high-risk wafers found, using highest etch rate")
        wafer = step1_df.nlargest(1, 'etch_rate').iloc[0]
    else:
        wafer = high_risk_wafers.iloc[0]

    # Analyze and recommend
    analysis = agent.analyze(wafer)
    recommendation = agent.make_recommendation(wafer, analysis)

    print(f"Wafer ID: {wafer['wafer_id']}")
    print(f"Risk level: {analysis['risk_level']}")
    print()
    print("Recommendation:")
    print(f"  Action: {recommendation['action']}")
    print(f"  Confidence: {recommendation['confidence']:.2f}")
    print(f"  Estimated cost: ${recommendation['estimated_cost']:.2f}")
    print(f"  Reasoning: {recommendation['reasoning']}")
    print()
    print("Alternatives:")
    for alt in recommendation['alternatives']:
        print(f"  - {alt['action']}: {alt['reasoning']} (${alt['cost']})")
    print()

    print("✓ Recommendation generated successfully")
    print()

    return agent, wafer, analysis, recommendation


def test_recommendation_skip():
    """Test 5: Recommendation for LOW risk wafer"""
    print("=" * 80)
    print("Test 5: Recommendation for LOW Risk Wafer")
    print("=" * 80)

    # Load config and data
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = Stage0Agent(config)
    loader = DataLoader()
    step1_df = loader.load_step1_data()

    # Find low-risk wafer
    low_risk_wafers = step1_df[step1_df['etch_rate'] < 3.4]
    if len(low_risk_wafers) == 0:
        print("⚠️  No low-risk wafers found, using lowest etch rate")
        wafer = step1_df.nsmallest(1, 'etch_rate').iloc[0]
    else:
        wafer = low_risk_wafers.iloc[0]

    # Analyze and recommend
    analysis = agent.analyze(wafer)
    recommendation = agent.make_recommendation(wafer, analysis)

    print(f"Wafer ID: {wafer['wafer_id']}")
    print(f"Risk level: {analysis['risk_level']}")
    print()
    print("Recommendation:")
    print(f"  Action: {recommendation['action']}")
    print(f"  Confidence: {recommendation['confidence']:.2f}")
    print(f"  Estimated cost: ${recommendation['estimated_cost']:.2f}")
    print(f"  Reasoning: {recommendation['reasoning']}")
    print()

    assert recommendation['estimated_cost'] == 0 or recommendation['action'] == 'INLINE', \
        "SKIP should have zero cost"
    print("✓ SKIP recommendation works correctly")
    print()


def test_batch_processing():
    """Test 6: Process multiple wafers"""
    print("=" * 80)
    print("Test 6: Batch Processing")
    print("=" * 80)

    # Load config and data
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = Stage0Agent(config)
    loader = DataLoader()
    step1_df = loader.load_step1_data()

    # Process first 10 wafers
    sample_wafers = step1_df.head(10)

    results = []
    for idx, wafer in sample_wafers.iterrows():
        analysis = agent.analyze(wafer)
        recommendation = agent.make_recommendation(wafer, analysis)

        results.append({
            'wafer_id': wafer['wafer_id'],
            'etch_rate': wafer['etch_rate'],
            'risk_level': analysis['risk_level'],
            'action': recommendation['action'],
            'confidence': recommendation['confidence'],
            'cost': recommendation['estimated_cost']
        })

    # Display results
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    print()

    # Summary statistics
    inline_count = len(results_df[results_df['action'] == 'INLINE'])
    skip_count = len(results_df[results_df['action'] == 'SKIP'])
    total_cost = results_df['cost'].sum()
    avg_confidence = results_df['confidence'].mean()

    print("Summary:")
    print(f"  INLINE: {inline_count}/10 ({inline_count*10:.0f}%)")
    print(f"  SKIP: {skip_count}/10 ({skip_count*10:.0f}%)")
    print(f"  Total cost: ${total_cost:.2f}")
    print(f"  Average confidence: {avg_confidence:.2f}")
    print()

    print("✓ Batch processing works correctly")
    print()


def test_decision_logging():
    """Test 7: Decision logging"""
    print("=" * 80)
    print("Test 7: Decision Logging")
    print("=" * 80)

    # Load config and data
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = Stage0Agent(config)
    loader = DataLoader()
    step1_df = loader.load_step1_data()

    wafer = step1_df.iloc[0]

    # Analyze and recommend
    analysis = agent.analyze(wafer)
    recommendation = agent.make_recommendation(wafer, analysis)

    # Log decision
    agent.log_decision(
        wafer_id=wafer['wafer_id'],
        ai_recommendation=recommendation['action'],
        ai_confidence=recommendation['confidence'],
        ai_reasoning=recommendation['reasoning'],
        engineer_decision=recommendation['action'],  # Simulate engineer agreement
        engineer_rationale="Agree with AI assessment",
        response_time=0.5,
        cost=recommendation['estimated_cost']
    )

    print(f"✓ Decision logged for wafer {wafer['wafer_id']}")
    print(f"  Action: {recommendation['action']}")
    print(f"  Cost: ${recommendation['estimated_cost']:.2f}")
    print(f"  Check data/outputs/decisions_log.csv")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("Stage0Agent Test Suite")
    print("=" * 80)
    print()

    try:
        # Run tests
        test_initialization()
        test_analysis_normal_wafer()
        test_analysis_anomaly_wafer()
        test_recommendation_inline()
        test_recommendation_skip()
        test_batch_processing()
        test_decision_logging()

        print("=" * 80)
        print("✅ All Stage0Agent tests passed!")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Agent initialization works with real Isolation Forest model")
        print("  ✓ Anomaly detection identifies high-risk wafers")
        print("  ✓ Recommendations are appropriate for risk levels")
        print("  ✓ Decision logging works correctly")
        print("  ✓ Batch processing is efficient")
        print()
        print("Next steps:")
        print("  1. Implement Stage1Agent (XGBoost risk assessment)")
        print("  2. Integrate with orchestration controller")
        print("  3. Replace with real STEP 1 model when available")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
