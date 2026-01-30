"""
Stage 0 Agent: Inline Metrology Selection

Uses Isolation Forest to detect anomalies in sensor data
Currently using mock model - will be replaced with STEP 1 team's model

Decision: INLINE (perform inline metrology) or SKIP (continue to next stage)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import os

from src.agents.base_agent import BaseAgent


class Stage0Agent(BaseAgent):
    """
    Stage 0: Decide whether to perform inline metrology

    Model: Isolation Forest (from STEP 1 team)
    Input: 10 sensor measurements
    Output: INLINE or SKIP recommendation

    Risk Assessment:
    - HIGH risk (score > 0.7): Recommend INLINE
    - MEDIUM risk (0.4-0.7): Recommend INLINE if above confidence threshold
    - LOW risk (< 0.4): Recommend SKIP
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Stage 0 Agent

        Args:
            config: Full configuration dictionary (must include models.stage0)
        """
        # Extract stage0 config
        stage0_config = config['models']['stage0']

        # Initialize base agent
        super().__init__(
            stage_name="stage0",
            config=stage0_config
        )

        # Load scaler if available
        scaler_path = "models/stage0_scaler.pkl"
        if os.path.exists(scaler_path):
            self.scaler = self._load_model(scaler_path)
            self.logger.info(f"Loaded scaler from {scaler_path}")
        else:
            self.scaler = None
            self.logger.warning("Scaler not found - using raw sensor values")

        # Get configuration values
        self.confidence_threshold = self.get_config_value('confidence_threshold', 0.7)
        self.inline_cost = config.get('budget', {}).get('costs', {}).get('inline_per_wafer', 150)

        self.logger.info(
            f"Stage0Agent initialized: "
            f"confidence_threshold={self.confidence_threshold}, "
            f"inline_cost=${self.inline_cost}"
        )

    def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
        """
        Analyze sensor data for anomalies

        Args:
            wafer_data: Single wafer data as pandas Series with columns:
                - wafer_id: str
                - etch_rate, pressure, temperature, rf_power, gas_flow: float
                - sensor6, sensor7, sensor8, sensor9, sensor10: float
                - chamber: str
                - timestamp: str

        Returns:
            Dictionary with:
                - anomaly_score: float (0-1, higher = more anomalous)
                - risk_level: str ('HIGH', 'MEDIUM', 'LOW')
                - outlier_sensors: list of sensor names that are out of range
                - decision_score: float (raw model output)
                - sensor_values: dict of sensor readings
        """
        # Extract sensor values in order
        sensor_keys = [
            'etch_rate', 'pressure', 'temperature', 'rf_power',
            'gas_flow', 'sensor6', 'sensor7', 'sensor8',
            'sensor9', 'sensor10'
        ]

        # Build feature vector
        X = np.array([[wafer_data[k] for k in sensor_keys]])

        # Preprocess with scaler if available
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X

        # Get anomaly score from Isolation Forest
        if self.model is not None:
            # Isolation Forest returns negative scores
            # More negative = more anomalous
            decision_score = self.model.decision_function(X_scaled)[0]

            # Normalize to 0-1 using sigmoid (higher = more anomalous)
            anomaly_score = 1 / (1 + np.exp(decision_score))

            self.logger.debug(
                f"Wafer {wafer_data['wafer_id']}: "
                f"decision_score={decision_score:.3f}, "
                f"anomaly_score={anomaly_score:.3f}"
            )
        else:
            # Fallback if no model (shouldn't happen)
            self.logger.warning("No model available - using random score")
            anomaly_score = np.random.uniform(0.3, 0.8)
            decision_score = 0.0

        # Classify risk level
        if anomaly_score > 0.7:
            risk_level = 'HIGH'
        elif anomaly_score > 0.4:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        # Identify outlier sensors (sensors outside normal range)
        normal_ranges = {
            'etch_rate': (3.2, 3.6),
            'pressure': (145, 155),
            'temperature': (58, 63),
            'rf_power': (1800, 1900),
            'gas_flow': (235, 255)
        }

        outlier_sensors = []
        for sensor_name, (low, high) in normal_ranges.items():
            value = wafer_data.get(sensor_name, 0)
            if value < low or value > high:
                outlier_sensors.append(f"{sensor_name}={value:.2f}")

        # Store sensor values for reference
        sensor_values = {k: float(wafer_data[k]) for k in sensor_keys}

        return {
            'anomaly_score': float(anomaly_score),
            'risk_level': risk_level,
            'outlier_sensors': outlier_sensors,
            'decision_score': float(decision_score),
            'sensor_values': sensor_values
        }

    def make_recommendation(
        self,
        wafer_data: pd.Series,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate inline metrology recommendation

        Args:
            wafer_data: Single wafer data as pandas Series
            analysis_result: Output from analyze()

        Returns:
            Dictionary with:
                - action: 'INLINE' or 'SKIP'
                - confidence: float (0-1)
                - reasoning: str (explanation)
                - estimated_cost: float (USD)
                - risk_level: str
                - alternatives: list of alternative actions
        """
        anomaly_score = analysis_result['anomaly_score']
        risk_level = analysis_result['risk_level']
        outliers = analysis_result['outlier_sensors']

        # Decision logic based on risk level and threshold
        if risk_level == 'HIGH':
            action = 'INLINE'
            confidence = anomaly_score
        elif risk_level == 'MEDIUM' and anomaly_score > self.confidence_threshold:
            action = 'INLINE'
            confidence = 0.75
        else:
            action = 'SKIP'
            confidence = 1 - anomaly_score

        # Generate reasoning
        reasons = []
        if risk_level == 'HIGH':
            reasons.append(f"HIGH risk detected (anomaly score: {anomaly_score:.2f})")
        elif risk_level == 'MEDIUM':
            reasons.append(f"MEDIUM risk (anomaly score: {anomaly_score:.2f})")
        else:
            reasons.append(f"LOW risk (anomaly score: {anomaly_score:.2f})")

        if len(outliers) > 0:
            reasons.append(f"Outlier sensors: {', '.join(outliers)}")
        else:
            reasons.append("All sensors within normal range")

        if action == 'INLINE':
            reasons.append(f"Inline metrology recommended (cost: ${self.inline_cost})")
        else:
            reasons.append("No action needed - proceed to Stage 1")

        reasoning = " | ".join(reasons)

        # Calculate cost
        cost = self.inline_cost if action == 'INLINE' else 0

        # Alternative actions
        alternatives = []
        if action == 'INLINE':
            alternatives.append({
                'action': 'SKIP',
                'reasoning': 'Skip inline and proceed to Stage 1 (risky)',
                'cost': 0
            })
        else:
            alternatives.append({
                'action': 'INLINE',
                'reasoning': 'Perform inline metrology as precaution',
                'cost': self.inline_cost
            })

        self.logger.info(
            f"Stage0 recommendation for {wafer_data['wafer_id']}: "
            f"{action} (confidence={confidence:.2f}, risk={risk_level})"
        )

        return {
            'action': action,
            'confidence': float(confidence),
            'reasoning': reasoning,
            'estimated_cost': float(cost),
            'risk_level': risk_level,
            'alternatives': alternatives
        }
