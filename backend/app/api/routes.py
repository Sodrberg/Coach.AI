"""
FastAPI routes for training coach API.

All endpoints return JSON - either data or error responses.
"""

import logging
import uuid
from datetime import datetime
from typing import Union

from fastapi import APIRouter, HTTPException

from app.models.plan import CompletePlan, ThreeWeekBlock
from app.models.responses import ClarifyingQuestions, ErrorResponse, RestDayResponse
from app.models.user import UserFeedback, UserGoal, UserProfile
from app.models.workout import WorkoutLog, WorkoutPlan
from app.services.block_generator import block_generator
from app.services.high_level_plan_generator import high_level_plan_generator
from app.services.snapshot_builder import snapshot_builder
from app.services.workout_adjuster import workout_adjuster
from app.services.workout_generator import workout_generator
from app.storage.json_store import store

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Profile Endpoints ====================


@router.post("/profile", response_model=UserProfile)
async def save_profile(profile: UserProfile) -> UserProfile:
    """
    Save user profile.
    
    Returns the saved profile.
    """
    if not store.save_profile(profile):
        raise HTTPException(status_code=500, detail="Failed to save profile")

    logger.info(f"Saved profile for user {profile.user_id}")
    return profile


@router.get("/profile/{user_id}", response_model=Union[UserProfile, ErrorResponse])
async def get_profile(user_id: str) -> Union[UserProfile, ErrorResponse]:
    """Get user profile by ID."""
    profile = store.get_profile(user_id)

    if not profile:
        return ErrorResponse(
            error_code="PROFILE_NOT_FOUND",
            message=f"Profile not found for user {user_id}",
        )

    return profile


# ==================== Goal Endpoints ====================


@router.post("/goal", response_model=UserGoal)
async def save_goal(goal: UserGoal) -> UserGoal:
    """
    Save user goal.
    
    Returns the saved goal.
    """
    if not store.save_goal(goal):
        raise HTTPException(status_code=500, detail="Failed to save goal")

    logger.info(f"Saved goal {goal.goal_id} for user {goal.user_id}")
    return goal


@router.get("/goal/{user_id}", response_model=Union[UserGoal, ErrorResponse])
async def get_active_goal(user_id: str) -> Union[UserGoal, ErrorResponse]:
    """Get the active goal for a user."""
    goal = store.get_active_goal(user_id)

    if not goal:
        return ErrorResponse(
            error_code="GOAL_NOT_FOUND",
            message=f"No active goal found for user {user_id}",
        )

    return goal


# ==================== Plan Generation Endpoints ====================


@router.post(
    "/plan/generate",
    response_model=Union[CompletePlan, ClarifyingQuestions, ErrorResponse],
)
async def generate_plan(
    user_id: str,
    goal_id: str,
) -> Union[CompletePlan, ClarifyingQuestions, ErrorResponse]:
    """
    Generate a complete training plan.
    
    Creates:
    - 8-week high-level plan
    - Initial 21-day block with day slots
    - Detailed workouts for the first 7 days
    
    Returns CompletePlan or ClarifyingQuestions if info is missing.
    """
    # Build snapshot
    snapshot = snapshot_builder.build_snapshot(user_id)

    if not snapshot:
        return ClarifyingQuestions(
            questions=[
                "What is your current fitness level?",
                "What is your training goal?",
            ],
            missing_fields=["profile", "goal"],
            reason="User profile and goal are required to generate a plan",
        )

    # Check if goal matches
    if snapshot.goal.goal_id != goal_id:
        return ErrorResponse(
            error_code="GOAL_MISMATCH",
            message=f"Goal {goal_id} does not match user's active goal",
        )

    # Generate high-level plan
    high_level_plan = high_level_plan_generator.generate(snapshot)

    if not high_level_plan:
        return ErrorResponse(
            error_code="PLAN_GENERATION_FAILED",
            message="Failed to generate high-level plan",
            retry_allowed=True,
        )

    # Save high-level plan
    store.save_high_level_plan(high_level_plan)

    # Generate first 21-day block
    first_block = block_generator.generate(
        snapshot=snapshot,
        high_level_plan=high_level_plan,
        block_number=1,
    )

    if not first_block:
        return ErrorResponse(
            error_code="BLOCK_GENERATION_FAILED",
            message="Failed to generate training block",
            retry_allowed=True,
        )

    # Save block
    store.save_block(user_id, first_block)

    # Generate detailed workouts for first 7 days
    detailed_workouts = {}
    for slot in first_block.day_slots[:7]:
        if not slot.is_rest_day:
            workout = workout_generator.generate(snapshot, slot)
            if workout:
                store.save_workout(user_id, workout)
                detailed_workouts[slot.date] = workout.workout_id
                # Update slot with workout_id
                slot.workout_id = workout.workout_id

    # Save updated block with workout IDs
    store.save_block(user_id, first_block)

    # Create and save complete plan
    complete_plan = CompletePlan(
        high_level_plan=high_level_plan,
        current_block=first_block,
        blocks_generated=[1],
        detailed_workouts=detailed_workouts,
    )

    store.save_complete_plan(user_id, complete_plan)

    logger.info(f"Generated complete plan for user {user_id}")
    return complete_plan


# ==================== Workout Endpoints ====================


