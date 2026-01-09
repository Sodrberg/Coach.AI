"""
Unit tests for guardrail checks.

Tests deterministic guardrail enforcement rules.
"""

from datetime import datetime, timedelta

import pytest

from app.models.plan import DaySlot
from app.models.workout import WorkoutLog, WorkoutPlan
from app.rules.guardrails import (
    GuardrailViolation,
    check_consecutive_hard_days,
    check_muscle_group_recovery,
    check_pain_feedback_compliance,
    check_rest_day_requirements,
    check_return_to_training,
    check_weekly_progression,
    validate_block,
    validate_workout_plan,
)

from tests.fixtures.sample_data import (
    SAMPLE_WORKOUT_LOG,
    SAMPLE_WORKOUT_PLAN,
    generate_sample_day_slots,
)


class TestConsecutiveHardDays:
    """Tests for consecutive hard days check."""

    def test_no_violation_when_previous_days_easy(self):
        """Test no violation when previous days were easy."""
        # Create logs with easy RPE
        logs = [
            WorkoutLog(**{
                **SAMPLE_WORKOUT_LOG,
                "log_id": "log_1",
                "date": (datetime.now() - timedelta(days=1)).isoformat(),
                "rpe_actual": 6,
            }),
        ]

        result = check_consecutive_hard_days(logs, proposed_rpe=9)
        assert result is None

    def test_violation_when_previous_days_hard(self):
        """Test violation when consecutive hard days."""
        # Create logs with high RPE
        logs = [
            WorkoutLog(**{
                **SAMPLE_WORKOUT_LOG,
                "log_id": "log_1",
                "date": (datetime.now() - timedelta(days=1)).isoformat(),
                "rpe_actual": 9,
            }),
            WorkoutLog(**{
                **SAMPLE_WORKOUT_LOG,
                "log_id": "log_2",
                "date": (datetime.now() - timedelta(days=2)).isoformat(),
                "rpe_actual": 9,
            }),
        ]

        result = check_consecutive_hard_days(logs, proposed_rpe=9)
        assert result is not None
        assert result.rule == "consecutive_hard_days"

    def test_no_violation_for_easy_proposed_workout(self):
        """Test no violation when proposed workout is easy."""
        logs = [
            WorkoutLog(**{
                **SAMPLE_WORKOUT_LOG,
                "log_id": "log_1",
                "date": (datetime.now() - timedelta(days=1)).isoformat(),
                "rpe_actual": 9,
            }),
        ]

        # Easy workout (RPE 5) should be fine
        result = check_consecutive_hard_days(logs, proposed_rpe=5)
        assert result is None


class TestWeeklyProgression:
    """Tests for weekly progression check."""

    def test_no_violation_within_limit(self):
        """Test no violation when increase is within limit."""
        result = check_weekly_progression(
            last_week_volume=100,
            proposed_week_volume=108,  # 8% increase
            training_type="strength",
        )
        assert result is None

    def test_violation_exceeds_limit(self):
        """Test violation when increase exceeds limit."""
        result = check_weekly_progression(
            last_week_volume=100,
            proposed_week_volume=120,  # 20% increase (over 10% limit)
            training_type="strength",
        )
        assert result is not None
        assert result.rule == "weekly_progression"

    def test_no_violation_for_zero_baseline(self):
        """Test no violation when baseline is zero (new user)."""
        result = check_weekly_progression(
            last_week_volume=0,
            proposed_week_volume=50,
        )
        assert result is None


class TestRestDayRequirements:
    """Tests for rest day requirements check."""

    def test_no_violation_with_rest_days(self):
        """Test no violation when week has rest days."""
        slots = [
            DaySlot(
                day_number=i + 1,
                date=f"2025-01-0{i + 1}",
                workout_type="strength" if i < 5 else None,
                is_rest_day=i >= 5,  # 2 rest days
                status="planned",
            )
            for i in range(7)
        ]

        result = check_rest_day_requirements(slots)
        assert result is None

    def test_violation_no_rest_days(self):
        """Test violation when no rest days in week."""
        slots = [
            DaySlot(
                day_number=i + 1,
                date=f"2025-01-0{i + 1}",
                workout_type="strength",
                is_rest_day=False,
                status="planned",
            )
            for i in range(7)
        ]

        result = check_rest_day_requirements(slots)
        assert result is not None
        assert result.rule == "rest_day_requirement"


