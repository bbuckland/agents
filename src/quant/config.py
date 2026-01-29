"""Configuration module for the quant trading system."""

from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Alpaca broker settings
    alpaca_api_key: SecretStr
    alpaca_secret_key: SecretStr
    alpaca_base_url: str

    # Database settings
    database_url: str
    redis_url: str

    # Trading parameters
    base_reserve: Annotated[int, Field(gt=0)] = 1000
    max_position_size: Annotated[int, Field(gt=0)] = 1000
    confidence_threshold: Annotated[int, Field(ge=0, le=100)] = 70

    @field_validator("base_reserve", "max_position_size")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that value is positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence_range(cls, v: int) -> int:
        """Validate that confidence threshold is between 0 and 100."""
        if not 0 <= v <= 100:
            raise ValueError("Confidence threshold must be between 0 and 100")
        return v
