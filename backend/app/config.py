"""Application configuration."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    app_name: str = "Training Coach API"
    debug: bool = Field(default=False, description="Enable debug mode")

    # Anthropic API
    anthropic_api_key: str = Field(
        default="", description="Anthropic API key for Claude"
    )

    # Model configuration
    default_model: str = Field(
        default="claude-haiku-4-5-20251001",
        description="Default Claude model for generation",
    )
    fallback_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Stronger model for retries",
    )
    max_retries: int = Field(default=2, description="Maximum LLM retries")

    # Storage paths
    data_dir: Path = Field(
        default=Path("data"), description="Directory for JSON storage"
    )

    # Generation settings
    recent_workouts_days: int = Field(
        default=30, description="Days of recent workouts to include in snapshot"
    )
    max_recent_workouts: int = Field(
        default=20, description="Maximum recent workouts in snapshot"
    )
    workout_generation_window_days: int = Field(
        default=7, description="Days ahead to pre-generate workouts"
    )
    block_duration_days: int = Field(
        default=21, description="Number of days per training block"
    )
    pending_workout_lookback_days: int = Field(
        default=3, description="Days to check for incomplete workouts"
    )

    # Session
    session_duration_days: int = Field(
        default=30, description="Session expiry in days from creation"
    )

    # Rate limiting (per user)
    rate_limit_onboard_per_hour: int = Field(
        default=3, description="Max onboarding attempts per hour"
    )
    rate_limit_plan_generate_per_hour: int = Field(
        default=3, description="Max plan generation attempts per hour"
    )
    rate_limit_block_generate_per_day: int = Field(
        default=5, description="Max block generation attempts per day"
    )
    rate_limit_workout_today_per_hour: int = Field(
        default=30, description="Max workout-today requests per hour"
    )
    rate_limit_feedback_per_hour: int = Field(
        default=20, description="Max feedback submissions per hour"
    )
    rate_limit_swap_per_hour: int = Field(
        default=10, description="Max workout swap requests per hour"
    )

    # Generation caps
    max_blocks_per_user: int = Field(
        default=8, description="Maximum training blocks per user (~6 months)"
    )
    max_days_ahead_for_blocks: int = Field(
        default=42, description="Maximum days ahead blocks can extend beyond today"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore extra env vars like OPENAI_API_KEY
    }


# Global settings instance
settings = Settings()


def get_data_path(filename: str) -> Path:
    """Get full path to a data file."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir / filename

