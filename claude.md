# claude.md — Training Coach App (Fullstack)

You are Claude Code working in a codebase for a fullstack fitness coaching application. The app features an AI-powered coach that generates personalized training plans and workouts.

## Project Overview
- **Current state**: Fullstack web app with React frontend and FastAPI backend
- **Future state**: Native iOS app (using a dedicated iOS framework) with the same backend
- **Backend design principle**: The API is frontend-agnostic. All endpoints return JSON and are designed to support any client (web, iOS, Android). The backend must remain decoupled from any specific frontend implementation.

## Non-negotiables
- **API input = JSON object. API output = JSON object.**
- Never return free-form output from core endpoints; always conform to schemas.
- If required data is missing, output a **JSON object describing missing fields/questions** (still JSON out).
- Prioritize **simplicity, stability, and testability** over "clever agent architectures".
- All safety/guardrail rules must be enforceable in code (not only in prompts).
- **Backend must be frontend-agnostic**: Design APIs so they work with the current React web app and a future iOS native app without changes.

## Product scope (MVP)
- User has a profile + goal (e.g., Vasaloppet in 8 weeks).
- System generates a high-level 8-week plan overview (stored as `overview_markdown` inside JSON) to keep overall direction.
- System generates a 21-day block (3 weeks) as **day slots**, and generates full detailed workouts only **just-in-time** (up to 7 days ahead).
- As user progresses, system generates the next 21-day block when needed.
- Daily use: user opens app and presses "display my workout for today" to see the **pre-generated** workout (if present) for that date.
- Before training, user can provide feedback via a form (buttons: "I'm sore", "I'm tired", "I feel great", "I have pain") which triggers workout adjustment.
- If user provides negative feedback (sore, tired, pain), system adjusts current day's workout and may regenerate upcoming days in current block (typically next 1–3 days).
- System stores all completed workouts with exercise details, timestamps, and feedback as context for future workout generation.
- UI is a traditional workout list (exercises top-to-bottom; sets/reps or time/distance).

## How It Works (User Flow)
1. **Setup**: User creates profile + enters goal
2. **Plan Generation**:
   - System generates high-level 8-week plan overview (JSON-only, with `overview_markdown`)
   - System generates initial 21-day block as **day slots** (workout type + duration/intensity targets, rest days)
   - System generates **full WorkoutPlan objects only for workouts up to 7 days ahead**
3. **Daily use**:
   - User: Enters the app and presses "display my workout for today"
   - App: Shows specific workout for today's date (if detailed workout exists; otherwise generate it)
   - User (optional): Before training, opens feedback form and reports status ("I'm sore", "I'm tired", "I feel great", "I have pain")
   - App (if negative feedback): Adjusts that day's workout; optionally updates the next few days
   - User: Completes the workout (original or adjusted)
   - User: Logs completion with optional post-workout feedback
4. **Progressive generation**:
   - When user reaches day ~18-19 of current block, system generates next 21-day block (days 22-42)
   - For the new block, pre-generate full workouts only for the first 7 days (rolling window)
5. **Context storage**: The app saves each completed workout including:
   - Exercise details (name, sets, reps, weight, duration, distance)
   - Timestamp (date and time)
   - RPE actual
   - User feedback
   - History is summarized into a compact snapshot before sending to the LLM

## Architecture (keep it minimal)

### Frontend (Current: React Web App)
- **Stack**: React + Vite + Tailwind CSS
- **Location**: `frontend/`
- **Pages**: Login, Home, Profile, Goal, Workout, Plan, Log
- **Components**: FeedbackForm, WorkoutCard, ExerciseItem, Layout, LoadingSpinner, ExercisePicker
- **API layer**: `src/api/client.js` handles all backend communication
- **Design guidance**: See `.claude/frontend-design/SKILL.md` for UI/UX standards

### Frontend (Future: iOS Native App)
- A dedicated iOS framework will replace the React frontend
- The backend API remains unchanged—designed to be client-agnostic
- All current endpoints will serve the iOS app without modification

### Backend (FastAPI + LLM)
- **Any frontend client** talks only to **our backend** via REST API
- Backend is the "LLM gateway":
  - builds a compact `FitnessSnapshot` from stored data (raw history → summary)
  - calls LLM to generate plan/workout JSON
  - validates output JSON with schemas
  - applies hard guardrails (progression limits, rest rules)
  - persists plan/workout + logs
