"""
LLM Client for Anthropic Claude API integration

Simple wrapper for Claude API calls - no LangChain/LangGraph needed
"""

import anthropic
import os
import time
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import LLMLogger, SystemLogger


class LLMClient:
    """
    Simple wrapper for Anthropic Claude API

    No LangChain/LangGraph needed - just direct API calls

    Usage:
        config = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "temperature": 0.3,
            "api_key_env": "ANTHROPIC_API_KEY"
        }
        client = LLMClient(config)
        response = client.complete("Analyze this defect pattern...")
    """

    def __init__(self, config: dict):
        """
        Initialize LLM client

        Args:
            config: Dictionary with llm configuration
                   Should contain: model, max_tokens, temperature, api_key_env
        """
        self.api_key = os.getenv(config["api_key_env"])
        if not self.api_key:
            raise ValueError(f"API key not found in environment: {config['api_key_env']}")

        self.model = config["model"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Initialize loggers
        self.llm_logger = LLMLogger()
        self.system_logger = SystemLogger("llm.client")

        self.system_logger.info(f"LLM Client initialized with model: {self.model}")

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        category: str = "general",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Send prompt to Claude and get response

        Args:
            prompt: User prompt
            system: System prompt (optional)
            category: Log category (pattern_discovery, root_cause_analysis, learning_feedback)
            metadata: Optional metadata to log with conversation

        Returns:
            response_text (str)

        Example:
            >>> response = client.complete(
            ...     prompt="Analyze defect pattern...",
            ...     system="You are a semiconductor expert",
            ...     category="pattern_discovery"
            ... )
        """
        try:
            # Default system prompt
            if system is None:
                system = "You are an expert in semiconductor manufacturing and quality control."

            self.system_logger.debug(f"Sending request to {self.model}")

            # Make API call
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract response text
            response_text = message.content[0].text

            # Log conversation
            conversation_id = f"{category}_{int(time.time())}"
            self.llm_logger.log_conversation(
                category=category,
                conversation_id=conversation_id,
                prompt=prompt,
                response=response_text,
                metadata=metadata
            )

            self.system_logger.info(f"Received response ({len(response_text)} chars)")

            return response_text

        except anthropic.APIError as e:
            self.system_logger.error(f"API Error: {e}")
            raise

    def complete_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        Complete with retry logic for rate limits

        Args:
            prompt: User prompt
            max_retries: Maximum retry attempts (default: 3)
            **kwargs: Additional arguments for complete()

        Returns:
            response_text (str)

        Example:
            >>> response = client.complete_with_retry(
            ...     prompt="Analyze...",
            ...     max_retries=5,
            ...     category="root_cause_analysis"
            ... )
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return self.complete(prompt, **kwargs)

            except anthropic.RateLimitError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s...
                    self.system_logger.warning(
                        f"Rate limited. Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    self.system_logger.error("Max retries exceeded for rate limit")
                    raise

            except anthropic.APIConnectionError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.system_logger.warning(
                        f"Connection error. Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    self.system_logger.error("Max retries exceeded for connection error")
                    raise

            except anthropic.APIError as e:
                # Don't retry on other API errors
                self.system_logger.error(f"API Error (non-retryable): {e}")
                raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception

    def complete_structured(
        self,
        prompt: str,
        expected_format: str,
        **kwargs
    ) -> str:
        """
        Complete with instruction to return structured output

        Args:
            prompt: User prompt
            expected_format: Description of expected format (e.g., "JSON", "bullet points")
            **kwargs: Additional arguments for complete()

        Returns:
            response_text (str)

        Example:
            >>> response = client.complete_structured(
            ...     prompt="List defect types",
            ...     expected_format="JSON with 'type', 'severity', 'description' fields"
            ... )
        """
        # Enhance prompt with format instruction
        enhanced_prompt = f"""{prompt}

Please format your response as {expected_format}.
"""

        return self.complete(enhanced_prompt, **kwargs)

    def batch_complete(
        self,
        prompts: list[str],
        delay: float = 0.5,
        **kwargs
    ) -> list[str]:
        """
        Process multiple prompts with rate limiting

        Args:
            prompts: List of prompts
            delay: Delay between requests in seconds (default: 0.5)
            **kwargs: Additional arguments for complete()

        Returns:
            List of responses

        Example:
            >>> prompts = ["Analyze wafer 1", "Analyze wafer 2"]
            >>> responses = client.batch_complete(prompts, delay=1.0)
        """
        responses = []

        for i, prompt in enumerate(prompts):
            self.system_logger.info(f"Processing prompt {i + 1}/{len(prompts)}")

            response = self.complete_with_retry(prompt, **kwargs)
            responses.append(response)

            # Add delay between requests (except after last one)
            if i < len(prompts) - 1 and delay > 0:
                time.sleep(delay)

        return responses
