"""Fixed RAG flow: retrieve -> prompt -> Gemini -> answer + sources.

Phase 3.
"""

# TODO(phase-3): answer(question) -> {answer, sources: [{title, url, chunk_id}]}
#   - no hits left after the threshold -> NOT_IN_SOURCES without calling the LLM