- No multi-agent framework in MVP. Use a pipeline:
  1) Build snapshot (code)
  2) Generate (LLM)
  3) Validate (code)
  4) Repair (optional LLM) if validation fails

## Data model (schemas first)
Define Pydantic models (or equivalent) as the single source of truth.

### UserProfile
```python
class UserProfile(BaseModel):
    age: int
    weight_kg: float
    height_cm: int
    gender: Optional[str] = None
    fitness_level: Literal["beginner", "intermediate", "advanced"]
    training_history_years: int
    available_equipment: List[str]  # ["barbell", "ski_erg", "gym", "none"]
    injuries_or_limitations: Optional[str] = None
    training_days_per_week: int  # 3-6 days
    preferred_training_days: Optional[List[str]] = None  # ["monday", "wednesday", "friday"]
```

### UserGoal
```python
class UserGoal(BaseModel):
    goal_type: Literal["race", "strength", "weight_loss", "general_fitness"]
    target_event: Optional[str] = None  # "Vasaloppet 90km"
    target_date: str  # ISO format
    current_baseline: Optional[Dict] = None  # e.g., {"5k_time_min": 25, "squat_1rm_kg": 100}
    priority: Literal["performance", "health", "enjoyment"]
```

### Exercise Database
```python
class Exercise(BaseModel):
    id: str
    name: str
    category: Literal["cardio", "strength", "mobility", "recovery"]
    muscle_groups: List[str]  # ["quads", "glutes", "hamstrings"]
    equipment_required: List[str]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    substitutes: List[str]  # alternative exercise IDs
```

### Workout History Schema
Store complete workout details for context (DB), but do not send all of it to the LLM uncompressed.
```python
class ExerciseLog(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    duration_per_set_sec: Optional[int] = None
    distance_km: Optional[float] = None
    rest_sec: Optional[int] = None

class WorkoutLog(BaseModel):
    date: str  # ISO datetime
    completed: bool
    type: str  # "intervals", "hypertrophy", "endurance", "recovery"
    duration_min: int
    rpe_actual: int  # 1-10
    exercises: List[ExerciseLog]
    volume_km: Optional[float] = None  # total distance if applicable
    feedback: Optional[str] = None  # "felt_great", "sore", "tired", "pain"
    intensity: Optional[str] = None  # "low", "medium", "high"
```

### User Feedback Schema
Form-based feedback (no chat UI in MVP):
```python
class UserFeedback(BaseModel):
    status: Literal["sore", "tired", "great", "pain"]
    body_part: Optional[str] = None  # for pain (e.g., "shoulder", "knee")
    severity: Optional[int] = None  # 1-5 scale
    timestamp: str  # ISO datetime
```

## Plan Structure (JSON-only)
### HighLevelPlan (8-week strategic overview)
**High-level plan must be JSON-only.**
- Do not output standalone text or markdown files.
- Human-readable explanation is allowed only as a string field inside JSON.

```python
class HighLevelPlan(BaseModel):
    goal_id: str
    duration_weeks: int  # 8
    overview_markdown: str  # human-readable strategy text for UI
    phase_breakdown: List[Dict]  # [{"weeks": "1-3", "focus": "base building"}, ...]
    created_at: str
```

### Day Slot vs Detailed Workout
Prefer a 21-day block as **day slots** (lightweight schedule), and generate full workouts **just-in-time**.

```python
class DaySlot(BaseModel):
    day_number: int  # 1-21 per block
    date: str  # ISO date
    workout_type: Optional[str]  # e.g., "endurance", "intervals", "strength", "recovery"
    target_duration_min: Optional[int] = None
    target_distance_km: Optional[float] = None
    intensity_target: Optional[str] = None  # e.g., "RPE_6_7" or "zone2"
    is_rest_day: bool
    status: Literal["planned", "adjusted", "completed", "skipped"]
    workout_id: Optional[str] = None  # points to detailed WorkoutPlan when generated
```

```python
class ThreeWeekBlock(BaseModel):
    block_number: int  # 1, 2, 3...
    start_date: str
    end_date: str
    day_slots: List[DaySlot]  # length 21
    created_at: str
```

