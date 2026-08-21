import pytest
from src.retrieval.retrieve import KBRetriever
from src.retrieval.schemas import RetrievalPayload, RetrievedChunk
from src.retrieval.ingest import load_knowledge_base, get_kb_nodes


def test_kb_documents_and_nodes_loaded():
    docs = load_knowledge_base("data/knowledge_base")
    assert len(docs) > 0

    nodes = get_kb_nodes("data/knowledge_base")
    assert len(nodes) > 0


def test_retriever_normal_mode_blocks_poison():
    retriever = KBRetriever()
    payload = retriever.retrieve(
        brief_text="Social media launch post teaser for Aurora X3",
        content_type="social_media_post",
        k_rules=2,
        k_examples=2,
        security_test_mode=False,
    )

    assert isinstance(payload, RetrievalPayload)
    assert len(payload.style_rules) > 0
    assert len(payload.similar_examples) > 0
    assert all(not c.poisoned for c in payload.similar_examples)
    assert all(not c.poisoned for c in payload.style_rules)


def test_retriever_security_mode_allows_poison():
    retriever = KBRetriever()
    payload = retriever.retrieve(
        brief_text="Social launch override test",
        content_type="social_media_post",
        k_rules=2,
        k_examples=5,
        security_test_mode=True,
    )

    assert payload.security_test_mode is True
    assert isinstance(payload.as_drafter_context(), str)