class TestReturnToTraining:
    """Tests for return to training check."""

    def test_no_violation_normal_gap(self):
        """Test no violation when gap is 1 day."""
        result = check_return_to_training(days_since_last_workout=1, proposed_rpe=8)
        assert result is None

    def test_warning_extended_rest_high_rpe(self):
        """Test warning when returning from rest with high RPE."""
        result = check_return_to_training(days_since_last_workout=3, proposed_rpe=8)
        assert result is not None
        assert result.rule == "return_to_training"
        assert result.severity == "warning"

    def test_no_violation_extended_rest_low_rpe(self):
        """Test no violation when returning with appropriate RPE."""
        result = check_return_to_training(days_since_last_workout=5, proposed_rpe=5)
        assert result is None


class TestPainFeedbackCompliance:
    """Tests for pain feedback compliance check."""

    def test_no_violation_no_pain(self):
        """Test no violation when no pain feedback."""
        result = check_pain_feedback_compliance(
            has_pain_feedback=False,
            pain_body_part=None,
            proposed_rpe=9,
            proposed_exercises=["Squat", "Bench Press"],
        )
        assert result is None

    def test_violation_high_rpe_with_pain(self):
        """Test violation when RPE too high with pain."""
        result = check_pain_feedback_compliance(
            has_pain_feedback=True,
            pain_body_part="knee",
            proposed_rpe=7,  # Over max of 5
            proposed_exercises=["Walking"],
        )
        assert result is not None
        assert result.rule == "pain_intensity"
        assert result.severity == "critical"

    def test_violation_exercise_targets_pain_area(self):
        """Test violation when exercise targets painful area."""
        result = check_pain_feedback_compliance(
            has_pain_feedback=True,
            pain_body_part="shoulder",
            proposed_rpe=4,
            proposed_exercises=["Shoulder Press", "Walking"],
        )
        assert result is not None
        assert result.rule == "pain_exercise_exclusion"


class TestValidateWorkoutPlan:
    """Tests for full workout plan validation."""

    def test_validate_valid_workout(self):
        """Test validation of a valid workout."""
        workout = WorkoutPlan(**SAMPLE_WORKOUT_PLAN)
        is_valid, violations = validate_workout_plan(workout, recent_logs=[])
        assert is_valid

    def test_validate_workout_with_pain(self):
        """Test validation with pain feedback."""
        workout = WorkoutPlan(**SAMPLE_WORKOUT_PLAN)
        is_valid, violations = validate_workout_plan(
            workout,
            recent_logs=[],
            has_pain=True,
            pain_body_part="shoulder",
        )
        # Should have violations due to pain + high RPE
        assert len(violations) > 0


class TestValidateBlock:
    """Tests for full block validation."""

    def test_validate_valid_block(self):
        """Test validation of a valid block."""
        from app.models.plan import ThreeWeekBlock

        start_date = "2025-01-06"
        slots_data = generate_sample_day_slots(start_date)
        slots = [DaySlot(**s) for s in slots_data]

        block = ThreeWeekBlock(
            block_number=1,
            start_date=start_date,
            end_date="2025-01-26",
            day_slots=slots,
            created_at=datetime.now().isoformat(),
        )

        is_valid, violations = validate_block(block)
        assert is_valid

    def test_validate_block_no_rest_days(self):
        """Test validation fails with no rest days."""
        from app.models.plan import ThreeWeekBlock

        start_date = "2025-01-06"
        start = datetime.fromisoformat(start_date)

        # All training days
        slots = [
            DaySlot(
                day_number=i + 1,
                date=(start + timedelta(days=i)).strftime("%Y-%m-%d"),
                workout_type="strength",
                target_duration_min=45,
                intensity_target="RPE_7_8",
                is_rest_day=False,
                status="planned",
            )
            for i in range(21)
        ]

        block = ThreeWeekBlock(
            block_number=1,
            start_date=start_date,
            end_date="2025-01-26",
            day_slots=slots,
            created_at=datetime.now().isoformat(),
        )

        is_valid, violations = validate_block(block)
        assert not is_valid
        assert any(v.rule == "rest_day_requirement" for v in violations)

