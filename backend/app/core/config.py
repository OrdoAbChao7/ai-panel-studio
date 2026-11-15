"""Application Configuration & Environment Settings."""

import json
import os
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env if present
load_dotenv()


class Settings(BaseModel):
    """Global configuration settings for AI Panel Studio."""

    # Server Network
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))

    # LLM Gateway
    LLM_API_KEY: str = Field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    LLM_BASE_URL: str = Field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
    LLM_MODEL: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    LLM_TEMPERATURE: float = Field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.7")))
    LLM_MAX_TOKENS: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "1024")))
    LLM_TIMEOUT_SECONDS: int = Field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT_SECONDS", "60")))

    # Offline Mock Fallback
    ENABLE_MOCK_FALLBACK: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_MOCK_FALLBACK", "true").lower() == "true"
    )
    MOCK_STREAM_SPEED_CPS: int = Field(default_factory=lambda: int(os.getenv("MOCK_STREAM_SPEED_CPS", "25")))
    MOCK_DEFAULT_SCENARIO: int = Field(default_factory=lambda: int(os.getenv("MOCK_DEFAULT_SCENARIO", "1")))
    SPEECH_CHUNK_DELAY_MS: int = Field(default_factory=lambda: int(os.getenv("SPEECH_CHUNK_DELAY_MS", "40")))

    # Debate Hyperparameters
    DEFAULT_MAX_ROUNDS: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_ROUNDS", "6")))
    DEFAULT_PARTICIPANT_COUNT: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_PARTICIPANT_COUNT", "4")))
    ROUND_TIMEOUT_SECONDS: int = Field(default_factory=lambda: int(os.getenv("ROUND_TIMEOUT_SECONDS", "180")))
    SPEAKER_COOLDOWN_TURNS: int = Field(default_factory=lambda: int(os.getenv("SPEAKER_COOLDOWN_TURNS", "1")))

    # Arbitration Formula Weights: S_i = 0.20*U + 0.25*C + 0.15*T + 0.15*E + 0.10*N + 0.15*F
    ARBITRATOR_WEIGHT_URGENCY: float = Field(
        default_factory=lambda: float(os.getenv("ARBITRATOR_WEIGHT_URGENCY", "0.20"))
    )
    ARBITRATOR_WEIGHT_CONFLICT: float = Field(
        default_factory=lambda: float(os.getenv("ARBITRATOR_WEIGHT_CONFLICT", "0.25"))
    )
    ARBITRATOR_WEIGHT_TOPICAL: float = Field(
        default_factory=lambda: float(os.getenv("ARBITRATOR_WEIGHT_TOPICAL", "0.15"))
    )
    ARBITRATOR_WEIGHT_EVIDENCE: float = Field(
        default_factory=lambda: float(os.getenv("ARBITRATOR_WEIGHT_EVIDENCE", "0.15"))
    )
    ARBITRATOR_WEIGHT_NOVELTY: float = Field(
        default_factory=lambda: float(os.getenv("ARBITRATOR_WEIGHT_NOVELTY", "0.10"))
    )
    ARBITRATOR_WEIGHT_FAIRNESS: float = Field(
        default_factory=lambda: float(os.getenv("ARBITRATOR_WEIGHT_FAIRNESS", "0.15"))
    )

    # Database
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ai_panel_studio.db")
    )
    SQL_ECHO: bool = Field(default_factory=lambda: os.getenv("SQL_ECHO", "false").lower() == "true")

    # CORS
    @property
    def cors_origins(self) -> List[str]:
        raw = os.getenv("CORS_ORIGINS", '["http://localhost:5174", "http://127.0.0.1:5174"]')
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def is_mock_mode(self) -> bool:
        """Return True if system should run in Mock mode."""
        return not self.LLM_API_KEY or self.LLM_API_KEY.lower() == "mock" or self.ENABLE_MOCK_FALLBACK


settings = Settings()
