"""App settings, read from .env with pydantic-settings.

Phase 0. Model names live here only, never hard-coded elsewhere.
"""

# TODO(phase-0): class Settings(BaseSettings)
#   - Gemini auth: GOOGLE_API_KEY  or  GOOGLE_CLOUD_PROJECT + GOOGLE_GENAI_USE_VERTEXAI
#   - LLM_MODEL, EMBED_MODEL
#   - CHROMA_HOST, CHROMA_PORT, collection name
#   - WP_BASE_URL, WC_KEY, WC_SECRET
#   - retrieval knobs: top_k, distance threshold, retrieval mode (vector | bm25 | hybrid)
# TODO(phase-0): a single cached `get_settings()` accessor
