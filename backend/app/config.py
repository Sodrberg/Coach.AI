"""Application configuration."""

import os
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

