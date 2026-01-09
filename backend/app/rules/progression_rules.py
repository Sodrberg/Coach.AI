"""
Progression rules for training load management.

These rules define maximum safe progression rates and recovery requirements
to prevent overtraining and injury.
"""

from typing import Any, Dict, Literal

# Type alias for training type
TrainingType = Literal["strength", "endurance"]

# Progression rules configuration
PROGRESSION_RULES: Dict[TrainingType, Dict[str, Any]] = {
    "strength": {
        # Maximum weekly volume increase (percentage)
        "weekly_volume_increase_max": 0.10,  # 10%
        # Minimum weight increment (kg)
        "weight_increase_min_kg": 2.5,
        # Maximum weight increment (kg) per session
        "weight_increase_max_kg": 5.0,
        # Deload frequency (every N weeks)
        "deload_week_frequency": 4,
        # Deload volume reduction (percentage)
        "deload_volume_reduction": 0.40,  # -40% volume during deload
        # Maximum RPE for regular training
        "max_training_rpe": 9,
        # Minimum rest between same muscle group (hours)
        "min_muscle_group_rest_hours": 48,
        # Maximum consecutive high-intensity days
        "max_consecutive_hard_days": 2,
    },
    "endurance": {
        # Maximum weekly distance increase (percentage)
        "weekly_distance_increase_max": 0.15,  # 15%
        # Maximum intensity sessions per week
        "weekly_intensity_sessions_max": 2,
        # Recovery week frequency (every N weeks)
        "recovery_week_frequency": 3,
        # Recovery week volume reduction (percentage)
        "recovery_week_reduction": 0.30,  # -30% during recovery week
        # Maximum consecutive hard days (RPE > 7)
        "max_consecutive_hard_days": 1,
        # Minimum easy days between interval sessions
        "min_easy_days_between_intervals": 2,
        # Maximum long session as percentage of weekly volume
        "max_long_session_percentage": 0.30,  # 30% of weekly volume
    },
}


# General guardrail rules (apply to all training types)
GENERAL_GUARDRAILS: Dict[str, Any] = {
    # Maximum consecutive days without rest
    "max_consecutive_training_days": 5,
    # Minimum rest days per week
    "min_rest_days_per_week": 1,
    # Maximum RPE for consecutive days
    "max_rpe_consecutive_days": 8,
    # Days to ease back after extended rest (2+ days)
    "return_to_training_easy_days": 1,
    # Return-to-training maximum RPE
    "return_to_training_max_rpe": 6,
    # Maximum weekly training hours (general cap)
    "max_weekly_training_hours": 15,
}


def get_progression_rules(training_type: TrainingType) -> Dict[str, Any]:
    """Get progression rules for a specific training type."""
    return PROGRESSION_RULES.get(training_type, PROGRESSION_RULES["strength"])


def get_deload_week(current_week: int, training_type: TrainingType) -> bool:
    """Check if current week should be a deload/recovery week."""
    rules = get_progression_rules(training_type)
    frequency_key = (
        "deload_week_frequency"
        if training_type == "strength"
        else "recovery_week_frequency"
    )
    frequency = rules.get(frequency_key, 4)
    return current_week > 0 and current_week % frequency == 0


def calculate_max_volume_increase(
    current_volume: float, training_type: TrainingType
) -> float:
    """Calculate maximum allowed volume for next week."""
    rules = get_progression_rules(training_type)
    if training_type == "strength":
        max_increase = rules["weekly_volume_increase_max"]
    else:
        max_increase = rules["weekly_distance_increase_max"]
    return current_volume * (1 + max_increase)

