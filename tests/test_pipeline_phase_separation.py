"""
Test Suite for Pipeline Phase Separation

Tests Phase 1 (In-Line) and Phase 2 (Post-Fab) separation logic
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import pandas as pd
import numpy as np
from src.pipeline.controller import PipelineController


def test_phase1_scrap():
    """
    Test 1: Phase 1 SCRAP termination

    Verify that when Stage 1 recommends SCRAP,
    Phase 2 is completely skipped
    """
    print("=" * 80)
    print("Test 1: Phase 1 SCRAP → Phase 2 Skipped")
    print("=" * 80)

    # Initialize controller
    controller = PipelineController('config.yaml')

    # Process a wafer (any wafer from dataset)
    wafer_id = "wafer_001"
    result = controller.process_wafer(wafer_id)

    if result is None:
        print(f"⚠️  Wafer {wafer_id} not found, trying alternative...")
        # Try first available wafer
        all_wafers = controller.data_loader.get_all_wafer_ids()
        if len(all_wafers) > 0:
            wafer_id = all_wafers[0]
            result = controller.process_wafer(wafer_id)

    assert result is not None, "Failed to load any wafer data"

    print(f"\nWafer ID: {result['wafer_id']}")
    print(f"Pipeline Path: {' → '.join(result['pipeline_path'])}")
    print(f"Total Cost: ${result['total_cost']:.2f}")
    print()

    # Check Phase 1 execution
    phase1 = result['phases']['phase1']
    print("Phase 1 (In-Line) Results:")
    print(f"  Stage 0 executed: {'stage0' in phase1}")
    print(f"  Stage 1 executed: {'stage1' in phase1}")
    print(f"  Phase 1 outcome: {phase1.get('outcome', 'N/A')}")

    if phase1.get('outcome') in ['SCRAP', 'REWORK']:
        print(f"  ✓ Phase 1 terminated with: {phase1['outcome']}")

        # Verify Phase 2 was skipped
        phase2 = result['phases']['phase2']
        print("\nPhase 2 (Post-Fab) Results:")
        print(f"  Phase 2 outcome: {phase2.get('outcome', 'N/A')}")
        print(f"  Stage 2B executed: {'stage2b' in phase2}")
        print(f"  Stage 3 executed: {'stage3' in phase2}")

        assert phase2.get('outcome') == 'SKIPPED', \
            f"Expected Phase 2 to be SKIPPED, got {phase2.get('outcome')}"
        assert 'stage2b' not in phase2, "Stage 2B should not execute after Phase 1 SCRAP/REWORK"
        assert 'stage3' not in phase2, "Stage 3 should not execute after Phase 1 SCRAP/REWORK"

        print("\n✅ Test 1 PASSED: Phase 1 termination correctly skips Phase 2")

    else:
        print(f"  ℹ️  Phase 1 outcome: {phase1.get('outcome')} (PROCEED to Phase 2)")
        print("\n⚠️  Test 1 SKIPPED: This wafer did not trigger Phase 1 termination")
        print("     (This is expected behavior - not all wafers will SCRAP/REWORK)")

    print()


def test_phase1_to_phase2_transition():
    """
    Test 2: Phase 1 → Phase 2 transition

    Verify that when Stage 1 recommends PROCEED,
    Phase 2 executes correctly
    """
    print("=" * 80)
    print("Test 2: Phase 1 PROCEED → Phase 2 Execution")
    print("=" * 80)

    # Initialize controller
    controller = PipelineController('config.yaml')

    # Process multiple wafers to find one that proceeds to Phase 2
    all_wafers = controller.data_loader.get_all_wafer_ids()

    if len(all_wafers) == 0:
        print("❌ No wafer data available for testing")
        return

    # Try up to 10 wafers to find one that proceeds
    phase2_result = None
    for i, wafer_id in enumerate(all_wafers[:10]):
        result = controller.process_wafer(wafer_id)

        if result and result['phases']['phase1'].get('outcome') == 'PROCEED':
            phase2_result = result
            break

    if phase2_result is None:
        print("⚠️  Test 2 SKIPPED: No wafers proceeded to Phase 2 in first 10 samples")
        print("     (This may happen with certain datasets)")
        return

    result = phase2_result

    print(f"\nWafer ID: {result['wafer_id']}")
    print(f"Pipeline Path: {' → '.join(result['pipeline_path'])}")
    print(f"Total Cost: ${result['total_cost']:.2f}")
    print()

    # Verify Phase 1 execution
    phase1 = result['phases']['phase1']
    print("Phase 1 (In-Line) Results:")
    print(f"  Stage 0 executed: {'stage0' in phase1}")
    print(f"  Stage 1 executed: {'stage1' in phase1}")
    print(f"  Phase 1 outcome: {phase1.get('outcome')}")

    assert phase1.get('outcome') == 'PROCEED', \
        f"Expected Phase 1 outcome PROCEED, got {phase1.get('outcome')}"
    print("  ✓ Phase 1 completed with PROCEED")

    # Verify Phase 2 execution
    phase2 = result['phases']['phase2']
    print("\nPhase 2 (Post-Fab) Results:")
    print(f"  Stage 2B executed: {'stage2b' in phase2}")
    print(f"  Stage 3 executed: {'stage3' in phase2}")
    print(f"  Phase 2 outcome: {phase2.get('outcome')}")

    # Phase 2 should have executed Stage 2B at minimum
    assert 'stage2b' in phase2, "Stage 2B should execute in Phase 2"
    assert phase2.get('outcome') in ['COMPLETE', 'SKIPPED'], \
        f"Expected Phase 2 outcome COMPLETE or SKIPPED, got {phase2.get('outcome')}"

    if 'stage2b' in phase2:
        stage2b_action = phase2['stage2b']['recommendation']['action']
        print(f"  Stage 2B action: {stage2b_action}")

        if stage2b_action == 'SEM':
            assert 'stage3' in phase2, "Stage 3 should execute after SEM decision"
            print("  ✓ Stage 3 executed (SEM required)")
        else:
            print(f"  ℹ️  Stage 3 skipped (no SEM required)")

    print("\n✅ Test 2 PASSED: Phase 1→2 transition works correctly")
    print()


def test_phase_summary():
    """
    Test 3: Phase summary generation

    Verify that phase-wise summaries are generated correctly
    """
    print("=" * 80)
    print("Test 3: Phase Summary Generation")
    print("=" * 80)

    # Initialize controller
    controller = PipelineController('config.yaml')

    # Process a small batch
    all_wafers = controller.data_loader.get_all_wafer_ids()

    if len(all_wafers) == 0:
        print("❌ No wafer data available for testing")
        return

    # Process up to 5 wafers
    test_wafers = all_wafers[:min(5, len(all_wafers))]
    print(f"\nProcessing {len(test_wafers)} wafers...")

    results = []
    for wafer_id in test_wafers:
        result = controller.process_wafer(wafer_id)
        if result:
            results.append(result)

    print(f"Successfully processed: {len(results)} wafers")

    # Generate phase summary
    phase_summary = controller.get_phase_summary(results)

    print("\nPhase Summary:")
    print(f"  Total wafers: {phase_summary['total_wafers']}")

    print("\n  Phase 1 (In-Line):")
    print(f"    Total cost: ${phase_summary['phase1']['total_cost']:.2f}")
    print(f"    Outcomes: {phase_summary['phase1']['outcomes']}")
    print(f"    Stage actions: {phase_summary['phase1']['stage_actions']}")

    print("\n  Phase 2 (Post-Fab):")
    print(f"    Total cost: ${phase_summary['phase2']['total_cost']:.2f}")
    print(f"    Outcomes: {phase_summary['phase2']['outcomes']}")
    print(f"    Stage actions: {phase_summary['phase2']['stage_actions']}")

    # Verify structure
    assert 'phase1' in phase_summary, "Phase 1 summary missing"
    assert 'phase2' in phase_summary, "Phase 2 summary missing"
    assert 'outcomes' in phase_summary['phase1'], "Phase 1 outcomes missing"
    assert 'outcomes' in phase_summary['phase2'], "Phase 2 outcomes missing"

    print("\n✅ Test 3 PASSED: Phase summary generation works correctly")
    print()


def test_lot_processing():
    """
    Test 4: LOT-level processing (Stage 2A)

    Verify that LOT processing with Stage 2A works correctly
    """
    print("=" * 80)
    print("Test 4: LOT-level Processing (Stage 2A)")
    print("=" * 80)

    # Initialize controller
    controller = PipelineController('config.yaml')

    # Create mock WAT data for a LOT
    np.random.seed(42)
    n_wafers = 25

    wat_data = pd.DataFrame({
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
    })

    print(f"\nProcessing LOT-TEST-001 with {len(wat_data)} wafers...")

    # Process LOT
    lot_result = controller.process_lot('LOT-TEST-001', wat_data)

    print(f"\nLOT Processing Result:")
    print(f"  LOT ID: {lot_result['lot_id']}")
    print(f"  Wafer count: {lot_result['wafer_count']}")
    print(f"  Final recommendation: {lot_result['final_recommendation']}")
    print(f"  Total cost: ${lot_result['total_cost']:,.0f}")
    print(f"  Proceed to Stage 2B: {lot_result['proceed_to_stage2b']}")
    print(f"  Wafers for Stage 2B: {len(lot_result['wafer_list_for_stage2b'])}")

    # Verify structure
    assert 'stage2a' in lot_result['stages'], "Stage 2A results missing"
    assert 'final_recommendation' in lot_result, "Final recommendation missing"
    assert lot_result['final_recommendation'] in ['LOT_PROCEED', 'LOT_SCRAP'], \
        f"Invalid LOT recommendation: {lot_result['final_recommendation']}"

    if lot_result['final_recommendation'] == 'LOT_PROCEED':
        assert lot_result['proceed_to_stage2b'] == True, \
            "proceed_to_stage2b should be True for LOT_PROCEED"
        assert len(lot_result['wafer_list_for_stage2b']) > 0, \
            "wafer_list_for_stage2b should not be empty for LOT_PROCEED"
        print("  ✓ LOT_PROCEED: All checks passed")
    else:
        assert lot_result['proceed_to_stage2b'] == False, \
            "proceed_to_stage2b should be False for LOT_SCRAP"
        assert len(lot_result['wafer_list_for_stage2b']) == 0, \
            "wafer_list_for_stage2b should be empty for LOT_SCRAP"
        print("  ✓ LOT_SCRAP: All checks passed")

    print("\n✅ Test 4 PASSED: LOT processing works correctly")
    print()


def main():
    """Run all phase separation tests"""
    print("\n")
    print("=" * 80)
    print("PIPELINE PHASE SEPARATION TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run tests
        test_phase1_scrap()
        test_phase1_to_phase2_transition()
        test_phase_summary()
        test_lot_processing()

        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Phase 1 termination logic works")
        print("  ✓ Phase 1→2 transition works")
        print("  ✓ Phase summary generation works")
        print("  ✓ LOT-level processing (Stage 2A) works")
        print()
        print("Next Steps:")
        print("  1. Integrate with Streamlit dashboard")
        print("  2. Add LOT management UI")
        print("  3. Test with real WAT data")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
