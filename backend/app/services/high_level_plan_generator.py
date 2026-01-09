"""
High-level plan generator service.

Generates 8-week strategic training plans based on user profile and goal.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.plan import HighLevelPlan
from app.models.snapshot import FitnessSnapshot
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "high_level_plan.txt"


def load_prompt_template() -> str:
    """Load the prompt template from file."""
    try:
        with open(PROMPT_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template not found: {PROMPT_PATH}")
        raise


class HighLevelPlanGenerator:
    """Generates 8-week high-level training plans."""

    def __init__(self):
        """Initialize the generator."""
        self.prompt_template = load_prompt_template()

    def generate(self, snapshot: FitnessSnapshot) -> Optional[HighLevelPlan]:
        """
        Generate a high-level training plan.
        
        Args:
            snapshot: FitnessSnapshot with user context
            
        Returns:
            HighLevelPlan or None if generation failed
        """
        # Build the prompt
        prompt = self._build_prompt(snapshot)
        system_prompt = self._build_system_prompt()

        # Generate and validate
        plan, result = llm_client.generate_and_validate(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model_class=HighLevelPlan,
        )

        if plan:
            logger.info(f"Generated high-level plan: {plan.plan_id}")
            return plan

        logger.error(f"Failed to generate high-level plan: {result.all_errors}")
        return None

    def _build_system_prompt(self) -> str:
        """Build the system prompt."""
        return """You are an expert fitness coach with deep knowledge of periodization, 
training science, and personalized programming. Your task is to create strategic 
training plans that are safe, effective, and aligned with the user's goals.

CRITICAL RULES:
1. Always output valid JSON matching the specified schema
2. Use the provided data as source of truth - do not invent values
3. Consider safety: respect injuries, fitness level, and training history
4. Plans must be progressive and periodized appropriately
5. Include clear rationale in the overview_markdown"""

    def _build_prompt(self, snapshot: FitnessSnapshot) -> str:
        """Build the user prompt from snapshot."""
        profile = snapshot.profile
        goal = snapshot.goal
        timestamp = datetime.now().isoformat()
        plan_id = f"plan_{profile.user_id}_{uuid.uuid4().hex[:8]}"

        # Format equipment list
        equipment_str = ", ".join(profile.available_equipment) or "None specified"

        # Format preferred days
        preferred_days_str = (
            ", ".join(profile.preferred_training_days)
            if profile.preferred_training_days
            else "Not specified"
        )

        # Format baseline
        baseline_str = (
            str(goal.current_baseline) if goal.current_baseline else "Not measured"
        )

        return self.prompt_template.format(
            user_id=profile.user_id,
            age=profile.age,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            fitness_level=profile.fitness_level,
            training_history_years=profile.training_history_years,
            available_equipment=equipment_str,
            injuries_or_limitations=profile.injuries_or_limitations or "None",
            training_days_per_week=profile.training_days_per_week,
            preferred_training_days=preferred_days_str,
            goal_id=goal.goal_id,
            goal_type=goal.goal_type,
            target_event=goal.target_event or "General fitness",
            target_date=goal.target_date,
            days_until_goal=snapshot.days_until_goal,
            current_baseline=baseline_str,
            priority=goal.priority,
            timestamp=timestamp,
            plan_id=plan_id,
        )


# Global generator instance
high_level_plan_generator = HighLevelPlanGenerator()

