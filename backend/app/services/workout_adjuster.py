"""
Workout adjuster service.

Applies ADJUSTMENT_RULES to modify workouts based on user feedback.
"""

import copy
import logging
from typing import List, Optional

from app.models.user import UserFeedback
from app.models.workout import WorkoutItem, WorkoutPlan, WorkoutSection
from app.rules.adjustment_rules import (
    ADJUSTMENT_RULES,
    get_adjustment_for_status,
    get_muscle_groups_for_body_part,
)

logger = logging.getLogger(__name__)


class WorkoutAdjuster:
    """Adjusts workouts based on user feedback using ADJUSTMENT_RULES."""

    def adjust(
        self,
        workout: WorkoutPlan,
        feedback: UserFeedback,
    ) -> WorkoutPlan:
        """
        Adjust a workout based on user feedback.
        
        Args:
            workout: The original workout plan
            feedback: User's feedback (sore, tired, great, pain)
            
        Returns:
            Adjusted WorkoutPlan (new instance, original unchanged)
        """
        # Get adjustment rules for this feedback status
        rules = get_adjustment_for_status(feedback.status)

        if rules.get("no_adjustment"):
            logger.info(f"No adjustment needed for status: {feedback.status}")
            return workout

        # Create a deep copy to avoid mutating original
        adjusted = self._deep_copy_workout(workout)

        # Apply adjustments based on feedback type
        if feedback.status == "sore":
            adjusted = self._apply_sore_adjustments(adjusted, rules, feedback)
        elif feedback.status == "tired":
            adjusted = self._apply_tired_adjustments(adjusted, rules)
        elif feedback.status == "pain":
            adjusted = self._apply_pain_adjustments(adjusted, rules, feedback)

        # Update the title to indicate adjustment
        adjusted.title = f"[Adjusted] {adjusted.title}"

        logger.info(f"Adjusted workout for {feedback.status}: {adjusted.workout_id}")
        return adjusted

    def _deep_copy_workout(self, workout: WorkoutPlan) -> WorkoutPlan:
        """Create a deep copy of a workout plan."""
        return WorkoutPlan(
            workout_id=workout.workout_id,
            scheduled_for_date=workout.scheduled_for_date,
            title=workout.title,
            workout_type=workout.workout_type,
            estimated_duration_min=workout.estimated_duration_min,
            intensity_target=workout.intensity_target,
            sections=[
                WorkoutSection(
                    name=section.name,
                    items=[
                        WorkoutItem(**item.model_dump()) for item in section.items
                    ],
                )
                for section in workout.sections
            ],
            rationale=copy.copy(workout.rationale),
            questions=copy.copy(workout.questions) if workout.questions else None,
        )

    def _apply_sore_adjustments(
        self,
        workout: WorkoutPlan,
        rules: dict,
        feedback: UserFeedback,
    ) -> WorkoutPlan:
        """Apply adjustments for sore status."""
        volume_reduction = rules.get("reduce_volume", 0.30)
        intensity_reduction = rules.get("reduce_intensity", 0.20)
        skip_muscle_group = rules.get("skip_same_muscle_group", True)

        # Get affected muscle groups if body part specified
        affected_muscles = []
        if feedback.body_part and skip_muscle_group:
            affected_muscles = get_muscle_groups_for_body_part(feedback.body_part)

        for section in workout.sections:
            new_items = []
            for item in section.items:
                # Skip exercises targeting affected muscles
                if affected_muscles and self._targets_muscle_group(item, affected_muscles):
                    logger.info(f"Skipping {item.name} due to affected muscle group")
                    continue

                # Reduce volume (sets/reps)
                if item.sets:
                    item.sets = max(1, int(item.sets * (1 - volume_reduction)))
                if item.reps:
                    item.reps = max(1, int(item.reps * (1 - volume_reduction)))

                # Reduce intensity (weight)
                if item.weight_kg:
                    item.weight_kg = round(item.weight_kg * (1 - intensity_reduction), 1)

                new_items.append(item)

            section.items = new_items

        # Update intensity target
        workout.intensity_target = self._reduce_rpe_target(
            workout.intensity_target, 1
        )

        # Add rationale
        workout.rationale.append(
            f"Volume reduced by {int(volume_reduction * 100)}% due to soreness"
        )

        return workout

    def _apply_tired_adjustments(
        self,
        workout: WorkoutPlan,
        rules: dict,
    ) -> WorkoutPlan:
        """Apply adjustments for tired status."""
        rpe_reduction = rules.get("reduce_rpe_target", 2)
        duration_reduction = rules.get("reduce_duration", 0.15)

        # Reduce RPE target
        workout.intensity_target = self._reduce_rpe_target(
            workout.intensity_target, rpe_reduction
        )

        # Reduce duration
        workout.estimated_duration_min = int(
            workout.estimated_duration_min * (1 - duration_reduction)
        )

        # Optionally reduce sets in main section
        for section in workout.sections:
            if section.name == "main":
                for item in section.items:
                    if item.sets and item.sets > 2:
                        item.sets = max(2, item.sets - 1)

        # Add rationale
        workout.rationale.append(
            f"Intensity reduced by RPE {rpe_reduction} due to fatigue"
        )

        return workout

    def _apply_pain_adjustments(
        self,
        workout: WorkoutPlan,
        rules: dict,
        feedback: UserFeedback,
    ) -> WorkoutPlan:
        """Apply adjustments for pain status."""
        max_rpe = rules.get("max_rpe", 5)
        intensity_reduction = rules.get("reduce_intensity", 0.40)

        # Get affected muscle groups
        affected_muscles = []
        if feedback.body_part:
            affected_muscles = get_muscle_groups_for_body_part(feedback.body_part)

        for section in workout.sections:
            new_items = []
            for item in section.items:
                # Skip exercises targeting affected body part
                if affected_muscles and self._targets_muscle_group(item, affected_muscles):
                    logger.info(f"Excluding {item.name} due to pain in {feedback.body_part}")
                    continue

                # Significantly reduce intensity
                if item.weight_kg:
                    item.weight_kg = round(item.weight_kg * (1 - intensity_reduction), 1)

                # Convert high-intensity items to recovery/mobility
                if item.kind == "strength":
                    item.kind = "recovery"
                    if item.reps:
                        item.reps = max(5, item.reps // 2)

                new_items.append(item)

            section.items = new_items

        # Set max RPE
        workout.intensity_target = f"RPE_{max_rpe - 1}_{max_rpe}"

        # Reduce duration
        workout.estimated_duration_min = int(workout.estimated_duration_min * 0.6)

        # Add rationale and alert
        workout.rationale.append(
            f"Workout significantly modified due to pain in {feedback.body_part or 'reported area'}"
        )
        
        alert = rules.get("alert_user")
        if alert:
            workout.rationale.append(f"⚠️ {alert}")

        return workout

    def _targets_muscle_group(self, item: WorkoutItem, muscles: List[str]) -> bool:
        """Check if exercise targets any of the specified muscle groups."""
        item_name_lower = item.name.lower()
        for muscle in muscles:
            if muscle.lower() in item_name_lower:
                return True
        return False

    def _reduce_rpe_target(self, intensity_target: str, reduction: int) -> str:
        """Reduce RPE target in intensity string."""
        # Parse RPE from string like "RPE_6_7" or "RPE_8"
        try:
            parts = intensity_target.upper().replace("RPE", "").replace("_", " ").split()
            if len(parts) >= 2:
                low = max(1, int(parts[0]) - reduction)
                high = max(1, int(parts[1]) - reduction)
                return f"RPE_{low}_{high}"
            elif len(parts) == 1:
                rpe = max(1, int(parts[0]) - reduction)
                return f"RPE_{rpe}"
        except (ValueError, IndexError):
            pass
        return f"RPE_{max(1, 6 - reduction)}"


# Global adjuster instance
workout_adjuster = WorkoutAdjuster()

