"""LLM Gateway Interface and Factory."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional
import httpx

from app.core.config import settings


class ILLMClient(ABC):
    """Abstract interface for LLM operations."""

    @abstractmethod
    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict:
        """Generate structured JSON response."""
        pass

    @abstractmethod
    async def stream_speech(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Stream speech text chunk-by-chunk."""
        pass


class OpenAILLMClient(ILLMClient):
    """Client for OpenAI-compatible APIs."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict:
        # Full implementation wired in M2
        return {}

    async def stream_speech(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        # Full implementation wired in M2
        yield ""


def get_llm_client() -> ILLMClient:
    """Factory creating OpenAI or Mock LLM Client based on configuration."""
    from app.infrastructure.mock_engine import MockLLMClient

    if settings.is_mock_mode:
        return MockLLMClient()

    return OpenAILLMClient(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )
