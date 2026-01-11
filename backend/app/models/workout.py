"""Workout models: WorkoutItem, WorkoutSection, WorkoutPlan, WorkoutLog."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.exercise import ExerciseLog


class WorkoutItem(BaseModel):
    """Single exercise item within a workout section."""

    kind: Literal["strength", "endurance", "mobility", "recovery"] = Field(
        ..., description="Type of exercise"
    )
    exercise_id: Optional[str] = Field(
        None, description="Reference to exercise database ID"
    )
    name: str = Field(..., description="Exercise name")
    sets: Optional[int] = Field(None, ge=1, description="Number of sets")
    reps: Optional[int] = Field(None, ge=1, description="Reps per set")
    weight_kg: Optional[float] = Field(None, ge=0, description="Weight in kg")
    duration_min: Optional[float] = Field(None, ge=0, description="Duration in minutes")
    distance_km: Optional[float] = Field(None, ge=0, description="Distance in km")
    rest_sec: Optional[int] = Field(None, ge=0, description="Rest between sets in seconds")
    cues: Optional[str] = Field(None, description="Coaching cues for the exercise")


class WorkoutSection(BaseModel):
    """Section of a workout (warmup, main, cooldown)."""

    name: Literal["warmup", "main", "cooldown"] = Field(
        ..., description="Section name"
    )
    items: List[WorkoutItem] = Field(..., description="Exercises in this section")


class WorkoutPlan(BaseModel):
    """Detailed workout plan for a specific day."""

    workout_id: str = Field(..., description="Unique workout identifier")
    scheduled_for_date: str = Field(
        ..., description="Scheduled date in ISO format (YYYY-MM-DD)"
    )
    title: str = Field(..., description="Workout title (e.g., 'Strength: Upper Body')")
    workout_type: str = Field(
        ..., description="Type (e.g., 'intervals', 'hypertrophy', 'endurance', 'recovery')"
    )
    estimated_duration_min: int = Field(
        ..., ge=1, description="Estimated duration in minutes"
    )
    intensity_target: str = Field(
        ..., description="Target intensity (e.g., 'RPE_6_7', 'zone2')"
    )
    sections: List[WorkoutSection] = Field(
        ..., description="Workout sections (warmup, main, cooldown)"
    )
    rationale: List[str] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="1-3 bullets explaining why this workout was chosen",
    )
    questions: Optional[List[str]] = Field(
        None, description="Clarifying questions if critical info missing"
    )
    is_completed: bool = Field(
        default=False, description="Whether the workout has been logged/completed"
    )
    next_workout_date: Optional[str] = Field(
        None, description="Next scheduled workout date (populated when completed)"
    )


class CustomWorkoutRequest(BaseModel):
    """Request to create a custom standalone workout."""

    user_id: str = Field(..., description="User creating the workout")
    title: str = Field(..., description="Workout title")
    workout_type: str = Field(
        ..., description="Type (e.g., 'strength', 'endurance', 'recovery')"
    )
    estimated_duration_min: int = Field(..., ge=1, description="Estimated duration in minutes")
    intensity_target: str = Field(
        default="moderate", description="Target intensity"
    )
    sections: List[WorkoutSection] = Field(..., description="Workout sections")
    scheduled_for_date: Optional[str] = Field(
        None, description="Target date (YYYY-MM-DD). Defaults to today if not provided."
    )


class WorkoutLog(BaseModel):
    """Logged completed workout with details and feedback."""

    log_id: str = Field(..., description="Unique log identifier")
    user_id: str = Field(..., description="User who completed the workout")
    workout_id: Optional[str] = Field(
        None, description="Reference to the planned workout (if any)"
    )
    date: str = Field(..., description="Completion date in ISO format")
    completed: bool = Field(..., description="Whether workout was completed")
    workout_type: str = Field(
        ..., description="Type (e.g., 'intervals', 'hypertrophy', 'endurance')"
    )
    duration_min: int = Field(..., ge=0, description="Actual duration in minutes")
    rpe_actual: int = Field(..., ge=1, le=10, description="Actual RPE (1-10)")
    exercises: List[ExerciseLog] = Field(..., description="Logged exercises")
    volume_km: Optional[float] = Field(
        None, ge=0, description="Total distance if applicable"
    )
    feedback: Optional[Literal["felt_great", "sore", "tired", "pain"]] = Field(
        None, description="Post-workout feedback"
    )
    intensity: Optional[Literal["low", "medium", "high"]] = Field(
        None, description="Perceived intensity"
    )
    notes: Optional[str] = Field(None, description="Additional notes")

