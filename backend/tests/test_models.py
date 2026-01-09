"""
Unit tests for Pydantic models.

Tests schema validation for all model types.
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.exercise import Exercise, ExerciseLog
from app.models.plan import (
    CompletePlan,
    DaySlot,
    HighLevelPlan,
    PhaseBreakdown,
    ThreeWeekBlock,
)
from app.models.responses import ClarifyingQuestions, ErrorResponse, RestDayResponse
from app.models.user import UserFeedback, UserGoal, UserProfile
from app.models.workout import WorkoutItem, WorkoutLog, WorkoutPlan, WorkoutSection

from tests.fixtures.sample_data import (
    SAMPLE_HIGH_LEVEL_PLAN,
    SAMPLE_USER_GOAL,
    SAMPLE_USER_PROFILE,
    SAMPLE_WORKOUT_LOG,
    SAMPLE_WORKOUT_PLAN,
    generate_sample_day_slots,
)


class TestUserProfile:
    """Tests for UserProfile model."""

    def test_valid_profile(self):
        """Test creating a valid profile."""
        profile = UserProfile(**SAMPLE_USER_PROFILE)
        assert profile.user_id == "test_user_123"
        assert profile.fitness_level == "intermediate"
        assert len(profile.available_equipment) == 4

    def test_profile_age_validation(self):
        """Test age validation bounds."""
        # Too young
        with pytest.raises(ValidationError):
            data = SAMPLE_USER_PROFILE.copy()
            data["age"] = 10
            UserProfile(**data)

        # Too old
        with pytest.raises(ValidationError):
            data = SAMPLE_USER_PROFILE.copy()
            data["age"] = 150
            UserProfile(**data)

    def test_profile_fitness_level_literal(self):
        """Test fitness level must be one of allowed values."""
        with pytest.raises(ValidationError):
            data = SAMPLE_USER_PROFILE.copy()
            data["fitness_level"] = "expert"
            UserProfile(**data)

    def test_profile_training_days_validation(self):
        """Test training days per week bounds."""
        with pytest.raises(ValidationError):
            data = SAMPLE_USER_PROFILE.copy()
            data["training_days_per_week"] = 0
            UserProfile(**data)

        with pytest.raises(ValidationError):
            data = SAMPLE_USER_PROFILE.copy()
            data["training_days_per_week"] = 8
            UserProfile(**data)


class TestUserGoal:
    """Tests for UserGoal model."""

    def test_valid_goal(self):
        """Test creating a valid goal."""
        goal = UserGoal(**SAMPLE_USER_GOAL)
        assert goal.goal_type == "race"
        assert goal.target_event == "Vasaloppet 90km"
        assert goal.priority == "performance"

    def test_goal_type_literal(self):
        """Test goal type must be one of allowed values."""
        with pytest.raises(ValidationError):
            data = SAMPLE_USER_GOAL.copy()
            data["goal_type"] = "swimming"
            UserGoal(**data)


class TestUserFeedback:
    """Tests for UserFeedback model."""

    def test_valid_feedback_sore(self):
        """Test creating sore feedback."""
        feedback = UserFeedback(
            user_id="test_user",
            status="sore",
            body_part="shoulder",
            severity=3,
            timestamp=datetime.now().isoformat(),
        )
        assert feedback.status == "sore"
        assert feedback.severity == 3

    def test_valid_feedback_pain(self):
        """Test creating pain feedback."""
        feedback = UserFeedback(
            user_id="test_user",
            status="pain",
            body_part="knee",
            severity=4,
            timestamp=datetime.now().isoformat(),
        )
        assert feedback.status == "pain"
        assert feedback.body_part == "knee"

    def test_severity_bounds(self):
        """Test severity must be 1-5."""
        with pytest.raises(ValidationError):
            UserFeedback(
                user_id="test_user",
                status="sore",
                severity=6,
                timestamp=datetime.now().isoformat(),
            )


class TestWorkoutPlan:
    """Tests for WorkoutPlan model."""

    def test_valid_workout_plan(self):
        """Test creating a valid workout plan."""
        plan = WorkoutPlan(**SAMPLE_WORKOUT_PLAN)
        assert plan.workout_type == "strength"
        assert len(plan.sections) == 3
        assert plan.sections[0].name == "warmup"
        assert plan.sections[1].name == "main"

    def test_workout_rationale_length(self):
        """Test rationale must have 1-3 items."""
        # Empty rationale should fail
        data = SAMPLE_WORKOUT_PLAN.copy()
        data["rationale"] = []
        with pytest.raises(ValidationError):
            WorkoutPlan(**data)

        # More than 3 should fail
        data["rationale"] = ["a", "b", "c", "d"]
        with pytest.raises(ValidationError):
            WorkoutPlan(**data)

    def test_workout_section_names(self):
        """Test section names must be warmup, main, or cooldown."""
        with pytest.raises(ValidationError):
            WorkoutSection(name="stretch", items=[])


class TestDaySlot:
    """Tests for DaySlot model."""

    def test_valid_training_day(self):
        """Test creating a valid training day slot."""
        slot = DaySlot(
            day_number=1,
            date="2025-01-06",
            workout_type="strength",
            target_duration_min=45,
            intensity_target="RPE_7_8",
            is_rest_day=False,
            status="planned",
        )
        assert slot.workout_type == "strength"
        assert not slot.is_rest_day

    def test_valid_rest_day(self):
        """Test creating a valid rest day slot."""
        slot = DaySlot(
            day_number=3,
            date="2025-01-08",
            workout_type=None,
            is_rest_day=True,
            status="planned",
        )
        assert slot.is_rest_day
        assert slot.workout_type is None

    def test_day_number_bounds(self):
        """Test day number must be 1-21."""
        with pytest.raises(ValidationError):
            DaySlot(
                day_number=0,
                date="2025-01-06",
                is_rest_day=True,
                status="planned",
            )

        with pytest.raises(ValidationError):
            DaySlot(
                day_number=22,
                date="2025-01-06",
                is_rest_day=True,
                status="planned",
            )


class TestThreeWeekBlock:
    """Tests for ThreeWeekBlock model."""

    def test_valid_block(self):
        """Test creating a valid 21-day block."""
        start_date = "2025-01-06"
        slots = generate_sample_day_slots(start_date)

        block = ThreeWeekBlock(
            block_number=1,
            start_date=start_date,
            end_date="2025-01-26",
            day_slots=slots,
            created_at=datetime.now().isoformat(),
        )
        assert len(block.day_slots) == 21
        assert block.block_number == 1

    def test_block_requires_21_slots(self):
        """Test block must have exactly 21 day slots."""
        start_date = "2025-01-06"
        slots = generate_sample_day_slots(start_date)[:10]  # Only 10 slots

        with pytest.raises(ValidationError):
            ThreeWeekBlock(
                block_number=1,
                start_date=start_date,
                end_date="2025-01-26",
                day_slots=slots,
                created_at=datetime.now().isoformat(),
            )


class TestHighLevelPlan:
    """Tests for HighLevelPlan model."""

    def test_valid_high_level_plan(self):
        """Test creating a valid high-level plan."""
        plan = HighLevelPlan(**SAMPLE_HIGH_LEVEL_PLAN)
        assert plan.duration_weeks == 8
        assert len(plan.phase_breakdown) == 3
        assert "Vasaloppet" in plan.overview_markdown


class TestResponses:
    """Tests for response models."""

    def test_clarifying_questions(self):
        """Test ClarifyingQuestions response."""
        response = ClarifyingQuestions(
            questions=["What is your current fitness level?"],
            missing_fields=["fitness_level"],
            reason="Required for plan generation",
        )
        assert len(response.questions) == 1
        assert "fitness_level" in response.missing_fields

    def test_error_response(self):
        """Test ErrorResponse."""
        error = ErrorResponse(
            error_code="PLAN_GENERATION_FAILED",
            message="Failed to generate plan",
            retry_allowed=True,
        )
        assert error.error_code == "PLAN_GENERATION_FAILED"
        assert error.retry_allowed

    def test_rest_day_response(self):
        """Test RestDayResponse."""
        response = RestDayResponse(
            date="2025-01-06",
            next_workout_date="2025-01-07",
        )
        assert response.is_rest_day
        assert len(response.recovery_tips) > 0

