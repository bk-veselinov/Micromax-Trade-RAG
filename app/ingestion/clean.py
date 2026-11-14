"""Clean raw catalog records before chunking.

Phase 2.
"""
import re

from bs4 import BeautifulSoup

def inline(element: str | None) -> str:
    """Convert HTML to inline text, or return empty string if None."""
    if element is None:
        return ""
   
    soup = BeautifulSoup(element, "html.parser")
   
    return soup.get_text(separator=" ", strip=True)

def html_to_text(html: str | None) -> str:
    """Convert HTML to text, or return empty string if None."""
    if html is None:
        return ""
    
    soup = BeautifulSoup(html, "html.parser")

    for br in soup.find_all("br"):
        br.replace_with("\n")

    for tr in soup.find_all("tr"):
        cells = [inline(cell) for cell in tr.find_all(["td","th"])]
        sep = ": " if len(cells) == 2 else " | "
        tr.replace_with(f"\n{sep.join(cells)}\n")

    for li in soup.find_all("li"):
        li.replace_with(f"\n- {inline(li)}\n")

    for p in soup.find_all("p"):
        p.replace_with(f"\n{inline(p)}\n")

    for h in soup.find_all(["h1","h2","h3","h4","h5","h6"]):
        h.replace_with(f"\n### {inline(h)}\n")

    text = soup.get_text(separator="\n", strip=True)
    out: list[str] = []

    for line in text.splitlines():
        line = re.sub(r"[ \t\xa0]+", " ", line).strip()
        
        if not line:
            continue

        if line.startswith("### ") and out:
            out.append("")
        out.append(line)
    
    return "\n".join(out)

def variation_summary(variations: list[dict], max_values: int = 40) -> str:
    """Summarise variations by attribute values."""
    if not variations:
        return ""
    
    attr_values: dict[str, set[str]] = {}
    skus: list[str] = []

    for variation in variations:
        attributes = variation.get("attributes", [])
       
        for attr in attributes:
            name = attr.get("name")
            value = attr.get("option")
            if name and value:
                attr_values.setdefault(name, set()).add(value)

        if variation.get("sku"):
            skus.append(variation["sku"])

    lines: list[str] = []

    for name, values in attr_values.items():
        line = f"{name}: {', '.join(values[:max_values])}"
        if len(values) > max_values:
            line += f" ... {len(values) - max_values} още"
        lines.append(line)

    if skus:
        lines.append(f"Кодове на вариациите: {', '.join(skus)}")
    
    return "\n".join(lines)