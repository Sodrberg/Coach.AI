"""
Workout rescheduler service.

Handles rescheduling of skipped workouts by swapping with current day's workout.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from app.models.plan import DaySlot, ThreeWeekBlock
from app.models.workout import WorkoutPlan
from app.storage.json_store import store

logger = logging.getLogger(__name__)


class WorkoutRescheduler:
    """Service for rescheduling skipped workouts."""

    def find_incomplete_workouts(
        self,
        user_id: str,
        today: str,
        lookback_days: int = 3,
    ) -> list[DaySlot]:
        """
        Find incomplete workouts from the past N days.
        
        Args:
            user_id: User ID
            today: Today's date (YYYY-MM-DD)
            lookback_days: Number of days to look back
            
        Returns:
            List of DaySlots with status="planned" and is_rest_day=False from past days
        """
        from datetime import timedelta
        
        today_date = datetime.fromisoformat(today)
        incomplete = []
        
        # Get current block
        block = store.get_current_block(user_id, today)
        if not block:
            return incomplete
        
        # Check past N days
        for i in range(1, lookback_days + 1):
            check_date = (today_date - timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Find slot for this date
            for slot in block.day_slots:
                if slot.date == check_date:
                    # Check if it's an incomplete workout (not rest day, not completed/skipped)
                    if not slot.is_rest_day and slot.status == "planned":
                        incomplete.append(slot)
                    break
        
        # Return sorted by date (oldest first)
        return sorted(incomplete, key=lambda s: s.date)

    def reschedule_skipped_workout(
        self,
        user_id: str,
        skipped_date: str,
        target_date: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Reschedule a skipped workout to the target date by swapping.
        
        Args:
            user_id: User ID
            skipped_date: Date of the skipped workout
            target_date: Date to move the workout to (usually today)
            
        Returns:
            Tuple of (success, error_message)
        """
        # Get current block
        block = store.get_current_block(user_id, target_date)
        if not block:
            return False, "No active training block found"
        
        # Find the skipped slot and target slot
        skipped_slot: Optional[DaySlot] = None
        target_slot: Optional[DaySlot] = None
        skipped_idx: int = -1
        target_idx: int = -1
        
        for i, slot in enumerate(block.day_slots):
            if slot.date == skipped_date:
                skipped_slot = slot
                skipped_idx = i
            elif slot.date == target_date:
                target_slot = slot
                target_idx = i
        
        if not skipped_slot:
            return False, f"Could not find slot for skipped date {skipped_date}"
        if not target_slot:
            return False, f"Could not find slot for target date {target_date}"
        
        # Mark skipped slot as skipped
        skipped_slot.status = "skipped"
        
        # If target is a rest day, we need to find the next non-rest slot for today's workout
        # But first, let's move the skipped workout to today
        
        # Store target slot's original workout data
        target_original = {
            "workout_type": target_slot.workout_type,
            "target_duration_min": target_slot.target_duration_min,
            "target_distance_km": target_slot.target_distance_km,
            "intensity_target": target_slot.intensity_target,
            "is_rest_day": target_slot.is_rest_day,
            "workout_id": target_slot.workout_id,
        }
        
        # Move skipped workout data to target slot
        target_slot.workout_type = skipped_slot.workout_type
        target_slot.target_duration_min = skipped_slot.target_duration_min
        target_slot.target_distance_km = skipped_slot.target_distance_km
        target_slot.intensity_target = skipped_slot.intensity_target
        target_slot.is_rest_day = False  # No longer a rest day
        target_slot.status = "adjusted"
        target_slot.workout_id = None  # Will be generated fresh
        
        # If target wasn't a rest day, find next available slot for the displaced workout
        if not target_original["is_rest_day"]:
            next_available_idx = self._find_next_available_slot(
                block, target_idx, target_original["workout_type"]
            )
            
            if next_available_idx is not None:
                next_slot = block.day_slots[next_available_idx]
                # Move today's original workout to next available
                next_slot.workout_type = target_original["workout_type"]
                next_slot.target_duration_min = target_original["target_duration_min"]
                next_slot.target_distance_km = target_original["target_distance_km"]
                next_slot.intensity_target = target_original["intensity_target"]
                next_slot.is_rest_day = False
                next_slot.status = "adjusted"
                next_slot.workout_id = None
                
                logger.info(
                    f"Displaced workout from {target_date} moved to {next_slot.date}"
                )
        
        # Save updated block
        if store.save_block(user_id, block):
            logger.info(
                f"Rescheduled workout from {skipped_date} to {target_date}"
            )
            return True, None
        else:
            return False, "Failed to save updated block"

    def _find_next_available_slot(
        self,
        block: ThreeWeekBlock,
        after_idx: int,
        workout_type: Optional[str],
    ) -> Optional[int]:
        """
        Find the next available slot after the given index.
        
        Looks for rest days that can be converted, or slots that can be adjusted.
        
        Args:
            block: The training block
            after_idx: Index to start searching after
            workout_type: Type of workout being displaced (for compatibility)
            
        Returns:
            Index of next available slot, or None if not found
        """
        # First, look for rest days we can convert
        for i in range(after_idx + 1, len(block.day_slots)):
            slot = block.day_slots[i]
            if slot.is_rest_day and slot.status == "planned":
                return i
        
        # If no rest days, this is a more complex scenario
        # For MVP, we'll just return None and log a warning
        logger.warning(
            f"No available slot found after index {after_idx} for displaced workout"
        )
        return None

    def mark_workout_completed(
        self,
        user_id: str,
        workout_date: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Mark a workout as completed.
        
        Args:
            user_id: User ID
            workout_date: Date of the workout to mark complete
            
        Returns:
            Tuple of (success, error_message)
        """
        # Get current block containing this date
        block = store.get_current_block(user_id, workout_date)
        if not block:
            return False, "No active training block found"
        
        # Find the slot
        for slot in block.day_slots:
            if slot.date == workout_date:
                slot.status = "completed"
                
                if store.save_block(user_id, block):
                    logger.info(f"Marked workout on {workout_date} as completed")
                    return True, None
                else:
                    return False, "Failed to save updated block"
        
        return False, f"Could not find slot for date {workout_date}"


# Global instance
workout_rescheduler = WorkoutRescheduler()

