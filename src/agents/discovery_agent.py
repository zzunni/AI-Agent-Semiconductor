"""
Pattern Discovery Agent: Statistical Pattern Detection

Analyzes wafer data to discover statistically significant patterns
Uses LLM to interpret patterns and generate actionable insights

This agent performs:
- Sensor-pattern correlation analysis
- Chamber effect detection
- Temporal trend analysis
- LLM-powered interpretation (Korean)
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Any, Optional

from src.utils.data_loader import DataLoader
from src.utils.logger import SystemLogger
from src.llm.client import LLMClient
from src.llm.prompts import format_pattern_discovery_prompt


class DiscoveryAgent:
    """
    Pattern Discovery: Find statistically significant patterns in wafer data

    Methods:
    - discover_patterns(): Find all significant patterns
    - detect_correlations(): Sensor-defect correlations
    - detect_chamber_effects(): Chamber-specific patterns
    - analyze_with_llm(): LLM interpretation
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Pattern Discovery Agent

        Args:
            config: Full configuration dictionary
        """
        self.config = config
        self.logger = SystemLogger("DiscoveryAgent")
        self.data_loader = DataLoader()

        # Initialize LLM client for pattern interpretation
        try:
            self.llm_client = LLMClient(config['llm'])
            self.use_llm = True
            self.logger.info("LLM client initialized for pattern analysis")
        except Exception as e:
            self.logger.warning(f"LLM client unavailable: {e}")
            self.use_llm = False

        # Discovery parameters
        discovery_config = config.get('discovery', {})
        self.lookback_days = discovery_config.get('lookback_days', 14)
        self.significance_threshold = discovery_config.get('significance_threshold', 0.01)

        self.logger.info(
            f"DiscoveryAgent initialized: "
            f"lookback_days={self.lookback_days}, "
            f"significance_threshold={self.significance_threshold}"
        )

    def discover_patterns(self) -> List[Dict[str, Any]]:
        """
        Discover all statistically significant patterns

        Returns:
            List of discovered patterns with statistical analysis and LLM insights

        Example pattern:
            {
                'type': 'sensor_pattern_correlation',
                'sensor': 'etch_rate',
                'pattern': 'Edge-Ring',
                'correlation': 0.85,
                'p_value': 0.001,
                'evidence': '201 Edge-Ring wafers...',
                'llm_analysis': 'Korean root cause...'
            }
        """
        self.logger.info("Starting pattern discovery analysis")
        patterns = []

        try:
            # Load datasets
            step1_df = self.data_loader.load_step1_data()
            wm811k_df = self.data_loader.load_wm811k_proxy()

            # Merge for combined analysis
            merged_df = step1_df.merge(wm811k_df, on='wafer_id', how='inner')
            self.logger.info(f"Analyzing {len(merged_df)} wafers with complete data")

            # Pattern 1: Sensor-Pattern correlations
            sensor_patterns = self._detect_sensor_pattern_correlation(merged_df)
            patterns.extend(sensor_patterns)
            self.logger.info(f"Found {len(sensor_patterns)} sensor-pattern correlations")

            # Pattern 2: Chamber effects
            chamber_patterns = self._detect_chamber_effects(merged_df)
            patterns.extend(chamber_patterns)
            self.logger.info(f"Found {len(chamber_patterns)} chamber effects")

            # Pattern 3: Recipe effects
            recipe_patterns = self._detect_recipe_effects(merged_df)
            patterns.extend(recipe_patterns)
            self.logger.info(f"Found {len(recipe_patterns)} recipe effects")

            # Analyze patterns with LLM (if available)
            if self.use_llm:
                self.logger.info("Analyzing patterns with LLM")
                for i, pattern in enumerate(patterns):
                    try:
                        pattern['llm_analysis'] = self._analyze_pattern_with_llm(pattern)
                        self.logger.debug(f"LLM analysis completed for pattern {i+1}")
                    except Exception as e:
                        self.logger.error(f"LLM analysis failed for pattern {i+1}: {e}")
                        pattern['llm_analysis'] = f"분석 실패: {str(e)}"

            self.logger.info(f"Pattern discovery complete: {len(patterns)} patterns found")
            return patterns

        except Exception as e:
            self.logger.error(f"Pattern discovery failed: {e}")
            return []

    def _detect_sensor_pattern_correlation(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect correlations between sensors and defect patterns

        Args:
            df: Merged dataframe with sensor and pattern data

        Returns:
            List of significant sensor-pattern correlations
        """
        patterns = []
        sensors = ['etch_rate', 'pressure', 'temperature', 'rf_power', 'gas_flow']
        pattern_types = ['Edge-Ring', 'Center', 'Random']

        for sensor in sensors:
            for pattern_type in pattern_types:
                # Compare sensor values for this pattern vs others
                pattern_group = df[df['pattern_type'] == pattern_type]
                other_group = df[df['pattern_type'] != pattern_type]

                # Need sufficient samples for valid test
                if len(pattern_group) < 10 or len(other_group) < 10:
                    continue

                # Perform t-test
                try:
                    t_stat, p_value = stats.ttest_ind(
                        pattern_group[sensor],
                        other_group[sensor],
                        equal_var=False  # Welch's t-test
                    )

                    # Check for statistical significance
                    if p_value < self.significance_threshold:
                        pattern_mean = pattern_group[sensor].mean()
                        other_mean = other_group[sensor].mean()
                        correlation = df[sensor].corr(df['severity'])

                        patterns.append({
                            'type': 'sensor_pattern_correlation',
                            'sensor': sensor,
                            'pattern': pattern_type,
                            'correlation': float(correlation),
                            'p_value': float(p_value),
                            't_statistic': float(t_stat),
                            'pattern_mean': float(pattern_mean),
                            'other_mean': float(other_mean),
                            'pattern_count': int(len(pattern_group)),
                            'confidence': float(1 - p_value),
                            'evidence': (
                                f"{len(pattern_group)}개 {pattern_type} 웨이퍼에서 "
                                f"{sensor}={pattern_mean:.2f} "
                                f"(기타: {other_mean:.2f})"
                            )
                        })

                except Exception as e:
                    self.logger.warning(
                        f"T-test failed for {sensor} vs {pattern_type}: {e}"
                    )

        return patterns

    def _detect_chamber_effects(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect chamber-specific effects on defect patterns

        Args:
            df: Merged dataframe

        Returns:
            List of significant chamber effects
        """
        patterns = []

        try:
            chambers = df['chamber'].unique()

            # Need at least 2 chambers for comparison
            if len(chambers) < 2:
                return patterns

            # ANOVA test: Do chambers have different defect rates?
            chamber_groups = [
                df[df['chamber'] == chamber]['severity'].dropna()
                for chamber in chambers
            ]

            # Filter out empty groups
            chamber_groups = [g for g in chamber_groups if len(g) > 0]

            if len(chamber_groups) < 2:
                return patterns

            f_stat, p_value = stats.f_oneway(*chamber_groups)

            # Check for statistical significance
            if p_value < self.significance_threshold:
                chamber_stats = []
                for chamber in chambers:
                    chamber_df = df[df['chamber'] == chamber]
                    if len(chamber_df) > 0:
                        chamber_stats.append({
                            'chamber': chamber,
                            'mean_severity': float(chamber_df['severity'].mean()),
                            'std_severity': float(chamber_df['severity'].std()),
                            'count': int(len(chamber_df)),
                            'edge_ring_rate': float(
                                (chamber_df['pattern_type'] == 'Edge-Ring').sum() / len(chamber_df)
                            )
                        })

                # Sort by severity
                chamber_stats.sort(key=lambda x: x['mean_severity'], reverse=True)

                patterns.append({
                    'type': 'chamber_effect',
                    'p_value': float(p_value),
                    'f_statistic': float(f_stat),
                    'chamber_stats': chamber_stats,
                    'confidence': float(1 - p_value),
                    'evidence': (
                        f"챔버별 결함률 차이 발견 (F={f_stat:.2f}, p={p_value:.4f}). "
                        f"최고: {chamber_stats[0]['chamber']} ({chamber_stats[0]['mean_severity']:.2f}), "
                        f"최저: {chamber_stats[-1]['chamber']} ({chamber_stats[-1]['mean_severity']:.2f})"
                    )
                })

        except Exception as e:
            self.logger.warning(f"Chamber effect detection failed: {e}")

        return patterns

    def _detect_recipe_effects(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect recipe-specific effects

        Args:
            df: Merged dataframe

        Returns:
            List of significant recipe effects
        """
        patterns = []

        try:
            recipes = df['recipe'].unique()

            # Need at least 2 recipes for comparison
            if len(recipes) < 2:
                return patterns

            # ANOVA test for recipe effects
            recipe_groups = [
                df[df['recipe'] == recipe]['severity'].dropna()
                for recipe in recipes
            ]

            # Filter out empty groups
            recipe_groups = [g for g in recipe_groups if len(g) > 0]

            if len(recipe_groups) < 2:
                return patterns

            f_stat, p_value = stats.f_oneway(*recipe_groups)

            # Check for statistical significance
            if p_value < self.significance_threshold:
                recipe_stats = []
                for recipe in recipes:
                    recipe_df = df[df['recipe'] == recipe]
                    if len(recipe_df) > 0:
                        recipe_stats.append({
                            'recipe': recipe,
                            'mean_severity': float(recipe_df['severity'].mean()),
                            'count': int(len(recipe_df))
                        })

                # Sort by severity
                recipe_stats.sort(key=lambda x: x['mean_severity'], reverse=True)

                patterns.append({
                    'type': 'recipe_effect',
                    'p_value': float(p_value),
                    'f_statistic': float(f_stat),
                    'recipe_stats': recipe_stats,
                    'confidence': float(1 - p_value),
                    'evidence': (
                        f"레시피별 결함률 차이 발견 (F={f_stat:.2f}, p={p_value:.4f})"
                    )
                })

        except Exception as e:
            self.logger.warning(f"Recipe effect detection failed: {e}")

        return patterns

    def _analyze_pattern_with_llm(self, pattern: Dict[str, Any]) -> str:
        """
        Analyze discovered pattern using LLM (Korean prompts)

        Args:
            pattern: Pattern dictionary with statistical data

        Returns:
            LLM analysis text in Korean
        """
        if not self.use_llm:
            return "LLM 분석 불가 (API 키 미설정)"

        try:
            # Build appropriate prompt based on pattern type
            if pattern['type'] == 'sensor_pattern_correlation':
                prompt = format_pattern_discovery_prompt(
                    pattern_type=f"{pattern['sensor']} - {pattern['pattern']} 상관관계",
                    evidence=pattern['evidence'],
                    correlation=pattern['correlation'],
                    p_value=pattern['p_value'],
                    confidence=pattern['confidence'],
                    sensor_summary=f"""
{pattern['sensor']}:
- {pattern['pattern']} 패턴: {pattern['pattern_mean']:.2f}
- 기타 패턴: {pattern['other_mean']:.2f}
- 차이: {abs(pattern['pattern_mean'] - pattern['other_mean']):.2f}
                    """,
                    process_history=f"""
- 분석 웨이퍼 수: {pattern['pattern_count']}개
- 통계적 유의성: t={pattern['t_statistic']:.2f}, p={pattern['p_value']:.4f}
                    """
                )

            elif pattern['type'] == 'chamber_effect':
                chamber_summary = "\n".join([
                    f"- {cs['chamber']}: 평균 severity {cs['mean_severity']:.2f} ({cs['count']}개)"
                    for cs in pattern['chamber_stats']
                ])

                prompt = format_pattern_discovery_prompt(
                    pattern_type="챔버 효과",
                    evidence=pattern['evidence'],
                    correlation=0,  # N/A for chamber effects
                    p_value=pattern['p_value'],
                    confidence=pattern['confidence'],
                    sensor_summary=chamber_summary,
                    process_history=f"ANOVA: F={pattern['f_statistic']:.2f}"
                )

            else:
                # Generic pattern
                prompt = f"""
다음 패턴을 분석하세요:

패턴 유형: {pattern['type']}
증거: {pattern.get('evidence', 'N/A')}
P-value: {pattern.get('p_value', 'N/A')}
신뢰도: {pattern.get('confidence', 'N/A')}

근본 원인과 권장 조치를 제시하세요.
                """

            # Get LLM analysis
            analysis = self.llm_client.complete(
                prompt=prompt,
                category="pattern_discovery",
                metadata={
                    'pattern_type': pattern['type'],
                    'p_value': pattern.get('p_value')
                }
            )

            return analysis

        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return f"LLM 분석 실패: {str(e)}"
