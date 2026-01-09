"""Plan models: DaySlot, ThreeWeekBlock, HighLevelPlan, CompletePlan."""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class DaySlot(BaseModel):
    """A single day slot within a 21-day block (lightweight schedule)."""

    day_number: int = Field(..., ge=1, le=21, description="Day number within block (1-21)")
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    workout_type: Optional[str] = Field(
        None,
        description="Workout type (e.g., 'endurance', 'intervals', 'strength', 'recovery')",
    )
    target_duration_min: Optional[int] = Field(
        None, ge=0, description="Target duration in minutes"
    )
    target_distance_km: Optional[float] = Field(
        None, ge=0, description="Target distance in km"
    )
    intensity_target: Optional[str] = Field(
        None, description="Target intensity (e.g., 'RPE_6_7', 'zone2')"
    )
    is_rest_day: bool = Field(..., description="Whether this is a rest day")
    status: Literal["planned", "adjusted", "completed", "skipped"] = Field(
        default="planned", description="Current status of the day slot"
    )
    workout_id: Optional[str] = Field(
        None, description="Reference to detailed WorkoutPlan when generated"
    )


class ThreeWeekBlock(BaseModel):
    """21-day training block with day slots."""

    block_number: int = Field(..., ge=1, description="Block number (1, 2, 3...)")
    start_date: str = Field(..., description="Block start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Block end date (YYYY-MM-DD)")
    day_slots: List[DaySlot] = Field(
        ..., min_length=21, max_length=21, description="21 day slots"
    )
    created_at: str = Field(..., description="Creation timestamp in ISO format")


class PhaseBreakdown(BaseModel):
    """Phase breakdown within a high-level plan."""

    weeks: str = Field(..., description="Week range (e.g., '1-3')")
    focus: str = Field(..., description="Focus area (e.g., 'base building')")
    description: Optional[str] = Field(None, description="Additional details")


class HighLevelPlan(BaseModel):
    """8-week strategic training overview (JSON-only, with overview_markdown)."""

    plan_id: str = Field(..., description="Unique plan identifier")
    goal_id: str = Field(..., description="Associated goal ID")
    user_id: str = Field(..., description="Associated user ID")
    duration_weeks: int = Field(default=8, description="Plan duration in weeks")
    overview_markdown: str = Field(
        ..., description="Human-readable strategy text for UI display"
    )
    phase_breakdown: List[PhaseBreakdown] = Field(
        ..., description="Breakdown of training phases"
    )
    created_at: str = Field(..., description="Creation timestamp in ISO format")


class CompletePlan(BaseModel):
    """Complete plan response containing high-level plan and current block."""

    high_level_plan: HighLevelPlan = Field(..., description="8-week strategic overview")
    current_block: ThreeWeekBlock = Field(..., description="Current 21-day block")
    blocks_generated: List[int] = Field(
        ..., description="List of block numbers that have been generated"
    )
    detailed_workouts: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of date (YYYY-MM-DD) to workout_id for generated workouts",
    )

