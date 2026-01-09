"""
Validator service for schema and guardrail validation.

Combines Pydantic schema validation with deterministic guardrail checks.
This is the code enforcement layer - LLM outputs must pass all checks.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.models.plan import DaySlot, HighLevelPlan, ThreeWeekBlock
from app.models.workout import WorkoutLog, WorkoutPlan
from app.rules.guardrails import (
    GuardrailViolation,
    validate_block,
    validate_workout_plan,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ValidationResult:
    """Result of validation containing status and any errors."""

    def __init__(
        self,
        is_valid: bool,
        data: Optional[Any] = None,
        schema_errors: Optional[List[str]] = None,
        guardrail_violations: Optional[List[GuardrailViolation]] = None,
    ):
        self.is_valid = is_valid
        self.data = data
        self.schema_errors = schema_errors or []
        self.guardrail_violations = guardrail_violations or []

    @property
    def all_errors(self) -> List[str]:
        """Get all error messages."""
        errors = self.schema_errors.copy()
        for v in self.guardrail_violations:
            errors.append(f"[{v.rule}] {v.message}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for repair prompts."""
        return {
            "is_valid": self.is_valid,
            "schema_errors": self.schema_errors,
            "guardrail_violations": [
                {"rule": v.rule, "message": v.message, "severity": v.severity}
                for v in self.guardrail_violations
            ],
        }


class Validator:
    """Service for validating LLM outputs against schemas and guardrails."""

    def validate_schema(
        self, data: Dict[str, Any], model_class: Type[T]
    ) -> Tuple[Optional[T], List[str]]:
        """
        Validate data against a Pydantic model schema.
        
        Returns:
            Tuple of (parsed model or None, list of error messages)
        """
        try:
            model = model_class.model_validate(data)
            return model, []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                msg = error["msg"]
                errors.append(f"{loc}: {msg}")
            return None, errors

    def validate_high_level_plan(
        self, data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate a high-level plan."""
        model, schema_errors = self.validate_schema(data, HighLevelPlan)

        if not model:
            return ValidationResult(
                is_valid=False,
                schema_errors=schema_errors,
            )

        # High-level plan has minimal guardrails - mainly schema validation
        # Check that duration is reasonable
        violations = []
        if model.duration_weeks < 4 or model.duration_weeks > 16:
            violations.append(
                GuardrailViolation(
                    rule="plan_duration",
                    message=f"Plan duration {model.duration_weeks} weeks is outside 4-16 week range",
                    severity="warning",
                )
            )

        # Check that phase breakdown covers the duration
        total_weeks_covered = 0
        for phase in model.phase_breakdown:
            weeks_str = phase.weeks
            if "-" in weeks_str:
                start, end = weeks_str.split("-")
                total_weeks_covered += int(end) - int(start) + 1
            else:
                total_weeks_covered += 1

        if total_weeks_covered < model.duration_weeks:
            violations.append(
                GuardrailViolation(
                    rule="phase_coverage",
                    message=f"Phase breakdown covers {total_weeks_covered} weeks but plan is {model.duration_weeks} weeks",
                    severity="warning",
                )
            )

        is_valid = not any(v.severity == "error" for v in violations)

        return ValidationResult(
            is_valid=is_valid,
            data=model,
            guardrail_violations=violations,
        )

    def validate_three_week_block(
        self, data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate a 21-day block."""
        model, schema_errors = self.validate_schema(data, ThreeWeekBlock)

        if not model:
            return ValidationResult(
                is_valid=False,
                schema_errors=schema_errors,
            )

        # Run guardrail validation
        is_valid, violations = validate_block(model)

        # Additional checks
        # Verify dates are sequential
        from datetime import datetime, timedelta

        try:
            start = datetime.fromisoformat(model.start_date)
            for i, slot in enumerate(model.day_slots):
                expected_date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
                if slot.date != expected_date:
                    violations.append(
                        GuardrailViolation(
                            rule="date_sequence",
                            message=f"Day {i+1} has date {slot.date}, expected {expected_date}",
                            severity="error",
                        )
                    )
                    is_valid = False
                    break
        except ValueError as e:
            violations.append(
                GuardrailViolation(
                    rule="date_format",
                    message=f"Invalid date format: {e}",
                    severity="error",
                )
            )
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            data=model,
            guardrail_violations=violations,
        )

    def validate_workout_plan(
        self,
        data: Dict[str, Any],
        recent_logs: Optional[List[WorkoutLog]] = None,
        has_pain: bool = False,
        pain_body_part: Optional[str] = None,
        days_since_last_workout: int = 0,
    ) -> ValidationResult:
        """
        Validate a workout plan against schema and guardrails.
        
        Args:
            data: Raw JSON data from LLM
            recent_logs: Recent workout history for context
            has_pain: Whether user reported pain
            pain_body_part: Which body part has pain
            days_since_last_workout: Days since last completed workout
        """
        model, schema_errors = self.validate_schema(data, WorkoutPlan)

        if not model:
            return ValidationResult(
                is_valid=False,
                schema_errors=schema_errors,
            )

        # Run guardrail validation
        is_valid, violations = validate_workout_plan(
            workout=model,
            recent_logs=recent_logs or [],
            has_pain=has_pain,
            pain_body_part=pain_body_part,
            days_since_last_workout=days_since_last_workout,
        )

        # Additional workout-specific checks
        # Check that workout has at least one exercise in main section
        main_sections = [s for s in model.sections if s.name == "main"]
        if not main_sections or not main_sections[0].items:
            violations.append(
                GuardrailViolation(
                    rule="empty_workout",
                    message="Workout must have at least one exercise in main section",
                    severity="error",
                )
            )
            is_valid = False

        # Check duration is reasonable
        if model.estimated_duration_min < 10:
            violations.append(
                GuardrailViolation(
                    rule="duration_too_short",
                    message=f"Workout duration {model.estimated_duration_min}min is too short",
                    severity="warning",
                )
            )
        elif model.estimated_duration_min > 180:
            violations.append(
                GuardrailViolation(
                    rule="duration_too_long",
                    message=f"Workout duration {model.estimated_duration_min}min exceeds 3 hours",
                    severity="warning",
                )
            )

        return ValidationResult(
            is_valid=is_valid,
            data=model,
            guardrail_violations=violations,
        )

    def validate_day_slot(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate a single day slot."""
        model, schema_errors = self.validate_schema(data, DaySlot)

        if not model:
            return ValidationResult(
                is_valid=False,
                schema_errors=schema_errors,
            )

        violations = []

        # Check that rest days don't have workout details
        if model.is_rest_day and model.workout_type:
            violations.append(
                GuardrailViolation(
                    rule="rest_day_conflict",
                    message="Rest day should not have a workout type assigned",
                    severity="warning",
                )
            )

        # Check that non-rest days have workout type
        if not model.is_rest_day and not model.workout_type:
            violations.append(
                GuardrailViolation(
                    rule="missing_workout_type",
                    message="Training day must have a workout type",
                    severity="error",
                )
            )

        is_valid = not any(v.severity == "error" for v in violations)

        return ValidationResult(
            is_valid=is_valid,
            data=model,
            guardrail_violations=violations,
        )


# Global validator instance
validator = Validator()

