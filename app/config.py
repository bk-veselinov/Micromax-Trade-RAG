"""App settings, read from .env with pydantic-settings.

Phase 0. Model names live here only, never hard-coded elsewhere.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_model: str
    embed_model: str

    chroma_host: str = "localhost"
    chroma_port: int = 8000

    wc_key: str | None = None
    wc_secret: str | None = None
    wp_base_url: str
    services_rest_base: str | None = None
    branch_rest_base: str | None = None

settings = Settings()
