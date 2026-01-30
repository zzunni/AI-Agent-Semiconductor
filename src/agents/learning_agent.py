"""
Learning Agent: Feedback-based Learning

Analyzes engineer feedback to improve AI recommendations
Uses LLM to understand decision patterns and generate insights

This agent:
- Analyzes decision history from CSV logs
- Calculates approval/rejection rates
- Identifies cost sensitivity and confidence patterns
- Generates actionable insights with LLM (Korean)
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os

from src.utils.logger import SystemLogger
from src.llm.client import LLMClient
from src.llm.prompts import format_feedback_learning_prompt


class LearningAgent:
    """
    Learning Agent: Continuous improvement from engineer feedback

    Methods:
    - analyze_feedback(): Analyze recent decisions
    - identify_patterns(): Find approval/rejection patterns
    - generate_insights(): Use LLM for insights (Korean)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Learning Agent

        Args:
            config: Full configuration dictionary
        """
        self.config = config
        self.logger = SystemLogger("LearningAgent")

        # Initialize LLM client for insights generation
        try:
            self.llm_client = LLMClient(config['llm'])
            self.use_llm = True
            self.logger.info("LLM client initialized for feedback analysis")
        except Exception as e:
            self.logger.warning(f"LLM client unavailable: {e}")
            self.use_llm = False

        # Learning parameters
        learning_config = config.get('learning', {})
        self.minimum_feedbacks = learning_config.get('minimum_feedbacks', 50)
        self.decision_log_path = "data/outputs/decisions_log.csv"

        self.logger.info(
            f"LearningAgent initialized: "
            f"minimum_feedbacks={self.minimum_feedbacks}"
        )

    def analyze_feedback(self, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Analyze engineer feedback from recent decisions

        Args:
            lookback_days: Number of days to look back

        Returns:
            Dictionary with:
                - total_decisions: int
                - approval_rate: float (0-1)
                - rejection_reasons: dict {reason: count}
                - patterns: list of identified patterns
                - llm_insights: str (Korean analysis)
                - date_range: str
        """
        self.logger.info(f"Starting feedback analysis (lookback: {lookback_days} days)")

        # Load decision history
        try:
            decisions_df = pd.read_csv(self.decision_log_path)
            self.logger.info(f"Loaded {len(decisions_df)} decisions from log")
        except FileNotFoundError:
            self.logger.warning(f"Decision log not found: {self.decision_log_path}")
            return self._empty_analysis()
        except Exception as e:
            self.logger.error(f"Failed to load decision log: {e}")
            return self._empty_analysis()

        # Check minimum data requirement
        if len(decisions_df) < self.minimum_feedbacks:
            self.logger.warning(
                f"Insufficient data: {len(decisions_df)} < {self.minimum_feedbacks}"
            )
            return self._empty_analysis()

        # Filter recent decisions
        try:
            decisions_df['timestamp'] = pd.to_datetime(decisions_df['timestamp'])
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            recent_df = decisions_df[decisions_df['timestamp'] >= cutoff_date]

            self.logger.info(
                f"Analyzing {len(recent_df)} recent decisions "
                f"(from {cutoff_date.date()})"
            )

            if len(recent_df) == 0:
                self.logger.warning("No recent decisions found")
                return self._empty_analysis()

        except Exception as e:
            self.logger.error(f"Failed to filter decisions: {e}")
            return self._empty_analysis()

        # Calculate metrics
        total_decisions = len(recent_df)

        # Agreement: AI recommendation == Engineer decision
        recent_df['agreement'] = (
            recent_df['ai_recommendation'] == recent_df['engineer_decision']
        )
        approval_rate = recent_df['agreement'].mean()

        # Rejection analysis (disagreements)
        disagreements = recent_df[~recent_df['agreement']]
        rejection_reasons = self._analyze_rejection_reasons(disagreements)

        # Identify patterns
        patterns = self._identify_decision_patterns(recent_df)

        self.logger.info(
            f"Metrics calculated: {total_decisions} decisions, "
            f"{approval_rate:.1%} approval rate, "
            f"{len(disagreements)} disagreements"
        )

        # Generate LLM insights
        llm_insights = ""
        if self.use_llm:
            llm_insights = self._generate_llm_insights(
                recent_df,
                total_decisions,
                approval_rate,
                rejection_reasons,
                patterns
            )

        return {
            'total_decisions': int(total_decisions),
            'approval_rate': float(approval_rate),
            'agreement_count': int((recent_df['agreement']).sum()),
            'disagreement_count': int((~recent_df['agreement']).sum()),
            'rejection_reasons': rejection_reasons,
            'patterns': patterns,
            'llm_insights': llm_insights,
            'date_range': f"{cutoff_date.date()} ~ {datetime.now().date()}"
        }

    def _analyze_rejection_reasons(self, disagreements: pd.DataFrame) -> Dict[str, int]:
        """
        Analyze reasons for AI-Engineer disagreements

        Args:
            disagreements: DataFrame of disagreed decisions

        Returns:
            Dictionary of {reason: count}
        """
        if len(disagreements) == 0:
            return {}

        # Group by engineer rationale
        reasons = disagreements['engineer_rationale'].value_counts()

        # Convert to dict
        rejection_dict = {}
        for reason, count in reasons.items():
            if pd.notna(reason) and reason != "":
                rejection_dict[str(reason)] = int(count)

        # Add summary categories
        total_rejections = len(disagreements)

        # Categorize rejections
        categories = {
            '비용 관련': 0,
            '리스크 관련': 0,
            '신뢰도 관련': 0,
            '기타': 0
        }

        for reason in rejection_dict.keys():
            reason_lower = reason.lower()
            if any(word in reason_lower for word in ['cost', 'expensive', '비용', '가격']):
                categories['비용 관련'] += rejection_dict[reason]
            elif any(word in reason_lower for word in ['risk', '리스크', '위험']):
                categories['리스크 관련'] += rejection_dict[reason]
            elif any(word in reason_lower for word in ['confidence', '신뢰', 'false']):
                categories['신뢰도 관련'] += rejection_dict[reason]
            else:
                categories['기타'] += rejection_dict[reason]

        # Add categories to result
        result = rejection_dict.copy()
        result['_categories'] = categories

        return result

    def _identify_decision_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identify patterns in engineer decisions

        Args:
            df: DataFrame of decisions

        Returns:
            List of identified patterns
        """
        patterns = []

        # Pattern 1: Cost sensitivity
        try:
            high_cost = df[df['cost_usd'] > 500]
            low_cost = df[df['cost_usd'] <= 500]

            if len(high_cost) >= 10 and len(low_cost) >= 10:
                high_cost_approval = high_cost['agreement'].mean()
                low_cost_approval = low_cost['agreement'].mean()

                patterns.append({
                    'type': 'cost_sensitivity',
                    'high_cost_approval': float(high_cost_approval),
                    'low_cost_approval': float(low_cost_approval),
                    'high_cost_count': int(len(high_cost)),
                    'low_cost_count': int(len(low_cost)),
                    'finding': (
                        f"고비용 (>$500) 승인율: {high_cost_approval:.1%}, "
                        f"저비용 (≤$500) 승인율: {low_cost_approval:.1%}"
                    )
                })

                self.logger.info(f"Cost sensitivity pattern identified")
        except Exception as e:
            self.logger.warning(f"Cost sensitivity analysis failed: {e}")

        # Pattern 2: Confidence threshold
        try:
            high_conf = df[df['ai_confidence'] > 0.8]
            low_conf = df[df['ai_confidence'] <= 0.8]

            if len(high_conf) >= 10 and len(low_conf) >= 10:
                high_conf_approval = high_conf['agreement'].mean()
                low_conf_approval = low_conf['agreement'].mean()

                patterns.append({
                    'type': 'confidence_threshold',
                    'high_conf_approval': float(high_conf_approval),
                    'low_conf_approval': float(low_conf_approval),
                    'high_conf_count': int(len(high_conf)),
                    'low_conf_count': int(len(low_conf)),
                    'finding': (
                        f"고신뢰도 (>0.8) 승인율: {high_conf_approval:.1%}, "
                        f"저신뢰도 (≤0.8) 승인율: {low_conf_approval:.1%}"
                    )
                })

                self.logger.info(f"Confidence threshold pattern identified")
        except Exception as e:
            self.logger.warning(f"Confidence threshold analysis failed: {e}")

        # Pattern 3: Stage-specific approval rates
        try:
            stage_approval = df.groupby('stage')['agreement'].agg(['mean', 'count'])

            if len(stage_approval) > 1:
                stage_patterns = []
                for stage, row in stage_approval.iterrows():
                    if row['count'] >= 10:
                        stage_patterns.append({
                            'stage': stage,
                            'approval_rate': float(row['mean']),
                            'count': int(row['count'])
                        })

                if len(stage_patterns) > 0:
                    patterns.append({
                        'type': 'stage_approval',
                        'stages': stage_patterns,
                        'finding': (
                            f"스테이지별 승인율: " +
                            ", ".join([
                                f"{s['stage']}={s['approval_rate']:.1%}"
                                for s in stage_patterns
                            ])
                        )
                    })

                    self.logger.info(f"Stage-specific approval pattern identified")
        except Exception as e:
            self.logger.warning(f"Stage approval analysis failed: {e}")

        return patterns

    def _generate_llm_insights(
        self,
        df: pd.DataFrame,
        total: int,
        approval_rate: float,
        rejection_reasons: Dict[str, int],
        patterns: List[Dict[str, Any]]
    ) -> str:
        """
        Generate insights using LLM (Korean prompts)

        Args:
            df: Decisions dataframe
            total: Total decisions
            approval_rate: Approval rate
            rejection_reasons: Rejection reason counts
            patterns: Identified patterns

        Returns:
            LLM insights in Korean
        """
        if not self.use_llm:
            return "LLM 분석 불가 (API 키 미설정)"

        try:
            # Prepare example cases (disagreements)
            disagreements = df[~df['agreement']].head(10)
            example_cases = []

            for _, row in disagreements.iterrows():
                example_cases.append(
                    f"- {row['wafer_id']}: "
                    f"AI={row['ai_recommendation']} (신뢰도 {row['ai_confidence']:.2f}), "
                    f"Engineer={row['engineer_decision']}, "
                    f"이유=\"{row['engineer_rationale']}\""
                )

            example_text = "\n".join(example_cases) if example_cases else "사례 없음"

            # Format rejection reasons
            rejection_text = ""
            if '_categories' in rejection_reasons:
                categories = rejection_reasons['_categories']
                rejection_text += "카테고리별:\n"
                for cat, count in categories.items():
                    if count > 0:
                        rejection_text += f"- {cat}: {count}건\n"

            rejection_text += "\n구체적 이유:\n"
            for reason, count in rejection_reasons.items():
                if reason != '_categories':
                    rejection_text += f"- {reason}: {count}건\n"

            # Generate prompt
            prompt = format_feedback_learning_prompt(
                date_range=f"최근 {total}건 분석",
                total_decisions=total,
                approval_rate=approval_rate,
                rejection_reasons=rejection_text,
                example_cases=example_text
            )

            # Get LLM analysis
            self.logger.info("Requesting LLM feedback analysis")
            insights = self.llm_client.complete(
                prompt=prompt,
                category="learning_feedback",
                metadata={
                    'total_decisions': total,
                    'approval_rate': approval_rate
                }
            )

            self.logger.info("LLM feedback analysis completed")
            return insights

        except Exception as e:
            self.logger.error(f"LLM insights generation failed: {e}")
            return f"LLM 분석 실패: {str(e)}"

    def _empty_analysis(self) -> Dict[str, Any]:
        """
        Return empty analysis when insufficient data

        Returns:
            Empty analysis dictionary
        """
        return {
            'total_decisions': 0,
            'approval_rate': 0.0,
            'agreement_count': 0,
            'disagreement_count': 0,
            'rejection_reasons': {},
            'patterns': [],
            'llm_insights': "데이터 부족: 최소 {}건 필요".format(self.minimum_feedbacks),
            'date_range': "N/A"
        }
