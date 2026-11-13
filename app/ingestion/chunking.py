"""Turn the knowledge file and catalog records into chunks.

Phase 2. Chunk rules: see asd.md -> "Chunk rules".
"""

# TODO(phase-2): a Chunk model: id, text, metadata
# TODO(phase-2): chunk_knowledge(md_text) -> list[Chunk]     one per `##` section
# TODO(phase-2): chunk_product / chunk_category / chunk_service
# TODO(phase-2): split chunks over ~1,500 tokens on paragraphs, keep the title on each part
# TODO(phase-2): stable ids: knowledge:<slug>, product:<id>, category:<id>, service:<id>
