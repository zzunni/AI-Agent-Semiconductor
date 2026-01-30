"""
Comprehensive logging utilities for the semiconductor quality control system

Provides three types of logging:
1. SystemLogger: Standard Python logging for system events
2. LLMLogger: LLM conversation logging to markdown files
3. DecisionLogger: Agent decision logging to CSV
"""

import logging
import os
import csv
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


class SystemLogger:
    """Standard logging for system events"""

    def __init__(self, name: str, log_level: str = "INFO"):
        """
        Initialize system logger

        Args:
            name: Logger name (typically module name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Create logs directory
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_format)

            # File handler (detailed logs)
            log_file = log_dir / f"{name.replace('.', '_')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)

            # Add handlers
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log debug level message"""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info level message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning level message"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error level message"""
        self.logger.error(message)

    def critical(self, message: str):
        """Log critical level message"""
        self.logger.critical(message)


class LLMLogger:
    """Logger for LLM conversations"""

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize LLM conversation logger

        Args:
            log_dir: Base directory for logs
        """
        self.log_dir = Path(log_dir)
        self._lock = threading.Lock()

        # Create category directories
        self.categories = {
            'pattern_discovery': self.log_dir / 'pattern_discovery',
            'root_cause_analysis': self.log_dir / 'root_cause_analysis',
            'learning_feedback': self.log_dir / 'learning_feedback'
        }

        for category_dir in self.categories.values():
            category_dir.mkdir(parents=True, exist_ok=True)

    def log_conversation(
        self,
        category: str,
        conversation_id: str,
        prompt: str,
        response: str,
        metadata: Optional[dict] = None
    ):
        """
        Log LLM conversation to markdown file

        Args:
            category: Category (pattern_discovery, root_cause_analysis, learning_feedback)
            conversation_id: Unique conversation identifier
            prompt: Prompt sent to LLM
            response: Response from LLM
            metadata: Optional metadata dictionary
        """
        if category not in self.categories:
            raise ValueError(f"Invalid category: {category}")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        date_str = datetime.now().strftime('%Y%m%d')

        # Generate filename
        filename = f"{date_str}_{conversation_id}.md"
        filepath = self.categories[category] / filename

        # Build markdown content
        content = f"""# Conversation: {conversation_id}

**Date**: {timestamp}
**Category**: {category}

"""

        if metadata:
            content += "**Metadata**:\n"
            for key, value in metadata.items():
                content += f"- {key}: {value}\n"
            content += "\n"

        content += f"""---

## Prompt

{prompt}

---

## Response

{response}

---

*Logged at {timestamp}*
"""

        # Thread-safe file writing
        with self._lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        return filepath

    def get_conversation_log(self, category: str, conversation_id: str) -> Optional[str]:
        """
        Retrieve a logged conversation

        Args:
            category: Category name
            conversation_id: Conversation ID

        Returns:
            Markdown content or None if not found
        """
        if category not in self.categories:
            return None

        # Search for file (may have different date prefix)
        category_dir = self.categories[category]
        for filepath in category_dir.glob(f"*_{conversation_id}.md"):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()

        return None


class DecisionLogger:
    """Logger for agent decisions"""

    def __init__(self, output_path: str = "data/outputs/decisions_log.csv"):
        """
        Initialize decision logger

        Args:
            output_path: Path to CSV file
        """
        self.output_path = Path(output_path)
        self._lock = threading.Lock()

        # Create output directory
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create CSV with headers if it doesn't exist
        if not self.output_path.exists():
            with self._lock:
                self._initialize_csv()

    def _initialize_csv(self):
        """Initialize CSV file with headers"""
        headers = [
            'timestamp',
            'wafer_id',
            'stage',
            'ai_recommendation',
            'ai_confidence',
            'ai_reasoning',
            'engineer_decision',
            'engineer_rationale',
            'response_time_sec',
            'cost_usd'
        ]

        with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def log_decision(
        self,
        timestamp: str,
        wafer_id: str,
        stage: str,
        ai_recommendation: str,
        ai_confidence: float,
        ai_reasoning: str,
        engineer_decision: str,
        engineer_rationale: str = "",
        response_time: float = 0,
        cost: float = 0
    ):
        """
        Log agent decision to CSV

        Args:
            timestamp: ISO 8601 timestamp
            wafer_id: Wafer identifier
            stage: Pipeline stage (stage0, stage1, stage2b, stage3)
            ai_recommendation: AI's recommendation
            ai_confidence: Confidence score (0-1)
            ai_reasoning: AI's reasoning
            engineer_decision: Engineer's final decision
            engineer_rationale: Engineer's rationale (optional)
            response_time: Time to make decision in seconds
            cost: Cost in USD
        """
        row = [
            timestamp,
            wafer_id,
            stage,
            ai_recommendation,
            f"{ai_confidence:.4f}",
            ai_reasoning,
            engineer_decision,
            engineer_rationale,
            f"{response_time:.2f}",
            f"{cost:.2f}"
        ]

        # Thread-safe CSV writing
        with self._lock:
            with open(self.output_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def get_decisions(self, wafer_id: Optional[str] = None) -> list:
        """
        Retrieve logged decisions

        Args:
            wafer_id: Optional wafer ID to filter by

        Returns:
            List of decision dictionaries
        """
        if not self.output_path.exists():
            return []

        decisions = []
        with open(self.output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if wafer_id is None or row['wafer_id'] == wafer_id:
                    decisions.append(row)

        return decisions

    def get_agreement_rate(self, stage: Optional[str] = None) -> float:
        """
        Calculate agreement rate between AI and engineer

        Args:
            stage: Optional stage to filter by

        Returns:
            Agreement rate as percentage (0-100)
        """
        decisions = self.get_decisions()

        if stage:
            decisions = [d for d in decisions if d['stage'] == stage]

        if not decisions:
            return 0.0

        agreements = sum(
            1 for d in decisions
            if d['ai_recommendation'] == d['engineer_decision']
        )

        return (agreements / len(decisions)) * 100
