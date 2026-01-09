"""Pydantic models - single source of truth for all data schemas."""

from app.models.user import UserProfile, UserGoal, UserFeedback
from app.models.exercise import Exercise, ExerciseLog
from app.models.workout import WorkoutItem, WorkoutSection, WorkoutPlan, WorkoutLog
from app.models.plan import DaySlot, ThreeWeekBlock, HighLevelPlan, CompletePlan
from app.models.snapshot import FitnessSnapshot, HistorySummary, RecentWorkout
from app.models.responses import ClarifyingQuestions, ErrorResponse, RestDayResponse

__all__ = [
    # User models
    "UserProfile",
    "UserGoal",
    "UserFeedback",
    # Exercise models
    "Exercise",
    "ExerciseLog",
    # Workout models
    "WorkoutItem",
    "WorkoutSection",
    "WorkoutPlan",
    "WorkoutLog",
    # Plan models
    "DaySlot",
    "ThreeWeekBlock",
    "HighLevelPlan",
    "CompletePlan",
    # Snapshot models
    "FitnessSnapshot",
    "HistorySummary",
    "RecentWorkout",
    # Response models
    "ClarifyingQuestions",
    "ErrorResponse",
    "RestDayResponse",
]

