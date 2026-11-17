"""App settings, read from .env with pydantic-settings.

Phase 0. Model names live here only, never hard-coded elsewhere.
"""
from typing import Literal

from dataclasses import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str | None = None
    llm_model: str
    embed_model: str
    embed_dim: int = 768
    embed_batch_size: int = 100

    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection: str = "micromax-trade-catalog"

    wc_key: str | None = None
    wc_secret: str | None = None
    wp_base_url: str
    services_rest_base: str | None = None
    branch_rest_base: str | None = None

    top_k: int = Field(5, ge=1, le=20)           
    candidate_k: int = Field(20, ge=5, le=100)       
    rrf_k: int = 60
    distance_threshold: float = Field(0.6, ge=0.0, le=2.0)   
    retrieval_mode: Literal["vector", "bm25", "hybrid"] = "hybrid"

settings = Settings()
