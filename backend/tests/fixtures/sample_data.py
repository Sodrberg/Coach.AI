"""
Sample data fixtures for testing.

Provides mock data for tests without hitting external APIs.
"""

from datetime import datetime, timedelta

# Sample user profile
SAMPLE_USER_PROFILE = {
    "user_id": "test_user_123",
    "age": 35,
    "weight_kg": 80.0,
    "height_cm": 180,
    "gender": "male",
    "fitness_level": "intermediate",
    "training_history_years": 5,
    "available_equipment": ["barbell", "dumbbells", "pull_up_bar", "gym"],
    "injuries_or_limitations": None,
    "training_days_per_week": 4,
    "preferred_training_days": ["monday", "tuesday", "thursday", "friday"],
}

# Sample user goal
SAMPLE_USER_GOAL = {
    "goal_id": "goal_123",
    "user_id": "test_user_123",
    "goal_type": "race",
    "target_event": "Vasaloppet 90km",
    "target_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
    "current_baseline": {"5k_time_min": 25, "squat_1rm_kg": 100},
    "priority": "performance",
}

# Sample high-level plan
SAMPLE_HIGH_LEVEL_PLAN = {
    "plan_id": "plan_test_123",
    "goal_id": "goal_123",
    "user_id": "test_user_123",
    "duration_weeks": 8,
    "overview_markdown": """# 8-Week Vasaloppet Preparation Plan

## Overview
This plan builds your aerobic base while maintaining strength for the 90km ski race.

## Weekly Structure
- 4 training days per week
- Focus on endurance with 2 strength sessions
- Progressive overload with recovery weeks

## Key Milestones
- Week 3: First long session (2+ hours)
- Week 5: Test 10km time
- Week 7: Pre-race taper begins
""",
    "phase_breakdown": [
        {"weeks": "1-3", "focus": "Base Building", "description": "Build aerobic foundation"},
        {"weeks": "4-6", "focus": "Build Phase", "description": "Increase intensity and volume"},
        {"weeks": "7-8", "focus": "Taper", "description": "Reduce volume, maintain intensity"},
    ],
    "created_at": datetime.now().isoformat(),
}

# Sample day slots for a 21-day block
def generate_sample_day_slots(start_date: str):
    """Generate sample day slots for testing."""
    start = datetime.fromisoformat(start_date)
    slots = []

    workout_pattern = [
        # Week 1
        ("endurance", 60, "RPE_5_6"),
        ("strength", 45, "RPE_7_8"),
        None,  # Rest
        ("intervals", 45, "RPE_8_9"),
        ("recovery", 30, "RPE_4_5"),
        ("endurance", 90, "RPE_5_6"),
        None,  # Rest
        # Week 2
        ("endurance", 60, "RPE_5_6"),
        ("strength", 50, "RPE_7_8"),
        None,
        ("intervals", 50, "RPE_8_9"),
        ("recovery", 30, "RPE_4_5"),
        ("endurance", 100, "RPE_5_6"),
        None,
        # Week 3
        ("endurance", 45, "RPE_5_6"),
        ("strength", 40, "RPE_6_7"),
        None,
        ("recovery", 30, "RPE_4_5"),
        ("endurance", 60, "RPE_5_6"),
        None,
        None,
    ]

    for i, pattern in enumerate(workout_pattern):
        date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        if pattern is None:
            slots.append({
                "day_number": i + 1,
                "date": date,
                "workout_type": None,
                "target_duration_min": None,
                "target_distance_km": None,
                "intensity_target": None,
                "is_rest_day": True,
                "status": "planned",
                "workout_id": None,
            })
        else:
            workout_type, duration, intensity = pattern
            slots.append({
                "day_number": i + 1,
                "date": date,
                "workout_type": workout_type,
                "target_duration_min": duration,
                "target_distance_km": None,
                "intensity_target": intensity,
                "is_rest_day": False,
                "status": "planned",
                "workout_id": None,
            })

    return slots


# Sample workout plan
SAMPLE_WORKOUT_PLAN = {
    "workout_id": "workout_test_123",
    "scheduled_for_date": datetime.now().strftime("%Y-%m-%d"),
    "title": "Strength: Upper Body",
    "workout_type": "strength",
    "estimated_duration_min": 45,
    "intensity_target": "RPE_7_8",
    "sections": [
        {
            "name": "warmup",
            "items": [
                {
                    "kind": "mobility",
                    "exercise_id": None,
                    "name": "Arm Circles",
                    "sets": 1,
                    "reps": 10,
                    "weight_kg": None,
                    "duration_min": None,
                    "distance_km": None,
                    "rest_sec": 0,
                    "cues": "Start small, gradually increase range",
                },
                {
                    "kind": "mobility",
                    "exercise_id": None,
                    "name": "Cat-Cow Stretch",
                    "sets": 1,
                    "reps": 10,
                    "weight_kg": None,
                    "duration_min": None,
                    "distance_km": None,
                    "rest_sec": 0,
                    "cues": "Flow smoothly between positions",
                },
            ],
        },
        {
            "name": "main",
            "items": [
                {
                    "kind": "strength",
                    "exercise_id": None,
                    "name": "Bench Press",
                    "sets": 4,
                    "reps": 8,
                    "weight_kg": 60.0,
                    "duration_min": None,
                    "distance_km": None,
                    "rest_sec": 90,
                    "cues": "Control the descent, drive through heels",
                },
                {
                    "kind": "strength",
                    "exercise_id": None,
                    "name": "Barbell Row",
                    "sets": 4,
                    "reps": 8,
                    "weight_kg": 50.0,
                    "duration_min": None,
                    "distance_km": None,
                    "rest_sec": 90,
                    "cues": "Keep back flat, pull to lower chest",
                },
                {
                    "kind": "strength",
                    "exercise_id": None,
                    "name": "Overhead Press",
                    "sets": 3,
                    "reps": 10,
                    "weight_kg": 30.0,
                    "duration_min": None,
                    "distance_km": None,
                    "rest_sec": 60,
                    "cues": "Brace core, full lockout at top",
                },
            ],
        },
        {
            "name": "cooldown",
            "items": [
                {
                    "kind": "recovery",
                    "exercise_id": None,
                    "name": "Shoulder Stretch",
                    "sets": 1,
                    "reps": None,
                    "weight_kg": None,
                    "duration_min": 2,
                    "distance_km": None,
                    "rest_sec": 0,
                    "cues": "Hold each position for 30 seconds",
                },
            ],
        },
    ],
    "rationale": [
        "Upper body strength to support ski poling",
        "Compound movements for functional strength",
    ],
    "questions": None,
}

