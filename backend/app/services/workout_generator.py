"""
Workout generator service.

Generates detailed WorkoutPlan for specific days (just-in-time generation).
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.models.plan import DaySlot
from app.models.snapshot import FitnessSnapshot
from app.models.workout import WorkoutLog, WorkoutPlan
from app.services.llm_client import llm_client
from app.storage.json_store import store

logger = logging.getLogger(__name__)

# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "workout_generation.txt"

# Load exercise database
EXERCISE_DB_PATH = Path(__file__).parent.parent.parent / "exercises.json"


def load_prompt_template() -> str:
    """Load the prompt template from file."""
    try:
        with open(PROMPT_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template not found: {PROMPT_PATH}")
        raise


def load_exercise_names() -> List[str]:
    """Load exercise names from the database."""
    try:
        with open(EXERCISE_DB_PATH, "r") as f:
            data = json.load(f)
            exercises = data.get("data", {}).get("exercises", [])
            return [ex["name"] for ex in exercises]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load exercise database: {e}")
        return []


class WorkoutGenerator:
    """Generates detailed workout plans for specific days."""

    def __init__(self):
        """Initialize the generator."""
        self.prompt_template = load_prompt_template()
        self.exercise_names = load_exercise_names()

    def generate(
        self,
        snapshot: FitnessSnapshot,
        day_slot: DaySlot,
        recent_logs: Optional[List[WorkoutLog]] = None,
    ) -> Optional[WorkoutPlan]:
        """
        Generate a detailed workout for a specific day.
        
        Args:
            snapshot: FitnessSnapshot with user context
            day_slot: The day slot to generate a workout for
            recent_logs: Recent workout logs for context
            
        Returns:
            WorkoutPlan or None if generation failed
        """
        if day_slot.is_rest_day:
            logger.info(f"Day {day_slot.date} is a rest day - no workout to generate")
            return None

        # Get recent logs if not provided
        if recent_logs is None:
            recent_logs = store.get_workout_logs_for_user(
                snapshot.profile.user_id, limit=10
            )

        # Build the prompt
        prompt = self._build_prompt(snapshot, day_slot, recent_logs)
        system_prompt = self._build_system_prompt()

        # Validation context
        validation_context = {
            "recent_logs": recent_logs,
            "has_pain": any(f.status == "pain" for f in snapshot.recent_feedback),
            "pain_body_part": next(
                (f.body_part for f in snapshot.recent_feedback if f.status == "pain"),
                None,
            ),
            "days_since_last_workout": snapshot.days_since_last_workout,
        }

        # Generate and validate
        workout, result = llm_client.generate_and_validate(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model_class=WorkoutPlan,
            validation_context=validation_context,
        )

        if workout:
            logger.info(f"Generated workout: {workout.workout_id} for {workout.scheduled_for_date}")
            return workout

        logger.error(f"Failed to generate workout: {result.all_errors}")
        return None

    def _build_system_prompt(self) -> str:
        """Build the system prompt."""
        return """You are an expert fitness coach creating detailed workout plans.
Your task is to create a specific workout with exercises, sets, reps, and coaching cues.

MOST IMPORTANT RULE: The "kind" field for each exercise MUST be EXACTLY one of these four values:
- "strength"
- "endurance"
- "mobility"
- "recovery"

DO NOT use "cardio", "stretching", "warmup", "activation", "core", "plyometric" or any other value. Only the four values above are valid.

CRITICAL RULES:
1. Every "kind" field MUST be one of: "strength", "endurance", "mobility", "recovery"
2. Always output valid JSON matching the specified schema
3. Include warmup, main, and cooldown sections
4. Use appropriate exercises for the available equipment
5. Respect injuries and limitations - avoid exercises that could aggravate them
6. Match the target intensity (RPE)
7. Stay within the target duration (±10 minutes)
8. Provide clear, actionable coaching cues
9. If user has reported pain, significantly reduce intensity and avoid affected areas

Remember: "kind" can ONLY be "strength", "endurance", "mobility", or "recovery"."""

    def _build_prompt(
        self,
        snapshot: FitnessSnapshot,
        day_slot: DaySlot,
        recent_logs: List[WorkoutLog],
    ) -> str:
        """Build the user prompt from snapshot and day slot."""
        profile = snapshot.profile
        goal = snapshot.goal

        # Format recent workouts summary
        recent_summary = self._format_recent_logs(recent_logs)

        # Format current feedback
        feedback_summary = self._format_feedback(snapshot.recent_feedback)

        # Format exercise list (subset for prompt efficiency)
        relevant_exercises = self._get_relevant_exercises(
            day_slot.workout_type or "strength",
            profile.available_equipment,
        )
        exercise_list = ", ".join(relevant_exercises[:50])  # Limit for token efficiency

        # Generate workout ID
        workout_id = f"workout_{day_slot.date}_{uuid.uuid4().hex[:6]}"

        return self.prompt_template.format(
            fitness_level=profile.fitness_level,
            weight_kg=profile.weight_kg,
            available_equipment=", ".join(profile.available_equipment),
            injuries_or_limitations=profile.injuries_or_limitations or "None",
            goal_type=goal.goal_type,
            target_event=goal.target_event or "General fitness",
            days_until_goal=snapshot.days_until_goal,
            scheduled_date=day_slot.date,
            date=day_slot.date,
            workout_type=day_slot.workout_type or "general",
            target_duration_min=day_slot.target_duration_min or 45,
            intensity_target=day_slot.intensity_target or "RPE_6_7",
            recent_workouts_summary=recent_summary,
            days_since_last_workout=snapshot.days_since_last_workout,
            current_feedback=feedback_summary,
            exercise_list=exercise_list,
            workout_id=workout_id,
            type=day_slot.workout_type or "general",
        )

    def _format_recent_logs(self, logs: List[WorkoutLog]) -> str:
        """Format recent workout logs for the prompt."""
        if not logs:
            return "No recent workouts"

        lines = []
        for log in logs[:5]:  # Last 5 workouts
            exercises = ", ".join(e.name for e in log.exercises[:3])
            if len(log.exercises) > 3:
                exercises += f" (+{len(log.exercises) - 3} more)"
            line = f"- {log.date[:10]}: {log.workout_type}, {log.duration_min}min, RPE {log.rpe_actual}"
            line += f"\n  Exercises: {exercises}"
            lines.append(line)

        return "\n".join(lines)

    def _format_feedback(self, feedback_list) -> str:
        """Format recent feedback for the prompt."""
        if not feedback_list:
            return "No recent feedback"

        # Get most recent feedback
        latest = feedback_list[0]
        result = f"Status: {latest.status}"
        if latest.body_part:
            result += f", Affected area: {latest.body_part}"
        if latest.severity:
            result += f", Severity: {latest.severity}/5"
        return result

    def _get_relevant_exercises(
        self,
        workout_type: str,
        equipment: List[str],
    ) -> List[str]:
        """Get exercises relevant to workout type and equipment."""
        # For now, return all exercises - in production would filter by type/equipment
        return self.exercise_names


# Global generator instance
workout_generator = WorkoutGenerator()

