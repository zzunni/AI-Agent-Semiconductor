"""
Example usage of LLMClient for Claude API integration

This demonstrates how to use the LLMClient for various tasks
in the semiconductor quality control system.

Note: Requires valid ANTHROPIC_API_KEY in .env file
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from dotenv import load_dotenv
from src.llm.client import LLMClient


def example_pattern_discovery():
    """Example: Pattern discovery analysis"""
    print("=" * 80)
    print("Example 1: Pattern Discovery")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize client
    client = LLMClient(config['llm'])

    # Pattern discovery prompt
    prompt = """
    Analyze this defect pattern data from wafer etching:

    - Wafer W0025: Edge-Ring pattern, severity 0.85, etch_rate 3.95
    - Wafer W0026: Edge-Ring pattern, severity 0.82, etch_rate 3.91
    - Wafer W0036: Edge-Ring pattern, severity 0.88, etch_rate 4.01

    What is the likely root cause, and what corrective action would you recommend?
    Provide your answer in 2-3 sentences.
    """

    response = client.complete(
        prompt=prompt,
        system="You are an expert in semiconductor defect analysis and root cause investigation.",
        category="pattern_discovery",
        metadata={
            "wafer_count": 3,
            "pattern_type": "Edge-Ring"
        }
    )

    print("Prompt:")
    print(prompt)
    print("\nResponse:")
    print(response)
    print()


def example_root_cause_analysis():
    """Example: Root cause analysis"""
    print("=" * 80)
    print("Example 2: Root Cause Analysis")
    print("=" * 80)

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    client = LLMClient(config['llm'])

    prompt = """
    A semiconductor fab is experiencing increased Particle defects on wafers from Chamber A.

    Data:
    - Chamber A: 487 particle defects (38.9% of wafers)
    - Chamber B: 156 particle defects (12.5% of wafers)
    - Chamber C: 134 particle defects (10.7% of wafers)

    Particle defects correlate with pressure readings > 158 mTorr.

    What are the top 3 most likely root causes, and what diagnostic steps would you recommend?
    """

    response = client.complete(
        prompt=prompt,
        category="root_cause_analysis",
        metadata={
            "chamber": "A",
            "defect_type": "Particle"
        }
    )

    print("Analysis:")
    print(response)
    print()


def example_with_retry():
    """Example: Using retry logic for reliability"""
    print("=" * 80)
    print("Example 3: Complete with Retry")
    print("=" * 80)

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    client = LLMClient(config['llm'])

    prompt = "In one sentence, what causes Center defect patterns in wafer etching?"

    # Use retry logic for robustness
    response = client.complete_with_retry(
        prompt=prompt,
        max_retries=5,
        category="pattern_discovery"
    )

    print(f"Response: {response}")
    print()


def example_structured_output():
    """Example: Requesting structured output"""
    print("=" * 80)
    print("Example 4: Structured Output")
    print("=" * 80)

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    client = LLMClient(config['llm'])

    prompt = """
    List the 5 most common defect types in semiconductor wafer fabrication.
    """

    response = client.complete_structured(
        prompt=prompt,
        expected_format="numbered list with defect name and one-sentence description",
        category="general"
    )

    print("Structured response:")
    print(response)
    print()


def example_batch_processing():
    """Example: Batch processing multiple wafers"""
    print("=" * 80)
    print("Example 5: Batch Processing")
    print("=" * 80)

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    client = LLMClient(config['llm'])

    # Analyze multiple wafers
    wafer_prompts = [
        "Wafer W0001: Edge-Ring pattern, severity 0.75. Recommend action in one sentence.",
        "Wafer W0002: Center pattern, severity 0.60. Recommend action in one sentence.",
        "Wafer W0003: Random pattern, severity 0.45. Recommend action in one sentence."
    ]

    responses = client.batch_complete(
        prompts=wafer_prompts,
        delay=1.0,  # 1 second between requests
        category="pattern_discovery"
    )

    for i, (prompt, response) in enumerate(zip(wafer_prompts, responses), 1):
        print(f"Wafer {i}:")
        print(f"  Prompt: {prompt}")
        print(f"  Response: {response}")
        print()


def main():
    """Run all examples"""
    print("\n")
    print("=" * 80)
    print("LLMClient Example Usage")
    print("=" * 80)
    print()

    # Load environment
    load_dotenv()

    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in .env file")
        print("   Please add your API key to .env")
        return

    print(f"✓ API key found: {api_key[:20]}...")
    print()

    try:
        # Run examples (comment out as needed)
        example_pattern_discovery()
        # example_root_cause_analysis()
        # example_with_retry()
        # example_structured_output()
        # example_batch_processing()

        print("=" * 80)
        print("✅ Examples completed!")
        print()
        print("Check logs/pattern_discovery/ for conversation logs")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
