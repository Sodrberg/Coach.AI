"""Snapshot models for LLM context: FitnessSnapshot, HistorySummary."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.user import UserFeedback, UserGoal, UserProfile
from app.models.plan import HighLevelPlan, ThreeWeekBlock


class RecentWorkout(BaseModel):
    """Compact representation of a recent workout for LLM context."""

    date: str = Field(..., description="Workout date (YYYY-MM-DD)")
    workout_type: str = Field(..., description="Type of workout")
    duration_min: int = Field(..., description="Duration in minutes")
    rpe_actual: int = Field(..., description="Actual RPE (1-10)")
    exercises_summary: str = Field(
        ..., description="Brief summary of exercises performed"
    )
    volume_km: Optional[float] = Field(None, description="Total distance if applicable")
    feedback: Optional[str] = Field(None, description="User feedback")


class HistorySummary(BaseModel):
    """Aggregated statistics from workout history (for older data)."""

    total_workouts: int = Field(..., description="Total workouts completed")
    weeks_covered: int = Field(..., description="Number of weeks of data")
    avg_workouts_per_week: float = Field(..., description="Average workouts per week")
    avg_duration_min: float = Field(..., description="Average workout duration")
    avg_rpe: float = Field(..., description="Average RPE across workouts")
    workout_type_distribution: Dict[str, int] = Field(
        ..., description="Count of each workout type"
    )
    intensity_distribution: Dict[str, int] = Field(
        ..., description="Count of each intensity level"
    )
    common_exercises: List[str] = Field(
        ..., description="Most frequently performed exercises"
    )
    recent_prs: Dict[str, float] = Field(
        default_factory=dict,
        description="Recent personal records (e.g., {'squat_kg': 120, '5k_min': 23})",
    )
    total_volume_km: Optional[float] = Field(
        None, description="Total distance covered"
    )
    missed_workouts: int = Field(
        default=0, description="Number of skipped/missed workouts"
    )


class FitnessSnapshot(BaseModel):
    """
    Compact context for LLM generation.
    
    Contains all relevant user data compressed for token efficiency.
    This is the primary input to plan/workout generation.
    """

    # User context
    profile: UserProfile = Field(..., description="User's profile")
    goal: UserGoal = Field(..., description="User's current goal")

    # Current plan context (if exists)
    current_plan: Optional[HighLevelPlan] = Field(
        None, description="Current high-level plan"
    )
    current_block: Optional[ThreeWeekBlock] = Field(
        None, description="Current 21-day block"
    )
    current_day_in_block: Optional[int] = Field(
        None, description="Which day we are in current block (1-21)"
    )

    # Workout history
    recent_workouts: List[RecentWorkout] = Field(
        default_factory=list,
        description="Recent workouts (last 14-30 days, detailed)",
    )
    history_summary: Optional[HistorySummary] = Field(
        None, description="Aggregated stats for older history"
    )

    # Current state
    recent_feedback: List[UserFeedback] = Field(
        default_factory=list,
        description="Recent user feedback (last 7 days)",
    )
    days_since_last_workout: int = Field(
        default=0, description="Days since last completed workout"
    )
    consecutive_rest_days: int = Field(
        default=0, description="Number of consecutive rest days"
    )

    # Date context
    today_date: str = Field(..., description="Today's date (YYYY-MM-DD)")
    days_until_goal: int = Field(..., description="Days remaining until target date")

