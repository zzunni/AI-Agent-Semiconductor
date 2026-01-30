"""
Pipeline Controller: Multi-Phase Inspection Orchestration

Coordinates two-phase inspection pipeline with budget tracking

Pipeline Flow:
    Phase 1 (In-Line) - Rework Possible:
        Stage 0: Anomaly Detection → INLINE ($150) / SKIP
            ↓
        Stage 1: Yield Prediction → PROCEED / REWORK ($200) / SCRAP

    Phase 2 (Post-Fab) - Rework NOT Possible:
        Stage 2A: WAT Analysis (LOT-level) → LOT_PROCEED / LOT_SCRAP
            ↓
        Stage 2B: Pattern Classification → SEM ($800) / SKIP
            ↓
        Stage 3: Defect Classification → MONITOR / Process Improvement (if SEM)
"""

import yaml
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.agents.stage0_agent import Stage0Agent
from src.agents.stage1_agent import Stage1Agent
from src.agents.stage2a_agent import Stage2AAgent
from src.agents.stage2b_agent import Stage2BAgent
from src.agents.stage3_agent import Stage3Agent
from src.utils.data_loader import DataLoader
from src.utils.logger import SystemLogger
from src.utils.metrics import MetricsCalculator


class PipelineController:
    """
    Pipeline Controller: Multi-phase inspection orchestration

    Coordinates two inspection phases:
    - Phase 1 (In-Line): Stage 0, 1 - rework possible
    - Phase 2 (Post-Fab): Stage 2A, 2B, 3 - rework NOT possible
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize Pipeline Controller

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.logger = SystemLogger("PipelineController")
        self.data_loader = DataLoader()
        self.metrics_calculator = MetricsCalculator(config_path)

        # Initialize Phase 1 agents (In-Line, rework possible)
        self.logger.info("Initializing Phase 1 agents (In-Line)...")
        self.stage0 = Stage0Agent(self.config)
        self.stage1 = Stage1Agent(self.config)

        # Initialize Phase 2 agents (Post-Fab, rework NOT possible)
        self.logger.info("Initializing Phase 2 agents (Post-Fab)...")
        self.stage2a = Stage2AAgent(
            self.config['models'].get('stage2a', {}),
            self.config
        )
        self.stage2b = Stage2BAgent(self.config)
        self.stage3 = Stage3Agent(self.config)

        # Organize agents by phase
        self.phase1_agents = {
            'stage0': self.stage0,
            'stage1': self.stage1
        }
        self.phase2_agents = {
            'stage2a': self.stage2a,
            'stage2b': self.stage2b,
            'stage3': self.stage3
        }

        # Budget tracking
        self.monthly_budget = self.config['budget']['monthly']
        self.costs = self.config['budget']['costs']
        self.total_spent = {
            'inline': 0,
            'sem': 0,
            'rework': 0,
            'lot_scrap': 0,
            'total': 0
        }

        self.logger.info(
            f"PipelineController initialized: "
            f"Phase 1 (In-Line) agents: 2, Phase 2 (Post-Fab) agents: 3"
        )
        self.logger.info(
            f"Budget - Inline: ${self.monthly_budget['inline']}, "
            f"SEM: ${self.monthly_budget['sem']}"
        )

    def process_wafer(
        self,
        wafer_id: str,
        lot_id: Optional[str] = None,
        simulate_engineer: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Process single wafer through two-phase pipeline

        Args:
            wafer_id: Wafer identifier
            lot_id: LOT identifier (required for Phase 2)
            simulate_engineer: If True, simulate engineer decisions (for testing)

        Returns:
            Complete pipeline result dictionary with:
                - wafer_id: str
                - lot_id: str (if provided)
                - phases: dict {phase1: {...}, phase2: {...}}
                - total_cost: float
                - final_recommendation: str
                - pipeline_path: list (which stages executed)
        """
        self.logger.info(f"=" * 60)
        self.logger.info(f"Processing wafer: {wafer_id}")
        self.logger.info(f"=" * 60)

        # Load wafer data with proxies
        wafer_data_dict = self.data_loader.get_wafer_with_proxies(wafer_id)

        if wafer_data_dict is None:
            self.logger.error(f"Wafer {wafer_id} not found in dataset")
            return None

        # Extract components
        wafer_data = wafer_data_dict['wafer_data']

        # Result tracking
        result = {
            'wafer_id': wafer_id,
            'lot_id': lot_id,
            'phases': {
                'phase1': {},
                'phase2': {}
            },
            'total_cost': 0,
            'final_recommendation': None,
            'pipeline_path': []
        }

        # ====================================================================
        # PHASE 1: IN-LINE (Rework Possible)
        # ====================================================================
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"PHASE 1: IN-LINE INSPECTION (Rework Possible)")
        self.logger.info(f"{'='*60}")

        # Stage 0: Anomaly Detection
        self.logger.info(f"[Phase 1 - Stage 0] Anomaly Detection")

        stage0_analysis = self.stage0.analyze(wafer_data)
        stage0_rec = self.stage0.make_recommendation(wafer_data, stage0_analysis)

        result['phases']['phase1']['stage0'] = {
            'analysis': stage0_analysis,
            'recommendation': stage0_rec
        }
        result['total_cost'] += stage0_rec['estimated_cost']
        result['pipeline_path'].append('Phase1-Stage0')

        self.logger.info(
            f"[Stage 0] Result: {stage0_rec['action']} "
            f"(risk={stage0_analysis['risk_level']}, "
            f"cost=${stage0_rec['estimated_cost']})"
        )

        # Add inline data if INLINE performed
        if stage0_rec['action'] == 'INLINE':
            inline_data = self._perform_inline_measurement()
            wafer_data = wafer_data.copy()
            for key, value in inline_data.items():
                wafer_data[key] = value
            self.logger.info(f"[Stage 0] Inline metrology performed")

        # Stage 1: Yield Prediction
        self.logger.info(f"[Phase 1 - Stage 1] Yield Prediction")

        stage1_analysis = self.stage1.analyze(wafer_data)
        stage1_rec = self.stage1.make_recommendation(wafer_data, stage1_analysis)

        result['phases']['phase1']['stage1'] = {
            'analysis': stage1_analysis,
            'recommendation': stage1_rec
        }
        result['total_cost'] += stage1_rec['estimated_cost']
        result['pipeline_path'].append('Phase1-Stage1')

        self.logger.info(
            f"[Stage 1] Result: {stage1_rec['action']} "
            f"(yield={stage1_analysis['predicted_yield']:.1%}, "
            f"cost=${stage1_rec['estimated_cost']})"
        )

        # Phase 1 early termination conditions
        if stage1_rec['action'] == 'SCRAP':
            result['final_recommendation'] = 'SCRAP'
            result['phases']['phase1']['outcome'] = 'SCRAP'
            result['phases']['phase2']['outcome'] = 'SKIPPED'
            self.logger.info(f"[Phase 1] Terminated: SCRAP - Phase 2 will not execute")
            self._update_budget_tracking(result)
            return result

        if stage1_rec['action'] == 'REWORK':
            result['final_recommendation'] = 'REWORK'
            result['phases']['phase1']['outcome'] = 'REWORK'
            result['phases']['phase2']['outcome'] = 'SKIPPED'
            self.logger.info(f"[Phase 1] Terminated: REWORK - Phase 2 will not execute")
            self._update_budget_tracking(result)
            return result

        # Phase 1 complete - PROCEED to Phase 2
        result['phases']['phase1']['outcome'] = 'PROCEED'
        self.logger.info(f"[Phase 1] Complete: PROCEED to Phase 2")

        # ====================================================================
        # PHASE 2: POST-FAB (Rework NOT Possible)
        # ====================================================================
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"PHASE 2: POST-FAB INSPECTION (Rework NOT Possible)")
        self.logger.info(f"{'='*60}")

        # NOTE: Stage 2A operates at LOT-level, not wafer-level
        # In production, Stage 2A would be executed once per LOT
        # Here we'll skip Stage 2A for individual wafer processing
        # and proceed directly to Stage 2B
        self.logger.info(
            f"[Phase 2 - Stage 2A] Skipped (LOT-level analysis, "
            f"not applicable for single wafer processing)"
        )

        # Stage 2B: Pattern Classification
        self.logger.info(f"[Phase 2 - Stage 2B] Pattern Classification")

        stage2b_analysis = self.stage2b.analyze(wafer_data)
        stage2b_rec = self.stage2b.make_recommendation(wafer_data, stage2b_analysis)

        result['phases']['phase2']['stage2b'] = {
            'analysis': stage2b_analysis,
            'recommendation': stage2b_rec
        }
        result['total_cost'] += stage2b_rec['estimated_cost']
        result['pipeline_path'].append('Phase2-Stage2B')

        self.logger.info(
            f"[Stage 2B] Result: {stage2b_rec['action']} "
            f"(pattern={stage2b_analysis['pattern_type']}, "
            f"severity={stage2b_analysis['severity']:.2f}, "
            f"cost=${stage2b_rec['estimated_cost']})"
        )

        # Stage 3: Defect Classification (conditional on SEM)
        if stage2b_rec['action'] == 'SEM':
            self.logger.info(f"[Phase 2 - Stage 3] Defect Classification (SEM)")

            stage3_analysis = self.stage3.analyze(wafer_data)
            stage3_rec = self.stage3.make_recommendation(wafer_data, stage3_analysis)

            result['phases']['phase2']['stage3'] = {
                'analysis': stage3_analysis,
                'recommendation': stage3_rec
            }
            result['total_cost'] += stage3_rec['estimated_cost']
            result['pipeline_path'].append('Phase2-Stage3')

            # In Phase 2, no rework - only MONITOR or process improvement
            result['final_recommendation'] = stage3_rec['action']

            self.logger.info(
                f"[Stage 3] Result: {stage3_rec['action']} "
                f"(defect={stage3_analysis['defect_type']}, "
                f"count={stage3_analysis['defect_count']}, "
                f"cost=${stage3_rec['estimated_cost']})"
            )
        else:
            # No SEM, use Stage 2B recommendation
            result['final_recommendation'] = 'PROCEED'
            self.logger.info(f"[Phase 2 - Stage 3] Skipped (no SEM required)")

        result['phases']['phase2']['outcome'] = 'COMPLETE'

        # Update budget tracking
        self._update_budget_tracking(result)

        self.logger.info(
            f"\n[Pipeline] Complete: {result['final_recommendation']} "
            f"(Total cost: ${result['total_cost']}, "
            f"Path: {' → '.join(result['pipeline_path'])})"
        )

        return result

    def process_batch(
        self,
        wafer_ids: List[str],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Process multiple wafers through pipeline

        Args:
            wafer_ids: List of wafer identifiers
            verbose: If True, log detailed progress

        Returns:
            Batch results with summary statistics
        """
        self.logger.info(f"Starting batch processing: {len(wafer_ids)} wafers")

        results = []
        failed = []

        for i, wafer_id in enumerate(wafer_ids, 1):
            if verbose:
                self.logger.info(f"Batch progress: {i}/{len(wafer_ids)}")

            try:
                result = self.process_wafer(wafer_id)
                if result:
                    results.append(result)
                else:
                    failed.append(wafer_id)
            except Exception as e:
                self.logger.error(f"Failed to process {wafer_id}: {e}")
                failed.append(wafer_id)

        # Generate summary
        summary = self._generate_batch_summary(results, failed)

        self.logger.info(
            f"Batch processing complete: "
            f"{len(results)} successful, {len(failed)} failed, "
            f"Total cost: ${summary['total_cost']:.2f}"
        )

        return {
            'results': results,
            'failed': failed,
            'summary': summary
        }

    def _perform_inline_measurement(self) -> Dict[str, float]:
        """
        Perform inline measurement (Phase 1 only)

        In production, this would be replaced with actual metrology data

        Returns:
            Dictionary with inline measurements
        """
        return {
            'cd': np.random.uniform(6.7, 7.3),  # Critical Dimension (nm)
            'overlay': np.random.uniform(1.0, 4.0),  # Overlay error (nm)
            'thickness': np.random.uniform(95, 105),  # Film thickness (nm)
            'uniformity': np.random.uniform(1.0, 2.5)  # Uniformity (%)
        }

    def _update_budget_tracking(self, result: Dict[str, Any]) -> None:
        """
        Update budget tracking with latest result

        Args:
            result: Pipeline result dictionary (wafer or LOT)
        """
        # Handle wafer-level results (two-phase structure)
        if 'phases' in result:
            for phase_name, phase_data in result['phases'].items():
                for stage_name, stage_data in phase_data.items():
                    if stage_name in ['outcome']:
                        continue
                    if isinstance(stage_data, dict) and 'recommendation' in stage_data:
                        cost = stage_data['recommendation']['estimated_cost']
                        action = stage_data['recommendation']['action']

                        if action == 'INLINE':
                            self.total_spent['inline'] += cost
                        elif action == 'SEM':
                            self.total_spent['sem'] += cost
                        elif action == 'REWORK':
                            self.total_spent['rework'] += cost
                        elif action == 'LOT_SCRAP':
                            self.total_spent['lot_scrap'] += cost

        # Handle LOT-level results
        elif 'stage2a' in result.get('stages', {}):
            stage2a_data = result['stages']['stage2a']
            cost = stage2a_data['recommendation']['estimated_cost']
            action = stage2a_data['recommendation']['action']

            if action == 'LOT_SCRAP':
                self.total_spent['lot_scrap'] += cost

        self.total_spent['total'] += result.get('total_cost', 0)

    def process_lot(
        self,
        lot_id: str,
        wat_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Process LOT through Stage 2A (WAT Analysis)

        This is a LOT-level operation, not wafer-level.
        Determines if LOT proceeds to Stage 2B or is scrapped.

        Args:
            lot_id: LOT identifier
            wat_data: DataFrame with WAT measurements for all wafers in LOT

        Returns:
            LOT analysis result with recommendation
        """
        self.logger.info(f"=" * 60)
        self.logger.info(f"Processing LOT: {lot_id} ({len(wat_data)} wafers)")
        self.logger.info(f"=" * 60)

        # Stage 2A: WAT Analysis (LOT-level)
        self.logger.info(f"[Stage 2A] LOT-level WAT Electrical Analysis")

        stage2a_analysis = self.stage2a.analyze(lot_id, wat_data)
        stage2a_rec = self.stage2a.make_recommendation(lot_id, stage2a_analysis)

        result = {
            'lot_id': lot_id,
            'wafer_count': len(wat_data),
            'stages': {
                'stage2a': {
                    'analysis': stage2a_analysis,
                    'recommendation': stage2a_rec
                }
            },
            'total_cost': stage2a_rec['estimated_cost'],
            'final_recommendation': stage2a_rec['action'],
            'proceed_to_stage2b': stage2a_rec['proceed_to_stage2b'],
            'wafer_list_for_stage2b': stage2a_rec['wafer_list_for_stage2b']
        }

        self.logger.info(
            f"[Stage 2A] Result: {stage2a_rec['action']} "
            f"(quality={stage2a_analysis['electrical_quality']}, "
            f"uniformity={stage2a_analysis['uniformity_score']:.3f}, "
            f"cost=${stage2a_rec['estimated_cost']:,.0f})"
        )

        # Update budget tracking
        self._update_budget_tracking(result)

        if stage2a_rec['action'] == 'LOT_SCRAP':
            self.logger.info(
                f"[LOT {lot_id}] Terminated: LOT_SCRAP - "
                f"0 wafers proceed to Stage 2B/3"
            )
        else:
            self.logger.info(
                f"[LOT {lot_id}] PROCEED - "
                f"{len(stage2a_rec['wafer_list_for_stage2b'])} wafers to Stage 2B/3"
            )

        return result

    def get_phase_summary(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate phase-wise summary statistics

        Args:
            results: List of wafer pipeline results

        Returns:
            Summary statistics by phase
        """
        summary = {
            'total_wafers': len(results),
            'phase1': {
                'outcomes': {},
                'total_cost': 0,
                'stage_actions': {}
            },
            'phase2': {
                'outcomes': {},
                'total_cost': 0,
                'stage_actions': {}
            }
        }

        for result in results:
            # Phase 1 summary
            phase1 = result['phases']['phase1']
            phase1_outcome = phase1.get('outcome', 'UNKNOWN')
            summary['phase1']['outcomes'][phase1_outcome] = \
                summary['phase1']['outcomes'].get(phase1_outcome, 0) + 1

            for stage_name, stage_data in phase1.items():
                if stage_name == 'outcome':
                    continue
                if isinstance(stage_data, dict) and 'recommendation' in stage_data:
                    action = stage_data['recommendation']['action']
                    cost = stage_data['recommendation']['estimated_cost']

                    if stage_name not in summary['phase1']['stage_actions']:
                        summary['phase1']['stage_actions'][stage_name] = {}

                    summary['phase1']['stage_actions'][stage_name][action] = \
                        summary['phase1']['stage_actions'][stage_name].get(action, 0) + 1
                    summary['phase1']['total_cost'] += cost

            # Phase 2 summary
            phase2 = result['phases']['phase2']
            phase2_outcome = phase2.get('outcome', 'UNKNOWN')
            summary['phase2']['outcomes'][phase2_outcome] = \
                summary['phase2']['outcomes'].get(phase2_outcome, 0) + 1

            for stage_name, stage_data in phase2.items():
                if stage_name == 'outcome':
                    continue
                if isinstance(stage_data, dict) and 'recommendation' in stage_data:
                    action = stage_data['recommendation']['action']
                    cost = stage_data['recommendation']['estimated_cost']

                    if stage_name not in summary['phase2']['stage_actions']:
                        summary['phase2']['stage_actions'][stage_name] = {}

                    summary['phase2']['stage_actions'][stage_name][action] = \
                        summary['phase2']['stage_actions'][stage_name].get(action, 0) + 1
                    summary['phase2']['total_cost'] += cost

        return summary

    def _generate_batch_summary(
        self,
        results: List[Dict[str, Any]],
        failed: List[str]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for batch

        Args:
            results: List of successful pipeline results
            failed: List of failed wafer IDs

        Returns:
            Summary statistics dictionary
        """
        if len(results) == 0:
            return {
                'total_wafers': len(failed),
                'successful': 0,
                'failed': len(failed),
                'total_cost': 0,
                'final_recommendations': {},
                'phase_summary': {}
            }

        # Count final recommendations
        final_recs = {}
        for result in results:
            rec = result['final_recommendation']
            final_recs[rec] = final_recs.get(rec, 0) + 1

        # Cost analysis
        total_cost = sum(r['total_cost'] for r in results)
        avg_cost = total_cost / len(results) if results else 0

        # Phase-wise summary
        phase_summary = self.get_phase_summary(results)

        return {
            'total_wafers': len(results) + len(failed),
            'successful': len(results),
            'failed': len(failed),
            'total_cost': float(total_cost),
            'average_cost': float(avg_cost),
            'final_recommendations': final_recs,
            'phase_summary': phase_summary
        }

    def check_budget(self) -> Dict[str, Any]:
        """
        Check current budget status

        Returns:
            Budget status dictionary with spent/remaining amounts
        """
        budget_status = {}

        for category in ['inline', 'sem']:
            budget = self.monthly_budget[category]
            spent = self.total_spent[category]
            remaining = budget - spent
            utilization = (spent / budget * 100) if budget > 0 else 0

            budget_status[category] = {
                'budget': budget,
                'spent': spent,
                'remaining': remaining,
                'utilization': utilization,
                'status': 'OK' if remaining > 0 else 'EXCEEDED'
            }

        budget_status['total_spent'] = self.total_spent['total']

        return budget_status

    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate comprehensive pipeline report

        Args:
            results: List of pipeline results

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("TWO-PHASE PIPELINE EXECUTION REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        total_cost = sum(r['total_cost'] for r in results)
        report.append(f"Total Wafers Processed: {len(results)}")
        report.append(f"Total Cost: ${total_cost:.2f}")
        report.append(f"Average Cost per Wafer: ${total_cost/len(results):.2f}")
        report.append("")

        # Final recommendations
        report.append("Final Recommendations:")
        final_recs = {}
        for result in results:
            rec = result['final_recommendation']
            final_recs[rec] = final_recs.get(rec, 0) + 1

        for rec, count in final_recs.items():
            percentage = count / len(results) * 100
            report.append(f"  {rec}: {count} ({percentage:.1f}%)")
        report.append("")

        # Phase-wise summary
        phase_summary = self.get_phase_summary(results)

        report.append("Phase 1 (In-Line) Summary:")
        report.append(f"  Total Cost: ${phase_summary['phase1']['total_cost']:.2f}")
        report.append("  Outcomes:")
        for outcome, count in phase_summary['phase1']['outcomes'].items():
            percentage = count / len(results) * 100
            report.append(f"    {outcome}: {count} ({percentage:.1f}%)")
        report.append("")

        report.append("Phase 2 (Post-Fab) Summary:")
        report.append(f"  Total Cost: ${phase_summary['phase2']['total_cost']:.2f}")
        report.append("  Outcomes:")
        for outcome, count in phase_summary['phase2']['outcomes'].items():
            percentage = count / len(results) * 100
            report.append(f"    {outcome}: {count} ({percentage:.1f}%)")
        report.append("")

        # Budget status
        budget_status = self.check_budget()
        report.append("Budget Status:")
        for category in ['inline', 'sem']:
            status = budget_status[category]
            report.append(
                f"  {category.upper()}: "
                f"${status['spent']:.2f} / ${status['budget']:.2f} "
                f"({status['utilization']:.1f}%) - {status['status']}"
            )

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)
