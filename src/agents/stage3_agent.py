"""
Stage 3 Agent: SEM Defect Classification and Process Improvement

Uses ResNet to classify SEM defect types and LLM for root cause analysis
Currently using mock model - will be replaced with STEP 3 team's model

⚠️ PHASE 2 (POST-FAB) CHARACTERISTICS:
- Wafer is already completed - REWORK NOT POSSIBLE
- Current wafer cannot be modified
- Recommendations are for NEXT LOT application
- Focus: Process improvement and preventive actions

Output: Process improvement recommendations for next LOT
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from src.agents.base_agent import BaseAgent
from src.utils.data_loader import DataLoader
from src.llm.client import LLMClient
from src.llm.prompts import format_root_cause_prompt


class Stage3Agent(BaseAgent):
    """
    Stage 3: SEM Defect Analysis & Process Improvement Recommendations

    ⚠️ PHASE 2 (POST-FAB) CHARACTERISTICS:
    - Wafer fabrication is already completed
    - Current wafer CANNOT be reworked (Phase 2 = Post-Fab)
    - All recommendations are for NEXT LOT application
    - Current wafer is used for analysis purposes only

    Purpose:
    1. SEM defect classification (using ResNet)
    2. Root cause analysis (using LLM)
    3. Process improvement recommendations for next LOT
    4. Recipe adjustment suggestions
    5. Monitoring plan generation

    Model: ResNet (from STEP 3 team)
    Input: SEM image data (from Carinthia proxy)
    Output: Defect classification + Process improvement recommendations

    Priority Levels (for next LOT application):
    - HIGH severity (>20 defects) → HIGH_PRIORITY (apply immediately to next LOT)
    - MEDIUM severity (10-20 defects) → MEDIUM_PRIORITY (consider for next LOT)
    - LOW severity (<10 defects) → LOW_PRIORITY (monitor trend)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Stage 3 Agent

        Args:
            config: Full configuration dictionary (must include models.stage3)
        """
        # Extract stage3 config
        stage3_config = config['models']['stage3']

        # Initialize base agent
        super().__init__(
            stage_name="stage3",
            config=stage3_config
        )

        # Initialize data loader for Carinthia proxy
        self.data_loader = DataLoader()

        # Initialize LLM client for root cause analysis
        try:
            self.llm_client = LLMClient(config['llm'])
            self.use_llm = True
            self.logger.info("LLM client initialized for root cause analysis")
        except Exception as e:
            self.logger.warning(f"LLM client unavailable: {e}")
            self.use_llm = False

        # Get configuration
        self.confidence_threshold = self.get_config_value('confidence_threshold', 0.8)
        self.rework_cost = config.get('budget', {}).get('costs', {}).get('rework', 200)

        self.logger.info(
            f"Stage3Agent initialized: "
            f"llm_enabled={self.use_llm}, "
            f"confidence_threshold={self.confidence_threshold}"
        )

    def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
        """
        Classify SEM defect type using ResNet

        Args:
            wafer_data: Single wafer data as pandas Series with wafer_id

        Returns:
            Dictionary with:
                - defect_type: str (Particle, Scratch, Residue)
                - defect_count: int (number of defects detected)
                - location_pattern: str (edge, center, random)
                - confidence: float (0-1)
                - severity: str (HIGH, MEDIUM, LOW)
        """
        wafer_id = wafer_data['wafer_id']

        # Load Carinthia proxy data
        try:
            carinthia_df = self.data_loader.load_carinthia_proxy()
            wafer_row = carinthia_df[carinthia_df['wafer_id'] == wafer_id]

            if len(wafer_row) == 0:
                self.logger.warning(f"No Carinthia proxy data for {wafer_id} - using fallback")
                return self._fallback_analysis()

            proxy_data = wafer_row.iloc[0]

            # In production, ResNet model would process SEM image
            # For now, use proxy data directly
            if self.model is not None:
                # Mock ResNet returns defect type based on proxy
                defect_type = str(proxy_data['defect_type'])
                # Could use model.predict() with image data in production
            else:
                defect_type = str(proxy_data['defect_type'])

            defect_count = int(proxy_data['defect_count'])
            location_pattern = str(proxy_data.get('location_pattern', 'random'))
            confidence = float(proxy_data.get('confidence', 0.75))

            # Classify severity based on defect count
            if defect_count > 20:
                severity = 'HIGH'
            elif defect_count > 10:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'

            self.logger.debug(
                f"Wafer {wafer_id}: "
                f"defect={defect_type}, "
                f"count={defect_count}, "
                f"severity={severity}"
            )

            return {
                'defect_type': defect_type,
                'defect_count': defect_count,
                'location_pattern': location_pattern,
                'confidence': confidence,
                'severity': severity
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
            'defect_type': 'Particle',
            'defect_count': 10,
            'location_pattern': 'random',
            'confidence': 0.5,
            'severity': 'MEDIUM'
        }

    def make_recommendation(
        self,
        wafer_data: pd.Series,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate process improvement recommendations for next LOT

        ⚠️ PHASE 2 (POST-FAB): Current wafer is COMPLETED
        - Cannot rework current wafer
        - Recommendations are for NEXT LOT application
        - Focus on preventive actions and process optimization

        Args:
            wafer_data: Single wafer data as pandas Series
            analysis_result: Output from analyze()

        Returns:
            Dictionary with:
                - process_improvement_action: str (action for next LOT)
                - recipe_adjustment_for_next_lot: dict (recipe changes)
                - monitoring_plan: str (monitoring recommendations)
                - current_wafer_status: 'COMPLETED' (cannot be modified)
                - action_target: 'NEXT_LOT' (where to apply recommendations)
                - current_wafer_actionable: False
                - ai_recommendation: str (priority level)
                - ai_confidence: float (0-1)
                - ai_reasoning: str
                - expected_yield_improvement: float (%)
                - expected_cost_saving: float (USD)
                - implementation_cost: float (USD)
                - payback_period: str
                - root_cause_analysis: str (from LLM, in Korean)
                - defect_info: dict (defect details)
                - engineer_decision: None (to be filled by engineer)
                - engineer_note: None
        """
        wafer_id = wafer_data['wafer_id']
        defect_type = analysis_result['defect_type']
        defect_count = analysis_result['defect_count']
        location = analysis_result['location_pattern']
        confidence = analysis_result['confidence']
        severity = analysis_result['severity']

        # Determine priority for next LOT application
        priority = self._determine_priority(defect_type, defect_count, severity)

        # Generate process improvement recommendations
        improvement_action = self._generate_improvement_action(
            defect_type, location, severity
        )

        # Generate recipe adjustments for next LOT
        recipe_adjustment = self._generate_recipe_adjustment(
            defect_type, location, severity
        )

        # Generate monitoring plan
        monitoring_plan = self._generate_monitoring_plan(
            defect_type, location, severity
        )

        # Estimate expected impact
        expected_impact = self._estimate_improvement_impact(
            defect_type, defect_count, severity
        )

        # Perform LLM root cause analysis (Korean prompts)
        root_cause_analysis = self._perform_root_cause_analysis(
            wafer_id,
            wafer_data,
            analysis_result
        )

        # Generate AI reasoning
        reasoning = (
            f"Defect analysis: {defect_type} detected ({defect_count} defects, {location} pattern). "
            f"Severity: {severity}. Current wafer is already completed (Phase 2 Post-Fab). "
            f"Recommendations are for next LOT application to prevent similar issues. "
            f"Priority: {priority}."
        )

        # Defect info for reference
        defect_info = {
            'type': defect_type,
            'count': defect_count,
            'location': location,
            'severity': severity,
            'confidence': confidence
        }

        self.logger.info(
            f"Stage3 recommendation for {wafer_id}: "
            f"Priority={priority}, defect={defect_type}, count={defect_count}, "
            f"target=NEXT_LOT"
        )

        return {
            'wafer_id': wafer_id,

            # Process improvement recommendations (for next LOT)
            'process_improvement_action': improvement_action,
            'recipe_adjustment_for_next_lot': recipe_adjustment,
            'monitoring_plan': monitoring_plan,

            # Current wafer status (Phase 2 Post-Fab)
            'current_wafer_status': 'COMPLETED',
            'action_target': 'NEXT_LOT',
            'current_wafer_actionable': False,

            # AI recommendation
            'ai_recommendation': priority,
            'ai_confidence': float(confidence),
            'ai_reasoning': reasoning,

            # Expected impact (for next LOT)
            'expected_yield_improvement': expected_impact['yield_improvement'],
            'expected_cost_saving': expected_impact['cost_saving'],
            'implementation_cost': expected_impact['implementation_cost'],
            'payback_period': expected_impact['payback_period'],

            # Analysis details
            'root_cause_analysis': root_cause_analysis,
            'defect_info': defect_info,

            # Engineer decision (to be filled)
            'engineer_decision': None,  # APPLY_NEXT_LOT / INVESTIGATE / DEFER
            'engineer_note': None,
            'decision_timestamp': None,

            # For compatibility with pipeline
            'action': 'MONITOR',  # Phase 2 default (no immediate action on current wafer)
            'estimated_cost': 0.0  # No cost for current wafer
        }

    def _perform_root_cause_analysis(
        self,
        wafer_id: str,
        wafer_data: pd.Series,
        analysis_result: Dict[str, Any]
    ) -> str:
        """
        Perform LLM-powered root cause analysis with Korean prompts

        Args:
            wafer_id: Wafer identifier
            wafer_data: Wafer sensor data
            analysis_result: Defect analysis results

        Returns:
            Root cause analysis text (in Korean if LLM available)
        """
        if not self.use_llm:
            return "Root cause analysis unavailable (LLM not configured)"

        try:
            # Gather context for LLM
            defect_type = analysis_result['defect_type']
            defect_count = analysis_result['defect_count']
            location = analysis_result['location_pattern']
            confidence = analysis_result['confidence']

            # Process history from wafer data
            process_history = f"""
- Recipe: {wafer_data.get('recipe', 'Unknown')}
- Chamber: {wafer_data.get('chamber', 'Unknown')}
- Lot: {wafer_data.get('lot_id', 'Unknown')}
- Timestamp: {wafer_data.get('timestamp', 'Unknown')}
"""

            # Sensor data from wafer data
            sensor_data = f"""
- Etch rate: {wafer_data.get('etch_rate', 0):.2f} µm/min
- Pressure: {wafer_data.get('pressure', 0):.1f} mTorr
- Temperature: {wafer_data.get('temperature', 0):.1f}°C
- RF Power: {wafer_data.get('rf_power', 0):.0f} W
- Gas flow: {wafer_data.get('gas_flow', 0):.1f} sccm
"""

            # Find similar cases (simplified - would be more sophisticated in production)
            similar_cases = "과거 유사 사례 분석 중..."

            # Generate Korean prompt for root cause analysis
            llm_prompt = format_root_cause_prompt(
                wafer_id=wafer_id,
                defect_type=defect_type,
                defect_count=defect_count,
                location_pattern=location,
                confidence=confidence,
                process_history=process_history,
                sensor_data=sensor_data,
                similar_cases=similar_cases
            )

            # Get LLM analysis
            self.logger.debug(f"Requesting LLM root cause analysis for {wafer_id}")
            root_cause_analysis = self.llm_client.complete(
                prompt=llm_prompt,
                category="root_cause_analysis",
                metadata={
                    'wafer_id': wafer_id,
                    'defect_type': defect_type,
                    'defect_count': defect_count
                }
            )

            self.logger.info(f"LLM root cause analysis completed for {wafer_id}")
            return root_cause_analysis

        except Exception as e:
            self.logger.error(f"LLM analysis failed for {wafer_id}: {e}")
            return f"Root cause analysis failed: {str(e)}"

    def _determine_priority(
        self,
        defect_type: str,
        defect_count: int,
        severity: str
    ) -> str:
        """
        Determine priority level for next LOT application

        Args:
            defect_type: Type of defect
            defect_count: Number of defects
            severity: Severity level

        Returns:
            Priority level: 'HIGH_PRIORITY', 'MEDIUM_PRIORITY', or 'LOW_PRIORITY'
        """
        if severity == 'HIGH' or defect_count > 20:
            return 'HIGH_PRIORITY'  # Apply immediately to next LOT
        elif severity == 'MEDIUM' or defect_count > 10:
            return 'MEDIUM_PRIORITY'  # Consider for next LOT
        else:
            return 'LOW_PRIORITY'  # Monitor trend

    def _generate_improvement_action(
        self,
        defect_type: str,
        location: str,
        severity: str
    ) -> dict:
        """
        Generate process improvement action for next LOT

        Args:
            defect_type: Type of defect detected
            location: Defect location pattern
            severity: Severity level

        Returns:
            Dictionary with improvement action details
        """
        action_map = {
            'Particle': {
                'action': 'Chamber cleaning and filter replacement',
                'target': 'Next LOT',
                'urgency': 'HIGH',
                'timeline': 'Before next LOT start',
                'description': 'Perform deep chamber clean and replace HEPA filters to reduce particle contamination'
            },
            'Scratch': {
                'action': 'Wafer handling procedure review',
                'target': 'Next LOT',
                'urgency': 'MEDIUM',
                'timeline': '1-2 days',
                'description': 'Review and update wafer handling procedures, inspect robot end-effector'
            },
            'Pit': {
                'action': 'Etch recipe optimization',
                'target': 'Next LOT',
                'urgency': 'MEDIUM',
                'timeline': '2-3 days',
                'description': 'Optimize etch time and power settings to prevent over-etching'
            },
            'Residue': {
                'action': 'Clean process enhancement',
                'target': 'Next LOT',
                'urgency': 'MEDIUM',
                'timeline': '1-2 days',
                'description': 'Increase cleaning time or solvent concentration for next LOT'
            },
            'Edge defect': {
                'action': 'Edge exclusion zone adjustment',
                'target': 'Next LOT',
                'urgency': 'LOW',
                'timeline': '1 week',
                'description': 'Adjust edge exclusion parameters in process recipe'
            }
        }

        default_action = {
            'action': 'Monitor and investigate',
            'target': 'Next LOT',
            'urgency': 'LOW',
            'timeline': '1 week',
            'description': 'Continue monitoring defect trends before taking action'
        }

        return action_map.get(defect_type, default_action)

    def _generate_recipe_adjustment(
        self,
        defect_type: str,
        location: str,
        severity: str
    ) -> dict:
        """
        Generate recipe adjustment recommendations for next LOT

        Args:
            defect_type: Type of defect
            location: Defect location pattern
            severity: Severity level

        Returns:
            Dictionary with recipe adjustment parameters
        """
        adjustment_map = {
            'Particle': {
                'chamber_pressure': {'current': 100, 'recommended': 95, 'change': -5, 'unit': 'mTorr'},
                'gas_flow_rate': {'current': 100, 'recommended': 110, 'change': +10, 'unit': 'sccm'},
                'note': 'Reduce pressure and increase gas flow to minimize particle adhesion',
                'apply_to': 'Next LOT'
            },
            'Scratch': {
                'wafer_transfer_speed': {'current': 100, 'recommended': 80, 'change': -20, 'unit': '%'},
                'note': 'Reduce transfer speed to minimize mechanical stress',
                'apply_to': 'Next LOT'
            },
            'Pit': {
                'etch_time': {'current': 60, 'recommended': 55, 'change': -5, 'unit': 'sec'},
                'rf_power': {'current': 1000, 'recommended': 950, 'change': -50, 'unit': 'W'},
                'note': 'Reduce etch time and power to prevent over-etching',
                'apply_to': 'Next LOT'
            },
            'Residue': {
                'clean_time': {'current': 30, 'recommended': 40, 'change': +10, 'unit': 'sec'},
                'solvent_concentration': {'current': 100, 'recommended': 120, 'change': +20, 'unit': '%'},
                'note': 'Increase cleaning time and solvent strength',
                'apply_to': 'Next LOT'
            }
        }

        return adjustment_map.get(defect_type, {
            'note': 'No specific recipe adjustment needed',
            'apply_to': 'Next LOT'
        })

    def _generate_monitoring_plan(
        self,
        defect_type: str,
        location: str,
        severity: str
    ) -> str:
        """
        Generate monitoring plan for next LOT

        Args:
            defect_type: Type of defect
            location: Defect location pattern
            severity: Severity level

        Returns:
            Monitoring plan description
        """
        plan_map = {
            'Particle': (
                f"Monitor particle counts in next LOT. "
                f"Perform daily chamber particle monitoring. "
                f"Set alert threshold at 15 defects per wafer. "
                f"Inspect first wafer of next LOT with SEM."
            ),
            'Scratch': (
                f"Inspect wafer handling robot daily. "
                f"Monitor scratch defects on first and last wafer of next LOT. "
                f"Set alert if scratch count exceeds 10 per wafer."
            ),
            'Pit': (
                f"Monitor etch uniformity across next LOT wafers. "
                f"Measure etch depth on 3 wafers per LOT. "
                f"Alert if variation exceeds 5%."
            ),
            'Residue': (
                f"Monitor clean process effectiveness. "
                f"Inspect residue on 2 wafers per LOT. "
                f"Alert if residue count exceeds 8 per wafer."
            )
        }

        default_plan = (
            f"Monitor {defect_type} defects on next LOT. "
            f"Inspect first wafer with {location} pattern analysis. "
            f"Set alert threshold based on current defect count baseline."
        )

        return plan_map.get(defect_type, default_plan)

    def _estimate_improvement_impact(
        self,
        defect_type: str,
        defect_count: int,
        severity: str
    ) -> dict:
        """
        Estimate expected impact of implementing improvements

        Args:
            defect_type: Type of defect
            defect_count: Number of defects
            severity: Severity level

        Returns:
            Dictionary with impact estimates
        """
        # Base yield improvement estimate (%)
        if severity == 'HIGH':
            yield_improvement = 10.0  # 10% yield improvement expected
        elif severity == 'MEDIUM':
            yield_improvement = 5.0   # 5% yield improvement
        else:
            yield_improvement = 2.0   # 2% yield improvement

        # Estimate cost savings per LOT (25 wafers × $20K/wafer × yield improvement)
        wafers_per_lot = 25
        wafer_value = 20000
        cost_saving = wafers_per_lot * wafer_value * (yield_improvement / 100)

        # Implementation cost estimate
        implementation_cost_map = {
            'Particle': 5000,   # Chamber clean + filter replacement
            'Scratch': 2000,    # Robot inspection + procedure update
            'Pit': 3000,        # Recipe development + qualification
            'Residue': 2500     # Clean process optimization
        }
        implementation_cost = implementation_cost_map.get(defect_type, 2000)

        # Payback period (implementation cost / cost saving per LOT)
        if cost_saving > 0:
            lots_to_payback = implementation_cost / cost_saving
            if lots_to_payback < 1:
                payback_period = f"{int(lots_to_payback * 30)} days (< 1 LOT)"
            else:
                payback_period = f"{int(lots_to_payback)} LOTs (~{int(lots_to_payback * 30)} days)"
        else:
            payback_period = "N/A"

        return {
            'yield_improvement': float(yield_improvement),  # %
            'cost_saving': float(cost_saving),              # USD per LOT
            'implementation_cost': float(implementation_cost),  # USD one-time
            'payback_period': payback_period                # Description
        }
