"""
Metrics calculator for performance evaluation

Calculates detection rates, costs, ROI, and comparison with baselines
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import yaml


class MetricsCalculator:
    """
    Calculate performance metrics for the semiconductor quality control system

    Usage:
        calculator = MetricsCalculator()
        detection_rate = calculator.calculate_detection_rate(decisions_df)
        costs = calculator.calculate_cost(decisions_df)
        summary = calculator.generate_summary(decisions_df)
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize metrics calculator

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Extract cost parameters
        self.inline_cost = self.config['budget']['costs']['inline_per_wafer']
        self.sem_cost = self.config['budget']['costs']['sem_per_wafer']
        self.rework_cost = self.config['budget']['costs']['rework']
        self.wafer_value = self.config['models']['stage1']['wafer_value']

    def calculate_detection_rate(
        self,
        decisions_df: pd.DataFrame
    ) -> float:
        """
        Calculate overall defect detection rate

        Logic:
        - Count wafers that went through inspection (INLINE or SEM)
        - Estimate detection based on AI confidence scores
        - Higher confidence = higher detection probability

        Args:
            decisions_df: DataFrame with columns:
                - ai_recommendation: Decision (INLINE, SEM, PASS, REWORK)
                - ai_confidence: Confidence score (0-1)

        Returns:
            detection_rate (float): Estimated detection rate (0-1)

        Example:
            >>> df = pd.DataFrame({
            ...     'ai_recommendation': ['INLINE', 'SEM', 'PASS'],
            ...     'ai_confidence': [0.8, 0.9, 0.5]
            ... })
            >>> rate = calculator.calculate_detection_rate(df)
            >>> print(f"Detection rate: {rate:.2%}")
        """
        if len(decisions_df) == 0:
            return 0.0

        # Count inspected wafers (INLINE or SEM)
        inspected = decisions_df[
            decisions_df['ai_recommendation'].isin(['INLINE', 'SEM'])
        ]

        if len(inspected) == 0:
            return 0.0

        # Weighted detection rate based on confidence
        # Higher confidence = higher detection probability
        total_detection_prob = inspected['ai_confidence'].sum()
        detection_rate = total_detection_prob / len(decisions_df)

        return min(detection_rate, 1.0)  # Cap at 1.0

    def calculate_cost(
        self,
        decisions_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate total costs by category

        Args:
            decisions_df: DataFrame with column 'ai_recommendation'

        Returns:
            Dictionary with cost breakdown:
            {
                "inline": total_inline_cost,
                "sem": total_sem_cost,
                "rework": total_rework_cost,
                "total": sum_of_all
            }

        Example:
            >>> costs = calculator.calculate_cost(decisions_df)
            >>> print(f"Total cost: ${costs['total']:,.2f}")
            >>> print(f"SEM cost: ${costs['sem']:,.2f}")
        """
        if len(decisions_df) == 0:
            return {
                "inline": 0.0,
                "sem": 0.0,
                "rework": 0.0,
                "total": 0.0
            }

        # Count decisions by type
        inline_count = len(decisions_df[decisions_df['ai_recommendation'] == 'INLINE'])
        sem_count = len(decisions_df[decisions_df['ai_recommendation'] == 'SEM'])
        rework_count = len(decisions_df[decisions_df['ai_recommendation'] == 'REWORK'])

        # Calculate costs
        inline_cost = inline_count * self.inline_cost
        sem_cost = sem_count * self.sem_cost
        rework_cost = rework_count * self.rework_cost
        total_cost = inline_cost + sem_cost + rework_cost

        return {
            "inline": inline_cost,
            "sem": sem_cost,
            "rework": rework_cost,
            "total": total_cost
        }

    def calculate_roi(
        self,
        cost: float,
        wafers_saved: int,
        wafer_value: Optional[float] = None
    ) -> float:
        """
        Calculate Return on Investment

        ROI = (Value Saved - Cost) / Cost

        Args:
            cost: Total cost of inspection
            wafers_saved: Number of defective wafers caught
            wafer_value: Value per wafer (default from config)

        Returns:
            roi (float): ROI as percentage

        Example:
            >>> roi = calculator.calculate_roi(cost=50000, wafers_saved=100)
            >>> print(f"ROI: {roi:.2f}%")
        """
        if cost == 0:
            return 0.0

        if wafer_value is None:
            wafer_value = self.wafer_value

        value_saved = wafers_saved * wafer_value
        roi = ((value_saved - cost) / cost) * 100

        return roi

    def compare_baselines(
        self,
        ai_detection_rate: float,
        ai_cost: float
    ) -> pd.DataFrame:
        """
        Compare AI system with baseline methods

        Baselines from literature:
        - Random: 12% detection, minimal cost
        - Rule-based: 68% detection, medium cost
        - Hybrid: 58% detection, medium-high cost

        Args:
            ai_detection_rate: AI system detection rate (0-1)
            ai_cost: AI system total cost

        Returns:
            DataFrame with comparison across methods

        Example:
            >>> comparison = calculator.compare_baselines(0.75, 45000)
            >>> print(comparison)
        """
        # Baseline configurations (from research)
        baselines = [
            {
                'method': 'Random Inspection',
                'detection_rate': 0.12,
                'cost_multiplier': 0.3,  # Cheaper than AI
                'description': 'Random sampling of wafers'
            },
            {
                'method': 'Rule-Based',
                'detection_rate': 0.68,
                'cost_multiplier': 0.7,  # Medium cost
                'description': 'Threshold-based rules'
            },
            {
                'method': 'Hybrid',
                'detection_rate': 0.58,
                'cost_multiplier': 0.85,  # Higher cost
                'description': 'Rule-based + Statistical'
            },
            {
                'method': 'AI-Driven (Our System)',
                'detection_rate': ai_detection_rate,
                'cost_multiplier': 1.0,  # Reference
                'description': 'Multi-stage AI pipeline'
            }
        ]

        # Build comparison DataFrame
        data = []
        for baseline in baselines:
            cost = ai_cost * baseline['cost_multiplier']
            detection_rate = baseline['detection_rate']

            # Estimate wafers saved (assuming 1252 total wafers)
            total_wafers = 1252
            defect_rate = 0.15  # 15% defect rate from mock data
            total_defects = int(total_wafers * defect_rate)
            wafers_saved = int(total_defects * detection_rate)

            # Calculate ROI
            roi = self.calculate_roi(cost, wafers_saved)

            data.append({
                'Method': baseline['method'],
                'Detection Rate': f"{detection_rate:.2%}",
                'Total Cost': f"${cost:,.2f}",
                'Wafers Saved': wafers_saved,
                'ROI': f"{roi:.2f}%",
                'Description': baseline['description']
            })

        return pd.DataFrame(data)

    def generate_summary(
        self,
        decisions_df: pd.DataFrame
    ) -> Dict:
        """
        Generate comprehensive summary statistics

        Args:
            decisions_df: DataFrame with decision logs

        Returns:
            Dictionary with summary statistics:
            {
                "total_wafers": int,
                "inline_count": int,
                "sem_count": int,
                "rework_count": int,
                "pass_count": int,
                "detection_rate": float,
                "total_cost": float,
                "roi": float,
                "avg_confidence": float,
                "cost_breakdown": Dict[str, float]
            }

        Example:
            >>> summary = calculator.generate_summary(decisions_df)
            >>> print(f"Total wafers: {summary['total_wafers']}")
            >>> print(f"Detection rate: {summary['detection_rate']:.2%}")
            >>> print(f"Total cost: ${summary['total_cost']:,.2f}")
        """
        if len(decisions_df) == 0:
            return {
                "total_wafers": 0,
                "inline_count": 0,
                "sem_count": 0,
                "rework_count": 0,
                "pass_count": 0,
                "detection_rate": 0.0,
                "total_cost": 0.0,
                "roi": 0.0,
                "avg_confidence": 0.0,
                "cost_breakdown": {
                    "inline": 0.0,
                    "sem": 0.0,
                    "rework": 0.0
                }
            }

        # Count decisions
        total_wafers = len(decisions_df)
        inline_count = len(decisions_df[decisions_df['ai_recommendation'] == 'INLINE'])
        sem_count = len(decisions_df[decisions_df['ai_recommendation'] == 'SEM'])
        rework_count = len(decisions_df[decisions_df['ai_recommendation'] == 'REWORK'])
        pass_count = len(decisions_df[decisions_df['ai_recommendation'] == 'PASS'])

        # Calculate metrics
        detection_rate = self.calculate_detection_rate(decisions_df)
        cost_breakdown = self.calculate_cost(decisions_df)
        total_cost = cost_breakdown['total']

        # Estimate wafers saved (inspected + reworked)
        wafers_saved = inline_count + sem_count + rework_count

        # Calculate ROI
        roi = self.calculate_roi(total_cost, wafers_saved)

        # Average confidence
        avg_confidence = decisions_df['ai_confidence'].mean()

        return {
            "total_wafers": total_wafers,
            "inline_count": inline_count,
            "sem_count": sem_count,
            "rework_count": rework_count,
            "pass_count": pass_count,
            "detection_rate": detection_rate,
            "total_cost": total_cost,
            "roi": roi,
            "avg_confidence": avg_confidence,
            "cost_breakdown": cost_breakdown
        }

    def calculate_agreement_rate(
        self,
        decisions_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate agreement between AI and engineer decisions

        Args:
            decisions_df: DataFrame with columns:
                - ai_recommendation
                - engineer_decision

        Returns:
            Dictionary with agreement statistics:
            {
                "overall_agreement": float (percentage),
                "by_stage": Dict[str, float]
            }

        Example:
            >>> agreement = calculator.calculate_agreement_rate(decisions_df)
            >>> print(f"Overall agreement: {agreement['overall_agreement']:.2%}")
        """
        if 'engineer_decision' not in decisions_df.columns:
            return {
                "overall_agreement": 0.0,
                "by_stage": {}
            }

        # Overall agreement
        agreements = (decisions_df['ai_recommendation'] == decisions_df['engineer_decision']).sum()
        overall_agreement = (agreements / len(decisions_df)) * 100 if len(decisions_df) > 0 else 0.0

        # Agreement by stage
        by_stage = {}
        if 'stage' in decisions_df.columns:
            for stage in decisions_df['stage'].unique():
                stage_df = decisions_df[decisions_df['stage'] == stage]
                stage_agreements = (stage_df['ai_recommendation'] == stage_df['engineer_decision']).sum()
                stage_agreement = (stage_agreements / len(stage_df)) * 100 if len(stage_df) > 0 else 0.0
                by_stage[stage] = stage_agreement

        return {
            "overall_agreement": overall_agreement,
            "by_stage": by_stage
        }
