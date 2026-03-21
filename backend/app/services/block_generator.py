"""
Block generator service.

Generates training blocks with day slots based on high-level plan.
Block duration is configurable via settings.block_duration_days.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.plan import HighLevelPlan, ThreeWeekBlock
from app.models.snapshot import FitnessSnapshot
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "block_generation.txt"


def load_prompt_template() -> str:
    """Load the prompt template from file."""
    try:
        with open(PROMPT_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template not found: {PROMPT_PATH}")
        raise


class BlockGenerator:
    """Generates training blocks with configurable duration."""

    def __init__(self):
        """Initialize the generator."""
        self.prompt_template = load_prompt_template()

    def generate(
        self,
        snapshot: FitnessSnapshot,
        high_level_plan: HighLevelPlan,
        block_number: int = 1,
        start_date: Optional[str] = None,
    ) -> Optional[ThreeWeekBlock]:
        """
        Generate a training block.
        
        Args:
            snapshot: FitnessSnapshot with user context
            high_level_plan: The high-level plan to align with
            block_number: Which block number (1, 2, 3...)
            start_date: Start date for the block (defaults to today)
            
        Returns:
            ThreeWeekBlock or None if generation failed
        """
        # Determine start date
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.fromisoformat(snapshot.today_date)

        # Build the prompt
        prompt = self._build_prompt(snapshot, high_level_plan, block_number, start)
        system_prompt = self._build_system_prompt()

        # Generate and validate
        block, result = llm_client.generate_and_validate(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model_class=ThreeWeekBlock,
        )

        if block:
            logger.info(f"Generated block {block_number}: {block.start_date} to {block.end_date}")
            return block

        logger.error(f"Failed to generate block: {result.all_errors}")
        return None

    def _build_system_prompt(self) -> str:
        """Build the system prompt."""
        block_days = settings.block_duration_days
        return f"""You are an expert fitness coach creating detailed training schedules.

MOST IMPORTANT RULE: You MUST create EXACTLY {block_days} day_slots in your response. Not 14, not 7, not any other number - exactly {block_days}. This is mandatory and non-negotiable.

Your task is to create a {block_days}-day training block with appropriate workout types and rest days.

CRITICAL RULES:
1. Your day_slots array MUST contain EXACTLY {block_days} items
2. day_number must go from 1 to {block_days} sequentially
3. Always output valid JSON matching the specified schema
4. Dates must be sequential starting from start_date
5. Respect the user's preferred training days
6. Include minimum 1 rest day per 7-day period
7. Do not schedule high-intensity (RPE > 8) on consecutive days
8. Balance workout types appropriately for the training phase

Remember: EXACTLY {block_days} day_slots. Count them before responding."""

    def _build_prompt(
        self,
        snapshot: FitnessSnapshot,
        plan: HighLevelPlan,
        block_number: int,
        start_date: datetime,
    ) -> str:
        """Build the user prompt from snapshot and plan."""
        profile = snapshot.profile
        goal = snapshot.goal
        timestamp = datetime.now().isoformat()
        block_duration = settings.block_duration_days

        # Calculate end date
        end_date = start_date + timedelta(days=block_duration - 1)

        # Determine current phase based on block number
        current_phase = self._determine_phase(plan, block_number)

        # Format recent workouts summary
        recent_summary = self._format_recent_workouts(snapshot)

        # Format preferred days
        preferred_days_str = (
            ", ".join(profile.preferred_training_days)
            if profile.preferred_training_days
            else "Not specified"
        )

        return self.prompt_template.format(
            fitness_level=profile.fitness_level,
            training_days_per_week=profile.training_days_per_week,
            preferred_training_days=preferred_days_str,
            available_equipment=", ".join(profile.available_equipment),
            training_type_preference=getattr(profile, 'training_type_preference', None) or 'both',
            injuries_or_limitations=profile.injuries_or_limitations or "None",
            goal_type=goal.goal_type,
            target_event=goal.target_event or "General fitness",
            days_until_goal=snapshot.days_until_goal,
            overview_markdown=plan.overview_markdown,
            current_phase=current_phase,
            block_number=block_number,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            recent_workouts_summary=recent_summary,
            timestamp=timestamp,
            block_duration_days=block_duration,
        )

    def _determine_phase(self, plan: HighLevelPlan, block_number: int) -> str:
        """Determine which phase of the plan we're in based on block number."""
        # Each block is 3 weeks, so block 1 = weeks 1-3, block 2 = weeks 4-6, etc.
        start_week = (block_number - 1) * 3 + 1

        for phase in plan.phase_breakdown:
            weeks_str = phase.weeks
            if "-" in weeks_str:
                phase_start, phase_end = map(int, weeks_str.split("-"))
            else:
                phase_start = phase_end = int(weeks_str)

            if phase_start <= start_week <= phase_end:
                return f"{phase.focus}: {phase.description or ''}"

        # Default to first phase if not found
        if plan.phase_breakdown:
            first_phase = plan.phase_breakdown[0]
            return f"{first_phase.focus}: {first_phase.description or ''}"
        return "General Training"

    def _format_recent_workouts(self, snapshot: FitnessSnapshot) -> str:
        """Format recent workouts for the prompt."""
        if not snapshot.recent_workouts:
            return "No recent workout history"

        lines = []
        for workout in snapshot.recent_workouts[:7]:  # Last 7 workouts
            line = f"- {workout.date}: {workout.workout_type}, {workout.duration_min}min, RPE {workout.rpe_actual}"
            if workout.feedback:
                line += f" ({workout.feedback})"
            lines.append(line)

        return "\n".join(lines)


# Global generator instance
block_generator = BlockGenerator()

