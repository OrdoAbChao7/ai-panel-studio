"""LLM Gateway Protocol, Factory, and OpenAI Provider Implementation."""

import json
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    """Universal Protocol for LLM Operations."""

    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate plain unstructured text response."""
        ...

    async def generate_structured(
        self, prompt: str, schema: type[T], system_prompt: Optional[str] = None
    ) -> T:
        """Generate structured output validated against a Pydantic schema model."""
        ...

    async def stream_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Stream text tokens/chunks asynchronously with typing cadence."""
        ...


# Backward compatibility alias
ILLMClient = LLMClient


class OpenAILLMClient:
    """Client for OpenAI-compatible APIs with credential security."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 60,
    ) -> None:
        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def __repr__(self) -> str:
        return (
            f"OpenAILLMClient(model='{self.model}', base_url='{self.base_url}', "
            f"api_key='***')"
        )

    def __str__(self) -> str:
        return self.__repr__()

    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content or ""

    async def generate_structured(
        self, prompt: str, schema: type[T], system_prompt: Optional[str] = None
    ) -> T:
        messages = []
        sys = (
            (system_prompt or "")
            + "\nYou MUST respond strictly in valid JSON matching the schema."
        )
        messages.append({"role": "system", "content": sys})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=settings.LLM_TEMPERATURE,
        )
        raw_json = response.choices[0].message.content or "{}"
        return schema.model_validate_json(raw_json)

    async def stream_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    # Backward compatibility adapters
    async def generate_json(
        self, system_prompt: str, user_prompt: str
    ) -> Dict[str, Any]:
        text = await self.generate_text(prompt=user_prompt, system_prompt=system_prompt)
        try:
            return json.loads(text)
        except Exception:
            return {}

    async def stream_speech(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncIterator[str]:
        async for chunk in self.stream_text(
            prompt=user_prompt, system_prompt=system_prompt
        ):
            yield chunk


def get_llm_client() -> LLMClient:
    """Factory creating OpenAILLMClient or MockLLMClient based on settings."""
    from app.infrastructure.mock_engine import MockLLMClient

    if settings.is_mock_mode:
        return MockLLMClient()

    return OpenAILLMClient(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )
