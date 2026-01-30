"""
Example usage of Korean prompt templates with LLMClient

Demonstrates how to use the prompt templates for:
1. Pattern discovery analysis
2. Root cause analysis
3. Feedback learning

Note: Requires ANTHROPIC_API_KEY in .env
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from dotenv import load_dotenv
from src.llm.prompts import (
    format_pattern_discovery_prompt,
    format_root_cause_prompt,
    format_feedback_learning_prompt,
    build_edge_ring_analysis,
    build_particle_defect_analysis
)
from src.utils.data_loader import DataLoader


def example_pattern_discovery():
    """Example: Using pattern discovery prompt with real data"""
    print("=" * 80)
    print("Example 1: Pattern Discovery with Real Mock Data")
    print("=" * 80)

    # Load real wafer data
    loader = DataLoader()
    step1_df = loader.load_step1_data()

    # Find Edge-Ring patterns (high etch rate)
    edge_ring_wafers = step1_df[step1_df['etch_rate'] > 3.7]

    # Calculate statistics
    wafer_count = len(edge_ring_wafers)
    avg_etch_rate = edge_ring_wafers['etch_rate'].mean()
    avg_pressure = edge_ring_wafers['pressure'].mean()
    avg_temp = edge_ring_wafers['temperature'].mean()

    # Build prompt using quick builder
    prompt = build_edge_ring_analysis(
        wafer_count=wafer_count,
        avg_etch_rate=avg_etch_rate,
        avg_pressure=avg_pressure
    )

    print("Generated Prompt:")
    print("-" * 80)
    print(prompt)
    print()

    # Alternative: Using full formatter
    evidence = f"""
{wafer_count}개 웨이퍼에서 Edge-Ring 패턴 발견 (전체의 {(wafer_count/len(step1_df))*100:.1f}%)

주요 웨이퍼:
- {edge_ring_wafers['wafer_id'].iloc[0]}: etch rate {edge_ring_wafers['etch_rate'].iloc[0]:.2f}
- {edge_ring_wafers['wafer_id'].iloc[1]}: etch rate {edge_ring_wafers['etch_rate'].iloc[1]:.2f}
- {edge_ring_wafers['wafer_id'].iloc[2]}: etch rate {edge_ring_wafers['etch_rate'].iloc[2]:.2f}
"""

    sensor_summary = f"""
- 평균 etch rate: {avg_etch_rate:.2f} µm/min (정상 범위: 3.2-3.6)
- 평균 압력: {avg_pressure:.1f} mTorr (정상 범위: 145-155)
- 평균 온도: {avg_temp:.1f}°C
- 챔버별 분포: {dict(edge_ring_wafers['chamber'].value_counts())}
"""

    process_history = f"""
- 발생 기간: {step1_df['timestamp'].min()} ~ {step1_df['timestamp'].max()}
- 영향받은 Lot: {edge_ring_wafers['lot_id'].nunique()}개
- 주로 영향받은 챔버: {edge_ring_wafers['chamber'].mode()[0]}
"""

    prompt_full = format_pattern_discovery_prompt(
        pattern_type="Edge-Ring (고 Etch Rate)",
        evidence=evidence,
        correlation=0.85,
        p_value=0.001,
        confidence=0.90,
        sensor_summary=sensor_summary,
        process_history=process_history
    )

    print("Full Formatted Prompt:")
    print("-" * 80)
    print(prompt_full[:500] + "...")
    print()


def example_root_cause_analysis():
    """Example: Root cause analysis for specific wafer"""
    print("=" * 80)
    print("Example 2: Root Cause Analysis with Real Wafer Data")
    print("=" * 80)

    # Load wafer data with proxies
    loader = DataLoader()
    wafer_data = loader.get_wafer_with_proxies("W0100")

    if wafer_data is None:
        print("Wafer not found")
        return

    wafer = wafer_data['wafer_data']
    carinthia = wafer_data['carinthia']

    # Build process history
    process_history = f"""
- Recipe: {wafer['recipe']}
- Chamber: {wafer['chamber']}
- Lot: {wafer['lot_id']}
- Timestamp: {wafer['timestamp']}
"""

    # Build sensor data
    sensor_data = f"""
- Etch rate: {wafer['etch_rate']:.2f} µm/min
- 압력: {wafer['pressure']:.1f} mTorr
- 온도: {wafer['temperature']:.1f}°C
- RF Power: {wafer['rf_power']:.0f} W
- Gas flow: {wafer['gas_flow']:.1f} sccm
"""

    # Find similar cases (same defect type, similar chamber)
    step1_df = loader.load_step1_data()
    carinthia_df = loader.load_carinthia_proxy()

    merged = step1_df.merge(carinthia_df, on='wafer_id')
    similar = merged[
        (merged['defect_type'] == carinthia['defect_type']) &
        (merged['chamber'] == wafer['chamber']) &
        (merged['wafer_id'] != wafer['wafer_id'])
    ].head(3)

    similar_cases = "\n".join([
        f"- {row['wafer_id']}: {row['defect_type']}, {row['defect_count']}개, {row['location_pattern']}"
        for _, row in similar.iterrows()
    ])

    if not similar_cases:
        similar_cases = "유사 사례 없음"

    # Format prompt
    prompt = format_root_cause_prompt(
        wafer_id=wafer['wafer_id'],
        defect_type=carinthia['defect_type'],
        defect_count=carinthia['defect_count'],
        location_pattern=carinthia['location_pattern'],
        confidence=carinthia['confidence'],
        process_history=process_history,
        sensor_data=sensor_data,
        similar_cases=similar_cases
    )

    print("Generated Prompt:")
    print("-" * 80)
    print(prompt)
    print()


def example_feedback_learning():
    """Example: Feedback learning prompt"""
    print("=" * 80)
    print("Example 3: Feedback Learning Analysis")
    print("=" * 80)

    # Simulate decision feedback data
    rejection_reasons = """
1. 비용 과다 (SEM 검사): 40% (12건)
2. 리스크 평가 낮음: 35% (10건)
3. 다른 검사 방법 선호: 15% (5건)
4. 기타: 10% (3건)
"""

    example_cases = """
[최근 승인 사례]
1. W0001 - AI: INLINE ($150), Engineer: INLINE
   - 이유: "적절한 비용, 명확한 패턴"
   - Confidence: 0.85

2. W0015 - AI: REWORK ($200), Engineer: REWORK
   - 이유: "예방적 조치 필요"
   - Confidence: 0.78

3. W0032 - AI: INLINE ($150), Engineer: INLINE
   - 이유: "과거 유사 케이스에서 효과적"
   - Confidence: 0.82

[최근 거부 사례]
4. W0050 - AI: SEM ($800), Engineer: INLINE ($150)
   - 이유: "SEM 비용 대비 리스크 낮음, INLINE으로 충분"
   - AI Confidence: 0.70

5. W0067 - AI: INLINE ($150), Engineer: PASS
   - 이유: "패턴 불명확, false positive 가능성"
   - AI Confidence: 0.62

6. W0089 - AI: SEM ($800), Engineer: PASS
   - 이유: "월 예산 초과 우려"
   - AI Confidence: 0.75

[최근 수정 사례]
7. W0102 - AI: SEM ($800), Engineer: INLINE ($150)
   - 이유: "비용 절감, INLINE으로도 충분한 정보"
   - AI Confidence: 0.73
"""

    prompt = format_feedback_learning_prompt(
        date_range="2026-01-10 ~ 2026-01-23",
        total_decisions=100,
        approval_rate=0.70,  # 70% approval
        rejection_reasons=rejection_reasons,
        example_cases=example_cases
    )

    print("Generated Prompt:")
    print("-" * 80)
    print(prompt)
    print()


def main():
    """Run all examples"""
    print("\n")
    print("=" * 80)
    print("Korean Prompt Templates - Example Usage")
    print("=" * 80)
    print()

    # Load environment
    load_dotenv()

    try:
        # Run examples
        example_pattern_discovery()
        example_root_cause_analysis()
        example_feedback_learning()

        print("=" * 80)
        print("✅ All prompt examples generated successfully!")
        print()
        print("Next steps:")
        print("  1. Use these prompts with LLMClient for actual analysis")
        print("  2. Prompts are logged to logs/pattern_discovery/, logs/root_cause_analysis/")
        print("  3. Korean prompts provide better context understanding for Korean manufacturing data")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
