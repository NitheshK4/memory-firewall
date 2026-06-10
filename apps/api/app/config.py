from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Memory Firewall"
    api_v1_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    use_openai: bool = False
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    api_base_url: str = "http://localhost:8000"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/memory_firewall"
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    api_key: str | None = None  # X-API-Key for endpoint authentication; unset = open (dev mode)

    # Burst-write detection thresholds (passed to AuditService on startup).
    burst_window_seconds: int = 60
    burst_max_writes: int = 10

    # Retrieval threat configuration.
    # Minimum trust score returned when a credential-fishing query triggers
    # the 'medium' threat level in RetrievalService.
    retrieval_medium_trust_floor: float = 0.6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

