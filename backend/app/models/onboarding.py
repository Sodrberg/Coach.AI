"""Onboarding models for quick user setup."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.plan import CompletePlan
from app.models.user import UserGoal, UserProfile


class QuickOnboardRequest(BaseModel):
    """Request for quick onboarding flow."""

    user_id: str = Field(..., description="User ID from auth")
    goal_text: str = Field(
        ..., min_length=3, max_length=500, description="Free-text goal description"
    )
    training_days_per_week: int = Field(
        ..., ge=3, le=6, description="Desired training days per week"
    )
    training_type_preference: Optional[Literal["cardio", "strength", "both"]] = Field(
        None, description="Preferred training type focus"
    )
    gym_access: Optional[Literal["gym", "no_gym", "both"]] = Field(
        None, description="User's gym access level"
    )
    preferred_training_days: Optional[List[str]] = Field(
        None, description="Preferred days of week (e.g., ['monday', 'wednesday'])"
    )


class InferredGoal(BaseModel):
    """LLM-inferred structured goal from free text."""

    fitness_level: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., description="Inferred fitness level"
    )
    goal_type: Literal["race", "strength", "weight_loss", "general_fitness"] = Field(
        ..., description="Inferred goal type"
    )
    target_event: Optional[str] = Field(
        None, description="Specific event name if mentioned"
    )
    target_date: str = Field(
        ..., description="Target date in YYYY-MM-DD format"
    )
    priority: Literal["performance", "health", "enjoyment"] = Field(
        ..., description="Inferred priority"
    )


class QuickOnboardResponse(BaseModel):
    """Response from quick onboarding."""

    profile: UserProfile
    goal: UserGoal
    complete_plan: CompletePlan
