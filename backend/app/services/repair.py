"""
Repair service for fixing invalid LLM outputs.

This module is used by the LLM client when validation fails.
The repair logic is primarily handled in llm_client.py.
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def format_validation_errors(errors: List[str]) -> str:
    """Format validation errors for inclusion in repair prompt."""
    if not errors:
        return "No specific errors"

    formatted = []
    for i, error in enumerate(errors, 1):
        formatted.append(f"{i}. {error}")

    return "\n".join(formatted)


def create_repair_context(
    original_output: Dict[str, Any],
    validation_errors: List[str],
    schema_name: str,
) -> Dict[str, Any]:
    """Create context for a repair attempt."""
    return {
        "original_output": original_output,
        "errors": validation_errors,
        "schema_name": schema_name,
        "error_summary": format_validation_errors(validation_errors),
    }


def suggest_fixes(errors: List[str]) -> List[str]:
    """Suggest fixes based on common error patterns."""
    suggestions = []

    for error in errors:
        error_lower = error.lower()

        if "required" in error_lower or "missing" in error_lower:
            suggestions.append("Add the missing required field with an appropriate value")

        elif "type" in error_lower:
            suggestions.append("Ensure the field has the correct data type")

        elif "rpe" in error_lower or "intensity" in error_lower:
            suggestions.append("Reduce the RPE or intensity to comply with limits")

        elif "consecutive" in error_lower:
            suggestions.append("Add a rest day or lower intensity to avoid consecutive hard days")

        elif "rest day" in error_lower:
            suggestions.append("Include at least 1 rest day per week")

        elif "date" in error_lower:
            suggestions.append("Ensure dates are in YYYY-MM-DD format and sequential")

        elif "21" in error_lower or "day_slots" in error_lower:
            suggestions.append("Ensure exactly 21 day_slots are included")

        elif "pain" in error_lower:
            suggestions.append("Reduce intensity to RPE 5 or below when pain is reported")

    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)

    return unique_suggestions if unique_suggestions else ["Review the schema and ensure all fields match expected types"]

