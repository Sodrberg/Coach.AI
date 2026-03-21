"""
Quick onboarding service.

Orchestrates the fast onboarding flow: parse free-text goal via LLM,
create profile/goal with defaults, then run the existing plan generation pipeline.
"""

import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from app.models.onboarding import InferredGoal, QuickOnboardRequest, QuickOnboardResponse
from app.models.plan import CompletePlan
from app.models.user import UserGoal, UserProfile
from app.services.block_generator import block_generator
from app.services.high_level_plan_generator import high_level_plan_generator
from app.services.llm_client import llm_client
from app.services.snapshot_builder import snapshot_builder
from app.storage.json_store import store

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "quick_onboard.txt"

GYM_EQUIPMENT_MAP = {
    "gym": ["gym", "barbell", "dumbbells", "kettlebells", "pull_up_bar"],
    "no_gym": ["resistance_bands"],
    "both": ["gym", "barbell", "dumbbells", "kettlebells", "pull_up_bar", "resistance_bands"],
}


def _map_gym_access_to_equipment(gym_access: Optional[str]) -> List[str]:
    """Map gym access level to available equipment list."""
    if gym_access is None:
        return ["none"]
    return GYM_EQUIPMENT_MAP.get(gym_access, ["none"])


def _load_prompt_template() -> str:
    """Load the quick onboard prompt template."""
    try:
        with open(PROMPT_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template not found: {PROMPT_PATH}")
        raise


class QuickOnboardService:
    """Handles the quick onboarding flow."""

    def __init__(self):
        self.prompt_template = _load_prompt_template()

    def onboard(self, request: QuickOnboardRequest) -> Optional[QuickOnboardResponse]:
        """
        Run the full quick onboarding pipeline.

        1. LLM parses free-text goal into structured InferredGoal
        2. Build UserProfile with safe defaults
        3. Build UserGoal from inferred data
        4. Save profile + goal
        5. Run plan generation pipeline
        6. Return QuickOnboardResponse

        Returns None if any step fails.
        """
        # Step 1: Infer goal from free text
        inferred = self._infer_goal(request.goal_text)
        if not inferred:
            logger.error("Failed to infer goal from free text")
            return None

        # Step 2: Build profile with defaults
        profile = UserProfile(
            user_id=request.user_id,
            age=30,
            weight_kg=75.0,
            height_cm=175,
            fitness_level=inferred.fitness_level,
            training_history_years=1,
            available_equipment=_map_gym_access_to_equipment(request.gym_access),
            training_days_per_week=request.training_days_per_week,
            preferred_training_days=request.preferred_training_days,
            training_type_preference=request.training_type_preference,
        )

        # Step 3: Build goal
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        goal = UserGoal(
            goal_id=goal_id,
            user_id=request.user_id,
            goal_type=inferred.goal_type,
            target_event=inferred.target_event,
            target_date=inferred.target_date,
            priority=inferred.priority,
        )

        # Step 4: Save profile + goal
        if not store.save_profile(profile):
            logger.error("Failed to save profile during onboarding")
            return None
        if not store.save_goal(goal):
            logger.error("Failed to save goal during onboarding")
            return None

        # Step 5: Run plan generation pipeline
        complete_plan = self._generate_plan(request.user_id, goal_id)
        if not complete_plan:
            logger.error("Failed to generate plan during onboarding")
            return None

        logger.info(f"Quick onboarding complete for user {request.user_id}")
        return QuickOnboardResponse(
            profile=profile,
            goal=goal,
            complete_plan=complete_plan,
        )

    def _infer_goal(self, goal_text: str) -> Optional[InferredGoal]:
        """Use LLM to parse free-text goal into structured data."""
        today = datetime.now()
        today_date = today.strftime("%Y-%m-%d")
        default_target_date = (today + timedelta(weeks=8)).strftime("%Y-%m-%d")

        system_prompt = (
            "You are an expert fitness coach. Parse the user's goal "
            "description and return structured JSON. Use provided defaults "
            "when information is not explicitly stated."
        )

        user_prompt = self.prompt_template.format(
            goal_text=goal_text,
            today_date=today_date,
            default_target_date=default_target_date,
        )

        inferred, result = llm_client.generate_and_validate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_class=InferredGoal,
        )

        if inferred:
            logger.info(f"Inferred goal: type={inferred.goal_type}, event={inferred.target_event}")
            return inferred

        logger.error(f"Goal inference failed: {result.all_errors}")
        return None

    def _generate_plan(self, user_id: str, goal_id: str) -> Optional[CompletePlan]:
        """Run the existing plan generation pipeline."""
        # Build snapshot
        snapshot = snapshot_builder.build_snapshot(user_id)
        if not snapshot:
            return None

        # Generate high-level plan
        high_level_plan = high_level_plan_generator.generate(snapshot)
        if not high_level_plan:
            return None
        store.save_high_level_plan(high_level_plan)

        # Generate first 21-day block
        first_block = block_generator.generate(
            snapshot=snapshot,
            high_level_plan=high_level_plan,
            block_number=1,
        )
        if not first_block:
            return None
        store.save_block(user_id, first_block)

        # Detailed workouts are generated just-in-time when the user
        # requests their workout for a given day (GET /workout/today).
        # This keeps onboarding fast and avoids wasted LLM calls for
        # users who don't return.

        # Create and save complete plan
        complete_plan = CompletePlan(
            high_level_plan=high_level_plan,
            current_block=first_block,
            blocks_generated=[1],
            detailed_workouts={},
        )
        store.save_complete_plan(user_id, complete_plan)

        return complete_plan


# Global instance
quick_onboard_service = QuickOnboardService()
