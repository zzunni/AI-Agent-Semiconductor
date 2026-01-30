"""
Stage 2A: WAT (Wafer Acceptance Test) Analyzer Agent

Purpose: LOT-level electrical analysis → LOT SCRAP decision support
Phase: Phase 2 (Post-Fab)
Input: LOT-level WAT electrical measurement data
Output: LOT_PROCEED / LOT_SCRAP
"""

from .base_agent import BaseAgent
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


class Stage2AAgent(BaseAgent):
    """
    Stage 2A: WAT Electrical Analysis

    Analyzes LOT-level electrical characteristics from WAT
    Makes LOT_PROCEED / LOT_SCRAP decisions

    Key Features:
    - LOT-level analysis (not individual wafers)
    - Electrical parameter validation (vth, idsat, resistance, etc.)
    - Spec violation detection
    - Uniformity analysis
    - Economic decision-making
    """

    def __init__(self, model_config: Dict[str, Any], full_config: Dict[str, Any]):
        """
        Initialize Stage 2A Agent

        Args:
            model_config: Stage 2A specific configuration
            full_config: Full system configuration
        """
        super().__init__('stage2a', full_config)

        # Load model if path specified
        model_path = model_config.get('path')
        if model_path:
            self.model = self._load_model(model_path)
        else:
            self.model = None
            self.logger.warning("No model path specified for Stage 2A")

        # Load configuration
        self.model_config = model_config
        self.lot_scrap_cost = model_config.get('lot_scrap_cost', 500000)
        self.wafer_value = model_config.get('wafer_value', 20000)
        self.wafers_per_lot = model_config.get('wafers_per_lot', 25)

        # Load spec limits
        self.spec_limits = model_config.get('spec_limits', {})

        # Critical parameters that must pass
        self.critical_params = model_config.get('critical_params', [
            'vth_nmos', 'vth_pmos', 'idsat_nmos', 'idsat_pmos'
        ])

        # Uniformity thresholds
        self.uniformity_threshold = model_config.get('uniformity_threshold', 0.10)  # 10% CV

        self.logger.info(
            f"Stage2AAgent initialized: "
            f"lot_scrap_cost=${self.lot_scrap_cost:,}, "
            f"wafer_value=${self.wafer_value:,}, "
            f"wafers_per_lot={self.wafers_per_lot}"
        )

    def analyze(self, lot_id: str, wat_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze LOT-level WAT electrical data

        Args:
            lot_id: LOT identifier
            wat_data: DataFrame with WAT measurements for all wafers in LOT
                Columns: wafer_id, vth_nmos, vth_pmos, idsat_nmos, idsat_pmos,
                         contact_resistance, sheet_resistance, breakdown_voltage, etc.

        Returns:
            Dictionary with electrical analysis results
        """
        self.logger.info(f"Analyzing LOT {lot_id} with {len(wat_data)} wafers")

        wafer_count = len(wat_data)

        # Extract WAT parameters (excluding wafer_id)
        wat_params = [col for col in wat_data.columns if col != 'wafer_id']

        # 1. Spec violation check
        spec_violations = self._check_spec_violations(wat_data, wat_params)
        violation_count = len(spec_violations)
        critical_violation = self._has_critical_violation(spec_violations)

        # 2. Uniformity analysis
        uniformity_score = self._calculate_uniformity(wat_data, wat_params)

        # 3. Electrical quality prediction (using mock model)
        electrical_quality, quality_confidence = self._predict_electrical_quality(
            wat_data, wat_params
        )

        # 4. Risk assessment
        risk_level = self._assess_risk(
            electrical_quality,
            violation_count,
            critical_violation,
            uniformity_score
        )

        # 5. Yield loss estimation
        estimated_yield_loss = self._estimate_yield_loss(
            violation_count,
            uniformity_score,
            critical_violation
        )

        self.logger.info(
            f"LOT {lot_id} analysis: quality={electrical_quality}, "
            f"violations={violation_count}, uniformity={uniformity_score:.3f}, "
            f"risk={risk_level}"
        )

        return {
            'lot_id': lot_id,
            'wafer_count': wafer_count,

            # Electrical analysis
            'electrical_quality': electrical_quality,
            'quality_confidence': float(quality_confidence),
            'risk_level': risk_level,
            'uniformity_score': float(uniformity_score),

            # Spec violations
            'spec_violations': spec_violations,
            'violation_count': violation_count,
            'critical_violation': critical_violation,

            # Yield estimation
            'estimated_yield_loss': float(estimated_yield_loss),

            # WAT parameter summary
            'wat_summary': self._summarize_wat_params(wat_data, wat_params)
        }

    def make_recommendation(
        self,
        lot_id: str,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make LOT_PROCEED / LOT_SCRAP recommendation

        Args:
            lot_id: LOT identifier
            analysis_result: Results from analyze()

        Returns:
            Dictionary with recommendation and reasoning
        """
        # Economic analysis
        estimated_yield_loss = analysis_result['estimated_yield_loss']
        wafer_count = analysis_result['wafer_count']

        # Loss if we proceed
        expected_loss_if_proceed = estimated_yield_loss * wafer_count * self.wafer_value

        # Cost if we scrap
        lot_scrap_cost = self.lot_scrap_cost

        # Net benefit of scrapping
        net_benefit_of_scrap = expected_loss_if_proceed - lot_scrap_cost

        # Decision logic
        critical_violation = analysis_result['critical_violation']
        electrical_quality = analysis_result['electrical_quality']
        risk_level = analysis_result['risk_level']
        uniformity_score = analysis_result['uniformity_score']

        # Decision rules
        if critical_violation:
            # Always scrap if critical parameter fails
            action = 'LOT_SCRAP'
            confidence = 'HIGH'
            reasoning = (
                f"Critical electrical parameter violation detected. "
                f"LOT must be scrapped to prevent yield loss downstream."
            )
        elif electrical_quality == 'FAIL':
            # Scrap if quality prediction is FAIL
            action = 'LOT_SCRAP'
            confidence = 'HIGH'
            reasoning = (
                f"Electrical quality prediction: FAIL. "
                f"{analysis_result['violation_count']} spec violations detected. "
                f"Expected loss if proceed: ${expected_loss_if_proceed:,.0f}"
            )
        elif risk_level == 'HIGH':
            # High risk → likely scrap
            if net_benefit_of_scrap > 0:
                action = 'LOT_SCRAP'
                confidence = 'MEDIUM'
                reasoning = (
                    f"High risk LOT with poor uniformity (score={uniformity_score:.3f}). "
                    f"Economic analysis favors scrapping: "
                    f"Net benefit = ${net_benefit_of_scrap:,.0f}"
                )
            else:
                action = 'LOT_PROCEED'
                confidence = 'LOW'
                reasoning = (
                    f"High risk LOT, but scrapping cost (${lot_scrap_cost:,.0f}) "
                    f"exceeds expected loss (${expected_loss_if_proceed:,.0f}). "
                    f"Recommend proceed with caution."
                )
        else:
            # Low/Medium risk → proceed
            action = 'LOT_PROCEED'
            confidence = 'HIGH' if risk_level == 'LOW' else 'MEDIUM'
            reasoning = (
                f"Electrical quality: {electrical_quality}. "
                f"Risk: {risk_level}. "
                f"Uniformity: {uniformity_score:.3f}. "
                f"Safe to proceed to Stage 2B."
            )

        # Determine which wafers proceed to Stage 2B
        if action == 'LOT_PROCEED':
            # All wafers proceed if LOT passes
            proceed_to_stage2b = True
            wafer_list_for_stage2b = list(range(wafer_count))
        else:
            # No wafers proceed if LOT is scrapped
            proceed_to_stage2b = False
            wafer_list_for_stage2b = []

        # Estimated cost (scrap cost if scrapping, otherwise $0)
        estimated_cost = lot_scrap_cost if action == 'LOT_SCRAP' else 0

        self.logger.info(
            f"Stage2A recommendation for LOT {lot_id}: {action} "
            f"(confidence={confidence}, cost=${estimated_cost:,.0f})"
        )

        return {
            'lot_id': lot_id,
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning,

            # Economic details
            'estimated_cost': estimated_cost,
            'lot_scrap_cost': lot_scrap_cost,
            'expected_loss_if_proceed': expected_loss_if_proceed,
            'net_benefit_of_scrap': net_benefit_of_scrap,

            # Stage 2B routing
            'proceed_to_stage2b': proceed_to_stage2b,
            'wafer_list_for_stage2b': wafer_list_for_stage2b,
            'wafer_count': wafer_count,

            # For logging
            'stage': 'stage2a',
            'timestamp': pd.Timestamp.now().isoformat()
        }

    def _check_spec_violations(
        self,
        wat_data: pd.DataFrame,
        wat_params: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Check for spec violations across all wafers

        Returns:
            List of violations with details
        """
        violations = []

        for param in wat_params:
            if param not in self.spec_limits:
                continue

            lower, upper = self.spec_limits[param]

            # Check each wafer
            for idx, row in wat_data.iterrows():
                value = row[param]

                if value < lower or value > upper:
                    violations.append({
                        'parameter': param,
                        'wafer_id': row.get('wafer_id', f'W{idx}'),
                        'value': float(value),
                        'lower_limit': lower,
                        'upper_limit': upper,
                        'severity': 'CRITICAL' if param in self.critical_params else 'MINOR'
                    })

        return violations

    def _has_critical_violation(self, violations: List[Dict[str, Any]]) -> bool:
        """Check if any critical parameters have violations"""
        return any(v['severity'] == 'CRITICAL' for v in violations)

    def _calculate_uniformity(
        self,
        wat_data: pd.DataFrame,
        wat_params: List[str]
    ) -> float:
        """
        Calculate LOT uniformity score

        Returns:
            Uniformity score (0-1, higher is better)
            Based on coefficient of variation (CV) across wafers
        """
        cvs = []

        for param in wat_params:
            values = wat_data[param].values
            mean = np.mean(values)
            std = np.std(values)

            if mean != 0:
                cv = std / abs(mean)
                cvs.append(cv)

        # Average CV across all parameters
        avg_cv = np.mean(cvs) if cvs else 0

        # Convert to uniformity score (0-1)
        # Lower CV = higher uniformity
        # Use a gentler scaling: 1 at CV=0, decreasing to 0 at CV=threshold*2
        if avg_cv == 0:
            uniformity = 1.0
        elif avg_cv < self.uniformity_threshold:
            # Good uniformity: 0.7 to 1.0
            uniformity = 0.7 + 0.3 * (1 - avg_cv / self.uniformity_threshold)
        else:
            # Poor uniformity: 0.0 to 0.7
            uniformity = max(0, 0.7 * (1 - (avg_cv - self.uniformity_threshold) / self.uniformity_threshold))

        return uniformity

    def _predict_electrical_quality(
        self,
        wat_data: pd.DataFrame,
        wat_params: List[str]
    ) -> tuple:
        """
        Predict electrical quality using model

        Returns:
            (quality: 'PASS'/'FAIL', confidence: float)
        """
        if self.model is None:
            # Fallback: simple rule-based
            # PASS if no critical violations and good uniformity
            uniformity = self._calculate_uniformity(wat_data, wat_params)
            violations = self._check_spec_violations(wat_data, wat_params)
            critical = self._has_critical_violation(violations)

            if critical or uniformity < 0.7:
                return 'FAIL', 0.6
            else:
                return 'PASS', 0.8

        # Use model for prediction
        try:
            # Extract features: mean, std, min, max for each parameter
            features = []
            for param in wat_params:
                features.extend([
                    wat_data[param].mean(),
                    wat_data[param].std(),
                    wat_data[param].min(),
                    wat_data[param].max()
                ])

            X = np.array(features).reshape(1, -1)

            # Predict
            prediction = self.model.predict(X)[0]

            # Get confidence if available
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                confidence = float(max(proba))
            else:
                confidence = 0.7

            quality = 'PASS' if prediction == 1 else 'FAIL'

            return quality, confidence

        except Exception as e:
            self.logger.warning(f"Model prediction failed: {e}, using fallback")
            # Fallback
            return 'PASS', 0.5

    def _assess_risk(
        self,
        electrical_quality: str,
        violation_count: int,
        critical_violation: bool,
        uniformity_score: float
    ) -> str:
        """
        Assess overall risk level

        Returns:
            'HIGH', 'MEDIUM', or 'LOW'
        """
        if critical_violation:
            return 'HIGH'

        if electrical_quality == 'FAIL':
            return 'HIGH'

        if violation_count > 10:
            return 'HIGH'

        if uniformity_score < 0.6:
            return 'HIGH'

        if violation_count > 5 or uniformity_score < 0.8:
            return 'MEDIUM'

        return 'LOW'

    def _estimate_yield_loss(
        self,
        violation_count: int,
        uniformity_score: float,
        critical_violation: bool
    ) -> float:
        """
        Estimate yield loss percentage (0-1)

        Based on electrical issues
        """
        if critical_violation:
            # Critical violations likely mean complete yield loss
            return 0.9  # 90% yield loss

        # Base yield loss from violations
        violation_loss = min(0.5, violation_count * 0.02)  # 2% per violation, max 50%

        # Uniformity impact
        uniformity_loss = max(0, (0.8 - uniformity_score) * 0.5)

        # Total estimated yield loss
        total_loss = min(0.95, violation_loss + uniformity_loss)

        return total_loss

    def _summarize_wat_params(
        self,
        wat_data: pd.DataFrame,
        wat_params: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Summarize WAT parameters with statistics

        Returns:
            Dict of {param: {mean, std, min, max}}
        """
        summary = {}

        for param in wat_params:
            summary[param] = {
                'mean': float(wat_data[param].mean()),
                'std': float(wat_data[param].std()),
                'min': float(wat_data[param].min()),
                'max': float(wat_data[param].max()),
                'cv': float(wat_data[param].std() / wat_data[param].mean())
                      if wat_data[param].mean() != 0 else 0
            }

        return summary
