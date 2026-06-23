from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ZDR_",
        extra="ignore",
    )

    app_name: str = "Zero Day Radar"
    app_version: str = "0.1.0"
    debug: bool = False

    # Nitter instances for X/Twitter (no API key needed)
    # Comma-separated in .env — NoDecode prevents pydantic from JSON-parsing it
    nitter_instances: Annotated[list[str], NoDecode] = [
        "https://nitter.poast.org",
        "https://xcancel.com",
        "https://nitter.privacydev.net",
        "https://nitter.net",
    ]
    nitter_verify_ssl: bool = False
    nitter_timeout_seconds: int = 15

    @field_validator("nitter_instances", mode="before")
    @classmethod
    def parse_nitter_instances(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [u.strip() for u in v.split(",") if u.strip()]
        return v

    # API keys (optional — collectors degrade gracefully without them)
    twitter_bearer_token: str | None = None  # unused; Nitter is default for Twitter
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "zero-day-radar/0.1"
    github_token: str | None = None
    nvd_api_key: str | None = None

    # Hunt defaults
    default_lookback_days: int = 30
    min_confidence_score: float = 50.0
    max_results_per_source: int = 50
    request_timeout_seconds: int = 30

    # SQLite
    database_url: str = "sqlite+aiosqlite:///./data/zero_day_radar.db"

    # Celery + Redis background jobs
    redis_url: str = "redis://localhost:6379/0"
    celery_beat_interval_minutes: int = 20
    celery_enabled: bool = True

    # Ollama LLM (unified intel enrichment)
    ollama_enabled: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 120


settings = Settings()
