# Training Coach Backend

AI-powered fitness coaching backend that generates personalized training plans and workouts.

## Overview

This backend implements a JSON-in/JSON-out API for a mobile fitness app. It uses Claude (Anthropic) to generate:
- 8-week high-level training plans
- 21-day training blocks with day slots
- Detailed workout plans (just-in-time generation)
- Feedback-based workout adjustments

## Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. OpenAPI docs at `/docs`.

### Running Tests

```bash
pytest tests/ -v
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/profile` | POST | Save user profile |
| `/api/v1/profile/{user_id}` | GET | Get user profile |
| `/api/v1/goal` | POST | Save user goal |
| `/api/v1/goal/{user_id}` | GET | Get active goal |
| `/api/v1/plan/generate` | POST | Generate complete training plan |
| `/api/v1/workout/today` | GET | Get today's workout |
| `/api/v1/workout/feedback` | POST | Submit feedback, get adjusted workout |
| `/api/v1/workout/log` | POST | Log completed workout |
| `/api/v1/block/generate-next` | POST | Generate next 21-day block |
| `/api/v1/health` | GET | Health check |

## Architecture

```
app/
├── api/           # FastAPI routes
├── models/        # Pydantic schemas (source of truth)
├── services/      # Business logic
│   ├── snapshot_builder.py    # Builds LLM context
│   ├── llm_client.py          # Claude API wrapper
│   ├── high_level_plan_generator.py
│   ├── block_generator.py
│   ├── workout_generator.py
│   ├── workout_adjuster.py    # Feedback adjustments
│   └── validator.py           # Schema + guardrail validation
├── rules/         # ADJUSTMENT_RULES, PROGRESSION_RULES, guardrails
└── storage/       # JSON file storage (MVP)

prompts/           # Versioned prompt templates
tests/             # Unit tests
```

## Key Design Decisions

1. **JSON in, JSON out**: All endpoints return JSON conforming to defined schemas
2. **Guardrails in code**: Safety rules enforced by code, not just prompts
3. **Just-in-time generation**: Workouts generated when needed, not all upfront
4. **Feedback-based adjustment**: Real-time workout modifications based on user state

## Feedback Adjustment Rules

| Status | Adjustments |
|--------|-------------|
| `sore` | -30% volume, -20% intensity, skip affected muscle groups |
| `tired` | -2 RPE target, -15% duration |
| `pain` | Max RPE 5, exclude affected area, -40% intensity |
| `great` | No adjustments |

## Data Models

See `app/models/` for complete Pydantic schemas:
- `UserProfile`, `UserGoal`, `UserFeedback`
- `WorkoutPlan`, `WorkoutItem`, `WorkoutSection`, `WorkoutLog`
- `DaySlot`, `ThreeWeekBlock`, `HighLevelPlan`, `CompletePlan`
- `FitnessSnapshot` (LLM context)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `DEBUG` | Enable debug mode | `false` |
| `DEFAULT_MODEL` | Default Claude model | `claude-sonnet-4-20250514` |
| `DATA_DIR` | Data storage directory | `data` |

## License

MIT

