from __future__ import annotations
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schemas import RetrievalPayload

DEFAULT_LOG_PATH = Path("logs/retrieval_log.jsonl")

def log_retrieval(payload: "RetrievalPayload", log_path: str | Path = DEFAULT_LOG_PATH) -> None:
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "retrieved_at": payload.retrieved_at,
        "query": payload.query,
        "brief_content_type": payload.brief_content_type,
        "security_test_mode": payload.security_test_mode,
        "excluded_poisoned_count": payload.excluded_poisoned_count,
        "style_rules": [
            {"id": c.id, "section": c.section, "score": round(c.score, 4)} for c in payload.style_rules
        ],
        "similar_examples": [
            {"id": c.id, "content_type": c.content_type, "score": round(c.score, 4), "poisoned": c.poisoned}
            for c in payload.similar_examples
        ],
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")