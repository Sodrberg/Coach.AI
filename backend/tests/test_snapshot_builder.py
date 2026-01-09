"""
Unit tests for snapshot builder service.

Tests FitnessSnapshot construction from user data.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.models.plan import HighLevelPlan, PhaseBreakdown
from app.models.user import UserGoal, UserProfile
from app.models.workout import ExerciseLog, WorkoutLog
from app.services.snapshot_builder import SnapshotBuilder
from app.storage.json_store import JSONStore

from tests.fixtures.sample_data import (
    SAMPLE_HIGH_LEVEL_PLAN,
    SAMPLE_USER_GOAL,
    SAMPLE_USER_PROFILE,
    SAMPLE_WORKOUT_LOG,
)


@pytest.fixture
def temp_store():
    """Create a temporary storage directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = JSONStore(base_dir=Path(temp_dir))
        yield store


@pytest.fixture
def populated_store(temp_store):
    """Create a store with sample data."""
    # Save profile
    profile = UserProfile(**SAMPLE_USER_PROFILE)
    temp_store.save_profile(profile)

    # Save goal
    goal = UserGoal(**SAMPLE_USER_GOAL)
    temp_store.save_goal(goal)

    return temp_store


class TestSnapshotBuilderBasic:
    """Basic tests for snapshot builder."""

    def test_build_snapshot_requires_profile(self, temp_store):
        """Test that snapshot fails without profile."""
        builder = SnapshotBuilder()
        # Monkey-patch the store
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = temp_store

        try:
            snapshot = builder.build_snapshot("nonexistent_user")
            assert snapshot is None
        finally:
            snapshot_builder.store = original_store

    def test_build_snapshot_requires_goal(self, temp_store):
        """Test that snapshot fails without goal."""
        builder = SnapshotBuilder()
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = temp_store

        try:
            # Save profile but not goal
            profile = UserProfile(**SAMPLE_USER_PROFILE)
            temp_store.save_profile(profile)

            snapshot = builder.build_snapshot("test_user_123")
            assert snapshot is None
        finally:
            snapshot_builder.store = original_store

    def test_build_snapshot_success(self, populated_store):
        """Test successful snapshot building."""
        builder = SnapshotBuilder()
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = populated_store

        try:
            snapshot = builder.build_snapshot("test_user_123")
            assert snapshot is not None
            assert snapshot.profile.user_id == "test_user_123"
            assert snapshot.goal.goal_type == "race"
            assert snapshot.today_date is not None
        finally:
            snapshot_builder.store = original_store


class TestSnapshotWithWorkoutHistory:
    """Tests for snapshot with workout history."""

    def test_recent_workouts_included(self, populated_store):
        """Test that recent workouts are included in snapshot."""
        builder = SnapshotBuilder(recent_days=30, max_recent_workouts=10)
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = populated_store

        try:
            # Add some workout logs
            for i in range(5):
                log_data = SAMPLE_WORKOUT_LOG.copy()
                log_data["log_id"] = f"log_{i}"
                log_data["date"] = (datetime.now() - timedelta(days=i * 2)).isoformat()
                log = WorkoutLog(**log_data)
                populated_store.save_workout_log(log)

            snapshot = builder.build_snapshot("test_user_123")
            assert len(snapshot.recent_workouts) > 0
        finally:
            snapshot_builder.store = original_store

    def test_history_summary_calculated(self, populated_store):
        """Test that history summary is calculated correctly."""
        builder = SnapshotBuilder()
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = populated_store

        try:
            # Add workout logs
            for i in range(10):
                log_data = SAMPLE_WORKOUT_LOG.copy()
                log_data["log_id"] = f"log_{i}"
                log_data["date"] = (datetime.now() - timedelta(days=i * 3)).isoformat()
                log_data["rpe_actual"] = 6 + (i % 3)  # Vary RPE
                log = WorkoutLog(**log_data)
                populated_store.save_workout_log(log)

            snapshot = builder.build_snapshot("test_user_123")
            assert snapshot.history_summary is not None
            assert snapshot.history_summary.total_workouts == 10
            assert snapshot.history_summary.avg_rpe > 0
        finally:
            snapshot_builder.store = original_store


class TestSnapshotContextCalculations:
    """Tests for context calculations in snapshot."""

    def test_days_since_last_workout(self, populated_store):
        """Test days_since_last_workout calculation."""
        builder = SnapshotBuilder()
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = populated_store

        try:
            # Add a workout from 3 days ago
            log_data = SAMPLE_WORKOUT_LOG.copy()
            log_data["log_id"] = "log_recent"
            log_data["date"] = (datetime.now() - timedelta(days=3)).isoformat()
            log = WorkoutLog(**log_data)
            populated_store.save_workout_log(log)

            snapshot = builder.build_snapshot("test_user_123")
            assert snapshot.days_since_last_workout == 3
        finally:
            snapshot_builder.store = original_store

    def test_days_until_goal(self, populated_store):
        """Test days_until_goal calculation."""
        builder = SnapshotBuilder()
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = populated_store

        try:
            snapshot = builder.build_snapshot("test_user_123")
            # Goal is 60 days from now (set in fixtures)
            assert snapshot.days_until_goal > 50
            assert snapshot.days_until_goal <= 60
        finally:
            snapshot_builder.store = original_store

    def test_consecutive_rest_days(self, populated_store):
        """Test consecutive_rest_days calculation."""
        builder = SnapshotBuilder()
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = populated_store

        try:
            # Add a workout from 5 days ago (4 consecutive rest days)
            log_data = SAMPLE_WORKOUT_LOG.copy()
            log_data["log_id"] = "log_old"
            log_data["date"] = (datetime.now() - timedelta(days=5)).isoformat()
            log = WorkoutLog(**log_data)
            populated_store.save_workout_log(log)

            snapshot = builder.build_snapshot("test_user_123")
            assert snapshot.consecutive_rest_days == 4
        finally:
            snapshot_builder.store = original_store


class TestSnapshotWithPlan:
    """Tests for snapshot with existing plan context."""

    def test_current_plan_included(self, populated_store):
        """Test that current plan is included in snapshot."""
        builder = SnapshotBuilder()
        from app.services import snapshot_builder
        original_store = snapshot_builder.store
        snapshot_builder.store = populated_store

        try:
            # Add a high-level plan
            plan = HighLevelPlan(
                plan_id="plan_test",
                goal_id="goal_123",
                user_id="test_user_123",
                duration_weeks=8,
                overview_markdown="# Test Plan",
                phase_breakdown=[
                    PhaseBreakdown(weeks="1-8", focus="Training")
                ],
                created_at=datetime.now().isoformat(),
            )
            populated_store.save_high_level_plan(plan)

            snapshot = builder.build_snapshot("test_user_123")
            assert snapshot.current_plan is not None
            assert snapshot.current_plan.plan_id == "plan_test"
        finally:
            snapshot_builder.store = original_store

