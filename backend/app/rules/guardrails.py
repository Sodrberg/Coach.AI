"""
Deterministic guardrail checks for workout validation.

These functions enforce hard limits that the LLM cannot override.
Code is the enforcement, not prompts.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from app.models.plan import DaySlot, ThreeWeekBlock
from app.models.workout import WorkoutLog, WorkoutPlan
from app.rules.progression_rules import GENERAL_GUARDRAILS, get_progression_rules


class GuardrailViolation:
    """Represents a guardrail violation."""

    def __init__(self, rule: str, message: str, severity: str = "warning"):
        self.rule = rule
        self.message = message
        self.severity = severity  # "warning", "error", "critical"

    def __repr__(self) -> str:
        return f"GuardrailViolation({self.rule}: {self.message})"


def check_consecutive_hard_days(
    recent_logs: List[WorkoutLog],
    proposed_rpe: int,
    training_type: str = "strength",
) -> Optional[GuardrailViolation]:
    """
    Check if proposed workout would create too many consecutive hard days.
    
    Hard day = RPE > 8
    """
    rules = get_progression_rules(training_type if training_type in ("strength", "endurance") else "strength")
    max_consecutive = rules.get("max_consecutive_hard_days", 2)
    hard_threshold = 8

    if proposed_rpe <= hard_threshold:
        return None

    # Count recent consecutive hard days
    consecutive_hard = 0
    for log in sorted(recent_logs, key=lambda x: x.date, reverse=True):
        if log.rpe_actual > hard_threshold:
            consecutive_hard += 1
        else:
            break

    if consecutive_hard >= max_consecutive:
        return GuardrailViolation(
            rule="consecutive_hard_days",
            message=f"Cannot schedule RPE {proposed_rpe} workout after {consecutive_hard} consecutive hard days (max: {max_consecutive})",
            severity="error",
        )
    return None


def check_weekly_progression(
    last_week_volume: float,
    proposed_week_volume: float,
    training_type: str = "strength",
) -> Optional[GuardrailViolation]:
    """Check if weekly volume increase exceeds safe limits."""
    rules = get_progression_rules(training_type if training_type in ("strength", "endurance") else "strength")

    if training_type == "endurance":
        max_increase = rules["weekly_distance_increase_max"]
    else:
        max_increase = rules["weekly_volume_increase_max"]

    if last_week_volume == 0:
        return None

    actual_increase = (proposed_week_volume - last_week_volume) / last_week_volume

    if actual_increase > max_increase:
        return GuardrailViolation(
            rule="weekly_progression",
            message=f"Weekly volume increase {actual_increase:.1%} exceeds maximum {max_increase:.1%}",
            severity="error",
        )
    return None


def check_rest_day_requirements(
    week_day_slots: List[DaySlot],
) -> Optional[GuardrailViolation]:
    """Check if week has minimum required rest days."""
    min_rest = GENERAL_GUARDRAILS["min_rest_days_per_week"]
    rest_days = sum(1 for slot in week_day_slots if slot.is_rest_day)

    if rest_days < min_rest:
        return GuardrailViolation(
            rule="rest_day_requirement",
            message=f"Week has only {rest_days} rest day(s), minimum is {min_rest}",
            severity="error",
        )
    return None


def check_muscle_group_recovery(
    recent_logs: List[WorkoutLog],
    proposed_muscle_groups: List[str],
    proposed_intensity: str,
) -> Optional[GuardrailViolation]:
    """
    Check if muscle groups have had adequate recovery time.
    
    Requires 48h between high-intensity sessions targeting same muscle group.
    """
    if "low" in proposed_intensity.lower():
        return None

    rules = get_progression_rules("strength")
    min_rest_hours = rules["min_muscle_group_rest_hours"]

    now = datetime.now()
    cutoff = now - timedelta(hours=min_rest_hours)

    for log in recent_logs:
        try:
            log_date = datetime.fromisoformat(log.date.replace("Z", "+00:00"))
            if log_date.replace(tzinfo=None) < cutoff.replace(tzinfo=None):
                continue
        except ValueError:
            continue

        # Check if log intensity was high
        if log.intensity not in ("high", "medium") and log.rpe_actual <= 7:
            continue

        # Check for muscle group overlap
        for exercise in log.exercises:
            exercise_name_lower = exercise.name.lower()
            for muscle in proposed_muscle_groups:
                if muscle.lower() in exercise_name_lower:
                    return GuardrailViolation(
                        rule="muscle_group_recovery",
                        message=f"Muscle group '{muscle}' was trained within {min_rest_hours}h",
                        severity="warning",
                    )
    return None


def check_return_to_training(
    days_since_last_workout: int,
    proposed_rpe: int,
) -> Optional[GuardrailViolation]:
    """Check if returning from extended rest with appropriate intensity."""
    if days_since_last_workout < 2:
        return None

    max_rpe = GENERAL_GUARDRAILS["return_to_training_max_rpe"]

    if proposed_rpe > max_rpe:
        return GuardrailViolation(
            rule="return_to_training",
            message=f"After {days_since_last_workout} days rest, RPE should be ≤{max_rpe} (proposed: {proposed_rpe})",
            severity="warning",
        )
    return None


def check_pain_feedback_compliance(
    has_pain_feedback: bool,
    pain_body_part: Optional[str],
    proposed_rpe: int,
    proposed_exercises: List[str],
) -> Optional[GuardrailViolation]:
    """
    Check if workout respects pain feedback.
    
    When pain is reported:
    - RPE must be ≤ 5
    - Exercises targeting affected area must be excluded
    """
    if not has_pain_feedback:
        return None

    max_pain_rpe = 5
    if proposed_rpe > max_pain_rpe:
        return GuardrailViolation(
            rule="pain_intensity",
            message=f"With pain reported, RPE must be ≤{max_pain_rpe} (proposed: {proposed_rpe})",
            severity="critical",
        )

    if pain_body_part:
        body_part_lower = pain_body_part.lower()
        for exercise in proposed_exercises:
            if body_part_lower in exercise.lower():
                return GuardrailViolation(
                    rule="pain_exercise_exclusion",
                    message=f"Exercise '{exercise}' targets painful area '{pain_body_part}'",
                    severity="critical",
                )
    return None


def validate_workout_plan(
    workout: WorkoutPlan,
    recent_logs: List[WorkoutLog],
    has_pain: bool = False,
    pain_body_part: Optional[str] = None,
    days_since_last_workout: int = 0,
) -> Tuple[bool, List[GuardrailViolation]]:
    """
    Run all guardrail checks on a proposed workout plan.
    
    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations: List[GuardrailViolation] = []

    # Extract RPE from intensity target (e.g., "RPE_6_7" -> 7)
    try:
        if "RPE" in workout.intensity_target.upper():
            rpe_parts = workout.intensity_target.upper().replace("RPE", "").replace("_", " ").split()
            proposed_rpe = int(rpe_parts[-1]) if rpe_parts else 7
        else:
            proposed_rpe = 7  # Default assumption
    except (ValueError, IndexError):
        proposed_rpe = 7

    # Determine training type from workout type
    training_type = "endurance" if workout.workout_type in ("endurance", "intervals", "cardio") else "strength"

    # Check consecutive hard days
    violation = check_consecutive_hard_days(recent_logs, proposed_rpe, training_type)
    if violation:
        violations.append(violation)

    # Check return to training
    violation = check_return_to_training(days_since_last_workout, proposed_rpe)
    if violation:
        violations.append(violation)

    # Check pain compliance
    all_exercises = []
    for section in workout.sections:
        for item in section.items:
            all_exercises.append(item.name)

    violation = check_pain_feedback_compliance(
        has_pain, pain_body_part, proposed_rpe, all_exercises
    )
    if violation:
        violations.append(violation)

    # Determine validity (critical or error = invalid)
    is_valid = not any(v.severity in ("critical", "error") for v in violations)

    return is_valid, violations


def validate_block(block: ThreeWeekBlock) -> Tuple[bool, List[GuardrailViolation]]:
    """
    Validate a 21-day block against guardrail rules.
    
    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations: List[GuardrailViolation] = []

    # Check each week for rest day requirements
    for week_num in range(3):
        start_idx = week_num * 7
        end_idx = start_idx + 7
        week_slots = block.day_slots[start_idx:end_idx]

        violation = check_rest_day_requirements(week_slots)
        if violation:
            violation.message = f"Week {week_num + 1}: {violation.message}"
            violations.append(violation)

    # Check for consecutive training days
    max_consecutive = GENERAL_GUARDRAILS["max_consecutive_training_days"]
    consecutive_count = 0
    for slot in block.day_slots:
        if not slot.is_rest_day:
            consecutive_count += 1
            if consecutive_count > max_consecutive:
                violations.append(
                    GuardrailViolation(
                        rule="consecutive_training_days",
                        message=f"More than {max_consecutive} consecutive training days around day {slot.day_number}",
                        severity="error",
                    )
                )
                break
        else:
            consecutive_count = 0

    is_valid = not any(v.severity in ("critical", "error") for v in violations)
    return is_valid, violations

