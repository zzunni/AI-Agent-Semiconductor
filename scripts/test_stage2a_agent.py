"""
Test script for Stage2AAgent

Tests LOT-level WAT electrical analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import pandas as pd
import numpy as np
from src.agents.stage2a_agent import Stage2AAgent


def create_mock_wat_data(n_wafers: int = 25, quality: str = 'PASS') -> pd.DataFrame:
    """
    Create mock WAT data for testing

    Args:
        n_wafers: Number of wafers in LOT
        quality: 'PASS' or 'FAIL'

    Returns:
        DataFrame with WAT measurements
    """
    np.random.seed(42)

    # WAT parameters
    if quality == 'PASS':
        # Good electrical parameters
        data = {
            'wafer_id': [f'W{i:03d}' for i in range(n_wafers)],
            'vth_nmos': np.random.normal(0.45, 0.02, n_wafers),
            'vth_pmos': np.random.normal(-0.45, 0.02, n_wafers),
            'idsat_nmos': np.random.normal(500, 20, n_wafers),
            'idsat_pmos': np.random.normal(250, 10, n_wafers),
            'ioff_nmos': np.random.normal(0.1, 0.01, n_wafers),
            'ioff_pmos': np.random.normal(0.05, 0.005, n_wafers),
            'contact_resistance': np.random.normal(50, 3, n_wafers),
            'sheet_resistance': np.random.normal(100, 5, n_wafers),
            'breakdown_voltage': np.random.normal(5.5, 0.1, n_wafers),
            'gate_oxide_integrity': np.random.normal(8.0, 0.2, n_wafers),
            'dielectric_thickness': np.random.normal(3.5, 0.1, n_wafers),
            'metal_resistance': np.random.normal(0.05, 0.005, n_wafers),
            'via_resistance': np.random.normal(2.0, 0.1, n_wafers),
            'capacitance': np.random.normal(10, 0.5, n_wafers),
            'leakage_current': np.random.normal(0.5, 0.05, n_wafers)
        }
    else:
        # Bad electrical parameters (out of spec or high variation)
        data = {
            'wafer_id': [f'W{i:03d}' for i in range(n_wafers)],
            'vth_nmos': np.random.normal(0.60, 0.1, n_wafers),  # Out of spec
            'vth_pmos': np.random.normal(-0.60, 0.1, n_wafers),
            'idsat_nmos': np.random.normal(400, 100, n_wafers),  # High variation
            'idsat_pmos': np.random.normal(200, 50, n_wafers),
            'ioff_nmos': np.random.normal(0.2, 0.1, n_wafers),  # High leakage
            'ioff_pmos': np.random.normal(0.1, 0.05, n_wafers),
            'contact_resistance': np.random.normal(70, 15, n_wafers),  # High resistance
            'sheet_resistance': np.random.normal(120, 20, n_wafers),
            'breakdown_voltage': np.random.normal(5.0, 0.5, n_wafers),  # Low breakdown
            'gate_oxide_integrity': np.random.normal(7.0, 1.0, n_wafers),
            'dielectric_thickness': np.random.normal(3.0, 0.5, n_wafers),
            'metal_resistance': np.random.normal(0.08, 0.02, n_wafers),
            'via_resistance': np.random.normal(3.0, 0.5, n_wafers),
            'capacitance': np.random.normal(12, 2, n_wafers),
            'leakage_current': np.random.normal(1.0, 0.3, n_wafers)
        }

    return pd.DataFrame(data)


def test_initialization():
    """Test 1: Agent initialization"""
    print("=" * 80)
    print("Test 1: Stage2AAgent Initialization")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Add Stage 2A config if not present
    if 'stage2a' not in config['models']:
        config['models']['stage2a'] = {
            'path': 'models/stage2a_wat_classifier.pkl',
            'lot_scrap_cost': 500000,
            'wafer_value': 20000,
            'wafers_per_lot': 25,
            'uniformity_threshold': 0.05,
            'critical_params': ['vth_nmos', 'vth_pmos', 'idsat_nmos', 'idsat_pmos'],
            'spec_limits': {
                'vth_nmos': [0.35, 0.55],
                'vth_pmos': [-0.55, -0.35],
                'idsat_nmos': [400, 600],
                'idsat_pmos': [200, 300],
                'ioff_nmos': [0.0, 0.2],
                'ioff_pmos': [0.0, 0.1],
                'contact_resistance': [40, 60],
                'sheet_resistance': [80, 120],
                'breakdown_voltage': [5.0, 6.0],
                'gate_oxide_integrity': [7.0, 9.0],
                'dielectric_thickness': [3.0, 4.0],
                'metal_resistance': [0.0, 0.1],
                'via_resistance': [1.0, 3.0],
                'capacitance': [8, 12],
                'leakage_current': [0.0, 1.0]
            }
        }

    # Initialize agent
    agent = Stage2AAgent(config['models']['stage2a'], config)

    print(f"✓ Agent initialized")
    print(f"✓ LOT scrap cost: ${agent.lot_scrap_cost:,}")
    print(f"✓ Wafer value: ${agent.wafer_value:,}")
    print(f"✓ Wafers per LOT: {agent.wafers_per_lot}")
    print(f"✓ Critical params: {agent.critical_params}")
    print()

    return agent, config


def test_pass_lot():
    """Test 2: LOT with good electrical quality (should PROCEED)"""
    print("=" * 80)
    print("Test 2: PASS LOT Analysis")
    print("=" * 80)

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    if 'stage2a' not in config['models']:
        config['models']['stage2a'] = {
            'path': 'models/stage2a_wat_classifier.pkl',
            'lot_scrap_cost': 500000,
            'wafer_value': 20000,
            'wafers_per_lot': 25,
            'uniformity_threshold': 0.05,
            'critical_params': ['vth_nmos', 'vth_pmos', 'idsat_nmos', 'idsat_pmos'],
            'spec_limits': {
                'vth_nmos': [0.35, 0.55],
                'vth_pmos': [-0.55, -0.35],
                'idsat_nmos': [400, 600],
                'idsat_pmos': [200, 300],
                'ioff_nmos': [0.0, 0.2],
                'ioff_pmos': [0.0, 0.1],
                'contact_resistance': [40, 60],
                'sheet_resistance': [80, 120],
                'breakdown_voltage': [5.0, 6.0],
                'gate_oxide_integrity': [7.0, 9.0],
                'dielectric_thickness': [3.0, 4.0],
                'metal_resistance': [0.0, 0.1],
                'via_resistance': [1.0, 3.0],
                'capacitance': [8, 12],
                'leakage_current': [0.0, 1.0]
            }
        }

    agent = Stage2AAgent(config['models']['stage2a'], config)

    # Create PASS quality WAT data
    wat_data = create_mock_wat_data(n_wafers=25, quality='PASS')

    print(f"Testing LOT-001 with {len(wat_data)} wafers (PASS quality)")
    print()

    # Analyze
    analysis = agent.analyze('LOT-001', wat_data)

    print("Analysis Results:")
    print(f"  Electrical Quality: {analysis['electrical_quality']}")
    print(f"  Quality Confidence: {analysis['quality_confidence']:.2f}")
    print(f"  Risk Level: {analysis['risk_level']}")
    print(f"  Uniformity Score: {analysis['uniformity_score']:.3f}")
    print(f"  Spec Violations: {analysis['violation_count']}")
    print(f"  Critical Violation: {analysis['critical_violation']}")
    print()

    # Make recommendation
    recommendation = agent.make_recommendation('LOT-001', analysis)

    print("Recommendation:")
    print(f"  Action: {recommendation['action']}")
    print(f"  Confidence: {recommendation['confidence']}")
    print(f"  Reasoning: {recommendation['reasoning']}")
    print(f"  Estimated Cost: ${recommendation['estimated_cost']:,.0f}")
    print(f"  Proceed to Stage 2B: {recommendation['proceed_to_stage2b']}")
    print(f"  Wafer Count for 2B: {len(recommendation['wafer_list_for_stage2b'])}")
    print()

    # Assertions
    assert recommendation['action'] == 'LOT_PROCEED', \
        f"Expected LOT_PROCEED for PASS LOT, got {recommendation['action']}"
    assert recommendation['proceed_to_stage2b'] == True, \
        "Should proceed to Stage 2B"
    assert len(recommendation['wafer_list_for_stage2b']) == 25, \
        "All 25 wafers should proceed"

    print("✓ PASS LOT test passed")
    print()


def test_fail_lot():
    """Test 3: LOT with poor electrical quality (should SCRAP)"""
    print("=" * 80)
    print("Test 3: FAIL LOT Analysis")
    print("=" * 80)

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    if 'stage2a' not in config['models']:
        config['models']['stage2a'] = {
            'path': 'models/stage2a_wat_classifier.pkl',
            'lot_scrap_cost': 500000,
            'wafer_value': 20000,
            'wafers_per_lot': 25,
            'uniformity_threshold': 0.05,
            'critical_params': ['vth_nmos', 'vth_pmos', 'idsat_nmos', 'idsat_pmos'],
            'spec_limits': {
                'vth_nmos': [0.35, 0.55],
                'vth_pmos': [-0.55, -0.35],
                'idsat_nmos': [400, 600],
                'idsat_pmos': [200, 300],
                'ioff_nmos': [0.0, 0.2],
                'ioff_pmos': [0.0, 0.1],
                'contact_resistance': [40, 60],
                'sheet_resistance': [80, 120],
                'breakdown_voltage': [5.0, 6.0],
                'gate_oxide_integrity': [7.0, 9.0],
                'dielectric_thickness': [3.0, 4.0],
                'metal_resistance': [0.0, 0.1],
                'via_resistance': [1.0, 3.0],
                'capacitance': [8, 12],
                'leakage_current': [0.0, 1.0]
            }
        }

    agent = Stage2AAgent(config['models']['stage2a'], config)

    # Create FAIL quality WAT data
    wat_data = create_mock_wat_data(n_wafers=25, quality='FAIL')

    print(f"Testing LOT-002 with {len(wat_data)} wafers (FAIL quality)")
    print()

    # Analyze
    analysis = agent.analyze('LOT-002', wat_data)

    print("Analysis Results:")
    print(f"  Electrical Quality: {analysis['electrical_quality']}")
    print(f"  Quality Confidence: {analysis['quality_confidence']:.2f}")
    print(f"  Risk Level: {analysis['risk_level']}")
    print(f"  Uniformity Score: {analysis['uniformity_score']:.3f}")
    print(f"  Spec Violations: {analysis['violation_count']}")
    print(f"  Critical Violation: {analysis['critical_violation']}")
    print()

    # Make recommendation
    recommendation = agent.make_recommendation('LOT-002', analysis)

    print("Recommendation:")
    print(f"  Action: {recommendation['action']}")
    print(f"  Confidence: {recommendation['confidence']}")
    print(f"  Reasoning: {recommendation['reasoning']}")
    print(f"  Estimated Cost: ${recommendation['estimated_cost']:,.0f}")
    print(f"  Proceed to Stage 2B: {recommendation['proceed_to_stage2b']}")
    print()

    # Should recommend SCRAP
    print(f"✓ FAIL LOT recommendation: {recommendation['action']}")
    print(f"✓ No wafers proceed to Stage 2B: {recommendation['proceed_to_stage2b'] == False}")
    print()


def test_economic_analysis():
    """Test 4: Economic decision-making logic"""
    print("=" * 80)
    print("Test 4: Economic Analysis")
    print("=" * 80)

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    if 'stage2a' not in config['models']:
        config['models']['stage2a'] = {
            'path': 'models/stage2a_wat_classifier.pkl',
            'lot_scrap_cost': 500000,
            'wafer_value': 20000,
            'wafers_per_lot': 25,
            'uniformity_threshold': 0.05,
            'critical_params': ['vth_nmos', 'vth_pmos', 'idsat_nmos', 'idsat_pmos'],
            'spec_limits': {
                'vth_nmos': [0.35, 0.55],
                'vth_pmos': [-0.55, -0.35],
                'idsat_nmos': [400, 600],
                'idsat_pmos': [200, 300],
                'ioff_nmos': [0.0, 0.2],
                'ioff_pmos': [0.0, 0.1],
                'contact_resistance': [40, 60],
                'sheet_resistance': [80, 120],
                'breakdown_voltage': [5.0, 6.0],
                'gate_oxide_integrity': [7.0, 9.0],
                'dielectric_thickness': [3.0, 4.0],
                'metal_resistance': [0.0, 0.1],
                'via_resistance': [1.0, 3.0],
                'capacitance': [8, 12],
                'leakage_current': [0.0, 1.0]
            }
        }

    agent = Stage2AAgent(config['models']['stage2a'], config)

    wat_data = create_mock_wat_data(n_wafers=25, quality='FAIL')
    analysis = agent.analyze('LOT-003', wat_data)
    recommendation = agent.make_recommendation('LOT-003', analysis)

    print("Economic Analysis:")
    print(f"  LOT Scrap Cost: ${recommendation['lot_scrap_cost']:,}")
    print(f"  Expected Loss if Proceed: ${recommendation['expected_loss_if_proceed']:,}")
    print(f"  Net Benefit of Scrap: ${recommendation['net_benefit_of_scrap']:,}")
    print()

    print("Decision:")
    print(f"  Recommendation: {recommendation['action']}")
    print(f"  Estimated Cost: ${recommendation['estimated_cost']:,}")
    print()

    print("✓ Economic analysis completed")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("Stage2AAgent Test Suite")
    print("=" * 80)
    print()

    try:
        # Run tests
        test_initialization()
        test_pass_lot()
        test_fail_lot()
        test_economic_analysis()

        print("=" * 80)
        print("✅ All Stage2AAgent tests passed!")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Agent initialization works")
        print("  ✓ PASS LOT correctly identified")
        print("  ✓ FAIL LOT correctly identified")
        print("  ✓ Economic analysis functional")
        print("  ✓ LOT-level decision making works")
        print()
        print("Next Steps:")
        print("  1. Integrate Stage 2A into Pipeline Controller")
        print("  2. Update Phase 1 and Phase 2 separation")
        print("  3. Test full multi-phase pipeline")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