### WorkoutPlan (detailed)
Detailed workout JSON rendered by the UI (exercise list top-to-bottom).
```python
class WorkoutItem(BaseModel):
    kind: Literal["strength", "endurance", "mobility", "recovery"]
    exercise_id: Optional[str] = None
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    duration_min: Optional[int] = None
    distance_km: Optional[float] = None
    rest_sec: Optional[int] = None
    cues: Optional[str] = None

class WorkoutSection(BaseModel):
    name: Literal["warmup", "main", "cooldown"]
    items: List[WorkoutItem]

class WorkoutPlan(BaseModel):
    workout_id: str
    scheduled_for_date: str  # ISO date
    title: str
    workout_type: str
    estimated_duration_min: int
    intensity_target: str  # e.g. "RPE_6_7"
    sections: List[WorkoutSection]
    rationale: List[str]  # 1-3 bullets referencing snapshot signals
    questions: Optional[List[str]] = None  # only if critical info missing
```

```python
class CompletePlan(BaseModel):
    high_level_plan: HighLevelPlan
    current_block: ThreeWeekBlock
    blocks_generated: List[int]  # tracks which blocks are ready
```

## Adjustment Rules (code source of truth)
```python
ADJUSTMENT_RULES = {
    "sore": {
        "reduce_volume": 0.30,          # -30%
        "reduce_intensity": 0.20,       # -20%
        "skip_same_muscle_group": True
    },
    "tired": {
        "reduce_rpe_target": 2,         # RPE 8→6
        "add_rest_day": False
    },
    "pain": {
        "exclude_exercises_by_body_part": True,
        "max_rpe": 5,
        "alert_user": "Consider consulting a professional"
    },
    "great": {
        "no_adjustment": True
    }
}
```

## Progression Rules (code source of truth)
```python
PROGRESSION_RULES = {
    "strength": {
        "weekly_volume_increase_max": 0.10,   # 10%
        "weight_increase_min_kg": 2.5,
        "deload_week_frequency": 4
    },
    "endurance": {
        "weekly_distance_increase_max": 0.15, # 15%
        "weekly_intensity_sessions_max": 2,
        "recovery_week_frequency": 3
    }
}
```

## Output policy
All backend endpoints must return one of:
- `WorkoutPlan` (valid)
- `ThreeWeekBlock` (valid day slots; may contain some detailed `workout_id` references)
- `HighLevelPlan` (JSON-only; includes `overview_markdown`)
- `ClarifyingQuestions` (if missing info)
- `ErrorResponse` (for failures; still JSON)

No other shapes.

## Workout Generation Strategy

### Initial Plan Generation
1. Generate `HighLevelPlan` (JSON-only; `overview_markdown` is a string field)
2. Generate first `ThreeWeekBlock` as day slots (21 days)
3. Generate detailed `WorkoutPlan` only for workouts within the next 7 days
4. Store all; mark block 1 as generated

### Progressive Block Generation
- When user reaches day ~18-19 of current block, trigger next block generation.
- Generate next `ThreeWeekBlock` using:
  - `HighLevelPlan` for strategic alignment
  - summarized history (recent logs + aggregates)
- Pre-generate detailed `WorkoutPlan` only for the first 7 days of the new block

### Daily Workout Retrieval
- Determine today's date
- If a detailed workout exists for today: return it
- If today's slot exists but no detailed workout yet:
  - generate today's detailed workout (LLM)
  - validate and persist
  - return it

### Feedback-Based Adjustment
- User provides feedback before workout
- System adjusts today's detailed `WorkoutPlan` based on `ADJUSTMENT_RULES`
- May regenerate next 1–3 days if severe feedback (e.g., pain)
- Does NOT regenerate entire block

## Guardrails (must be in code)
Implement deterministic checks:
- Avoid consecutive hard days (e.g., RPE > 8 two days in a row)
- Weekly progression cap (e.g., +10–15% volume/distance)
- If pain reported → do not increase intensity; provide low-impact alternative
- If 2+ extra rest days → return-to-training session is easy
- If "sore" reported → reduce volume or intensity for that day
- Same muscle group worked → minimum 48h rest between high-intensity sessions
- Respect `preferred_training_days` when generating day slots (if provided)
- Include rest days between hard sessions

LLM should be guided, but **code is the enforcement**.

## LLM usage guidelines (Claude API)
- Default to a cheaper model for generation; promote to stronger model only on repeated failures.
- Prompts must:
  - state "Use provided JSON as source of truth; do not invent missing values"
  - require output to match schema
  - include constraints/guardrails explicitly
- Always implement:
  - JSON parsing + schema validation
  - retry strategy (1–2 retries max)
  - "repair call" path: feed validation errors and ask model to fix output

