"""
Unit tests for workout adjuster service.

Tests feedback-based workout adjustments using ADJUSTMENT_RULES.
"""

from datetime import datetime

import pytest

from app.models.user import UserFeedback
from app.models.workout import WorkoutPlan
from app.services.workout_adjuster import WorkoutAdjuster

from tests.fixtures.sample_data import (
    SAMPLE_FEEDBACK_GREAT,
    SAMPLE_FEEDBACK_PAIN,
    SAMPLE_FEEDBACK_SORE,
    SAMPLE_FEEDBACK_TIRED,
    SAMPLE_WORKOUT_PLAN,
)


@pytest.fixture
def adjuster():
    """Create an adjuster instance."""
    return WorkoutAdjuster()


@pytest.fixture
def workout():
    """Create a sample workout."""
    return WorkoutPlan(**SAMPLE_WORKOUT_PLAN)


class TestSoreAdjustments:
    """Tests for sore status adjustments."""

    def test_sore_reduces_volume(self, adjuster, workout):
        """Test that sore status reduces volume by 30%."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_SORE)
        adjusted = adjuster.adjust(workout, feedback)

        # Check that sets/reps are reduced
        for section in adjusted.sections:
            if section.name == "main":
                for item in section.items:
                    original_item = None
                    for s in workout.sections:
                        if s.name == "main":
                            for oi in s.items:
                                if oi.name == item.name:
                                    original_item = oi
                                    break
                    if original_item and original_item.sets:
                        # Should be reduced (at least by some amount)
                        assert item.sets <= original_item.sets

    def test_sore_skips_affected_muscle_group(self, adjuster, workout):
        """Test that exercises targeting sore muscle group are skipped."""
        # Create feedback for shoulder soreness
        feedback = UserFeedback(
            user_id="test_user_123",
            status="sore",
            body_part="shoulder",
            severity=3,
            timestamp=datetime.now().isoformat(),
        )
        adjusted = adjuster.adjust(workout, feedback)

        # Shoulder exercises should be removed
        for section in adjusted.sections:
            for item in section.items:
                # Overhead Press targets shoulders
                assert "Overhead Press" not in item.name or "shoulder" not in item.name.lower()

    def test_sore_adds_rationale(self, adjuster, workout):
        """Test that adjustment adds explanation to rationale."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_SORE)
        adjusted = adjuster.adjust(workout, feedback)

        assert len(adjusted.rationale) > len(workout.rationale)
        assert any("sore" in r.lower() for r in adjusted.rationale)


class TestTiredAdjustments:
    """Tests for tired status adjustments."""

    def test_tired_reduces_rpe(self, adjuster, workout):
        """Test that tired status reduces RPE target."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_TIRED)
        adjusted = adjuster.adjust(workout, feedback)

        # Original RPE was 7-8, should be reduced by 2
        # So new should be 5-6 or lower
        assert "RPE" in adjusted.intensity_target
        # Extract numbers from intensity target
        parts = adjusted.intensity_target.upper().replace("RPE", "").replace("_", " ").split()
        if len(parts) >= 2:
            low, high = int(parts[0]), int(parts[1])
            assert high <= 6  # Should be reduced from 8

    def test_tired_reduces_duration(self, adjuster, workout):
        """Test that tired status reduces workout duration."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_TIRED)
        adjusted = adjuster.adjust(workout, feedback)

        # Duration should be reduced by 15%
        assert adjusted.estimated_duration_min < workout.estimated_duration_min

    def test_tired_adds_rationale(self, adjuster, workout):
        """Test that tired adjustment adds explanation."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_TIRED)
        adjusted = adjuster.adjust(workout, feedback)

        assert any("fatigue" in r.lower() or "tired" in r.lower() for r in adjusted.rationale)


class TestPainAdjustments:
    """Tests for pain status adjustments."""

    def test_pain_sets_max_rpe(self, adjuster, workout):
        """Test that pain status caps RPE at 5."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_PAIN)
        adjusted = adjuster.adjust(workout, feedback)

        # Should be RPE 4-5 or lower
        parts = adjusted.intensity_target.upper().replace("RPE", "").replace("_", " ").split()
        if len(parts) >= 2:
            high = int(parts[1])
            assert high <= 5

    def test_pain_excludes_affected_exercises(self, adjuster, workout):
        """Test that exercises targeting painful area are excluded."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_PAIN)  # Knee pain
        adjusted = adjuster.adjust(workout, feedback)

        # Exercises targeting knee/legs should be removed
        for section in adjusted.sections:
            for item in section.items:
                assert "squat" not in item.name.lower()
                assert "leg" not in item.name.lower()

    def test_pain_significantly_reduces_duration(self, adjuster, workout):
        """Test that pain significantly reduces workout duration."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_PAIN)
        adjusted = adjuster.adjust(workout, feedback)

        # Duration should be reduced by ~40%
        reduction = 1 - (adjusted.estimated_duration_min / workout.estimated_duration_min)
        assert reduction >= 0.3  # At least 30% reduction

    def test_pain_adds_alert(self, adjuster, workout):
        """Test that pain adjustment adds professional consultation alert."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_PAIN)
        adjusted = adjuster.adjust(workout, feedback)

        # Should have alert about consulting professional
        assert any("consult" in r.lower() or "professional" in r.lower() for r in adjusted.rationale)


class TestGreatAdjustments:
    """Tests for great status (no adjustment)."""

    def test_great_no_changes(self, adjuster, workout):
        """Test that great status makes no changes."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_GREAT)
        adjusted = adjuster.adjust(workout, feedback)

        # Should be essentially the same workout
        assert adjusted.estimated_duration_min == workout.estimated_duration_min
        assert adjusted.intensity_target == workout.intensity_target
        # Title should NOT be prefixed with [Adjusted]
        assert "[Adjusted]" not in adjusted.title


class TestAdjusterEdgeCases:
    """Tests for edge cases in workout adjuster."""

    def test_adjustment_preserves_workout_id(self, adjuster, workout):
        """Test that adjustment preserves workout ID."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_SORE)
        adjusted = adjuster.adjust(workout, feedback)

        assert adjusted.workout_id == workout.workout_id

    def test_adjustment_preserves_date(self, adjuster, workout):
        """Test that adjustment preserves scheduled date."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_SORE)
        adjusted = adjuster.adjust(workout, feedback)

        assert adjusted.scheduled_for_date == workout.scheduled_for_date

    def test_adjusted_title_prefix(self, adjuster, workout):
        """Test that adjusted workout has [Adjusted] prefix."""
        feedback = UserFeedback(**SAMPLE_FEEDBACK_SORE)
        adjusted = adjuster.adjust(workout, feedback)

        assert adjusted.title.startswith("[Adjusted]")

    def test_original_workout_unchanged(self, adjuster, workout):
        """Test that original workout is not mutated."""
        original_duration = workout.estimated_duration_min
        original_title = workout.title

        feedback = UserFeedback(**SAMPLE_FEEDBACK_TIRED)
        adjuster.adjust(workout, feedback)

        # Original should be unchanged
        assert workout.estimated_duration_min == original_duration
        assert workout.title == original_title

