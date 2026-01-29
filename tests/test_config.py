"""Tests for the configuration module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from quant.config import Settings


class TestSettings:
    """Tests for the Settings class."""

    @pytest.fixture
    def valid_env_vars(self) -> dict[str, str]:
        """Provide valid environment variables for testing."""
        return {
            "ALPACA_API_KEY": "test-api-key",
            "ALPACA_SECRET_KEY": "test-secret-key",
            "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
        }

    def test_loads_from_environment_variables(self, valid_env_vars: dict[str, str]) -> None:
        """Test that settings loads values from environment variables."""
        with patch.dict(os.environ, valid_env_vars, clear=True):
            settings = Settings()

            assert settings.alpaca_api_key == "test-api-key"
            assert settings.alpaca_secret_key == "test-secret-key"
            assert settings.alpaca_base_url == "https://paper-api.alpaca.markets"
            assert settings.database_url == "postgresql://user:pass@localhost/db"
            assert settings.redis_url == "redis://localhost:6379"

    def test_default_values(self, valid_env_vars: dict[str, str]) -> None:
        """Test that default values are applied correctly."""
        with patch.dict(os.environ, valid_env_vars, clear=True):
            settings = Settings()

            assert settings.base_reserve == 1000
            assert settings.max_position_size == 1000
            assert settings.confidence_threshold == 70

    def test_overrides_defaults_from_env(self, valid_env_vars: dict[str, str]) -> None:
        """Test that environment variables override default values."""
        env_with_overrides = {
            **valid_env_vars,
            "BASE_RESERVE": "2000",
            "MAX_POSITION_SIZE": "500",
            "CONFIDENCE_THRESHOLD": "85",
        }
        with patch.dict(os.environ, env_with_overrides, clear=True):
            settings = Settings()

            assert settings.base_reserve == 2000
            assert settings.max_position_size == 500
            assert settings.confidence_threshold == 85

    def test_base_reserve_must_be_positive(self, valid_env_vars: dict[str, str]) -> None:
        """Test that base_reserve must be a positive integer."""
        env_with_zero = {**valid_env_vars, "BASE_RESERVE": "0"}
        with patch.dict(os.environ, env_with_zero, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "base_reserve" in str(exc_info.value)

        env_with_negative = {**valid_env_vars, "BASE_RESERVE": "-100"}
        with patch.dict(os.environ, env_with_negative, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "base_reserve" in str(exc_info.value)

    def test_max_position_size_must_be_positive(self, valid_env_vars: dict[str, str]) -> None:
        """Test that max_position_size must be a positive integer."""
        env_with_zero = {**valid_env_vars, "MAX_POSITION_SIZE": "0"}
        with patch.dict(os.environ, env_with_zero, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "max_position_size" in str(exc_info.value)

    def test_confidence_threshold_must_be_0_to_100(self, valid_env_vars: dict[str, str]) -> None:
        """Test that confidence_threshold must be between 0 and 100."""
        # Test below range
        env_with_negative = {**valid_env_vars, "CONFIDENCE_THRESHOLD": "-1"}
        with patch.dict(os.environ, env_with_negative, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "confidence_threshold" in str(exc_info.value)

        # Test above range
        env_with_above = {**valid_env_vars, "CONFIDENCE_THRESHOLD": "101"}
        with patch.dict(os.environ, env_with_above, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "confidence_threshold" in str(exc_info.value)

    def test_confidence_threshold_accepts_boundary_values(
        self, valid_env_vars: dict[str, str]
    ) -> None:
        """Test that confidence_threshold accepts 0 and 100."""
        # Test lower boundary
        env_with_zero = {**valid_env_vars, "CONFIDENCE_THRESHOLD": "0"}
        with patch.dict(os.environ, env_with_zero, clear=True):
            settings = Settings()
            assert settings.confidence_threshold == 0

        # Test upper boundary
        env_with_hundred = {**valid_env_vars, "CONFIDENCE_THRESHOLD": "100"}
        with patch.dict(os.environ, env_with_hundred, clear=True):
            settings = Settings()
            assert settings.confidence_threshold == 100

    def test_missing_required_fields_raises_error(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            error_str = str(exc_info.value)
            assert "alpaca_api_key" in error_str
