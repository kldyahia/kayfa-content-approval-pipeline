from __future__ import annotations
from pathlib import Path
from llama_index.core.vector_stores import (
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from .index import load_index
from .logging_utils import log_retrieval
from .schemas import RetrievalPayload, RetrievedChunk

class KBRetriever:
    def __init__(
        self,
        chroma_dir: str | Path = "storage/chroma_db",
        log_path: str | Path = "logs/retrieval_log.jsonl"
    ):
        self.chroma_dir = chroma_dir
        self.log_path = log_path
        self._index = load_index(chroma_dir)

    def _filters(self, doc_type: str, content_type: str | None, exclude_poisoned: bool) -> MetadataFilters:
        filters = [MetadataFilter(key="doc_type", value=doc_type, operator=FilterOperator.EQ)]
        if content_type:
            filters.append(
                MetadataFilter(key="content_type", value=[content_type, "general"], operator=FilterOperator.IN)
            )
        if exclude_poisoned:
            filters.append(MetadataFilter(key="poisoned", value="false", operator=FilterOperator.EQ))
        return MetadataFilters(filters=filters, condition=FilterCondition.AND)

    def retrieve(
        self,
        brief_text: str,
        content_type: str,
        k_rules: int = 4,
        k_examples: int = 2,
        security_test_mode: bool = False,
    ) -> RetrievalPayload:
        exclude_poisoned = not security_test_mode

        rules_retriever = self._index.as_retriever(
            similarity_top_k=k_rules,
            filters=self._filters("style_guide", content_type, exclude_poisoned),
        )
        examples_retriever = self._index.as_retriever(
            similarity_top_k=k_examples,
            filters=self._filters("approved_example", content_type, exclude_poisoned),
        )

        rule_nodes = rules_retriever.retrieve(brief_text)
        example_nodes = examples_retriever.retrieve(brief_text)

        excluded_count = 0
        if exclude_poisoned:
            unfiltered = self._index.as_retriever(
                similarity_top_k=k_examples + 2,
                filters=self._filters("approved_example", content_type, exclude_poisoned=False),
            ).retrieve(brief_text)
            excluded_count = sum(1 for n in unfiltered if n.node.metadata.get("poisoned") == "true")

        def to_chunk(node) -> RetrievedChunk:
            m = node.node.metadata
            return RetrievedChunk(
                id=m.get("id", node.node.node_id),
                doc_type=m.get("doc_type", "approved_example"),
                content_type=m.get("content_type", "general"),
                section=m.get("section"),
                text=node.node.get_content(),
                score=float(node.score or 0.0),
                source_file=m.get("source_file", ""),
                poisoned=(m.get("poisoned") == "true"),
                approved=(m.get("approved", "true") == "true"),
            )

        payload = RetrievalPayload(
            query=brief_text,
            brief_content_type=content_type,
            style_rules=[to_chunk(n) for n in rule_nodes],
            similar_examples=[to_chunk(n) for n in example_nodes],
            excluded_poisoned_count=excluded_count,
            security_test_mode=security_test_mode,
        )
        log_retrieval(payload, self.log_path)
        return payload