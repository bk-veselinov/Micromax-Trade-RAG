"""Turn the knowledge file and catalog records into chunks.
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.ingestion.clean import html_to_text, variation_summary

KNOWLEDGE = Path("data/knowledge/micromax-catalog-rag.md")
CATALOG = Path("data/raw/catalog.json")
BRANCHES = Path("data/raw/branches.json")
CATEGORY_URL = "https://shop.micromaxtrade.com/produkt-kategoriya/{slug}/"
MAX_CHARS = 4000

Metadata = dict[str, str | bool | int | float]

@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    metadata: Metadata = field(default_factory=dict)

def clean_meta(metadata: dict) -> Metadata:
    """Coerce metadata to vector-store-friendly scalars; drop None/empty values."""
    out: Metadata = {}
    for k, v in metadata.items():
        if v is None or v == "" or v == []:
            continue
        if isinstance(v, (str, bool, int, float)):
            out[k] = v
        elif isinstance(v, list):
            out[k] = ", ".join(str(i) for i in v)
        else:
            out[k] = str(v)
    return out

def _join(lines: list[str]) -> str:
    """Join non-empty lines as paragraphs so split_chunk has boundaries to split on."""
    return "\n\n".join(line for line in lines if line)

SECTION_KINDS = {"Фирма": "company", "Категория": "category", "Услуга": "service"}
KEYWORDS_PREFIX = "Ключови думи:"

def _parse_frontmatter(md_text: str) -> tuple[dict[str, str], str]:
    """Split a leading `---` YAML-ish block into a flat dict and the remaining body."""
    match = re.match(r"\A---\n(.*?)\n---\n", md_text, flags=re.DOTALL)
    if not match:
        return {}, md_text
    meta = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta, md_text[match.end():]

def _slug(text: str) -> str:
    return re.sub(r"[^\w]+", "-", text.lower()).strip("-")

def chunk_knowledge(md_text: str) -> list[Chunk]:
    """One chunk per `##` section; the frontmatter and anything before the first `##` are skipped."""
    front, body = _parse_frontmatter(md_text.replace("\r\n", "\n"))
    sections = re.split(r"^## +", body, flags=re.MULTILINE)[1:]

    chunks: list[Chunk] = []
    seen: set[str] = set()
    for section in sections:
        heading, _, content = section.partition("\n")
        heading = heading.strip()
        content = re.sub(r"^-{3,}\s*$", "", content, flags=re.MULTILINE).strip()
        if not content:
            continue

        keywords = next(
            (line[len(KEYWORDS_PREFIX):].strip().rstrip(".")
             for line in content.splitlines() if line.startswith(KEYWORDS_PREFIX)),
            "",
        )
        prefix, sep, title = heading.partition(":")
        kind = SECTION_KINDS.get(prefix.strip(), "general") if sep else "general"

        chunk_id = f"knowledge:{_slug(heading)}"
        if chunk_id in seen:
            raise ValueError(f"Duplicate knowledge section heading: {heading!r}")
        seen.add(chunk_id)

        chunks.append(Chunk(
            id=chunk_id,
            text=f"{heading}\n\n{content}",
            metadata=clean_meta({
                "type": "knowledge",
                "section": kind,
                "title": title.strip() if sep else heading,
                "keywords": keywords,
                "version": front.get("version"),
            }),
        ))
    return chunks

def chunk_product(product: dict) -> Chunk:
    """Turn a product record into a chunk."""
    meta = {m["key"]: m["value"] for m in product.get("meta_data", [])}
    blueprint = html_to_text(meta.get("blueprint_data"))

    product_id = str(product["id"])
    categories = [cat["name"] for cat in product.get("categories", []) if cat]
    sku = product.get("sku")
    permalink = product.get("permalink")

    header = " | ".join(p for p in [
        product["name"],
        f"Код (SKU): {sku}" if sku else "",
        f"Категории: {', '.join(categories)}" if categories else "",
    ] if p)

    lines = [
        header,
        html_to_text(product.get("short_description")),
        html_to_text(product.get("description")),
        f"### Означения и работни условия\n{blueprint}" if blueprint else "",
        variation_summary(product.get("variations_data", [])),
        f"Линк: {permalink}" if permalink else "",
    ]

    return Chunk(
        id=f"product:{product_id}",
        text=_join(lines),
        metadata=clean_meta({
            "type": "product",
            "title": product["name"],
            "sku": sku,
            "category": categories,
            "permalink": permalink,
        }),
    )

def chunk_category(category: dict, names_by_id: dict[int, str] | None = None) -> Chunk:
    """Turn a category record into a chunk."""
    names_by_id = names_by_id or {}
    category_id = str(category["id"])
    url = CATEGORY_URL.format(slug=category["slug"])
    parent_name = names_by_id.get(category.get("parent") or 0)
    path = f"{parent_name} / {category['name']}" if parent_name else category["name"]

    lines = [
        category["name"],
        f"Път: {path}",
        html_to_text(category.get("description")),
        f"Линк: {url}",
    ]
    return Chunk(
        id=f"category:{category_id}",
        text=_join(lines),
        metadata=clean_meta({
            "type": "category",
            "title": category["name"],
            "permalink": url,
        }),
    )

def chunk_service(service: dict) -> Chunk:
    """Turn a service record into a chunk."""
    service_id = str(service["id"])
    acf = service.get("acf") or {}
    name = acf.get("service_name") or html_to_text((service.get("title") or {}).get("rendered"))
    link = service.get("link")

    summaries = [
        _join([acf.get(f"service_icon_text_{i}") or "", html_to_text(acf.get(f"service_summary_{i}"))])
        for i in range(1, 5)
    ]
    lines = [
        name,
        html_to_text(acf.get("service_short_description")),
        html_to_text(acf.get("service_description")),
        html_to_text(acf.get("service_additional_information")),
        *summaries,
        f"Линк: {link}" if link else "",
    ]
    return Chunk(
        id=f"service:{service_id}",
        text=_join(lines),
        metadata=clean_meta({
            "type": "service",
            "title": name,
            "permalink": link,
        }),
    )

def chunk_branch(branch: dict) -> Chunk:
    """Turn a branch (physical shop) record into a chunk."""
    branch_id = str(branch["id"])
    acf = {k: v.strip() if isinstance(v, str) else v for k, v in (branch.get("acf") or {}).items()}
    title = html_to_text((branch.get("title") or {}).get("rendered")) or acf.get("address_city", "")
    city = acf.get("address_city")
    link = branch.get("link")

    address = ", ".join(p for p in [
        acf.get("address_street"),
        " ".join(p for p in [acf.get("address_postcode"), f"гр. {city}" if city else ""] if p),
    ] if p)
    person, person_tel = acf.get("name_person_tel"), acf.get("tel_person")
    contact = " – ".join(p for p in [person, person_tel] if p)
    description = re.sub(r"\n{3,}", "\n\n", (acf.get("description") or "").replace("\r\n", "\n")).strip()

    lines = [
        title,
        f"Адрес: {address}" if address else "",
        f"Телефон: {acf['tel']}" if acf.get("tel") else "",
        f"Лице за контакт: {contact}" if contact else "",
        f"Имейл: {acf['email']}" if acf.get("email") else "",
        f"Google Maps: {acf['gbp_url']}" if acf.get("gbp_url") else "",
        description,
        f"Линк: {link}" if link else "",
    ]
    return Chunk(
        id=f"branch:{branch_id}",
        text=_join(lines),
        metadata=clean_meta({
            "type": "branch",
            "title": title,
            "city": city,
            "email": acf.get("email"),
            "phone": acf.get("tel"),
            "permalink": link,
        }),
    )

def _hard_split(text: str, limit: int) -> list[str]:
    """Split text longer than limit on whitespace (mid-word only as a last resort)."""
    parts = []
    while len(text) > limit:
        cut = text.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        parts.append(text)
    return parts

def split_chunk(chunk: Chunk, max_chars: int = MAX_CHARS) -> list[Chunk]:
    """Split a chunk into parts of at most max_chars, repeating the heading on each part."""
    if len(chunk.text) <= max_chars:
        return [chunk]

    heading, _, body = chunk.text.partition("\n")
    budget = max_chars - len(heading) - 2
    if budget <= 0:
        raise ValueError(f"Heading of {chunk.id} is longer than max_chars")

    sep = "\n\n" if "\n\n" in body else "\n"
    units: list[str] = []
    for para in body.strip().split(sep):
        para = para.strip()
        if para:
            units.extend(_hard_split(para, budget))

    parts: list[str] = []
    current = ""
    for unit in units:
        candidate = f"{current}{sep}{unit}" if current else unit
        if len(candidate) > budget:
            parts.append(current)
            current = unit
        else:
            current = candidate
    if current:
        parts.append(current)

    return [
        Chunk(
            id=f"{chunk.id}:{i}",
            text=f"{heading}\n\n{text}",
            metadata={**chunk.metadata, "parent_id": chunk.id},
        )
        for i, text in enumerate(parts)
    ]

def all_chunks() -> list[Chunk]:
    """Return all chunks from knowledge, catalog and branches."""
    chunks: list[Chunk] = []
    if KNOWLEDGE.exists():
        chunks.extend(chunk_knowledge(KNOWLEDGE.read_text(encoding="utf-8")))

    if CATALOG.exists():
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        categories = catalog.get("categories", [])
        names_by_id = {c["id"]: c["name"] for c in categories}
        chunks.extend(chunk_product(p) for p in catalog.get("products", []))
        chunks.extend(chunk_category(c, names_by_id) for c in categories)
        chunks.extend(chunk_service(s) for s in catalog.get("services", []))

    if BRANCHES.exists():
        branches = json.loads(BRANCHES.read_text(encoding="utf-8"))
        chunks.extend(chunk_branch(b) for b in branches)

    result: list[Chunk] = []
    for chunk in chunks:
        result.extend(split_chunk(chunk, max_chars=MAX_CHARS))
    return result
