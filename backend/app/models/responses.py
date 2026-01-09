"""Response models: ClarifyingQuestions, ErrorResponse, RestDayResponse, PendingWorkoutPrompt, WorkoutCompletedResponse, AuthResponse."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ClarifyingQuestions(BaseModel):
    """Response when required information is missing."""

    questions: List[str] = Field(
        ..., min_length=1, description="Questions to ask the user"
    )
    missing_fields: List[str] = Field(
        ..., description="List of missing required fields"
    )
    reason: str = Field(..., description="Why this information is needed")
    context: Optional[str] = Field(
        None, description="Additional context for the questions"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error_code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")
    retry_allowed: bool = Field(
        default=True, description="Whether the request can be retried"
    )


class RestDayResponse(BaseModel):
    """Response when today is a scheduled rest day."""

    is_rest_day: Literal[True] = Field(default=True, description="Indicates rest day")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    message: str = Field(
        default="Today is a scheduled rest day. Take time to recover!",
        description="Message for the user",
    )
    next_workout_date: Optional[str] = Field(
        None, description="Date of next scheduled workout"
    )
    recovery_tips: List[str] = Field(
        default_factory=lambda: [
            "Stay hydrated",
            "Get quality sleep",
            "Light stretching or walking is fine",
        ],
        description="Recovery suggestions",
    )


class PendingWorkoutPrompt(BaseModel):
    """Prompt when there are incomplete workouts from past days."""

    has_pending_workout: Literal[True] = Field(
        default=True, description="Indicates there is a pending workout"
    )
    pending_date: str = Field(..., description="Date of incomplete workout (YYYY-MM-DD)")
    workout_type: str = Field(..., description="Type of the incomplete workout")
    message: str = Field(..., description="Message asking about the workout")
    options: List[str] = Field(
        default_factory=lambda: ["completed", "skipped"],
        description="Available resolution options",
    )


class WorkoutCompletedResponse(BaseModel):
    """Response after successfully logging a completed workout."""

    message: str = Field(
        default="Today's workout completed!",
        description="Confirmation message",
    )
    log_id: str = Field(..., description="Reference to the saved workout log")
    next_workout_date: Optional[str] = Field(
        None, description="Date of next scheduled workout (YYYY-MM-DD)"
    )
    next_workout_type: Optional[str] = Field(
        None, description="Type of next scheduled workout"
    )
    next_workout_message: Optional[str] = Field(
        None, description="Human-friendly message about next workout (e.g., 'Next workout is on Friday')"
    )


class AuthResponse(BaseModel):
    """Response after successful authentication."""

    session_id: str = Field(..., description="Session ID for subsequent requests")
    user_id: str = Field(..., description="User's unique identifier")
    name: str = Field(..., description="User's display name")
    email: str = Field(..., description="User's email address")

