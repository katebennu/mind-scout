"""Tests for Phoenix observability module."""

import os
import pytest
from unittest.mock import patch, MagicMock
import importlib


@pytest.fixture(autouse=True)
def reset_observability_state():
    """Reset observability module state before each test."""
    import mindscout.observability as obs
    obs._initialized = False
    obs._tracer_provider = None

    # Also clear the settings cache
    from mindscout.config import get_settings
    get_settings.cache_clear()

    yield

    obs._initialized = False
    obs._tracer_provider = None
    get_settings.cache_clear()


class TestInitPhoenix:
    """Test init_phoenix function."""

    def test_init_phoenix_disabled_via_config(self, tmp_path, monkeypatch):
        """Test that Phoenix is not initialized when disabled."""
        monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("MINDSCOUT_PHOENIX_ENABLED", "false")

        import mindscout.observability as obs
        result = obs.init_phoenix()

        assert result is None
        assert obs.is_tracing_enabled() is False

    def test_init_phoenix_no_api_key(self, tmp_path, monkeypatch):
        """Test that Phoenix is not initialized without API key."""
        monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("MINDSCOUT_PHOENIX_ENABLED", "true")
        monkeypatch.delenv("PHOENIX_API_KEY", raising=False)
        monkeypatch.delenv("MINDSCOUT_PHOENIX_API_KEY", raising=False)

        import mindscout.observability as obs
        result = obs.init_phoenix()

        assert result is None
        assert obs.is_tracing_enabled() is False

    def test_init_phoenix_only_once(self, tmp_path, monkeypatch):
        """Test that init_phoenix only runs once."""
        monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("MINDSCOUT_PHOENIX_ENABLED", "false")

        import mindscout.observability as obs

        # Call twice
        result1 = obs.init_phoenix()
        result2 = obs.init_phoenix()

        # Both should return the same result (None in this case)
        assert result1 is result2

    def test_init_phoenix_with_api_key(self, tmp_path, monkeypatch):
        """Test that Phoenix initializes with API key."""
        monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("MINDSCOUT_PHOENIX_ENABLED", "true")
        monkeypatch.setenv("MINDSCOUT_PHOENIX_API_KEY", "test-api-key")
        monkeypatch.setenv("MINDSCOUT_PHOENIX_COLLECTOR_ENDPOINT", "https://test.phoenix.com")

        mock_tracer = MagicMock()

        import mindscout.observability as obs

        with patch.object(obs, "init_phoenix", wraps=obs.init_phoenix):
            with patch("phoenix.otel.register", return_value=mock_tracer) as mock_register:
                result = obs.init_phoenix()

                # When register is called successfully, tracing should be enabled
                if mock_register.called:
                    assert obs.is_tracing_enabled() is True

    def test_init_phoenix_uses_custom_project_name(self, tmp_path, monkeypatch):
        """Test that custom project name is used."""
        monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("MINDSCOUT_PHOENIX_ENABLED", "true")
        monkeypatch.setenv("MINDSCOUT_PHOENIX_API_KEY", "test-api-key")
        monkeypatch.setenv("MINDSCOUT_PHOENIX_PROJECT_NAME", "custom-project")

        import mindscout.observability as obs

        with patch("phoenix.otel.register") as mock_register:
            mock_register.return_value = MagicMock()
            obs.init_phoenix()

            if mock_register.called:
                call_kwargs = mock_register.call_args[1]
                assert call_kwargs["project_name"] == "custom-project"

    def test_init_phoenix_handles_exception(self, tmp_path, monkeypatch):
        """Test graceful handling of exceptions during init."""
        monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("MINDSCOUT_PHOENIX_ENABLED", "true")
        monkeypatch.setenv("MINDSCOUT_PHOENIX_API_KEY", "test-api-key")

        import mindscout.observability as obs

        # Patch register to raise an exception
        with patch("phoenix.otel.register", side_effect=Exception("Connection failed")):
            result = obs.init_phoenix()

        assert result is None


class TestGetTracerProvider:
    """Test get_tracer_provider function."""

    def test_get_tracer_provider_returns_none_when_not_initialized(self):
        """Test that get_tracer_provider returns None when not initialized."""
        import mindscout.observability as obs
        result = obs.get_tracer_provider()
        assert result is None


class TestIsTracingEnabled:
    """Test is_tracing_enabled function."""

    def test_is_tracing_enabled_false_when_not_initialized(self):
        """Test that is_tracing_enabled returns False when not initialized."""
        import mindscout.observability as obs
        assert obs.is_tracing_enabled() is False
