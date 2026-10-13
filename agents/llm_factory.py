"""
Deterministic local mock response adapter; no external inference providers are implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Mtb Orchestrator Pro"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} Mock]: No external model was invoked. Received query: '{prompt[:60]}...'. This response is not clinical analysis."


class LLMFactory:
    """Constructs the mock adapter; rejects provider names that are not implemented."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Mtb Orchestrator Pro"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(f"Unsupported model provider: {provider}. Only mock/deterministic/test are implemented.")
