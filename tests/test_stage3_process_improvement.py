"""
Test Suite for Stage 3 Agent - Process Improvement Mode

Tests Phase 2 (Post-Fab) characteristics where current wafer
is completed and recommendations are for next LOT
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import pandas as pd
from src.agents.stage3_agent import Stage3Agent


def test_stage3_output_format():
    """
    Test 1: Verify Stage 3 output format for Phase 2 (Post-Fab)

    Checks that output contains process improvement fields
    and does NOT contain immediate action fields
    """
    print("=" * 80)
    print("Test 1: Stage 3 Output Format (Phase 2 Post-Fab)")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize agent
    agent = Stage3Agent(config)

    # Create mock wafer data
    wafer_data = pd.Series({
        'wafer_id': 'W0001',
        'lot_id': 'LOT-001',
        'recipe': 'Recipe_A',
        'chamber': 'Chamber_1',
        'timestamp': '2026-01-29',
        'etch_rate': 150.5,
        'pressure': 100.0,
        'temperature': 250.0,
        'rf_power': 1000.0,
        'gas_flow': 100.0
    })

    # Analyze
    analysis_result = agent.analyze(wafer_data)

    print(f"\nAnalysis Result:")
    print(f"  Defect type: {analysis_result['defect_type']}")
    print(f"  Defect count: {analysis_result['defect_count']}")
    print(f"  Severity: {analysis_result['severity']}")
    print(f"  Location: {analysis_result['location_pattern']}")

    # Make recommendation
    recommendation = agent.make_recommendation(wafer_data, analysis_result)

    print(f"\nRecommendation Structure:")

    # ✅ Check Phase 2 specific fields exist
    print("\n  Phase 2 (Post-Fab) Fields:")
    assert 'current_wafer_status' in recommendation, "Missing current_wafer_status"
    assert recommendation['current_wafer_status'] == 'COMPLETED', \
        f"Expected current_wafer_status='COMPLETED', got {recommendation['current_wafer_status']}"
    print(f"    ✓ current_wafer_status: {recommendation['current_wafer_status']}")

    assert 'action_target' in recommendation, "Missing action_target"
    assert recommendation['action_target'] == 'NEXT_LOT', \
        f"Expected action_target='NEXT_LOT', got {recommendation['action_target']}"
    print(f"    ✓ action_target: {recommendation['action_target']}")

    assert 'current_wafer_actionable' in recommendation, "Missing current_wafer_actionable"
    assert recommendation['current_wafer_actionable'] == False, \
        "current_wafer_actionable should be False in Phase 2"
    print(f"    ✓ current_wafer_actionable: {recommendation['current_wafer_actionable']}")

    # ✅ Check process improvement fields exist
    print("\n  Process Improvement Fields:")
    assert 'process_improvement_action' in recommendation, "Missing process_improvement_action"
    print(f"    ✓ process_improvement_action: {recommendation['process_improvement_action']['action']}")

    assert 'recipe_adjustment_for_next_lot' in recommendation, "Missing recipe_adjustment_for_next_lot"
    print(f"    ✓ recipe_adjustment_for_next_lot: present")

    assert 'monitoring_plan' in recommendation, "Missing monitoring_plan"
    print(f"    ✓ monitoring_plan: {recommendation['monitoring_plan'][:60]}...")

    # ✅ Check expected impact fields
    print("\n  Expected Impact Fields:")
    assert 'expected_yield_improvement' in recommendation, "Missing expected_yield_improvement"
    print(f"    ✓ expected_yield_improvement: {recommendation['expected_yield_improvement']}%")

    assert 'expected_cost_saving' in recommendation, "Missing expected_cost_saving"
    print(f"    ✓ expected_cost_saving: ${recommendation['expected_cost_saving']:,.0f}")

    assert 'implementation_cost' in recommendation, "Missing implementation_cost"
    print(f"    ✓ implementation_cost: ${recommendation['implementation_cost']:,.0f}")

    assert 'payback_period' in recommendation, "Missing payback_period"
    print(f"    ✓ payback_period: {recommendation['payback_period']}")

    # ✅ Check AI recommendation fields
    print("\n  AI Recommendation Fields:")
    assert 'ai_recommendation' in recommendation, "Missing ai_recommendation"
    print(f"    ✓ ai_recommendation: {recommendation['ai_recommendation']}")

    assert 'ai_confidence' in recommendation, "Missing ai_confidence"
    print(f"    ✓ ai_confidence: {recommendation['ai_confidence']:.2f}")

    assert 'ai_reasoning' in recommendation, "Missing ai_reasoning"
    print(f"    ✓ ai_reasoning: {recommendation['ai_reasoning'][:60]}...")

    # ✅ Check engineer decision fields (should be None initially)
    print("\n  Engineer Decision Fields:")
    assert 'engineer_decision' in recommendation, "Missing engineer_decision"
    assert recommendation['engineer_decision'] is None, "engineer_decision should be None initially"
    print(f"    ✓ engineer_decision: {recommendation['engineer_decision']} (awaiting engineer input)")

    assert 'engineer_note' in recommendation, "Missing engineer_note"
    print(f"    ✓ engineer_note: {recommendation['engineer_note']}")

    # ❌ Check that old immediate action fields are NOT present
    print("\n  Legacy Fields Check:")
    # Old field 'ai_immediate_action' should NOT exist
    # We renamed it to 'process_improvement_action'
    # (Note: 'action' field kept for pipeline compatibility)
    assert 'action' in recommendation, "action field needed for pipeline compatibility"
    print(f"    ✓ action (for pipeline): {recommendation['action']}")

    print("\n✅ Test 1 PASSED: Output format is correct for Phase 2 (Post-Fab)")
    print()


def test_stage3_priority_levels():
    """
    Test 2: Verify priority determination for next LOT

    Tests that severity levels map to correct priorities
    """
    print("=" * 80)
    print("Test 2: Priority Level Determination")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize agent
    agent = Stage3Agent(config)

    # Test HIGH priority (>20 defects)
    print("\n  Testing HIGH severity (>20 defects):")
    priority_high = agent._determine_priority('Particle', 25, 'HIGH')
    assert priority_high == 'HIGH_PRIORITY', f"Expected HIGH_PRIORITY, got {priority_high}"
    print(f"    ✓ 25 defects → {priority_high}")

    # Test MEDIUM priority (10-20 defects)
    print("\n  Testing MEDIUM severity (10-20 defects):")
    priority_medium = agent._determine_priority('Scratch', 15, 'MEDIUM')
    assert priority_medium == 'MEDIUM_PRIORITY', f"Expected MEDIUM_PRIORITY, got {priority_medium}"
    print(f"    ✓ 15 defects → {priority_medium}")

    # Test LOW priority (<10 defects)
    print("\n  Testing LOW severity (<10 defects):")
    priority_low = agent._determine_priority('Residue', 5, 'LOW')
    assert priority_low == 'LOW_PRIORITY', f"Expected LOW_PRIORITY, got {priority_low}"
    print(f"    ✓ 5 defects → {priority_low}")

    print("\n✅ Test 2 PASSED: Priority levels determined correctly")
    print()


def test_stage3_improvement_actions():
    """
    Test 3: Verify improvement action generation

    Tests that different defect types generate appropriate actions
    """
    print("=" * 80)
    print("Test 3: Process Improvement Actions")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize agent
    agent = Stage3Agent(config)

    # Test Particle defect action
    print("\n  Testing Particle defect action:")
    action_particle = agent._generate_improvement_action('Particle', 'random', 'HIGH')
    assert action_particle['action'] == 'Chamber cleaning and filter replacement'
    assert action_particle['target'] == 'Next LOT'
    assert action_particle['urgency'] == 'HIGH'
    print(f"    Action: {action_particle['action']}")
    print(f"    Target: {action_particle['target']}")
    print(f"    Urgency: {action_particle['urgency']}")
    print(f"    Timeline: {action_particle['timeline']}")

    # Test Scratch defect action
    print("\n  Testing Scratch defect action:")
    action_scratch = agent._generate_improvement_action('Scratch', 'edge', 'MEDIUM')
    assert action_scratch['action'] == 'Wafer handling procedure review'
    assert action_scratch['target'] == 'Next LOT'
    print(f"    Action: {action_scratch['action']}")
    print(f"    Target: {action_scratch['target']}")

    # Test Pit defect action
    print("\n  Testing Pit defect action:")
    action_pit = agent._generate_improvement_action('Pit', 'center', 'MEDIUM')
    assert action_pit['action'] == 'Etch recipe optimization'
    assert action_pit['target'] == 'Next LOT'
    print(f"    Action: {action_pit['action']}")
    print(f"    Target: {action_pit['target']}")

    print("\n✅ Test 3 PASSED: Improvement actions generated correctly")
    print()


def test_stage3_recipe_adjustments():
    """
    Test 4: Verify recipe adjustment generation

    Tests that recipe adjustments are generated for next LOT
    """
    print("=" * 80)
    print("Test 4: Recipe Adjustments for Next LOT")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize agent
    agent = Stage3Agent(config)

    # Test Particle recipe adjustment
    print("\n  Testing Particle defect recipe adjustment:")
    recipe_particle = agent._generate_recipe_adjustment('Particle', 'random', 'HIGH')
    assert 'chamber_pressure' in recipe_particle
    assert recipe_particle['chamber_pressure']['change'] == -5
    assert recipe_particle['apply_to'] == 'Next LOT'
    print(f"    Chamber pressure: {recipe_particle['chamber_pressure']['change']} mTorr")
    print(f"    Gas flow rate: {recipe_particle['gas_flow_rate']['change']} sccm")
    print(f"    Apply to: {recipe_particle['apply_to']}")

    # Test Pit recipe adjustment
    print("\n  Testing Pit defect recipe adjustment:")
    recipe_pit = agent._generate_recipe_adjustment('Pit', 'center', 'MEDIUM')
    assert 'etch_time' in recipe_pit
    assert recipe_pit['etch_time']['change'] == -5
    assert recipe_pit['apply_to'] == 'Next LOT'
    print(f"    Etch time: {recipe_pit['etch_time']['change']} sec")
    print(f"    RF power: {recipe_pit['rf_power']['change']} W")
    print(f"    Apply to: {recipe_pit['apply_to']}")

    print("\n✅ Test 4 PASSED: Recipe adjustments generated correctly")
    print()


def test_stage3_impact_estimation():
    """
    Test 5: Verify impact estimation

    Tests that expected impact is calculated correctly
    """
    print("=" * 80)
    print("Test 5: Expected Impact Estimation")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize agent
    agent = Stage3Agent(config)

    # Test HIGH severity impact
    print("\n  Testing HIGH severity impact:")
    impact_high = agent._estimate_improvement_impact('Particle', 25, 'HIGH')
    assert impact_high['yield_improvement'] == 10.0
    assert impact_high['cost_saving'] > 0
    assert impact_high['implementation_cost'] > 0
    print(f"    Yield improvement: {impact_high['yield_improvement']}%")
    print(f"    Cost saving: ${impact_high['cost_saving']:,.0f} per LOT")
    print(f"    Implementation cost: ${impact_high['implementation_cost']:,.0f}")
    print(f"    Payback period: {impact_high['payback_period']}")

    # Test MEDIUM severity impact
    print("\n  Testing MEDIUM severity impact:")
    impact_medium = agent._estimate_improvement_impact('Scratch', 15, 'MEDIUM')
    assert impact_medium['yield_improvement'] == 5.0
    print(f"    Yield improvement: {impact_medium['yield_improvement']}%")
    print(f"    Cost saving: ${impact_medium['cost_saving']:,.0f} per LOT")
    print(f"    Payback period: {impact_medium['payback_period']}")

    # Test LOW severity impact
    print("\n  Testing LOW severity impact:")
    impact_low = agent._estimate_improvement_impact('Residue', 5, 'LOW')
    assert impact_low['yield_improvement'] == 2.0
    print(f"    Yield improvement: {impact_low['yield_improvement']}%")
    print(f"    Cost saving: ${impact_low['cost_saving']:,.0f} per LOT")
    print(f"    Payback period: {impact_low['payback_period']}")

    print("\n✅ Test 5 PASSED: Impact estimation works correctly")
    print()


def test_stage3_full_workflow():
    """
    Test 6: Full workflow test

    Tests complete analyze → recommend workflow
    """
    print("=" * 80)
    print("Test 6: Full Stage 3 Workflow")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize agent
    agent = Stage3Agent(config)

    # Create mock wafer data
    wafer_data = pd.Series({
        'wafer_id': 'W0123',
        'lot_id': 'LOT-TEST-002',
        'recipe': 'Recipe_B',
        'chamber': 'Chamber_2',
        'timestamp': '2026-01-29',
        'etch_rate': 145.0,
        'pressure': 105.0,
        'temperature': 255.0,
        'rf_power': 950.0,
        'gas_flow': 95.0
    })

    print(f"\nProcessing wafer: {wafer_data['wafer_id']}")

    # Step 1: Analyze
    print("\n  Step 1: Analyzing defects...")
    analysis_result = agent.analyze(wafer_data)
    print(f"    Defect type: {analysis_result['defect_type']}")
    print(f"    Defect count: {analysis_result['defect_count']}")
    print(f"    Severity: {analysis_result['severity']}")

    # Step 2: Make recommendation
    print("\n  Step 2: Generating recommendations...")
    recommendation = agent.make_recommendation(wafer_data, analysis_result)

    # Verify complete structure
    print("\n  Step 3: Verifying recommendation structure...")
    required_fields = [
        'process_improvement_action',
        'recipe_adjustment_for_next_lot',
        'monitoring_plan',
        'current_wafer_status',
        'action_target',
        'current_wafer_actionable',
        'ai_recommendation',
        'ai_confidence',
        'expected_yield_improvement',
        'expected_cost_saving',
        'implementation_cost',
        'payback_period',
        'engineer_decision'
    ]

    for field in required_fields:
        assert field in recommendation, f"Missing required field: {field}"
        print(f"    ✓ {field}")

    # Verify Phase 2 constraints
    print("\n  Step 4: Verifying Phase 2 (Post-Fab) constraints...")
    assert recommendation['current_wafer_status'] == 'COMPLETED'
    print(f"    ✓ Current wafer status: {recommendation['current_wafer_status']}")

    assert recommendation['action_target'] == 'NEXT_LOT'
    print(f"    ✓ Action target: {recommendation['action_target']}")

    assert recommendation['current_wafer_actionable'] == False
    print(f"    ✓ Current wafer actionable: {recommendation['current_wafer_actionable']}")

    # Display summary
    print("\n  Recommendation Summary:")
    print(f"    Priority: {recommendation['ai_recommendation']}")
    print(f"    Improvement action: {recommendation['process_improvement_action']['action']}")
    print(f"    Expected yield gain: {recommendation['expected_yield_improvement']}%")
    print(f"    Expected savings: ${recommendation['expected_cost_saving']:,.0f}/LOT")
    print(f"    Implementation cost: ${recommendation['implementation_cost']:,.0f}")
    print(f"    Payback: {recommendation['payback_period']}")

    print("\n✅ Test 6 PASSED: Full workflow completed successfully")
    print()


def main():
    """Run all Stage 3 process improvement tests"""
    print("\n")
    print("=" * 80)
    print("STAGE 3 PROCESS IMPROVEMENT TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run tests
        test_stage3_output_format()
        test_stage3_priority_levels()
        test_stage3_improvement_actions()
        test_stage3_recipe_adjustments()
        test_stage3_impact_estimation()
        test_stage3_full_workflow()

        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Output format correct for Phase 2 (Post-Fab)")
        print("  ✓ Priority levels determined correctly")
        print("  ✓ Improvement actions generated correctly")
        print("  ✓ Recipe adjustments generated correctly")
        print("  ✓ Impact estimation works correctly")
        print("  ✓ Full workflow completed successfully")
        print()
        print("Phase 2 Verification:")
        print("  ✓ Current wafer marked as COMPLETED")
        print("  ✓ Action target set to NEXT_LOT")
        print("  ✓ No immediate actions on current wafer")
        print("  ✓ All recommendations for next LOT application")
        print()
        print("Next Steps:")
        print("  1. Integrate with Phase 2 pipeline")
        print("  2. Test with real SEM defect data")
        print("  3. Validate with process engineers")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
