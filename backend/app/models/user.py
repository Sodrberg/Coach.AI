"""User-related models: UserProfile, UserGoal, UserFeedback, Session."""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User's physical profile and training preferences."""

    user_id: str = Field(..., description="Unique user identifier")
    age: int = Field(..., ge=13, le=100, description="User age in years")
    weight_kg: float = Field(..., gt=0, description="Body weight in kilograms")
    height_cm: int = Field(..., gt=0, description="Height in centimeters")
    gender: Optional[str] = Field(None, description="User's gender (optional)")
    fitness_level: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., description="Current fitness level"
    )
    training_history_years: int = Field(
        ..., ge=0, description="Years of training experience"
    )
    available_equipment: List[str] = Field(
        ..., description="Equipment available (e.g., 'barbell', 'ski_erg', 'gym', 'none')"
    )
    injuries_or_limitations: Optional[str] = Field(
        None, description="Any injuries or physical limitations"
    )
    training_days_per_week: int = Field(
        ..., ge=1, le=7, description="Preferred training days per week (1-7)"
    )
    preferred_training_days: Optional[List[str]] = Field(
        None,
        description="Preferred days of week (e.g., ['monday', 'wednesday', 'friday'])",
    )
    training_type_preference: Optional[Literal["cardio", "strength", "both"]] = Field(
        None,
        description="Preferred training type focus (cardio, strength, or both)",
    )


class UserGoal(BaseModel):
    """User's training goal and target."""

    goal_id: str = Field(..., description="Unique goal identifier")
    user_id: str = Field(..., description="Associated user ID")
    goal_type: Literal["race", "strength", "weight_loss", "general_fitness"] = Field(
        ..., description="Type of goal"
    )
    target_event: Optional[str] = Field(
        None, description="Target event name (e.g., 'Vasaloppet 90km')"
    )
    target_date: str = Field(..., description="Target date in ISO format (YYYY-MM-DD)")
    current_baseline: Optional[Dict[str, float]] = Field(
        None,
        description="Current performance baseline (e.g., {'5k_time_min': 25, 'squat_1rm_kg': 100})",
    )
    priority: Literal["performance", "health", "enjoyment"] = Field(
        ..., description="User's priority for training"
    )


class UserFeedback(BaseModel):
    """Form-based feedback from user before/after workout."""

    user_id: str = Field(..., description="User ID providing feedback")
    status: Literal["sore", "tired", "great", "pain"] = Field(
        ..., description="User's current status"
    )
    body_part: Optional[str] = Field(
        None, description="Affected body part (required if status is 'pain')"
    )
    severity: Optional[int] = Field(
        None, ge=1, le=5, description="Severity on 1-5 scale (for pain/sore)"
    )
    timestamp: str = Field(..., description="Timestamp in ISO format")


class Session(BaseModel):
    """User session for authentication."""

    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="Associated user ID")
    name: str = Field(..., description="User's display name")
    email: str = Field(..., description="User's email address")
    created_at: str = Field(..., description="Session creation timestamp in ISO format")
    expires_at: Optional[str] = Field(
        None, description="Session expiration timestamp (optional)"
    )

