from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

@dataclass
class ParsedFile:
    metadata: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    source_path: str = ""

def parse_frontmatter(path: Path) -> ParsedFile:
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return ParsedFile(metadata={}, body=raw.strip(), source_path=str(path))
    meta_raw, body = match.groups()
    metadata = yaml.safe_load(meta_raw) or {}
    return ParsedFile(metadata=metadata, body=body.strip(), source_path=str(path))

def _normalize_metadata(meta: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    out = {**defaults, **meta}
    out["approved"] = "true" if bool(out.get("approved", True)) else "false"
    out["poisoned"] = "true" if bool(out.get("poisoned", False)) else "false"
    out.setdefault("content_type", "general")
    out.setdefault("doc_type", "unknown")
    tags = out.get("tags", [])
    if isinstance(tags, list):
        out["tags"] = ",".join(str(t) for t in tags)
    return out

def load_style_guide(path: Path) -> list[Document]:
    parsed = parse_frontmatter(path)
    base_meta = _normalize_metadata(
        parsed.metadata, defaults={"doc_type": "style_guide", "content_type": "general"}
    )
    sections = re.split(r"(?m)^(## .+)$", parsed.body)
    docs: list[Document] = []

    preamble = sections[0].strip()
    if preamble:
        docs.append(
            Document(
                text=preamble,
                metadata={
                    **base_meta,
                    "id": f"{base_meta.get('doc_id', 'style-guide')}::intro",
                    "section": "Introduction",
                    "source_file": parsed.source_path,
                },
            )
        )

    content_type_names = [
        "product launch", "feature announcement", "product campaign",
        "promotional email", "software update", "brand campaign", "social media post",
    ]

    for i in range(1, len(sections), 2):
        header = sections[i].strip().lstrip("#").strip()
        body = sections[i + 1].strip() if i + 1 < len(sections) else ""

        if header.lower() == "content-type rules":
            sub_parts = re.split(r"(?m)^(### .+)$", body)
            for j in range(1, len(sub_parts), 2):
                sub_header = sub_parts[j].strip().lstrip("#").strip()
                sub_body = sub_parts[j + 1].strip() if j + 1 < len(sub_parts) else ""
                sub_text = f"{sub_parts[j].strip()}\n\n{sub_body}".strip()
                sub_ct = next(
                    (ct.replace(" ", "_") for ct in content_type_names if ct in sub_header.lower()),
                    base_meta["content_type"],
                )
                docs.append(
                    Document(
                        text=sub_text,
                        metadata={
                            **base_meta,
                            "content_type": sub_ct,
                            "id": f"{base_meta.get('doc_id', 'style-guide')}::{sub_header}",
                            "section": f"{header} > {sub_header}",
                            "source_file": parsed.source_path,
                        },
                    )
                )
            continue

        text = f"{sections[i].strip()}\n\n{body}".strip()
        docs.append(
            Document(
                text=text,
                metadata={
                    **base_meta,
                    "id": f"{base_meta.get('doc_id', 'style-guide')}::{header}",
                    "section": header,
                    "source_file": parsed.source_path,
                },
            )
        )
    return docs

def load_flat_doc(path: Path, doc_type_default: str) -> Document:
    parsed = parse_frontmatter(path)
    meta = _normalize_metadata(parsed.metadata, defaults={"doc_type": doc_type_default})
    meta.setdefault("id", path.stem)
    meta["source_file"] = parsed.source_path
    return Document(text=parsed.body, metadata=meta)

def load_knowledge_base(kb_dir: str | Path) -> list[Document]:
    kb_dir = Path(kb_dir)
    docs: list[Document] = []

    style_guide_path = kb_dir / "brand_style_guide.md"
    if not style_guide_path.exists():
        style_guide_path = kb_dir / "style_guide.md"
    if style_guide_path.exists():
        docs.extend(load_style_guide(style_guide_path))

    examples_dir = kb_dir / "approved_examples"
    if not examples_dir.exists():
        examples_dir = kb_dir / "examples"
    if examples_dir.exists():
        for p in sorted(examples_dir.glob("*.md")):
            docs.append(load_flat_doc(p, doc_type_default="approved_example"))

    briefs_dir = kb_dir / "briefs"
    if briefs_dir.exists():
        for p in sorted(briefs_dir.glob("*.md")):
            docs.append(load_flat_doc(p, doc_type_default="brief"))

    return docs


def get_kb_nodes(kb_dir: str | Path, chunk_size: int = 512, chunk_overlap: int = 50) -> list[BaseNode]:
    docs = load_knowledge_base(kb_dir)
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    nodes = splitter.get_nodes_from_documents(docs)

    # Ensure chunk nodes retain original doc IDs for evaluation tracking
    for node in nodes:
        if "id" not in node.metadata and hasattr(node, "ref_doc_id"):
            node.metadata["id"] = node.ref_doc_id

    return nodes