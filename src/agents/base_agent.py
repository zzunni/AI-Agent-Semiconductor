"""
Base Agent Class for Multi-Stage Inspection Pipeline

This abstract base class provides common functionality for all agents:
- Model loading and inference
- Decision logging
- Configuration management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pickle
import os
import pandas as pd
from datetime import datetime

from src.utils.logger import SystemLogger, DecisionLogger


class BaseAgent(ABC):
    """
    Abstract base class for all inspection agents

    All child agents (Stage0Agent, Stage1Agent, etc.) must inherit from this
    and implement the abstract methods.
    """

    def __init__(
        self,
        stage_name: str,
        config: Dict[str, Any],
        logger: Optional[SystemLogger] = None
    ):
        """
        Initialize base agent

        Args:
            stage_name: Name of the stage (e.g., "stage0", "stage1")
            config: Configuration dictionary for this stage
            logger: Optional SystemLogger instance
        """
        self.stage_name = stage_name
        self.config = config
        self.logger = logger or SystemLogger(f"Agent-{stage_name}")

        # Initialize decision logger
        self.decision_logger = DecisionLogger()

        # Load model
        self.model = None
        model_path = config.get('path')
        if model_path and os.path.exists(model_path):
            self.model = self._load_model(model_path)
            self.logger.info(f"Loaded model from {model_path}")
        else:
            self.logger.warning(f"Model path not found: {model_path}")

    def _load_model(self, model_path: str) -> Any:
        """
        Load pickled model from disk

        Args:
            model_path: Path to .pkl file

        Returns:
            Loaded model object

        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: If unpickling fails
        """
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            self.logger.info(f"Successfully loaded model: {model_path}")
            return model
        except FileNotFoundError:
            self.logger.error(f"Model file not found: {model_path}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise

    @abstractmethod
    def analyze(self, wafer_data: pd.Series) -> Dict[str, Any]:
        """
        Analyze wafer data and produce results

        Args:
            wafer_data: Single wafer data as pandas Series

        Returns:
            Dictionary containing analysis results
            Example: {
                'anomaly_score': 0.85,
                'is_anomaly': True,
                'confidence': 0.92
            }
        """
        pass

    @abstractmethod
    def make_recommendation(
        self,
        wafer_data: pd.Series,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate recommendation based on analysis

        Args:
            wafer_data: Single wafer data as pandas Series
            analysis_result: Output from analyze() method

        Returns:
            Dictionary containing recommendation
            Example: {
                'action': 'INLINE',  # or 'SEM', 'REWORK', 'PASS'
                'confidence': 0.85,
                'estimated_cost': 150,
                'reasoning': 'High anomaly score detected'
            }
        """
        pass

    def log_decision(
        self,
        wafer_id: str,
        ai_recommendation: str,
        ai_confidence: float,
        ai_reasoning: str,
        engineer_decision: str = "",
        engineer_rationale: str = "",
        response_time: float = 0,
        cost: float = 0
    ) -> None:
        """
        Log decision to CSV file

        Args:
            wafer_id: Wafer identifier
            ai_recommendation: AI's recommended action
            ai_confidence: Confidence score (0-1)
            ai_reasoning: AI's reasoning for recommendation
            engineer_decision: Engineer's actual decision (empty string if not decided)
            engineer_rationale: Engineer's reasoning (optional)
            response_time: Time to make decision in seconds (optional)
            cost: Cost in USD (optional)
        """
        self.decision_logger.log_decision(
            timestamp=datetime.now().isoformat(),
            wafer_id=wafer_id,
            stage=self.stage_name,
            ai_recommendation=ai_recommendation,
            ai_confidence=ai_confidence,
            ai_reasoning=ai_reasoning,
            engineer_decision=engineer_decision,
            engineer_rationale=engineer_rationale,
            response_time=response_time,
            cost=cost
        )

        self.logger.info(
            f"Logged decision for {wafer_id}: "
            f"AI={ai_recommendation} ({ai_confidence:.2f}), "
            f"Engineer={engineer_decision or 'N/A'}"
        )

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Safely retrieve configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
