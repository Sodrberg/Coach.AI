"""
Snapshot builder service.

Builds a compact FitnessSnapshot from user data for LLM context.
This is the primary input to plan/workout generation, designed for token efficiency.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.config import settings
from app.models.plan import HighLevelPlan, ThreeWeekBlock
from app.models.snapshot import FitnessSnapshot, HistorySummary, RecentWorkout
from app.models.user import UserFeedback, UserGoal, UserProfile
from app.models.workout import WorkoutLog
from app.storage.json_store import store

logger = logging.getLogger(__name__)


class SnapshotBuilder:
    """Builds compact FitnessSnapshot for LLM context."""

    def __init__(
        self,
        recent_days: int = None,
        max_recent_workouts: int = None,
    ):
        """
        Initialize the snapshot builder.
        
        Args:
            recent_days: Days of recent workouts to include (default from settings)
            max_recent_workouts: Maximum recent workouts to include (default from settings)
        """
        self.recent_days = recent_days or settings.recent_workouts_days
        self.max_recent_workouts = max_recent_workouts or settings.max_recent_workouts

    def build_snapshot(
        self,
        user_id: str,
        today_date: Optional[str] = None,
    ) -> Optional[FitnessSnapshot]:
        """
        Build a complete FitnessSnapshot for a user.
        
        Args:
            user_id: User ID to build snapshot for
            today_date: Override for today's date (YYYY-MM-DD), defaults to actual today
            
        Returns:
            FitnessSnapshot or None if required data is missing
        """
        # Get user profile
        profile = store.get_profile(user_id)
        if not profile:
            logger.error(f"No profile found for user {user_id}")
            return None

        # Get active goal
        goal = store.get_active_goal(user_id)
        if not goal:
            logger.error(f"No active goal found for user {user_id}")
            return None

        # Set today's date
        if today_date:
            today = datetime.fromisoformat(today_date)
        else:
            today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        # Calculate days until goal
        try:
            target_date = datetime.fromisoformat(goal.target_date)
            days_until_goal = (target_date - today).days
        except ValueError:
            days_until_goal = 0

        # Get current plan and block
        current_plan = store.get_plan_for_user(user_id)
        current_block = store.get_current_block(user_id, today_str)

        # Calculate current day in block
        current_day_in_block = None
        if current_block:
            try:
                block_start = datetime.fromisoformat(current_block.start_date)
                current_day_in_block = (today - block_start).days + 1
                if current_day_in_block < 1 or current_day_in_block > 21:
                    current_day_in_block = None
            except ValueError:
                pass

        # Get workout logs
        all_logs = store.get_workout_logs_for_user(user_id)

        # Build recent workouts
        recent_workouts = self._build_recent_workouts(all_logs, today)

        # Build history summary
        history_summary = self._build_history_summary(all_logs, today)

        # Get recent feedback
        recent_feedback = store.get_recent_feedback(user_id, days=7)

        # Calculate days since last workout and consecutive rest days
        days_since_last_workout = self._calculate_days_since_last_workout(all_logs, today)
        consecutive_rest_days = self._calculate_consecutive_rest_days(all_logs, today)

        return FitnessSnapshot(
            profile=profile,
            goal=goal,
            current_plan=current_plan,
            current_block=current_block,
            current_day_in_block=current_day_in_block,
            recent_workouts=recent_workouts,
            history_summary=history_summary,
            recent_feedback=recent_feedback,
            days_since_last_workout=days_since_last_workout,
            consecutive_rest_days=consecutive_rest_days,
            today_date=today_str,
            days_until_goal=days_until_goal,
        )

    def _build_recent_workouts(
        self,
        all_logs: List[WorkoutLog],
        today: datetime,
    ) -> List[RecentWorkout]:
        """Build list of recent workouts for LLM context."""
        cutoff = today - timedelta(days=self.recent_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        recent = []
        for log in all_logs:
            log_date = log.date[:10]  # Get YYYY-MM-DD part
            if log_date < cutoff_str:
                continue
            if not log.completed:
                continue

            # Summarize exercises
            exercise_summary = self._summarize_exercises(log)

            recent.append(
                RecentWorkout(
                    date=log_date,
                    workout_type=log.workout_type,
                    duration_min=log.duration_min,
                    rpe_actual=log.rpe_actual,
                    exercises_summary=exercise_summary,
                    volume_km=log.volume_km,
                    feedback=log.feedback,
                )
            )

            if len(recent) >= self.max_recent_workouts:
                break

        return recent

    def _summarize_exercises(self, log: WorkoutLog) -> str:
        """Create a brief summary of exercises in a workout log."""
        if not log.exercises:
            return "No exercises logged"

        exercise_names = [e.name for e in log.exercises[:5]]
        summary = ", ".join(exercise_names)
        if len(log.exercises) > 5:
            summary += f" (+{len(log.exercises) - 5} more)"
        return summary

    def _build_history_summary(
        self,
        all_logs: List[WorkoutLog],
        today: datetime,
    ) -> Optional[HistorySummary]:
        """Build aggregated statistics from workout history."""
        # Only include completed workouts
        completed_logs = [log for log in all_logs if log.completed]

        if not completed_logs:
            return None

        # Calculate date range
        dates = [log.date[:10] for log in completed_logs]
        min_date = min(dates)
        max_date = max(dates)

        try:
            start = datetime.fromisoformat(min_date)
            end = datetime.fromisoformat(max_date)
            weeks_covered = max(1, (end - start).days // 7)
        except ValueError:
            weeks_covered = 1

        total_workouts = len(completed_logs)

        # Calculate averages
        avg_duration = sum(log.duration_min for log in completed_logs) / total_workouts
        avg_rpe = sum(log.rpe_actual for log in completed_logs) / total_workouts

        # Workout type distribution
        workout_types = Counter(log.workout_type for log in completed_logs)

        # Intensity distribution
        intensity_counts: Dict[str, int] = {"low": 0, "medium": 0, "high": 0}
        for log in completed_logs:
            if log.intensity:
                intensity_counts[log.intensity] = intensity_counts.get(log.intensity, 0) + 1

        # Common exercises
        all_exercises: List[str] = []
        for log in completed_logs:
            for exercise in log.exercises:
                all_exercises.append(exercise.name)
        exercise_counts = Counter(all_exercises)
        common_exercises = [name for name, _ in exercise_counts.most_common(10)]

        # Total volume
        total_volume = sum(log.volume_km or 0 for log in completed_logs)

        # Count missed workouts (not completed)
        missed_workouts = sum(1 for log in all_logs if not log.completed)

        return HistorySummary(
            total_workouts=total_workouts,
            weeks_covered=weeks_covered,
            avg_workouts_per_week=total_workouts / weeks_covered,
            avg_duration_min=round(avg_duration, 1),
            avg_rpe=round(avg_rpe, 1),
            workout_type_distribution=dict(workout_types),
            intensity_distribution=intensity_counts,
            common_exercises=common_exercises,
            recent_prs={},  # Would need PR tracking logic
            total_volume_km=total_volume if total_volume > 0 else None,
            missed_workouts=missed_workouts,
        )

    def _calculate_days_since_last_workout(
        self,
        all_logs: List[WorkoutLog],
        today: datetime,
    ) -> int:
        """Calculate days since last completed workout."""
        completed_logs = [log for log in all_logs if log.completed]

        if not completed_logs:
            return 999  # No workout history

        # Find most recent completed workout
        latest_date = max(log.date[:10] for log in completed_logs)

        try:
            last_workout = datetime.fromisoformat(latest_date)
            return (today - last_workout).days
        except ValueError:
            return 999

    def _calculate_consecutive_rest_days(
        self,
        all_logs: List[WorkoutLog],
        today: datetime,
    ) -> int:
        """Calculate number of consecutive rest days (no completed workout)."""
        completed_logs = [log for log in all_logs if log.completed]

        if not completed_logs:
            return 0

        # Get set of dates with completed workouts
        workout_dates = {log.date[:10] for log in completed_logs}

        # Count backwards from yesterday
        consecutive = 0
        check_date = today - timedelta(days=1)

        for _ in range(30):  # Max 30 days to check
            date_str = check_date.strftime("%Y-%m-%d")
            if date_str in workout_dates:
                break
            consecutive += 1
            check_date -= timedelta(days=1)

        return consecutive


# Global snapshot builder instance
snapshot_builder = SnapshotBuilder()

