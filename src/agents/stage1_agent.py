"""
Stage 1 Agent: Wafer Yield Prediction and Rework Decision

Uses XGBoost to predict wafer yield and make economic recommendations
Currently using mock model - will be replaced with STEP 2 team's model

Decision: PROCEED (use as-is), REWORK (re-process), or SCRAP (discard)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from src.agents.base_agent import BaseAgent


class Stage1Agent(BaseAgent):
    """
    Stage 1: Predict wafer yield and recommend action

    Model: XGBoost (from STEP 2 team)
    Input: 10 sensors + 4 inline measurements (optional from Stage 0)
    Output: PROCEED, REWORK, or SCRAP recommendation

    Economic Optimization:
    - PROCEED: Use wafer as-is (value = predicted_yield * wafer_value)
    - REWORK: Re-process to improve yield (value = improved_yield * wafer_value - rework_cost)
    - SCRAP: Discard wafer (value = 0)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Stage 1 Agent

        Args:
            config: Full configuration dictionary (must include models.stage1)
        """
        # Extract stage1 config
        stage1_config = config['models']['stage1']

        # Initialize base agent
        super().__init__(
            stage_name="stage1",
            config=stage1_config
        )

        # Get economic parameters
        self.wafer_value = self.get_config_value('wafer_value', 1000)
        self.rework_cost = self.get_config_value('rework_cost', 200)

        self.logger.info(
            f"Stage1Agent initialized: "
            f"wafer_value=${self.wafer_value}, "
            f"rework_cost=${self.rework_cost}"
        )

    def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
        """
        Predict wafer yield using XGBoost

        Args:
            wafer_data: Single wafer data as pandas Series with:
                - wafer_id: str
                - etch_rate, pressure, temperature, rf_power, gas_flow: float
                - sensor6, sensor7, sensor8, sensor9, sensor10: float
                - Optional inline data (cd, overlay, thickness, uniformity)

        Returns:
            Dictionary with:
                - predicted_yield: float (0-1)
                - yield_lower: float (lower confidence bound)
                - yield_upper: float (upper confidence bound)
                - uncertainty: float
                - has_inline_data: bool
                - inline_issues: list of detected issues
        """
        # Extract sensor values
        sensor_keys = [
            'etch_rate', 'pressure', 'temperature', 'rf_power',
            'gas_flow', 'sensor6', 'sensor7', 'sensor8',
            'sensor9', 'sensor10'
        ]

        sensor_values = [float(wafer_data[k]) for k in sensor_keys]

        # Check for inline data (from Stage 0 inspection)
        inline_keys = ['cd', 'overlay', 'thickness', 'uniformity']
        # Handle both dict and Series
        if isinstance(wafer_data, pd.Series):
            has_inline = all(k in wafer_data.index for k in inline_keys)
        else:  # dict
            has_inline = all(k in wafer_data for k in inline_keys)

        if has_inline:
            inline_values = [float(wafer_data[k]) for k in inline_keys]
            self.logger.debug(f"Wafer {wafer_data['wafer_id']}: Using inline data")
        else:
            # No inline data - use zeros as placeholder
            inline_values = [0.0, 0.0, 0.0, 0.0]
            self.logger.debug(f"Wafer {wafer_data['wafer_id']}: No inline data available")

        # Combine features: 10 sensors + 4 inline = 14 features
        X = np.array([sensor_values + inline_values])

        # Predict yield using XGBoost
        if self.model is not None:
            predicted_yield = float(self.model.predict(X)[0])

            # Clip to valid range [0, 1]
            predicted_yield = np.clip(predicted_yield, 0.0, 1.0)

            # Estimate uncertainty
            # Lower uncertainty if we have inline data
            uncertainty = 0.05 if has_inline else 0.10

            yield_lower = max(0.0, predicted_yield - uncertainty)
            yield_upper = min(1.0, predicted_yield + uncertainty)

            self.logger.debug(
                f"Wafer {wafer_data['wafer_id']}: "
                f"predicted_yield={predicted_yield:.3f}, "
                f"uncertainty={uncertainty:.3f}"
            )
        else:
            # Fallback if no model
            self.logger.warning("No model available - using random prediction")
            predicted_yield = np.random.uniform(0.5, 0.9)
            uncertainty = 0.10
            yield_lower = max(0.0, predicted_yield - uncertainty)
            yield_upper = min(1.0, predicted_yield + uncertainty)

        # Check for inline issues (if inline data available)
        inline_issues = []
        if has_inline:
            # CD (Critical Dimension) spec: 7.0 ± 0.3 nm
            cd = wafer_data['cd']
            if abs(cd - 7.0) > 0.3:
                inline_issues.append(f"CD deviation: {cd:.2f}nm (spec: 7.0±0.3)")

            # Overlay spec: < 3.0 nm
            overlay = wafer_data['overlay']
            if overlay > 3.0:
                inline_issues.append(f"Overlay error: {overlay:.2f}nm (spec: <3.0)")

            # Thickness spec: 100 ± 5 nm
            thickness = wafer_data['thickness']
            if abs(thickness - 100) > 5:
                inline_issues.append(f"Thickness deviation: {thickness:.1f}nm (spec: 100±5)")

            # Uniformity spec: < 2.0%
            uniformity = wafer_data['uniformity']
            if uniformity > 2.0:
                inline_issues.append(f"Poor uniformity: {uniformity:.2f}% (spec: <2.0)")

        return {
            'predicted_yield': float(predicted_yield),
            'yield_lower': float(yield_lower),
            'yield_upper': float(yield_upper),
            'uncertainty': float(uncertainty),
            'has_inline_data': has_inline,
            'inline_issues': inline_issues
        }

    def make_recommendation(
        self,
        wafer_data: pd.Series,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate economic recommendation: PROCEED, REWORK, or SCRAP

        Args:
            wafer_data: Single wafer data as pandas Series
            analysis_result: Output from analyze()

        Returns:
            Dictionary with:
                - action: 'PROCEED', 'REWORK', or 'SCRAP'
                - confidence: float (0-1)
                - reasoning: str
                - estimated_cost: float (USD)
                - expected_value: float (USD)
                - expected_yield: float (0-1)
                - alternatives: list of alternative actions
        """
        predicted_yield = analysis_result['predicted_yield']
        uncertainty = analysis_result['uncertainty']
        has_inline = analysis_result['has_inline_data']
        issues = analysis_result['inline_issues']

        # Calculate economic value for each option

        # Option A: PROCEED (use wafer as-is)
        value_proceed = predicted_yield * self.wafer_value

        # Option B: REWORK (re-process to fix issues)
        # Estimate rework improvement based on issues
        if len(issues) > 0:
            # If we have specific issues, rework can significantly improve
            rework_improvement = 0.15  # 15 percentage points
        else:
            # No specific issues identified, smaller improvement potential
            rework_improvement = 0.05  # 5 percentage points

        expected_yield_after_rework = min(0.95, predicted_yield + rework_improvement)
        value_rework = (expected_yield_after_rework * self.wafer_value) - self.rework_cost

        # Option C: SCRAP (discard wafer)
        value_scrap = 0.0

        # Choose optimal action based on expected value
        options = {
            'PROCEED': value_proceed,
            'REWORK': value_rework,
            'SCRAP': value_scrap
        }

        optimal_action = max(options, key=options.get)
        optimal_value = options[optimal_action]

        # Calculate confidence based on uncertainty and data availability
        if uncertainty < 0.05 and has_inline:
            confidence = 0.90
        elif uncertainty < 0.10:
            confidence = 0.75
        else:
            confidence = 0.60

        # Generate reasoning
        reasons = []
        reasons.append(f"Predicted yield: {predicted_yield:.1%}")

        if has_inline:
            reasons.append("Inline data available")
        else:
            reasons.append("No inline data (higher uncertainty)")

        if len(issues) > 0:
            reasons.append(f"{len(issues)} issue(s) detected: {', '.join(issues)}")

        reasons.append(
            f"Economic values - PROCEED: ${value_proceed:.0f}, "
            f"REWORK: ${value_rework:.0f}, SCRAP: $0"
        )
        reasons.append(f"Optimal action: {optimal_action} (expected value: ${optimal_value:.0f})")

        reasoning = " | ".join(reasons)

        # Calculate cost
        cost = self.rework_cost if optimal_action == 'REWORK' else 0.0

        # Determine expected yield after action
        if optimal_action == 'REWORK':
            expected_yield = expected_yield_after_rework
        elif optimal_action == 'PROCEED':
            expected_yield = predicted_yield
        else:  # SCRAP
            expected_yield = 0.0

        # Build alternatives
        alternatives = []
        for action, value in options.items():
            if action != optimal_action:
                alternatives.append({
                    'action': action,
                    'expected_value': float(value),
                    'description': self._get_action_description(
                        action, value, predicted_yield, expected_yield_after_rework
                    )
                })

        self.logger.info(
            f"Stage1 recommendation for {wafer_data['wafer_id']}: "
            f"{optimal_action} (confidence={confidence:.2f}, "
            f"predicted_yield={predicted_yield:.2%})"
        )

        return {
            'action': optimal_action,
            'confidence': float(confidence),
            'reasoning': reasoning,
            'estimated_cost': float(cost),
            'expected_value': float(optimal_value),
            'expected_yield': float(expected_yield),
            'alternatives': alternatives
        }

    def _get_action_description(
        self,
        action: str,
        value: float,
        current_yield: float,
        rework_yield: float
    ) -> str:
        """
        Generate description for alternative action

        Args:
            action: Action name
            value: Expected value for this action
            current_yield: Current predicted yield
            rework_yield: Expected yield after rework

        Returns:
            Description string
        """
        if action == 'PROCEED':
            return (
                f"Use wafer as-is with {current_yield:.1%} yield "
                f"(expected value: ${value:.0f})"
            )
        elif action == 'REWORK':
            return (
                f"Re-process to improve yield from {current_yield:.1%} to {rework_yield:.1%} "
                f"(net value: ${value:.0f} after ${self.rework_cost} cost)"
            )
        elif action == 'SCRAP':
            return "Discard wafer (value: $0)"
        return ""
