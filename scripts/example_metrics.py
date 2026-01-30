"""
Example usage of MetricsCalculator

This script demonstrates how to calculate performance metrics
for the semiconductor quality control system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.utils.metrics import MetricsCalculator


def create_mock_decisions(n_wafers=200):
    """Create mock decision data for testing"""
    np.random.seed(42)

    decisions_data = []
    for i in range(n_wafers):
        # Simulate realistic decision distribution
        rand = np.random.random()

        if rand < 0.15:  # 15% INLINE inspection
            decision = 'INLINE'
            confidence = np.random.uniform(0.7, 0.9)
        elif rand < 0.20:  # 5% SEM inspection (expensive)
            decision = 'SEM'
            confidence = np.random.uniform(0.8, 0.95)
        elif rand < 0.30:  # 10% REWORK
            decision = 'REWORK'
            confidence = np.random.uniform(0.6, 0.8)
        else:  # 70% PASS
            decision = 'PASS'
            confidence = np.random.uniform(0.5, 0.7)

        # Add engineer decision (simulated agreement)
        engineer_agrees = np.random.random() < 0.85  # 85% agreement
        engineer_decision = decision if engineer_agrees else np.random.choice(['PASS', 'REWORK'])

        decisions_data.append({
            'wafer_id': f'W{i:04d}',
            'stage': f'stage{np.random.randint(0, 4)}',
            'ai_recommendation': decision,
            'ai_confidence': confidence,
            'engineer_decision': engineer_decision,
            'engineer_rationale': ''
        })

    return pd.DataFrame(decisions_data)


def main():
    print("=" * 80)
    print("MetricsCalculator Example Usage")
    print("=" * 80)
    print()

    # Create mock decisions
    print("Generating mock decision data...")
    decisions_df = create_mock_decisions(n_wafers=200)
    print(f"✓ Generated {len(decisions_df)} decisions")
    print()

    # Initialize calculator
    calculator = MetricsCalculator()
    print("✓ MetricsCalculator initialized")
    print()

    # Example 1: Calculate detection rate
    print("=" * 80)
    print("Example 1: Detection Rate")
    print("=" * 80)
    detection_rate = calculator.calculate_detection_rate(decisions_df)
    print(f"Overall detection rate: {detection_rate:.2%}")
    print()

    # Example 2: Calculate costs
    print("=" * 80)
    print("Example 2: Cost Analysis")
    print("=" * 80)
    costs = calculator.calculate_cost(decisions_df)
    print("Cost Breakdown:")
    print(f"  Inline inspection: ${costs['inline']:>12,.2f}")
    print(f"  SEM inspection:    ${costs['sem']:>12,.2f}")
    print(f"  Rework:            ${costs['rework']:>12,.2f}")
    print(f"  {'─' * 35}")
    print(f"  Total:             ${costs['total']:>12,.2f}")
    print()

    # Example 3: Calculate ROI
    print("=" * 80)
    print("Example 3: Return on Investment")
    print("=" * 80)
    # Estimate wafers saved based on inspections
    inspected = decisions_df[
        decisions_df['ai_recommendation'].isin(['INLINE', 'SEM', 'REWORK'])
    ]
    wafers_saved = len(inspected)

    roi = calculator.calculate_roi(costs['total'], wafers_saved)
    print(f"Wafers saved: {wafers_saved}")
    print(f"Total cost: ${costs['total']:,.2f}")
    print(f"Value saved: ${wafers_saved * calculator.wafer_value:,.2f}")
    print(f"ROI: {roi:.2f}%")
    print()

    # Example 4: Generate comprehensive summary
    print("=" * 80)
    print("Example 4: Comprehensive Summary")
    print("=" * 80)
    summary = calculator.generate_summary(decisions_df)

    print("Decision Distribution:")
    print(f"  Total wafers:      {summary['total_wafers']:>6}")
    print(f"  INLINE:            {summary['inline_count']:>6}")
    print(f"  SEM:               {summary['sem_count']:>6}")
    print(f"  REWORK:            {summary['rework_count']:>6}")
    print(f"  PASS:              {summary['pass_count']:>6}")
    print()

    print("Performance Metrics:")
    print(f"  Detection rate:    {summary['detection_rate']:>6.2%}")
    print(f"  Avg confidence:    {summary['avg_confidence']:>6.2%}")
    print(f"  Total cost:        ${summary['total_cost']:>10,.2f}")
    print(f"  ROI:               {summary['roi']:>6.2f}%")
    print()

    # Example 5: Compare with baselines
    print("=" * 80)
    print("Example 5: Baseline Comparison")
    print("=" * 80)
    comparison = calculator.compare_baselines(
        ai_detection_rate=detection_rate,
        ai_cost=costs['total']
    )

    print(comparison.to_string(index=False))
    print()

    # Example 6: Calculate agreement rate
    print("=" * 80)
    print("Example 6: AI-Engineer Agreement")
    print("=" * 80)
    agreement = calculator.calculate_agreement_rate(decisions_df)
    print(f"Overall agreement: {agreement['overall_agreement']:.2%}")

    if agreement['by_stage']:
        print("\nAgreement by stage:")
        for stage, rate in agreement['by_stage'].items():
            print(f"  {stage}: {rate:.2%}")
    print()

    # Example 7: Decision distribution analysis
    print("=" * 80)
    print("Example 7: Decision Distribution by Confidence")
    print("=" * 80)

    # Analyze confidence distribution for each decision type
    for decision_type in ['INLINE', 'SEM', 'REWORK', 'PASS']:
        subset = decisions_df[decisions_df['ai_recommendation'] == decision_type]
        if len(subset) > 0:
            avg_conf = subset['ai_confidence'].mean()
            print(f"{decision_type:>8}: {len(subset):>3} wafers, avg confidence: {avg_conf:.2%}")
    print()

    print("=" * 80)
    print("✅ All examples completed!")
    print()
    print("Key Insights:")
    print(f"  - Our AI system achieves {detection_rate:.2%} detection rate")
    print(f"  - Total operational cost: ${costs['total']:,.2f}")
    print(f"  - ROI of {summary['roi']:.2f}% demonstrates economic value")
    print(f"  - {agreement['overall_agreement']:.2%} agreement with engineers shows reliability")
    print("=" * 80)


if __name__ == "__main__":
    main()