@router.get(
    "/workout/today",
    response_model=Union[WorkoutPlan, RestDayResponse, ErrorResponse],
)
async def get_workout_today(
    user_id: str,
) -> Union[WorkoutPlan, RestDayResponse, ErrorResponse]:
    """
    Get today's workout.
    
    Returns:
    - WorkoutPlan if there's a workout scheduled
    - RestDayResponse if today is a rest day
    - ErrorResponse if no plan exists or generation fails
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # Check for existing workout
    existing_workout = store.get_workout_for_date(user_id, today)
    if existing_workout:
        return existing_workout

    # Get current block
    block = store.get_current_block(user_id, today)
    if not block:
        return ErrorResponse(
            error_code="NO_ACTIVE_PLAN",
            message="No active training plan found. Please generate a plan first.",
        )

    # Find today's slot
    today_slot = None
    for slot in block.day_slots:
        if slot.date == today:
            today_slot = slot
            break

    if not today_slot:
        return ErrorResponse(
            error_code="DATE_OUT_OF_RANGE",
            message=f"Today ({today}) is not within the current training block",
        )

    # Check if rest day
    if today_slot.is_rest_day:
        # Find next workout date
        next_workout_date = None
        for slot in block.day_slots:
            if slot.date > today and not slot.is_rest_day:
                next_workout_date = slot.date
                break

        return RestDayResponse(
            date=today,
            next_workout_date=next_workout_date,
        )

    # Generate workout just-in-time
    snapshot = snapshot_builder.build_snapshot(user_id, today)
    if not snapshot:
        return ErrorResponse(
            error_code="SNAPSHOT_FAILED",
            message="Failed to build user context",
        )

    workout = workout_generator.generate(snapshot, today_slot)
    if not workout:
        return ErrorResponse(
            error_code="WORKOUT_GENERATION_FAILED",
            message="Failed to generate workout",
            retry_allowed=True,
        )

    # Save and return
    store.save_workout(user_id, workout)

    # Update slot with workout_id
    today_slot.workout_id = workout.workout_id
    store.save_block(user_id, block)

    return workout


@router.post(
    "/workout/feedback",
    response_model=Union[WorkoutPlan, RestDayResponse, ErrorResponse],
)
async def submit_feedback(
    feedback: UserFeedback,
) -> Union[WorkoutPlan, RestDayResponse, ErrorResponse]:
    """
    Submit pre-workout feedback and get adjusted workout.
    
    Applies ADJUSTMENT_RULES based on feedback status.
    Returns adjusted WorkoutPlan.
    """
    # Save feedback
    store.save_feedback(feedback)

    today = datetime.now().strftime("%Y-%m-%d")

    # Get today's workout
    workout = store.get_workout_for_date(feedback.user_id, today)

    if not workout:
        # Try to generate it first
        result = await get_workout_today(feedback.user_id)
        if isinstance(result, ErrorResponse):
            return result
        if isinstance(result, RestDayResponse):
            return result
        workout = result

    # Apply adjustments if needed
    if feedback.status != "great":
        adjusted_workout = workout_adjuster.adjust(workout, feedback)
        # Save adjusted workout (overwrites original)
        store.save_workout(feedback.user_id, adjusted_workout)
        return adjusted_workout

    return workout


@router.post("/workout/log", response_model=WorkoutLog)
async def log_workout(log: WorkoutLog) -> WorkoutLog:
    """
    Log a completed workout.
    
    Saves the workout log with all exercise details and feedback.
    """
    # Generate log ID if not provided
    if not log.log_id:
        log.log_id = f"log_{uuid.uuid4().hex[:8]}"

    if not store.save_workout_log(log):
        raise HTTPException(status_code=500, detail="Failed to save workout log")

    logger.info(f"Saved workout log {log.log_id} for user {log.user_id}")

    # Update day slot status if workout_id matches
    block = store.get_current_block(log.user_id, log.date[:10])
    if block:
        for slot in block.day_slots:
            if slot.workout_id == log.workout_id:
                slot.status = "completed" if log.completed else "skipped"
                store.save_block(log.user_id, block)
                break

    return log


# ==================== Block Management Endpoints ====================


@router.post(
    "/block/generate-next",
    response_model=Union[ThreeWeekBlock, ErrorResponse],
)
async def generate_next_block(
    user_id: str,
) -> Union[ThreeWeekBlock, ErrorResponse]:
    """
    Generate the next 21-day training block.
    
    Called when approaching end of current block (day ~18-19).
    """
    # Get current plan
    complete_plan = store.get_complete_plan(user_id)
    if not complete_plan:
        return ErrorResponse(
            error_code="NO_ACTIVE_PLAN",
            message="No active training plan found",
        )

    # Determine next block number
    current_block_num = max(complete_plan.blocks_generated)
    next_block_num = current_block_num + 1

    # Calculate start date (day after current block ends)
    current_block = complete_plan.current_block
    from datetime import timedelta

    end_date = datetime.fromisoformat(current_block.end_date)
    next_start = end_date + timedelta(days=1)

    # Build snapshot
    snapshot = snapshot_builder.build_snapshot(user_id)
    if not snapshot:
        return ErrorResponse(
            error_code="SNAPSHOT_FAILED",
            message="Failed to build user context",
        )

    # Generate next block
    next_block = block_generator.generate(
        snapshot=snapshot,
        high_level_plan=complete_plan.high_level_plan,
        block_number=next_block_num,
        start_date=next_start.strftime("%Y-%m-%d"),
    )

    if not next_block:
        return ErrorResponse(
            error_code="BLOCK_GENERATION_FAILED",
            message="Failed to generate next block",
            retry_allowed=True,
        )

    # Save block
    store.save_block(user_id, next_block)

    # Generate workouts for first 7 days of new block
    for slot in next_block.day_slots[:7]:
        if not slot.is_rest_day:
            workout = workout_generator.generate(snapshot, slot)
            if workout:
                store.save_workout(user_id, workout)
                slot.workout_id = workout.workout_id

    # Update and save complete plan
    complete_plan.current_block = next_block
    complete_plan.blocks_generated.append(next_block_num)
    store.save_complete_plan(user_id, complete_plan)

    logger.info(f"Generated block {next_block_num} for user {user_id}")
    return next_block


# ==================== Health Check ====================


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

