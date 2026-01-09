"""
Pytest configuration and shared fixtures.
"""

import sys
from pathlib import Path

import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # This helps ensure test isolation
    yield
    # Cleanup after test if needed


@pytest.fixture
def mock_llm_response(monkeypatch):
    """Mock LLM client to return predefined responses."""
    from tests.fixtures.sample_data import MOCK_LLM_WORKOUT_RESPONSE

    class MockLLMClient:
        def generate(self, *args, **kwargs):
            return MOCK_LLM_WORKOUT_RESPONSE

        def generate_json(self, *args, **kwargs):
            import json
            # Extract JSON from the mock response
            response = MOCK_LLM_WORKOUT_RESPONSE
            start = response.find("{")
            end = response.rfind("}") + 1
            return json.loads(response[start:end])

        def generate_and_validate(self, *args, **kwargs):
            from app.services.validator import ValidationResult
            json_data = self.generate_json()
            return None, ValidationResult(is_valid=False)

    # Monkeypatch the global llm_client
    from app.services import llm_client as llm_module
    mock = MockLLMClient()
    monkeypatch.setattr(llm_module, "llm_client", mock)
    return mock

