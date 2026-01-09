"""
LLM client for Claude API interactions.

Handles model selection, JSON parsing, retry logic, and repair calls.
"""

import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar

from anthropic import Anthropic
from pydantic import BaseModel

from app.config import settings
from app.services.validator import ValidationResult, Validator

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Client for Claude API with retry and repair logic."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        max_retries: int = None,
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: Anthropic API key (defaults to settings)
            default_model: Default model to use (defaults to settings)
            fallback_model: Stronger model for retries (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.default_model = default_model or settings.default_model
        self.fallback_model = fallback_model or settings.fallback_model
        self.max_retries = max_retries if max_retries is not None else settings.max_retries
        self.validator = Validator()

        # Initialize Anthropic client
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("No Anthropic API key provided - LLM calls will fail")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        """
        Generate a response from Claude.
        
        Args:
            system_prompt: System prompt for context
            user_prompt: User message/prompt
            model: Model to use (defaults to default_model)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text or None if failed
        """
        if not self.client:
            logger.error("Anthropic client not initialized")
            return None

        model = model or self.default_model

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            if response.content and len(response.content) > 0:
                return response.content[0].text

            logger.error("Empty response from Claude")
            return None

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate JSON response from Claude.
        
        Args:
            system_prompt: System prompt (should instruct JSON output)
            user_prompt: User message/prompt
            model: Model to use
            max_tokens: Maximum tokens
            
        Returns:
            Parsed JSON dict or None if failed
        """
        response = self.generate(system_prompt, user_prompt, model, max_tokens)

        if not response:
            return None

        return self._extract_json(response)

    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from response text."""
        # Try to find JSON in the response
        text = response.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try to find JSON block without language tag
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try to find { ... } pattern
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        logger.error(f"Failed to extract JSON from response: {text[:200]}...")
        return None

    def generate_and_validate(
        self,
        system_prompt: str,
        user_prompt: str,
        model_class: Type[T],
        validation_context: Optional[Dict[str, Any]] = None,
    ) -> tuple[Optional[T], ValidationResult]:
        """
        Generate JSON and validate against a Pydantic model with retry logic.
        
        Args:
            system_prompt: System prompt for generation
            user_prompt: User prompt
            model_class: Pydantic model class to validate against
            validation_context: Additional context for validation (e.g., recent_logs)
            
        Returns:
            Tuple of (validated model or None, validation result)
        """
        validation_context = validation_context or {}
        model = self.default_model
        last_result: Optional[ValidationResult] = None

        for attempt in range(self.max_retries + 1):
            # Switch to stronger model only on final retry (cost optimization)
            if attempt == self.max_retries and self.max_retries > 0:
                model = self.fallback_model
                logger.info(f"Final retry {attempt}/{self.max_retries} with stronger model {model}")
            elif attempt > 0:
                logger.info(f"Retry {attempt}/{self.max_retries} with model {model}")

            # Generate JSON
            json_data = self.generate_json(system_prompt, user_prompt, model=model)

            if not json_data:
                logger.warning(f"Attempt {attempt + 1}: Failed to generate JSON")
                continue

            # Validate based on model class name
            if model_class.__name__ == "WorkoutPlan":
                result = self.validator.validate_workout_plan(
                    json_data,
                    recent_logs=validation_context.get("recent_logs"),
                    has_pain=validation_context.get("has_pain", False),
                    pain_body_part=validation_context.get("pain_body_part"),
                    days_since_last_workout=validation_context.get("days_since_last_workout", 0),
                )
            elif model_class.__name__ == "ThreeWeekBlock":
                result = self.validator.validate_three_week_block(json_data)
            elif model_class.__name__ == "HighLevelPlan":
                result = self.validator.validate_high_level_plan(json_data)
            else:
                # Generic schema validation
                validated, errors = self.validator.validate_schema(json_data, model_class)
                result = ValidationResult(
                    is_valid=validated is not None,
                    data=validated,
                    schema_errors=errors,
                )

            last_result = result

            if result.is_valid:
                logger.info(f"Validation passed on attempt {attempt + 1}")
                return result.data, result

            # Log validation errors
            logger.warning(f"Attempt {attempt + 1} validation failed: {result.all_errors}")

            # Try repair on next iteration
            if attempt < self.max_retries:
                user_prompt = self._build_repair_prompt(
                    user_prompt, json_data, result
                )

        logger.error(f"All {self.max_retries + 1} attempts failed")
        return None, last_result or ValidationResult(is_valid=False)

    def _build_repair_prompt(
        self,
        original_prompt: str,
        failed_json: Dict[str, Any],
        validation_result: ValidationResult,
    ) -> str:
        """Build a repair prompt including validation errors."""
        errors_text = "\n".join(f"- {e}" for e in validation_result.all_errors)

        return f"""Your previous response had validation errors. Please fix them.

ORIGINAL REQUEST:
{original_prompt}

YOUR PREVIOUS OUTPUT (with errors):
```json
{json.dumps(failed_json, indent=2)}
```

VALIDATION ERRORS:
{errors_text}

Please provide a corrected JSON response that fixes all the above errors.
Ensure your response is valid JSON matching the required schema.
"""


# Global LLM client instance
llm_client = LLMClient()