# Sample workout log
SAMPLE_WORKOUT_LOG = {
    "log_id": "log_test_123",
    "user_id": "test_user_123",
    "workout_id": "workout_test_123",
    "date": datetime.now().isoformat(),
    "completed": True,
    "workout_type": "strength",
    "duration_min": 50,
    "rpe_actual": 8,
    "exercises": [
        {
            "name": "Bench Press",
            "sets": 4,
            "reps": 8,
            "weight_kg": 60.0,
            "duration_per_set_sec": None,
            "distance_km": None,
            "rest_sec": 90,
        },
        {
            "name": "Barbell Row",
            "sets": 4,
            "reps": 8,
            "weight_kg": 50.0,
            "duration_per_set_sec": None,
            "distance_km": None,
            "rest_sec": 90,
        },
    ],
    "volume_km": None,
    "feedback": "felt_great",
    "intensity": "high",
    "notes": None,
}

# Sample user feedback
SAMPLE_FEEDBACK_SORE = {
    "user_id": "test_user_123",
    "status": "sore",
    "body_part": "shoulder",
    "severity": 3,
    "timestamp": datetime.now().isoformat(),
}

SAMPLE_FEEDBACK_TIRED = {
    "user_id": "test_user_123",
    "status": "tired",
    "body_part": None,
    "severity": None,
    "timestamp": datetime.now().isoformat(),
}

SAMPLE_FEEDBACK_PAIN = {
    "user_id": "test_user_123",
    "status": "pain",
    "body_part": "knee",
    "severity": 4,
    "timestamp": datetime.now().isoformat(),
}

SAMPLE_FEEDBACK_GREAT = {
    "user_id": "test_user_123",
    "status": "great",
    "body_part": None,
    "severity": None,
    "timestamp": datetime.now().isoformat(),
}


# Mock LLM response for high-level plan
MOCK_LLM_HIGH_LEVEL_PLAN_RESPONSE = """```json
{
  "plan_id": "plan_test_user_123_abc12345",
  "goal_id": "goal_123",
  "user_id": "test_user_123",
  "duration_weeks": 8,
  "overview_markdown": "# Training Plan\\n\\nYour 8-week plan focuses on building endurance.",
  "phase_breakdown": [
    {"weeks": "1-3", "focus": "Base Building", "description": "Aerobic foundation"},
    {"weeks": "4-6", "focus": "Build", "description": "Increase intensity"},
    {"weeks": "7-8", "focus": "Taper", "description": "Reduce volume"}
  ],
  "created_at": "2025-01-06T12:00:00"
}
```"""

# Mock LLM response for workout
MOCK_LLM_WORKOUT_RESPONSE = """```json
{
  "workout_id": "workout_2025-01-06_abc123",
  "scheduled_for_date": "2025-01-06",
  "title": "Endurance: Easy Run",
  "workout_type": "endurance",
  "estimated_duration_min": 45,
  "intensity_target": "RPE_5_6",
  "sections": [
    {
      "name": "warmup",
      "items": [
        {
          "kind": "mobility",
          "exercise_id": null,
          "name": "Walking",
          "sets": null,
          "reps": null,
          "weight_kg": null,
          "duration_min": 5,
          "distance_km": null,
          "rest_sec": null,
          "cues": "Easy pace to warm up"
        }
      ]
    },
    {
      "name": "main",
      "items": [
        {
          "kind": "endurance",
          "exercise_id": null,
          "name": "Easy Run",
          "sets": null,
          "reps": null,
          "weight_kg": null,
          "duration_min": 35,
          "distance_km": 5.0,
          "rest_sec": null,
          "cues": "Conversational pace, nose breathing"
        }
      ]
    },
    {
      "name": "cooldown",
      "items": [
        {
          "kind": "recovery",
          "exercise_id": null,
          "name": "Walking",
          "sets": null,
          "reps": null,
          "weight_kg": null,
          "duration_min": 5,
          "distance_km": null,
          "rest_sec": null,
          "cues": "Gradually slow down"
        }
      ]
    }
  ],
  "rationale": [
    "Building aerobic base for race preparation",
    "Low intensity to allow recovery from previous sessions"
  ],
  "questions": null
}
```"""

