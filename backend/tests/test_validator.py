"""
Unit tests for validator service.

Tests schema validation and guardrail checks.
"""

from datetime import datetime, timedelta

import pytest

from app.models.plan import DaySlot, ThreeWeekBlock
from app.models.workout import WorkoutLog, WorkoutPlan
from app.services.validator import ValidationResult, Validator

from tests.fixtures.sample_data import (
    SAMPLE_WORKOUT_LOG,
    SAMPLE_WORKOUT_PLAN,
    generate_sample_day_slots,
)


@pytest.fixture
def validator():
    """Create a validator instance."""
    return Validator()


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_valid_workout_plan_schema(self, validator):
        """Test validation of valid workout plan."""
        result = validator.validate_workout_plan(SAMPLE_WORKOUT_PLAN)
        assert result.is_valid
        assert result.data is not None
        assert len(result.schema_errors) == 0

    def test_invalid_workout_plan_missing_field(self, validator):
        """Test validation fails with missing required field."""
        data = SAMPLE_WORKOUT_PLAN.copy()
        del data["workout_type"]
        result = validator.validate_workout_plan(data)
        assert not result.is_valid
        assert len(result.schema_errors) > 0

    def test_valid_day_slot(self, validator):
        """Test validation of valid day slot."""
        slot_data = {
            "day_number": 1,
            "date": "2025-01-06",
            "workout_type": "strength",
            "target_duration_min": 45,
            "intensity_target": "RPE_7_8",
            "is_rest_day": False,
            "status": "planned",
        }
        result = validator.validate_day_slot(slot_data)
        assert result.is_valid

    def test_rest_day_with_workout_type_warning(self, validator):
        """Test that rest day with workout type generates warning."""
        slot_data = {
            "day_number": 1,
            "date": "2025-01-06",
            "workout_type": "strength",  # Should be None for rest day
            "is_rest_day": True,
            "status": "planned",
        }
        result = validator.validate_day_slot(slot_data)
        # Should pass but have a warning
        assert result.is_valid
        assert len(result.guardrail_violations) > 0


class TestWorkoutPlanGuardrails:
    """Tests for workout plan guardrail validation."""

    def test_workout_with_pain_feedback_high_rpe(self, validator):
        """Test that high RPE is rejected when pain feedback is present."""
        data = SAMPLE_WORKOUT_PLAN.copy()
        data["intensity_target"] = "RPE_8_9"  # Too high for pain

        result = validator.validate_workout_plan(
            data,
            has_pain=True,
            pain_body_part="shoulder",
        )

        # Should have a critical violation for pain + high RPE
        violations = [v for v in result.guardrail_violations if v.rule == "pain_intensity"]
        assert len(violations) > 0

    def test_workout_empty_main_section(self, validator):
        """Test that empty main section fails validation."""
        data = SAMPLE_WORKOUT_PLAN.copy()
        # Remove all items from main section
        for section in data["sections"]:
            if section["name"] == "main":
                section["items"] = []

        result = validator.validate_workout_plan(data)
        assert not result.is_valid
        violations = [v for v in result.guardrail_violations if v.rule == "empty_workout"]
        assert len(violations) > 0


class TestBlockValidation:
    """Tests for three-week block validation."""

    def test_valid_block(self, validator):
        """Test validation of valid 21-day block."""
        start_date = "2025-01-06"
        slots = generate_sample_day_slots(start_date)

        block_data = {
            "block_number": 1,
            "start_date": start_date,
            "end_date": "2025-01-26",
            "day_slots": slots,
            "created_at": datetime.now().isoformat(),
        }

        result = validator.validate_three_week_block(block_data)
        assert result.is_valid

    def test_block_missing_rest_days(self, validator):
        """Test that block without rest days fails."""
        start_date = "2025-01-06"
        start = datetime.fromisoformat(start_date)

        # Create 21 training days (no rest)
        slots = []
        for i in range(21):
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            slots.append({
                "day_number": i + 1,
                "date": date,
                "workout_type": "endurance",
                "target_duration_min": 45,
                "intensity_target": "RPE_6_7",
                "is_rest_day": False,
                "status": "planned",
                "workout_id": None,
            })

        block_data = {
            "block_number": 1,
            "start_date": start_date,
            "end_date": "2025-01-26",
            "day_slots": slots,
            "created_at": datetime.now().isoformat(),
        }

        result = validator.validate_three_week_block(block_data)
        assert not result.is_valid
        # Should have rest day requirement violations
        assert len(result.guardrail_violations) > 0

    def test_block_wrong_date_sequence(self, validator):
        """Test that non-sequential dates fail validation."""
        start_date = "2025-01-06"
        slots = generate_sample_day_slots(start_date)
        # Mess up a date
        slots[5]["date"] = "2025-02-15"

        block_data = {
            "block_number": 1,
            "start_date": start_date,
            "end_date": "2025-01-26",
            "day_slots": slots,
            "created_at": datetime.now().isoformat(),
        }

        result = validator.validate_three_week_block(block_data)
        assert not result.is_valid
        violations = [v for v in result.guardrail_violations if v.rule == "date_sequence"]
        assert len(violations) > 0


class TestHighLevelPlanValidation:
    """Tests for high-level plan validation."""

    def test_valid_plan(self, validator):
        """Test validation of valid high-level plan."""
        plan_data = {
            "plan_id": "plan_123",
            "goal_id": "goal_123",
            "user_id": "user_123",
            "duration_weeks": 8,
            "overview_markdown": "# Training Plan\n\nThis is the plan overview.",
            "phase_breakdown": [
                {"weeks": "1-3", "focus": "Base Building"},
                {"weeks": "4-6", "focus": "Build Phase"},
                {"weeks": "7-8", "focus": "Taper"},
            ],
            "created_at": datetime.now().isoformat(),
        }

        result = validator.validate_high_level_plan(plan_data)
        assert result.is_valid
        assert result.data is not None

    def test_plan_duration_warning(self, validator):
        """Test that unusual duration generates warning."""
        plan_data = {
            "plan_id": "plan_123",
            "goal_id": "goal_123",
            "user_id": "user_123",
            "duration_weeks": 20,  # Too long
            "overview_markdown": "# Plan",
            "phase_breakdown": [
                {"weeks": "1-20", "focus": "Long Phase"},
            ],
            "created_at": datetime.now().isoformat(),
        }

        result = validator.validate_high_level_plan(plan_data)
        # Should have a warning about duration
        assert len(result.guardrail_violations) > 0


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_all_errors_combines_schema_and_guardrail(self):
        """Test that all_errors includes both schema and guardrail errors."""
        from app.rules.guardrails import GuardrailViolation

        result = ValidationResult(
            is_valid=False,
            schema_errors=["field X is required"],
            guardrail_violations=[
                GuardrailViolation("test_rule", "violation message", "error")
            ],
        )

        errors = result.all_errors
        assert len(errors) == 2
        assert "field X is required" in errors
        assert "[test_rule] violation message" in errors

    def test_to_dict(self):
        """Test to_dict for repair prompts."""
        from app.rules.guardrails import GuardrailViolation

        result = ValidationResult(
            is_valid=False,
            schema_errors=["error 1"],
            guardrail_violations=[
                GuardrailViolation("rule1", "message1", "warning")
            ],
        )

        d = result.to_dict()
        assert d["is_valid"] is False
        assert len(d["schema_errors"]) == 1
        assert len(d["guardrail_violations"]) == 1
        assert d["guardrail_violations"][0]["rule"] == "rule1"