### Context management (token cost control)
- Never send full workout history to the LLM.
- Snapshot builder must provide:
  - `recent_workouts`: last 14–30 days (or last N workouts) detailed logs
  - `history_summary`: aggregated stats for older history (weekly averages, intensity distribution, common exercises, recent PRs)
- The LLM should base decisions on `FitnessSnapshot` only.

## Files & folders

### Backend (`backend/`)
- `app/`
  - `models/` (Pydantic schemas)
  - `services/`
    - `snapshot_builder.py`
    - `llm_client.py`
    - `high_level_plan_generator.py`
    - `block_generator.py`
    - `workout_generator.py`
    - `workout_adjuster.py`
    - `validator.py`
    - `repair.py`
  - `api/` (FastAPI routes)
- `tests/`
- `prompts/` (versioned prompt templates)
- `data/` (JSON fixtures)

### Frontend (`frontend/`)
- `src/`
  - `api/` (API client)
  - `components/` (reusable UI components)
  - `pages/` (route pages: Login, Home, Profile, Goal, Workout, Plan, Log)
  - `hooks/` (custom React hooks)
  - `assets/` (static assets)
- `public/` (public assets)
- Tailwind config, Vite config, ESLint config

### Project Root
- `.claude/` (AI assistant configuration and skills)

## Endpoint contracts (MVP)
Design endpoints as pure JSON I/O:
- `POST /profile` → saves `UserProfile`
- `POST /goal` → saves `UserGoal`
- `POST /plan/generate` → returns `CompletePlan` OR `ClarifyingQuestions`
- `GET /workout/today` → returns today's `WorkoutPlan` (or rest day indicator JSON)
- `POST /workout/feedback` → accepts `UserFeedback`, returns adjusted `WorkoutPlan`
- `POST /workout/log` → saves `WorkoutLog`
- `POST /block/generate-next` → generates next `ThreeWeekBlock` (triggered automatically or manually)

## Testing requirements

### Backend
- Unit tests for:
  - snapshot builder (deterministic)
  - validator rules
  - schema validation
  - workout adjustment logic
  - date → day_number/slot mapping
- Golden tests:
  - fixed snapshots → expected JSON shapes
  - feedback scenarios → expected adjustments
- Mock LLM responses for tests; do not hit external APIs in unit tests.

### Frontend
- Component tests for key UI components
- Integration tests for API client
- E2E tests for critical user flows (login, view workout, submit feedback)

## Coding standards
- Type hints everywhere.
- Small functions, single responsibility.
- Explicit error handling; never swallow exceptions.
- Log:
  - snapshot inputs (sanitized)
  - model used + prompt version
  - validation errors
  - final output version
  - user feedback and resulting adjustments

## Security & privacy (consumer app)
- Never request or store unnecessary sensitive data.
- Treat health data as sensitive. Do not store or transmit PII unnecessarily.
- User feedback (pain/body parts) is health data—handle with care.

## Decision rules for asking clarifying questions
If any required fields are missing for the requested action:
- return `ClarifyingQuestions` JSON with:
  - `questions[]` (short)
  - `missing_fields[]`
  - `reason`
Do not guess missing values.

## When unsure
- Prefer deterministic code over prompting.
- Prefer adding/adjusting schema fields over stuffing more text into prompts.
- Keep MVP scope tight: HighLevelPlan + ThreeWeekBlock (slots) + WorkoutPlan (just-in-time) + Feedback + Adjustment + Log.

## Out of Scope (MVP)
- Social features (sharing workouts)
- Video demonstrations
- Nutrition tracking
- Wearable integrations (heart rate, sleep)
- Payment/subscriptions
- Multi-language support
- Native iOS app (planned for post-MVP)
- Full production DB migrations (focus on logic/services first)

## Future considerations (post-MVP)
- **Native iOS app**: Replace React web frontend with a dedicated iOS framework (backend API remains unchanged)
- Chat interface for nuanced coaching
- Context compression improvements
- Advanced adaptation (multi-week replanning)
- Exercise variety engine (frequency tracking)
- Indexing/caching for performance


<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific file, you MUST read the file before answering. Make sure to investigate and read relevant files BEFORE answering questions about the codebase. Never make any claims about code before investigating unless you are certain of the correct answer - give grounded and hallucination-free answers.
</investigate_before_answering>

