"""Exercise-related models: Exercise database entry and ExerciseLog."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Exercise(BaseModel):
    """Exercise definition from the exercise database."""

    id: str = Field(..., description="Unique exercise identifier")
    name: str = Field(..., description="Exercise name")
    category: Literal["cardio", "strength", "mobility", "recovery"] = Field(
        ..., description="Exercise category"
    )
    muscle_groups: List[str] = Field(
        ..., description="Target muscle groups (e.g., ['quads', 'glutes', 'hamstrings'])"
    )
    equipment_required: List[str] = Field(
        ..., description="Required equipment (e.g., ['barbell', 'rack'])"
    )
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., description="Exercise difficulty level"
    )
    substitutes: List[str] = Field(
        default_factory=list, description="Alternative exercise IDs"
    )


class ExerciseLog(BaseModel):
    """Logged exercise within a completed workout."""

    name: str = Field(..., description="Exercise name")
    sets: Optional[int] = Field(None, ge=1, description="Number of sets performed")
    reps: Optional[int] = Field(None, ge=1, description="Reps per set")
    weight_kg: Optional[float] = Field(None, ge=0, description="Weight used in kg")
    duration_per_set_sec: Optional[int] = Field(
        None, ge=0, description="Duration per set in seconds"
    )
    distance_km: Optional[float] = Field(
        None, ge=0, description="Distance covered in km"
    )
    rest_sec: Optional[int] = Field(
        None, ge=0, description="Rest between sets in seconds"
    )

