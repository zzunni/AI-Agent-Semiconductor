"""
Stage 2B Agent: Wafermap Pattern Classification and SEM Selection

Uses CNN to classify wafermap defect patterns and decide on SEM inspection
Currently using mock model - will be replaced with STEP 3 team's model

Decision: SEM (expensive detailed inspection) or SKIP
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from src.agents.base_agent import BaseAgent
from src.utils.data_loader import DataLoader


class Stage2BAgent(BaseAgent):
    """
    Stage 2B: Classify wafermap patterns and recommend SEM inspection

    Model: CNN (from STEP 3 team)
    Input: Wafermap pattern data (from WM-811K proxy)
    Output: SEM or SKIP recommendation

    SEM Decision Criteria:
    - High-priority patterns (Edge-Ring, Loc, Scratch) → SEM
    - Severity >= threshold (0.7) → SEM
    - Defect density > 300 → SEM
    - Otherwise → SKIP (not cost-effective)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Stage 2B Agent

        Args:
            config: Full configuration dictionary (must include models.stage2b)
        """
        # Extract stage2b config
        stage2b_config = config['models']['stage2b']

        # Initialize base agent
        super().__init__(
            stage_name="stage2b",
            config=stage2b_config
        )

        # Get economic parameters
        self.sem_cost = self.get_config_value('sem_cost', 800)
        self.severity_threshold = self.get_config_value('severity_threshold', 0.7)

        # Initialize data loader for WM-811K proxy
        self.data_loader = DataLoader()

        self.logger.info(
            f"Stage2BAgent initialized: "
            f"sem_cost=${self.sem_cost}, "
            f"severity_threshold={self.severity_threshold}"
        )

    def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
        """
        Classify wafermap pattern using CNN

        Args:
            wafer_data: Single wafer data as pandas Series with wafer_id

        Returns:
            Dictionary with:
                - pattern_type: str (Edge-Ring, Center, Random, Loc, Scratch, etc.)
                - severity: float (0-1)
                - defect_density: int (defects per wafer)
                - location: str (edge, center, random)
                - confidence: float (0-1)
        """
        wafer_id = wafer_data['wafer_id']

        # Load WM-811K proxy data
        try:
            wm811k_df = self.data_loader.load_wm811k_proxy()
            wafer_row = wm811k_df[wm811k_df['wafer_id'] == wafer_id]

            if len(wafer_row) == 0:
                self.logger.warning(f"No WM-811K proxy data for {wafer_id} - using fallback")
                return self._fallback_analysis()

            proxy_data = wafer_row.iloc[0]

            # In production, CNN model would process wafermap image
            # For now, use proxy data directly
            if self.model is not None:
                # Mock CNN returns pattern type based on proxy
                pattern_type = str(proxy_data['pattern_type'])
                # Could use model.predict() with image data in production
            else:
                pattern_type = str(proxy_data['pattern_type'])

            severity = float(proxy_data['severity'])
            defect_density = int(proxy_data['defect_density'])
            confidence = float(proxy_data.get('confidence', 0.75))

            location = self._infer_location(pattern_type)

            self.logger.debug(
                f"Wafer {wafer_id}: "
                f"pattern={pattern_type}, "
                f"severity={severity:.2f}, "
                f"density={defect_density}"
            )

            return {
                'pattern_type': pattern_type,
                'severity': severity,
                'defect_density': defect_density,
                'location': location,
                'confidence': confidence
            }

        except Exception as e:
            self.logger.error(f"Error analyzing wafer {wafer_id}: {e}")
            return self._fallback_analysis()

    def _fallback_analysis(self) -> Dict[str, Any]:
        """
        Fallback analysis when proxy data not available

        Returns:
            Default analysis result
        """
        return {
            'pattern_type': 'Random',
            'severity': 0.5,
            'defect_density': 150,
            'location': 'random',
            'confidence': 0.5
        }

    def _infer_location(self, pattern_type: str) -> str:
        """
        Infer defect location from pattern type

        Args:
            pattern_type: Pattern classification

        Returns:
            Location string (edge, center, or random)
        """
        pattern_lower = pattern_type.lower()

        if 'edge' in pattern_lower or 'ring' in pattern_lower:
            return 'edge'
        elif 'center' in pattern_lower:
            return 'center'
        else:
            return 'random'

    def make_recommendation(
        self,
        wafer_data: pd.Series,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend SEM inspection based on pattern severity

        Args:
            wafer_data: Single wafer data as pandas Series
            analysis_result: Output from analyze()

        Returns:
            Dictionary with:
                - action: 'SEM' or 'SKIP'
                - confidence: float (0-1)
                - reasoning: str
                - estimated_cost: float (USD)
                - pattern_info: dict with pattern details
                - alternatives: list of alternative actions

        Decision Logic:
        - High-priority patterns (Edge-Ring, Loc, Scratch) → SEM
        - Severity >= threshold (0.7) → SEM
        - Defect density > 300 → SEM
        - Otherwise → SKIP (not cost-effective)
        """
        pattern_type = analysis_result['pattern_type']
        severity = analysis_result['severity']
        defect_density = analysis_result['defect_density']
        confidence = analysis_result['confidence']
        location = analysis_result['location']

        # High-priority patterns that warrant SEM inspection
        high_priority_patterns = ['Edge-Ring', 'Loc', 'Scratch']

        # Evaluate criteria for SEM
        needs_sem = False
        reasons = []

        # Criterion 1: High-priority pattern type
        if pattern_type in high_priority_patterns:
            needs_sem = True
            reasons.append(f"High-priority pattern: {pattern_type}")

        # Criterion 2: High severity
        if severity >= self.severity_threshold:
            needs_sem = True
            reasons.append(f"High severity: {severity:.2f} (threshold: {self.severity_threshold})")

        # Criterion 3: High defect density
        if defect_density > 300:
            needs_sem = True
            reasons.append(f"High defect density: {defect_density} defects")

        # Generate recommendation
        if needs_sem:
            action = 'SEM'
            rec_confidence = confidence
            cost = self.sem_cost
            reason_text = (
                f"Pattern: {pattern_type} at {location} | "
                f"Severity: {severity:.2f} | "
                f"Density: {defect_density} defects | "
                f"Criteria met: {'; '.join(reasons)}"
            )
        else:
            action = 'SKIP'
            rec_confidence = 1.0 - severity  # Higher confidence for low severity
            cost = 0
            reason_text = (
                f"Pattern: {pattern_type} at {location} | "
                f"Severity: {severity:.2f} (below {self.severity_threshold}) | "
                f"Density: {defect_density} defects | "
                f"Low severity - SEM not cost-effective (save ${self.sem_cost})"
            )

        # Build alternatives
        alternatives = []
        if action == 'SEM':
            alternatives.append({
                'action': 'SKIP',
                'cost': 0,
                'description': f"Skip SEM and accept risk (save ${self.sem_cost})"
            })
        else:
            alternatives.append({
                'action': 'SEM',
                'cost': self.sem_cost,
                'description': f"Perform SEM for detailed root cause analysis"
            })

        # Pattern info for reference
        pattern_info = {
            'type': pattern_type,
            'severity': severity,
            'density': defect_density,
            'location': location
        }

        self.logger.info(
            f"Stage2B recommendation for {wafer_data['wafer_id']}: "
            f"{action} (confidence={rec_confidence:.2f}, "
            f"pattern={pattern_type}, severity={severity:.2f})"
        )

        return {
            'action': action,
            'confidence': float(rec_confidence),
            'reasoning': reason_text,
            'estimated_cost': float(cost),
            'pattern_info': pattern_info,
            'alternatives': alternatives
        }
