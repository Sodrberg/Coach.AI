"""
JSON file-based storage for MVP persistence.

This is a simple file-based storage solution for the MVP.
In production, this would be replaced with a proper database.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from app.config import get_data_path
from app.models.plan import CompletePlan, HighLevelPlan, ThreeWeekBlock
from app.models.user import Session, UserFeedback, UserGoal, UserProfile
from app.models.workout import WorkoutLog, WorkoutPlan

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class JSONStore:
    """Simple JSON file-based storage."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the JSON store."""
        self.base_dir = base_dir or get_data_path("")
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Subdirectories for different data types
        self.profiles_dir = self.base_dir / "profiles"
        self.goals_dir = self.base_dir / "goals"
        self.plans_dir = self.base_dir / "plans"
        self.blocks_dir = self.base_dir / "blocks"
        self.workouts_dir = self.base_dir / "workouts"
        self.workout_logs_dir = self.base_dir / "workout_logs"
        self.feedback_dir = self.base_dir / "feedback"
        self.sessions_dir = self.base_dir / "sessions"

        # Create all subdirectories
        for dir_path in [
            self.profiles_dir,
            self.goals_dir,
            self.plans_dir,
            self.blocks_dir,
            self.workouts_dir,
            self.workout_logs_dir,
            self.feedback_dir,
            self.sessions_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _read_json(self, file_path: Path) -> Optional[Dict]:
        """Read JSON from file."""
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None

    def _write_json(self, file_path: Path, data: Dict) -> bool:
        """Write JSON to file."""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except IOError as e:
            logger.error(f"Error writing {file_path}: {e}")
            return False

    def _load_model(self, file_path: Path, model_class: Type[T]) -> Optional[T]:
        """Load a Pydantic model from JSON file."""
        data = self._read_json(file_path)
        if data is None:
            return None
        try:
            return model_class.model_validate(data)
        except Exception as e:
            logger.error(f"Error parsing {file_path} as {model_class.__name__}: {e}")
            return None

    def _save_model(self, file_path: Path, model: BaseModel) -> bool:
        """Save a Pydantic model to JSON file."""
        return self._write_json(file_path, model.model_dump())

    # ==================== User Profile ====================

    def save_profile(self, profile: UserProfile) -> bool:
        """Save user profile."""
        file_path = self.profiles_dir / f"{profile.user_id}.json"
        return self._save_model(file_path, profile)

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        file_path = self.profiles_dir / f"{user_id}.json"
        return self._load_model(file_path, UserProfile)

    # ==================== User Goal ====================

    def save_goal(self, goal: UserGoal) -> bool:
        """Save user goal."""
        file_path = self.goals_dir / f"{goal.goal_id}.json"
        return self._save_model(file_path, goal)

    def get_goal(self, goal_id: str) -> Optional[UserGoal]:
        """Get goal by ID."""
        file_path = self.goals_dir / f"{goal_id}.json"
        return self._load_model(file_path, UserGoal)

    def get_goals_for_user(self, user_id: str) -> List[UserGoal]:
        """Get all goals for a user."""
        goals = []
        for file_path in self.goals_dir.glob("*.json"):
            goal = self._load_model(file_path, UserGoal)
            if goal and goal.user_id == user_id:
                goals.append(goal)
        return goals

    def get_active_goal(self, user_id: str) -> Optional[UserGoal]:
        """Get the most recently created goal for a user."""
        goals = self.get_goals_for_user(user_id)
        if not goals:
            return None
        # Return the most recently created goal (goal_id contains timestamp: goal_{timestamp})
        # Sort by goal_id descending to get the most recently created
        return max(goals, key=lambda g: g.goal_id)

    # ==================== High Level Plan ====================

    def save_high_level_plan(self, plan: HighLevelPlan) -> bool:
        """Save high-level plan."""
        file_path = self.plans_dir / f"{plan.plan_id}.json"
        return self._save_model(file_path, plan)

    def get_high_level_plan(self, plan_id: str) -> Optional[HighLevelPlan]:
        """Get high-level plan by ID."""
        file_path = self.plans_dir / f"{plan_id}.json"
        return self._load_model(file_path, HighLevelPlan)

    def get_plan_for_user(self, user_id: str) -> Optional[HighLevelPlan]:
        """Get the current high-level plan for a user."""
        for file_path in self.plans_dir.glob("*.json"):
            plan = self._load_model(file_path, HighLevelPlan)
            if plan and plan.user_id == user_id:
                return plan
        return None

    # ==================== Three Week Block ====================

    def save_block(self, user_id: str, block: ThreeWeekBlock) -> bool:
        """Save a 21-day block."""
        file_path = self.blocks_dir / f"{user_id}_block_{block.block_number}.json"
        return self._save_model(file_path, block)

    def get_block(self, user_id: str, block_number: int) -> Optional[ThreeWeekBlock]:
        """Get a specific block by user and block number."""
        file_path = self.blocks_dir / f"{user_id}_block_{block_number}.json"
        return self._load_model(file_path, ThreeWeekBlock)

    def get_current_block(self, user_id: str, today: str) -> Optional[ThreeWeekBlock]:
        """Get the current block for a user based on today's date."""
        for file_path in self.blocks_dir.glob(f"{user_id}_block_*.json"):
            block = self._load_model(file_path, ThreeWeekBlock)
            if block and block.start_date <= today <= block.end_date:
                return block
        return None

    def get_latest_block(self, user_id: str) -> Optional[ThreeWeekBlock]:
        """Get the most recent block for a user."""
        blocks = []
        for file_path in self.blocks_dir.glob(f"{user_id}_block_*.json"):
            block = self._load_model(file_path, ThreeWeekBlock)
            if block:
                blocks.append(block)
        if not blocks:
            return None
        return max(blocks, key=lambda b: b.block_number)

    # ==================== Workout Plan ====================

    def save_workout(self, user_id: str, workout: WorkoutPlan) -> bool:
        """Save a detailed workout plan."""
        file_path = self.workouts_dir / f"{user_id}_{workout.workout_id}.json"
        return self._save_model(file_path, workout)

    def get_workout(self, user_id: str, workout_id: str) -> Optional[WorkoutPlan]:
        """Get a workout by ID."""
        file_path = self.workouts_dir / f"{user_id}_{workout_id}.json"
        return self._load_model(file_path, WorkoutPlan)

    def get_workout_for_date(
        self, user_id: str, date: str
    ) -> Optional[WorkoutPlan]:
        """Get the workout scheduled for a specific date."""
        for file_path in self.workouts_dir.glob(f"{user_id}_*.json"):
            workout = self._load_model(file_path, WorkoutPlan)
            if workout and workout.scheduled_for_date == date:
                return workout
        return None

    def get_workouts_in_range(
        self, user_id: str, start_date: str, end_date: str
    ) -> List[WorkoutPlan]:
        """Get all workouts in a date range."""
        workouts = []
        for file_path in self.workouts_dir.glob(f"{user_id}_*.json"):
            workout = self._load_model(file_path, WorkoutPlan)
            if workout and start_date <= workout.scheduled_for_date <= end_date:
                workouts.append(workout)
        return sorted(workouts, key=lambda w: w.scheduled_for_date)

    # ==================== Workout Log ====================

    def save_workout_log(self, log: WorkoutLog) -> bool:
        """Save a completed workout log."""
        file_path = self.workout_logs_dir / f"{log.user_id}_{log.log_id}.json"
        return self._save_model(file_path, log)

    def get_workout_log(self, user_id: str, log_id: str) -> Optional[WorkoutLog]:
        """Get a workout log by ID."""
        file_path = self.workout_logs_dir / f"{user_id}_{log_id}.json"
        return self._load_model(file_path, WorkoutLog)

    def get_workout_logs_for_user(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[WorkoutLog]:
        """Get all workout logs for a user, sorted by date (newest first)."""
        logs = []
        for file_path in self.workout_logs_dir.glob(f"{user_id}_*.json"):
            log = self._load_model(file_path, WorkoutLog)
            if log:
                logs.append(log)
        logs = sorted(logs, key=lambda x: x.date, reverse=True)
        if limit:
            logs = logs[:limit]
        return logs

    def get_workout_logs_in_range(
        self, user_id: str, start_date: str, end_date: str
    ) -> List[WorkoutLog]:
        """Get workout logs in a date range."""
        logs = []
        for file_path in self.workout_logs_dir.glob(f"{user_id}_*.json"):
            log = self._load_model(file_path, WorkoutLog)
            if log:
                # Extract date part for comparison
                log_date = log.date[:10]  # Get YYYY-MM-DD part
                if start_date <= log_date <= end_date:
                    logs.append(log)
        return sorted(logs, key=lambda x: x.date)

    # ==================== User Feedback ====================

    def save_feedback(self, feedback: UserFeedback) -> bool:
        """Save user feedback."""
        # Use timestamp as unique identifier
        timestamp_clean = feedback.timestamp.replace(":", "-").replace(".", "-")
        file_path = self.feedback_dir / f"{feedback.user_id}_{timestamp_clean}.json"
        return self._save_model(file_path, feedback)

    def get_recent_feedback(
        self, user_id: str, days: int = 7
    ) -> List[UserFeedback]:
        """Get recent feedback for a user."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()

        feedbacks = []
        for file_path in self.feedback_dir.glob(f"{user_id}_*.json"):
            feedback = self._load_model(file_path, UserFeedback)
            if feedback and feedback.timestamp >= cutoff_str:
                feedbacks.append(feedback)
        return sorted(feedbacks, key=lambda x: x.timestamp, reverse=True)

    # ==================== Complete Plan ====================

    def save_complete_plan(self, user_id: str, plan: CompletePlan) -> bool:
        """Save a complete plan (high-level + current block)."""
        file_path = self.plans_dir / f"{user_id}_complete.json"
        return self._save_model(file_path, plan)

    def get_complete_plan(self, user_id: str) -> Optional[CompletePlan]:
        """Get the complete plan for a user."""
        file_path = self.plans_dir / f"{user_id}_complete.json"
        return self._load_model(file_path, CompletePlan)

    # ==================== Sessions ====================

    def save_session(self, session: Session) -> bool:
        """Save a user session."""
        file_path = self.sessions_dir / f"{session.session_id}.json"
        return self._save_model(file_path, session)

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        file_path = self.sessions_dir / f"{session_id}.json"
        return self._load_model(file_path, Session)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        file_path = self.sessions_dir / f"{session_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except IOError as e:
                logger.error(f"Error deleting session {session_id}: {e}")
                return False
        return True  # Already doesn't exist

    def find_user_by_email(self, email: str) -> Optional[Session]:
        """Find an existing user session by email."""
        for file_path in self.sessions_dir.glob("*.json"):
            session = self._load_model(file_path, Session)
            if session and session.email.lower() == email.lower():
                return session
        return None

    def get_sessions_for_user(self, user_id: str) -> List[Session]:
        """Get all sessions for a user."""
        sessions = []
        for file_path in self.sessions_dir.glob("*.json"):
            session = self._load_model(file_path, Session)
            if session and session.user_id == user_id:
                sessions.append(session)
        return sessions


# Global store instance
store = JSONStore()

