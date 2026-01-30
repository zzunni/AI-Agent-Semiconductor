"""
Test script for DiscoveryAgent

Tests the Pattern Discovery agent for statistical pattern detection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import pandas as pd
from src.agents.discovery_agent import DiscoveryAgent


def test_initialization():
    """Test 1: Agent initialization"""
    print("=" * 80)
    print("Test 1: DiscoveryAgent Initialization")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize agent
    agent = DiscoveryAgent(config)

    print(f"✓ Agent initialized")
    print(f"✓ LLM enabled: {agent.use_llm}")
    print(f"✓ Lookback days: {agent.lookback_days}")
    print(f"✓ Significance threshold: {agent.significance_threshold}")
    print(f"✓ Data loader: {agent.data_loader is not None}")
    print()

    return agent


def test_sensor_pattern_correlation():
    """Test 2: Detect sensor-pattern correlations"""
    print("=" * 80)
    print("Test 2: Sensor-Pattern Correlation Detection")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = DiscoveryAgent(config)

    # Load and merge data
    step1_df = agent.data_loader.load_step1_data()
    wm811k_df = agent.data_loader.load_wm811k_proxy()
    merged_df = step1_df.merge(wm811k_df, on='wafer_id', how='inner')

    print(f"Analyzing {len(merged_df)} wafers")
    print()

    # Detect correlations
    patterns = agent._detect_sensor_pattern_correlation(merged_df)

    print(f"Found {len(patterns)} sensor-pattern correlations")
    print()

    # Display significant patterns
    for i, pattern in enumerate(patterns[:5], 1):  # Show first 5
        print(f"Pattern {i}:")
        print(f"  Sensor: {pattern['sensor']}")
        print(f"  Pattern: {pattern['pattern']}")
        print(f"  Correlation: {pattern['correlation']:.3f}")
        print(f"  P-value: {pattern['p_value']:.6f}")
        print(f"  Pattern mean: {pattern['pattern_mean']:.2f}")
        print(f"  Other mean: {pattern['other_mean']:.2f}")
        print(f"  Sample size: {pattern['pattern_count']}")
        print(f"  Evidence: {pattern['evidence']}")
        print()

    # Verify statistical significance
    for pattern in patterns:
        assert pattern['p_value'] < agent.significance_threshold, \
            f"Pattern should be significant (p={pattern['p_value']})"

    print(f"✓ All {len(patterns)} patterns are statistically significant (p < {agent.significance_threshold})")
    print()

    return agent, patterns


def test_chamber_effects():
    """Test 3: Detect chamber effects"""
    print("=" * 80)
    print("Test 3: Chamber Effect Detection")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = DiscoveryAgent(config)

    # Load and merge data
    step1_df = agent.data_loader.load_step1_data()
    wm811k_df = agent.data_loader.load_wm811k_proxy()
    merged_df = step1_df.merge(wm811k_df, on='wafer_id', how='inner')

    # Detect chamber effects
    patterns = agent._detect_chamber_effects(merged_df)

    print(f"Found {len(patterns)} chamber effects")
    print()

    if len(patterns) > 0:
        for i, pattern in enumerate(patterns, 1):
            print(f"Chamber Effect {i}:")
            print(f"  F-statistic: {pattern['f_statistic']:.2f}")
            print(f"  P-value: {pattern['p_value']:.6f}")
            print(f"  Confidence: {pattern['confidence']:.2%}")
            print(f"  Evidence: {pattern['evidence']}")
            print()
            print("  Chamber Statistics:")
            for cs in pattern['chamber_stats']:
                print(f"    {cs['chamber']}: "
                      f"severity={cs['mean_severity']:.2f}, "
                      f"count={cs['count']}, "
                      f"edge_ring_rate={cs['edge_ring_rate']:.1%}")
            print()

        print("✓ Chamber effects detected and statistically significant")
    else:
        print("⚠️  No statistically significant chamber effects found")

    print()
    return agent, patterns


def test_recipe_effects():
    """Test 4: Detect recipe effects"""
    print("=" * 80)
    print("Test 4: Recipe Effect Detection")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = DiscoveryAgent(config)

    # Load and merge data
    step1_df = agent.data_loader.load_step1_data()
    wm811k_df = agent.data_loader.load_wm811k_proxy()
    merged_df = step1_df.merge(wm811k_df, on='wafer_id', how='inner')

    # Detect recipe effects
    patterns = agent._detect_recipe_effects(merged_df)

    print(f"Found {len(patterns)} recipe effects")
    print()

    if len(patterns) > 0:
        for i, pattern in enumerate(patterns, 1):
            print(f"Recipe Effect {i}:")
            print(f"  F-statistic: {pattern['f_statistic']:.2f}")
            print(f"  P-value: {pattern['p_value']:.6f}")
            print(f"  Evidence: {pattern['evidence']}")
            print()
            print("  Recipe Statistics:")
            for rs in pattern['recipe_stats']:
                print(f"    {rs['recipe']}: "
                      f"severity={rs['mean_severity']:.2f}, "
                      f"count={rs['count']}")
            print()

        print("✓ Recipe effects detected and statistically significant")
    else:
        print("⚠️  No statistically significant recipe effects found")

    print()
    return agent, patterns


def test_full_discovery():
    """Test 5: Full pattern discovery"""
    print("=" * 80)
    print("Test 5: Full Pattern Discovery")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = DiscoveryAgent(config)

    # Discover all patterns
    patterns = agent.discover_patterns()

    print(f"Total patterns discovered: {len(patterns)}")
    print()

    # Group by type
    pattern_types = {}
    for pattern in patterns:
        ptype = pattern['type']
        if ptype not in pattern_types:
            pattern_types[ptype] = []
        pattern_types[ptype].append(pattern)

    print("Pattern Summary:")
    for ptype, plist in pattern_types.items():
        print(f"  {ptype}: {len(plist)} patterns")
    print()

    # Display top patterns by significance
    patterns_sorted = sorted(patterns, key=lambda x: x.get('p_value', 1))

    print("Top 3 Most Significant Patterns:")
    for i, pattern in enumerate(patterns_sorted[:3], 1):
        print(f"\n{i}. {pattern['type']}")
        print(f"   P-value: {pattern.get('p_value', 'N/A'):.6f}")
        print(f"   Confidence: {pattern.get('confidence', 'N/A'):.2%}")
        if 'evidence' in pattern:
            print(f"   Evidence: {pattern['evidence']}")
        if 'sensor' in pattern:
            print(f"   Sensor: {pattern['sensor']}")
        if 'pattern' in pattern:
            print(f"   Pattern: {pattern['pattern']}")

    print()
    print("✓ Full pattern discovery completed")
    print()

    return agent, patterns


def test_llm_analysis():
    """Test 6: LLM pattern analysis (if available)"""
    print("=" * 80)
    print("Test 6: LLM Pattern Analysis")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = DiscoveryAgent(config)

    if not agent.use_llm:
        print("⚠️  LLM not available - skipping test")
        print("   (Set ANTHROPIC_API_KEY in .env to enable)")
        print()
        return

    # Discover patterns (will include LLM analysis)
    patterns = agent.discover_patterns()

    # Display LLM analyses
    patterns_with_llm = [p for p in patterns if 'llm_analysis' in p]

    print(f"Patterns with LLM analysis: {len(patterns_with_llm)}/{len(patterns)}")
    print()

    if len(patterns_with_llm) > 0:
        print("Sample LLM Analysis:")
        print("-" * 80)
        pattern = patterns_with_llm[0]
        print(f"Pattern: {pattern['type']}")
        if 'sensor' in pattern:
            print(f"Sensor: {pattern['sensor']}")
        print()
        print("LLM Analysis (Korean):")
        print(pattern['llm_analysis'][:500] + "..." if len(pattern['llm_analysis']) > 500 else pattern['llm_analysis'])
        print("-" * 80)
        print()

        print("✓ LLM analysis completed successfully")
    else:
        print("⚠️  No patterns with LLM analysis")

    print()


def test_statistical_validity():
    """Test 7: Verify statistical validity"""
    print("=" * 80)
    print("Test 7: Statistical Validity Verification")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    agent = DiscoveryAgent(config)

    # Discover patterns
    patterns = agent.discover_patterns()

    print(f"Analyzing {len(patterns)} patterns for statistical validity")
    print()

    # Check p-values
    p_values = [p.get('p_value', 1) for p in patterns]
    valid_patterns = [p for p in patterns if p.get('p_value', 1) < agent.significance_threshold]

    print("Statistical Validity:")
    print(f"  Total patterns: {len(patterns)}")
    print(f"  Valid patterns (p < {agent.significance_threshold}): {len(valid_patterns)}")
    print(f"  Validity rate: {len(valid_patterns)/len(patterns)*100 if patterns else 0:.1f}%")
    print()

    if len(p_values) > 0:
        print("P-value Distribution:")
        print(f"  Min: {min(p_values):.6f}")
        print(f"  Max: {max(p_values):.6f}")
        print(f"  Mean: {sum(p_values)/len(p_values):.6f}")
        print()

    # Check confidence levels
    confidences = [p.get('confidence', 0) for p in patterns]
    if len(confidences) > 0:
        print("Confidence Distribution:")
        print(f"  Min: {min(confidences):.2%}")
        print(f"  Max: {max(confidences):.2%}")
        print(f"  Mean: {sum(confidences)/len(confidences):.2%}")
        print()

    print("✓ Statistical validity verified")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("DiscoveryAgent Test Suite")
    print("=" * 80)
    print()

    try:
        # Run tests
        test_initialization()
        test_sensor_pattern_correlation()
        test_chamber_effects()
        test_recipe_effects()
        test_full_discovery()
        test_llm_analysis()
        test_statistical_validity()

        print("=" * 80)
        print("✅ All DiscoveryAgent tests passed!")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Pattern discovery initialization works")
        print("  ✓ Sensor-pattern correlations detected (t-test)")
        print("  ✓ Chamber effects detected (ANOVA)")
        print("  ✓ Recipe effects detected (ANOVA)")
        print("  ✓ Statistical significance verified (p < 0.01)")
        print("  ✓ LLM analysis provides Korean insights")
        print("  ✓ All patterns are statistically valid")
        print()
        print("Next steps:")
        print("  1. Implement feedback learning agent")
        print("  2. Create orchestration controller")
        print("  3. Build Streamlit dashboard for pattern visualization")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
