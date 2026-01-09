"""
Adjustment rules for modifying workouts based on user feedback.

These rules are the source of truth for how workouts are adjusted
when users report soreness, tiredness, pain, or feeling great.
"""

from typing import Any, Dict, Literal

# Type alias for feedback status
FeedbackStatus = Literal["sore", "tired", "great", "pain"]

# Adjustment rules configuration
ADJUSTMENT_RULES: Dict[FeedbackStatus, Dict[str, Any]] = {
    "sore": {
        # Volume reduction (percentage)
        "reduce_volume": 0.30,  # -30% volume
        # Intensity reduction (percentage)
        "reduce_intensity": 0.20,  # -20% intensity
        # Skip exercises targeting same muscle group
        "skip_same_muscle_group": True,
        # Whether to consider adding an extra rest day
        "consider_rest_day": False,
        # Maximum RPE for adjusted workout
        "max_rpe": 7,
        # User message
        "message": "Workout adjusted for muscle soreness - reduced volume and intensity.",
    },
    "tired": {
        # RPE target reduction (absolute points)
        "reduce_rpe_target": 2,  # e.g., RPE 8 → 6
        # Whether to add a rest day instead
        "add_rest_day": False,
        # Reduce duration by percentage
        "reduce_duration": 0.15,  # -15% duration
        # Maximum RPE for adjusted workout
        "max_rpe": 6,
        # User message
        "message": "Workout adjusted for fatigue - reduced intensity target.",
    },
    "pain": {
        # Exclude exercises targeting affected body part
        "exclude_exercises_by_body_part": True,
        # Maximum allowed RPE when pain is reported
        "max_rpe": 5,
        # Alert message to show user
        "alert_user": "Consider consulting a healthcare professional if pain persists.",
        # Reduce overall intensity significantly
        "reduce_intensity": 0.40,  # -40% intensity
        # Replace with recovery/mobility work
        "suggest_recovery_alternatives": True,
        # How many days to potentially adjust going forward
        "adjust_future_days": 3,
        # User message
        "message": "Workout significantly modified due to pain - prioritizing recovery.",
    },
    "great": {
        # No adjustments needed
        "no_adjustment": True,
        # Optional: slight increase allowed (but not automatic)
        "allow_progression": True,
        # User message
        "message": "Great! Proceeding with planned workout.",
    },
}

# Body part to muscle group mapping for exercise exclusion
BODY_PART_MUSCLE_MAPPING: Dict[str, list[str]] = {
    "shoulder": ["shoulders", "deltoids", "rotator_cuff", "traps"],
    "knee": ["quadriceps", "hamstrings", "calves"],
    "back": ["lats", "lower_back", "upper_back", "erectors", "rhomboids"],
    "neck": ["neck", "traps", "upper_back"],
    "hip": ["hip_flexors", "glutes", "adductors", "abductors"],
    "ankle": ["calves", "tibialis", "feet"],
    "wrist": ["forearms", "wrist_flexors", "wrist_extensors"],
    "elbow": ["biceps", "triceps", "forearms"],
    "chest": ["pectorals", "chest"],
    "core": ["abdominals", "obliques", "lower_back"],
}


def get_muscle_groups_for_body_part(body_part: str) -> list[str]:
    """Get list of muscle groups associated with a body part."""
    body_part_lower = body_part.lower()
    return BODY_PART_MUSCLE_MAPPING.get(body_part_lower, [body_part_lower])


def get_adjustment_for_status(status: FeedbackStatus) -> Dict[str, Any]:
    """Get adjustment rules for a given feedback status."""
    return ADJUSTMENT_RULES.get(status, ADJUSTMENT_RULES["great"])

