"""
FastAPI routes for training coach API.

All endpoints return JSON - either data or error responses.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_authenticated_user, validate_user_id_matches_session
from app.api.rate_limiter import require_rate_limit
from app.config import settings
from app.models.onboarding import QuickOnboardRequest, QuickOnboardResponse
from app.models.plan import CompletePlan, ThreeWeekBlock
from app.models.responses import ClarifyingQuestions, ErrorResponse, RestDayResponse
from app.models.user import Session, UserFeedback, UserGoal, UserProfile
from app.models.workout import CustomWorkoutRequest, WorkoutLog, WorkoutPlan
from app.services.block_generator import block_generator
from app.services.workout_rescheduler import workout_rescheduler
from app.services.high_level_plan_generator import high_level_plan_generator
from app.services.quick_onboard import quick_onboard_service
from app.services.snapshot_builder import snapshot_builder
from app.services.workout_adjuster import workout_adjuster
from app.services.workout_generator import workout_generator
from app.storage.json_store import store

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Auth Endpoints ====================


@router.post("/auth/register")
async def register(name: str, email: str) -> dict:
    """
    Register a new user.
    
    Creates a new session and returns session data.
    """
    # Check if user already exists
    existing = store.find_user_by_email(email)
    if existing:
        return {
            "session_id": existing.session_id,
            "user_id": existing.user_id,
            "name": existing.name,
            "email": existing.email,
        }

    # Create new user
    session_id = f"sess_{uuid.uuid4().hex}"
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    session = Session(
        session_id=session_id,
        user_id=user_id,
        name=name,
        email=email,
        created_at=datetime.now().isoformat(),
        expires_at=(datetime.now() + timedelta(days=settings.session_duration_days)).isoformat(),
    )
    
    if not store.save_session(session):
        raise HTTPException(status_code=500, detail="Failed to create session")
    
    logger.info(f"Registered new user {user_id} with email {email}")
    return {
        "session_id": session_id,
        "user_id": user_id,
        "name": name,
        "email": email,
    }


@router.post("/auth/login")
async def login(email: str) -> dict:
    """
    Login an existing user by email.
    
    Returns existing session or creates a new one if user exists.
    """
    existing = store.find_user_by_email(email)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found. Please register first.")
    
    logger.info(f"User {existing.user_id} logged in")
    return {
        "session_id": existing.session_id,
        "user_id": existing.user_id,
        "name": existing.name,
        "email": existing.email,
    }


@router.post("/auth/logout")
async def logout(session_id: str) -> dict:
    """
    Logout a user by deleting their session.
    """
    store.delete_session(session_id)
    logger.info(f"Session {session_id} logged out")
    return {"success": True}


@router.get("/auth/me")
async def get_current_user(session_id: str) -> dict:
    """
    Get current user info from session.
    """
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "name": session.name,
        "email": session.email,
    }


# ==================== Profile Endpoints ====================


@router.post("/profile", response_model=UserProfile)
async def save_profile(
    profile: UserProfile,
    session: Session = Depends(get_authenticated_user),
) -> UserProfile:
    """
    Save user profile.

    Returns the saved profile.
    """
    validate_user_id_matches_session(profile.user_id, session)

    if not store.save_profile(profile):
        raise HTTPException(status_code=500, detail="Failed to save profile")

    logger.info(f"Saved profile for user {session.user_id}")
    return profile


@router.get("/profile/{user_id}", response_model=Union[UserProfile, ErrorResponse])
async def get_profile(
    user_id: str,
    session: Session = Depends(get_authenticated_user),
) -> Union[UserProfile, ErrorResponse]:
    """Get user profile by ID."""
    profile = store.get_profile(session.user_id)

    if not profile:
        return ErrorResponse(
            error_code="PROFILE_NOT_FOUND",
            message=f"Profile not found for user {session.user_id}",
        )

    return profile


# ==================== Goal Endpoints ====================


@router.post("/goal", response_model=UserGoal)
async def save_goal(
    goal: UserGoal,
    session: Session = Depends(get_authenticated_user),
) -> UserGoal:
    """
    Save user goal.

    Returns the saved goal.
    """
    validate_user_id_matches_session(goal.user_id, session)

    if not store.save_goal(goal):
        raise HTTPException(status_code=500, detail="Failed to save goal")

    logger.info(f"Saved goal {goal.goal_id} for user {session.user_id}")
    return goal


@router.get("/goal/{user_id}", response_model=Union[UserGoal, ErrorResponse])
async def get_active_goal(
    user_id: str,
    session: Session = Depends(get_authenticated_user),
) -> Union[UserGoal, ErrorResponse]:
    """Get the active goal for a user."""
    goal = store.get_active_goal(session.user_id)

    if not goal:
        return ErrorResponse(
            error_code="GOAL_NOT_FOUND",
            message=f"No active goal found for user {session.user_id}",
        )

    return goal


# ==================== Onboarding Endpoints ====================


@router.post(
    "/onboard/quick",
    response_model=Union[QuickOnboardResponse, ErrorResponse],
)
async def quick_onboard(
    request: QuickOnboardRequest,
    session: Session = Depends(require_rate_limit(settings.rate_limit_onboard_per_hour, 3600)),
) -> Union[QuickOnboardResponse, ErrorResponse]:
    """
    Quick onboarding for new users.

    Takes a free-text goal and training days per week, infers structured
    profile/goal via LLM, then generates a complete training plan.
    """
    validate_user_id_matches_session(request.user_id, session)

    # Idempotency: return existing plan if user already onboarded
    existing_plan = store.get_complete_plan(session.user_id)
    if existing_plan:
        profile = store.get_profile(session.user_id)
        goal = store.get_active_goal(session.user_id)
        if profile and goal:
            logger.info(f"Returning existing plan for already-onboarded user {session.user_id}")
            return QuickOnboardResponse(
                profile=profile, goal=goal, complete_plan=existing_plan
            )

    result = quick_onboard_service.onboard(request)

    if not result:
        return ErrorResponse(
            error_code="ONBOARDING_FAILED",
            message="Failed to complete onboarding. Please try again.",
            retry_allowed=True,
        )

    logger.info(f"Quick onboarding completed for user {session.user_id}")
    return result


# ==================== Plan Generation Endpoints ====================


@router.post(
    "/plan/generate",
    response_model=Union[CompletePlan, ClarifyingQuestions, ErrorResponse],
)
async def generate_plan(
    goal_id: str,
    session: Session = Depends(require_rate_limit(settings.rate_limit_plan_generate_per_hour, 3600)),
) -> Union[CompletePlan, ClarifyingQuestions, ErrorResponse]:
    """
    Generate a complete training plan.

    Creates:
    - 8-week high-level plan
    - Initial 21-day block with day slots
    - Detailed workouts for the first 7 days

    Returns CompletePlan or ClarifyingQuestions if info is missing.
    """
    user_id = session.user_id

    # Idempotency: return existing plan if already generated
    existing_plan = store.get_complete_plan(user_id)
    if existing_plan:
        logger.info(f"Returning existing plan for user {user_id}")
        return existing_plan

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

    # Detailed workouts are generated just-in-time when the user
    # requests their workout for a given day (GET /workout/today).

    # Create and save complete plan
    complete_plan = CompletePlan(
        high_level_plan=high_level_plan,
        current_block=first_block,
        blocks_generated=[1],
        detailed_workouts={},
    )

    store.save_complete_plan(user_id, complete_plan)

    logger.info(f"Generated complete plan for user {user_id}")
    return complete_plan


@router.get(
    "/plan/complete",
    response_model=Union[CompletePlan, ErrorResponse],
)
async def get_complete_plan(
    session: Session = Depends(get_authenticated_user),
) -> Union[CompletePlan, ErrorResponse]:
    """
    Get the complete training plan for a user.

    Returns the high-level plan and current block.
    """
    complete_plan = store.get_complete_plan(session.user_id)
    
    if not complete_plan:
        return ErrorResponse(
            error_code="NO_ACTIVE_PLAN",
            message="No training plan found. Please generate a plan first.",
        )
    
    return complete_plan


# ==================== Workout Endpoints ====================


@router.get(
    "/workout/today",
    response_model=Union[WorkoutPlan, RestDayResponse, ErrorResponse],
)
async def get_workout_today(
    session: Session = Depends(require_rate_limit(settings.rate_limit_workout_today_per_hour, 3600)),
) -> Union[WorkoutPlan, RestDayResponse, ErrorResponse]:
    """
    Get today's workout.

    Returns:
    - WorkoutPlan if there's a workout scheduled (with is_completed status)
    - RestDayResponse if today is a rest day
    - ErrorResponse if no plan exists or generation fails
    """
    user_id = session.user_id
    today = datetime.now().strftime("%Y-%m-%d")

    # Get current block to check slot status
    block = store.get_current_block(user_id, today)
    
    # Find today's slot if block exists
    today_slot = None
    if block:
        for slot in block.day_slots:
            if slot.date == today:
                today_slot = slot
                break

    # Check for existing workout
    existing_workout = store.get_workout_for_date(user_id, today)
    if existing_workout:
        # Check if workout has been completed:
        # 1. Check slot status (for scheduled workouts)
        # 2. Check if there's a workout log with this workout_id (for custom workouts)
        is_completed = False
        
        if today_slot and today_slot.status == "completed":
            is_completed = True
        else:
            # Check workout logs for this workout_id
            today_logs = store.get_workout_logs_in_range(user_id, today, today)
            for log in today_logs:
                if log.workout_id == existing_workout.workout_id:
                    is_completed = True
                    break
        
        existing_workout.is_completed = is_completed
        
        # Find next workout date if completed
        if is_completed and block:
            for slot in block.day_slots:
                if slot.date > today and not slot.is_rest_day:
                    existing_workout.next_workout_date = slot.date
                    break
        
        return existing_workout

    if not block:
        return ErrorResponse(
            error_code="NO_ACTIVE_PLAN",
            message="No active training plan found. Please generate a plan first.",
        )

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

    # New workout is not completed
    workout.is_completed = False
    return workout


@router.get(
    "/workout/by-date",
    response_model=Union[WorkoutPlan, RestDayResponse, dict, ErrorResponse],
)
async def get_workout_by_date(
    date: str,
    session: Session = Depends(get_authenticated_user),
) -> Union[WorkoutPlan, RestDayResponse, dict, ErrorResponse]:
    """
    Get a workout for a specific date (read-only, no JIT generation).

    Returns:
    - WorkoutPlan if a detailed workout exists for that date
    - RestDayResponse if the date is a rest day
    - {"status": "not_generated"} if no workout has been generated yet
    - ErrorResponse if no plan exists or date is out of range
    """
    user_id = session.user_id
    block = store.get_current_block(user_id, date)
    if not block:
        return ErrorResponse(
            error_code="NO_ACTIVE_PLAN",
            message="No active training plan found.",
        )

    day_slot = None
    for slot in block.day_slots:
        if slot.date == date:
            day_slot = slot
            break

    if not day_slot:
        return ErrorResponse(
            error_code="DATE_OUT_OF_RANGE",
            message=f"Date {date} is not within the current training block",
        )

    if day_slot.is_rest_day:
        next_workout_date = None
        for slot in block.day_slots:
            if slot.date > date and not slot.is_rest_day:
                next_workout_date = slot.date
                break
        return RestDayResponse(date=date, next_workout_date=next_workout_date)

    existing_workout = store.get_workout_for_date(user_id, date)
    if existing_workout:
        # Check completion status
        is_completed = day_slot.status == "completed"
        if not is_completed:
            logs = store.get_workout_logs_in_range(user_id, date, date)
            for log in logs:
                if log.workout_id == existing_workout.workout_id:
                    is_completed = True
                    break
        existing_workout.is_completed = is_completed
        return existing_workout

    return {"status": "not_generated", "message": "This workout hasn't been generated yet."}


@router.post(
    "/workout/feedback",
    response_model=Union[WorkoutPlan, RestDayResponse, ErrorResponse],
)
async def submit_feedback(
    feedback: UserFeedback,
    session: Session = Depends(require_rate_limit(settings.rate_limit_feedback_per_hour, 3600)),
) -> Union[WorkoutPlan, RestDayResponse, ErrorResponse]:
    """
    Submit pre-workout feedback and get adjusted workout.

    Applies ADJUSTMENT_RULES based on feedback status.
    Returns adjusted WorkoutPlan.
    """
    validate_user_id_matches_session(feedback.user_id, session)
    user_id = session.user_id

    # Save feedback
    store.save_feedback(feedback)

    today = datetime.now().strftime("%Y-%m-%d")

    # Get today's workout
    workout = store.get_workout_for_date(user_id, today)

    if not workout:
        # Try to generate it first
        result = await get_workout_today(session=session)
        if isinstance(result, ErrorResponse):
            return result
        if isinstance(result, RestDayResponse):
            return result
        workout = result

    # Apply adjustments if needed
    if feedback.status != "great":
        adjusted_workout = workout_adjuster.adjust(workout, feedback)
        # Save adjusted workout (overwrites original)
        store.save_workout(user_id, adjusted_workout)
        return adjusted_workout

    return workout


@router.post("/workout/log", response_model=WorkoutLog)
async def log_workout(
    log: WorkoutLog,
    session: Session = Depends(get_authenticated_user),
) -> WorkoutLog:
    """
    Log a completed workout.

    Saves the workout log with all exercise details and feedback.
    """
    validate_user_id_matches_session(log.user_id, session)
    user_id = session.user_id

    # Generate log ID if not provided
    if not log.log_id:
        log.log_id = f"log_{uuid.uuid4().hex[:8]}"

    if not store.save_workout_log(log):
        raise HTTPException(status_code=500, detail="Failed to save workout log")

    logger.info(f"Saved workout log {log.log_id} for user {user_id}")

    # Update day slot status if workout_id matches
    block = store.get_current_block(user_id, log.date[:10])
    if block:
        for slot in block.day_slots:
            if slot.workout_id == log.workout_id:
                slot.status = "completed" if log.completed else "skipped"
                store.save_block(user_id, block)
                break

    return log


@router.post(
    "/workout/swap-to-today",
    response_model=Union[WorkoutPlan, ErrorResponse],
)
async def swap_workout_to_today(
    session: Session = Depends(require_rate_limit(settings.rate_limit_swap_per_hour, 3600)),
) -> Union[WorkoutPlan, ErrorResponse]:
    """
    Swap the next scheduled workout with today's rest day.

    This moves the next workout to today and makes that day a rest day instead.
    """
    user_id = session.user_id
    today = datetime.now().strftime("%Y-%m-%d")

    # Get current block
    block = store.get_current_block(user_id, today)
    if not block:
        return ErrorResponse(
            error_code="NO_ACTIVE_PLAN",
            message="No active training plan found",
        )

    # Find today's slot and verify it's a rest day
    today_slot = None
    today_idx = -1
    for i, slot in enumerate(block.day_slots):
        if slot.date == today:
            today_slot = slot
            today_idx = i
            break

    if not today_slot:
        return ErrorResponse(
            error_code="DATE_OUT_OF_RANGE",
            message=f"Today ({today}) is not within the current training block",
        )

    if not today_slot.is_rest_day:
        return ErrorResponse(
            error_code="NOT_REST_DAY",
            message="Today is not a rest day",
        )

    # Find next workout day
    next_workout_slot = None
    next_workout_idx = -1
    for i in range(today_idx + 1, len(block.day_slots)):
        slot = block.day_slots[i]
        if not slot.is_rest_day:
            next_workout_slot = slot
            next_workout_idx = i
            break

    if not next_workout_slot:
        return ErrorResponse(
            error_code="NO_UPCOMING_WORKOUT",
            message="No upcoming workout found to swap",
        )

    # Swap the slots
    # Store next workout's data
    workout_data = {
        "workout_type": next_workout_slot.workout_type,
        "target_duration_min": next_workout_slot.target_duration_min,
        "target_distance_km": next_workout_slot.target_distance_km,
        "intensity_target": next_workout_slot.intensity_target,
        "workout_id": next_workout_slot.workout_id,
    }

    # Make today a workout day
    today_slot.is_rest_day = False
    today_slot.workout_type = workout_data["workout_type"]
    today_slot.target_duration_min = workout_data["target_duration_min"]
    today_slot.target_distance_km = workout_data["target_distance_km"]
    today_slot.intensity_target = workout_data["intensity_target"]
    today_slot.status = "planned"
    today_slot.workout_id = None  # Will generate fresh

    # Make the next workout day a rest day
    next_workout_slot.is_rest_day = True
    next_workout_slot.workout_type = None
    next_workout_slot.target_duration_min = None
    next_workout_slot.target_distance_km = None
    next_workout_slot.intensity_target = None
    next_workout_slot.workout_id = None
    next_workout_slot.status = "planned"

    # Save the updated block
    store.save_block(user_id, block)

    logger.info(f"Swapped workout from {next_workout_slot.date} to {today} for user {user_id}")

    # Now generate and return today's workout
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
    today_slot.workout_id = workout.workout_id
    store.save_block(user_id, block)

    return workout


@router.post(
    "/workout/custom",
    response_model=WorkoutPlan,
)
async def save_custom_workout(
    workout_request: CustomWorkoutRequest,
    session: Session = Depends(get_authenticated_user),
) -> WorkoutPlan:
    """
    Save a user-created custom workout.

    Links the workout to the corresponding DaySlot in the training block
    so it appears in the schedule view.
    """
    validate_user_id_matches_session(workout_request.user_id, session)
    user_id = session.user_id

    today = datetime.now().strftime("%Y-%m-%d")
    target_date = workout_request.scheduled_for_date or today
    workout_id = f"custom_{uuid.uuid4().hex[:8]}"

    # Create the workout plan
    workout = WorkoutPlan(
        workout_id=workout_id,
        scheduled_for_date=target_date,
        title=workout_request.title,
        workout_type=workout_request.workout_type,
        estimated_duration_min=workout_request.estimated_duration_min,
        intensity_target=workout_request.intensity_target,
        sections=workout_request.sections,
        rationale=["Custom workout created by user"],
    )

    # Save the workout
    store.save_workout(user_id, workout)

    # Link to day slot if block exists
    block = store.get_current_block(user_id, target_date)
    if block:
        for slot in block.day_slots:
            if slot.date == target_date:
                slot.workout_id = workout_id
                slot.workout_type = workout_request.workout_type
                slot.is_rest_day = False
                slot.status = "planned"
                store.save_block(user_id, block)

                # Also update the complete plan so /plan/complete returns updated data
                complete_plan = store.get_complete_plan(user_id)
                if complete_plan:
                    complete_plan.current_block = block
                    store.save_complete_plan(user_id, complete_plan)
                break

    logger.info(f"Saved custom workout {workout_id} for user {user_id} on {target_date}")

    return workout


@router.post(
    "/workout/move",
    response_model=Union[dict, ErrorResponse],
)
async def move_workout(
    from_date: str,
    to_date: str,
    session: Session = Depends(get_authenticated_user),
) -> Union[dict, ErrorResponse]:
    """
    Move a workout from one date to another.

    If the target date has a workout, the two workouts are swapped.
    If the target date is a rest day, the workout is moved there and the source becomes a rest day.
    """
    user_id = session.user_id
    if from_date == to_date:
        return ErrorResponse(
            error_code="SAME_DATE",
            message="Source and target dates are the same",
        )

    # Get current block
    block = store.get_current_block(user_id, from_date)
    if not block:
        return ErrorResponse(
            error_code="NO_ACTIVE_PLAN",
            message="No active training block found",
        )

    # Verify target date is also in the block
    if not (block.start_date <= to_date <= block.end_date):
        return ErrorResponse(
            error_code="DATE_OUT_OF_RANGE",
            message=f"Target date {to_date} is not within the current training block",
        )

    # Find both slots
    from_slot = None
    to_slot = None
    for slot in block.day_slots:
        if slot.date == from_date:
            from_slot = slot
        elif slot.date == to_date:
            to_slot = slot

    if not from_slot:
        return ErrorResponse(
            error_code="SOURCE_NOT_FOUND",
            message=f"Could not find slot for source date {from_date}",
        )
    if not to_slot:
        return ErrorResponse(
            error_code="TARGET_NOT_FOUND",
            message=f"Could not find slot for target date {to_date}",
        )

    if from_slot.is_rest_day:
        return ErrorResponse(
            error_code="NO_WORKOUT_TO_MOVE",
            message="Source date is a rest day with no workout to move",
        )

    # Store from_slot data
    from_data = {
        "workout_type": from_slot.workout_type,
        "target_duration_min": from_slot.target_duration_min,
        "target_distance_km": from_slot.target_distance_km,
        "intensity_target": from_slot.intensity_target,
        "workout_id": from_slot.workout_id,
        "is_rest_day": from_slot.is_rest_day,
        "status": from_slot.status,
    }

    # Store to_slot data
    to_data = {
        "workout_type": to_slot.workout_type,
        "target_duration_min": to_slot.target_duration_min,
        "target_distance_km": to_slot.target_distance_km,
        "intensity_target": to_slot.intensity_target,
        "workout_id": to_slot.workout_id,
        "is_rest_day": to_slot.is_rest_day,
        "status": to_slot.status,
    }

    # Move from_slot data to to_slot
    to_slot.workout_type = from_data["workout_type"]
    to_slot.target_duration_min = from_data["target_duration_min"]
    to_slot.target_distance_km = from_data["target_distance_km"]
    to_slot.intensity_target = from_data["intensity_target"]
    to_slot.workout_id = from_data["workout_id"]
    to_slot.is_rest_day = False
    to_slot.status = "planned"

    # Move to_slot data to from_slot (swap) or make it a rest day
    if to_data["is_rest_day"]:
        # Target was rest day, source becomes rest day
        from_slot.workout_type = None
        from_slot.target_duration_min = None
        from_slot.target_distance_km = None
        from_slot.intensity_target = None
        from_slot.workout_id = None
        from_slot.is_rest_day = True
        from_slot.status = "planned"
    else:
        # Swap: target had a workout, move it to source
        from_slot.workout_type = to_data["workout_type"]
        from_slot.target_duration_min = to_data["target_duration_min"]
        from_slot.target_distance_km = to_data["target_distance_km"]
        from_slot.intensity_target = to_data["intensity_target"]
        from_slot.workout_id = to_data["workout_id"]
        from_slot.is_rest_day = False
        from_slot.status = "planned"

    # Update scheduled_for_date on affected WorkoutPlan objects
    if from_data["workout_id"]:
        from_workout = store.get_workout(user_id, from_data["workout_id"])
        if from_workout:
            from_workout.scheduled_for_date = to_date
            store.save_workout(user_id, from_workout)

    if not to_data["is_rest_day"] and to_data["workout_id"]:
        to_workout = store.get_workout(user_id, to_data["workout_id"])
        if to_workout:
            to_workout.scheduled_for_date = from_date
            store.save_workout(user_id, to_workout)

    # Save the updated block
    store.save_block(user_id, block)

    # Also update the complete plan so /plan/complete returns updated data
    complete_plan = store.get_complete_plan(user_id)
    if complete_plan:
        complete_plan.current_block = block
        store.save_complete_plan(user_id, complete_plan)

    logger.info(f"Moved workout from {from_date} to {to_date} for user {user_id}")

    return {
        "success": True,
        "from_date": from_date,
        "to_date": to_date,
        "swapped": not to_data["is_rest_day"],
    }


# ==================== Block Management Endpoints ====================


@router.post(
    "/block/generate-next",
    response_model=Union[ThreeWeekBlock, ErrorResponse],
)
async def generate_next_block(
    session: Session = Depends(require_rate_limit(settings.rate_limit_block_generate_per_day, 86400)),
) -> Union[ThreeWeekBlock, ErrorResponse]:
    """
    Generate the next 21-day training block.

    Called when approaching end of current block (day ~18-19).
    """
    user_id = session.user_id

    # Get current plan
    complete_plan = store.get_complete_plan(user_id)
    if not complete_plan:
        return ErrorResponse(
            error_code="NO_ACTIVE_PLAN",
            message="No active training plan found",
        )

    # Guard: max total blocks per user
    if len(complete_plan.blocks_generated) >= settings.max_blocks_per_user:
        return ErrorResponse(
            error_code="MAX_BLOCKS_REACHED",
            message=f"Maximum of {settings.max_blocks_per_user} training blocks reached.",
        )

    # Guard: don't generate blocks too far ahead
    latest_block = store.get_latest_block(user_id)
    if latest_block:
        days_ahead = (datetime.fromisoformat(latest_block.end_date) - datetime.now()).days
        if days_ahead > settings.max_days_ahead_for_blocks:
            return ErrorResponse(
                error_code="BLOCKS_TOO_FAR_AHEAD",
                message="You already have enough upcoming training blocks generated.",
            )

    # Determine next block number
    current_block_num = max(complete_plan.blocks_generated)
    next_block_num = current_block_num + 1

    # Calculate start date (day after current block ends)
    current_block = complete_plan.current_block

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


# ==================== Exercises Endpoints ====================


# Load exercises from JSON file once at startup
_exercises_cache: Optional[List[dict]] = None


def _load_exercises() -> List[dict]:
    """Load exercises from the JSON file."""
    global _exercises_cache
    if _exercises_cache is None:
        exercises_path = Path(__file__).parent.parent.parent / "exercises.json"
        if exercises_path.exists():
            with open(exercises_path, "r") as f:
                data = json.load(f)
                _exercises_cache = data.get("data", {}).get("exercises", [])
        else:
            _exercises_cache = []
            logger.warning(f"Exercises file not found at {exercises_path}")
    return _exercises_cache


@router.get("/exercises")
async def get_exercises(
    search: Optional[str] = None,
    exercise_type: Optional[str] = None,
    body_part: Optional[str] = None,
) -> dict:
    """
    Get exercises from the database with optional filtering.
    
    Args:
        search: Search term to filter by name
        exercise_type: Filter by exercise type (strength, cardio, mobility, etc.)
        body_part: Filter by body part (legs, back, chest, etc.)
    
    Returns:
        List of exercises matching the filters
    """
    exercises = _load_exercises()
    
    # Apply filters
    filtered = exercises
    
    if search:
        search_lower = search.lower()
        filtered = [
            ex for ex in filtered
            if search_lower in ex.get("name", "").lower()
            or search_lower in (ex.get("alternativeName") or "").lower()
        ]
    
    if exercise_type:
        filtered = [
            ex for ex in filtered
            if ex.get("exerciseType", "").lower() == exercise_type.lower()
        ]
    
    if body_part:
        filtered = [
            ex for ex in filtered
            if ex.get("bodyPart", "").lower() == body_part.lower()
        ]
    
    return {
        "exercises": filtered,
        "total": len(filtered),
    }


# ==================== Health Check ====================


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

