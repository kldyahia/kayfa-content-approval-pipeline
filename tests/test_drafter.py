from src.agent.nodes import (
    drafter_node,
    generate_content_with_repair,
)
from src.schemas import ContentStatus


class FakeLLM:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        return self.response


def test_drafter_creates_content():
    llm = FakeLLM(
        {
            "title": "New Smartphone",
            "body": "A modern smartphone for everyday use.",
            "tags": ["phone", "technology"],
        }
    )

    state = {
        "brief": "Create a short smartphone advertisement.",
        "retrieved_context": {
            "style": "Clear and simple marketing language."
        },
    }

    result = drafter_node(
        state,
        llm,
    )

    content = result["current_content"]

    assert content.title == "New Smartphone"
    assert content.body == (
        "A modern smartphone for everyday use."
    )
    assert content.tags == [
        "phone",
        "technology",
    ]

    assert content.status == ContentStatus.DRAFT
    assert content.revision_count == 0

    assert result["current_version"] == 1
    assert len(result["version_history"]) == 1


def test_drafter_repairs_missing_optional_fields():
    llm = FakeLLM(
        {
            "title": "Phone X",
            "body": "A powerful smartphone.",
        }
    )

    state = {
        "brief": "Write a smartphone description.",
        "retrieved_context": {},
    }

    result = drafter_node(
        state,
        llm,
    )

    content = result["current_content"]

    assert content.title == "Phone X"
    assert content.body == "A powerful smartphone."
    assert content.tags == []
    assert content.reviewer_feedback == []
    assert content.revision_count == 0


def test_repair_loop_accepts_valid_output():
    llm = FakeLLM(
        {
            "title": "Valid Content",
            "body": "This is valid content.",
        }
    )

    result = generate_content_with_repair(
        llm=llm,
        initial_prompt="Create content.",
    )

    assert result.title == "Valid Content"
    assert result.body == "This is valid content."

    assert llm.calls == 1


def test_repair_loop_fixes_malformed_output():
    class RepairLLM:
        def __init__(self):
            self.calls = 0

        def invoke(self, prompt):
            self.calls += 1

            if self.calls == 1:
                return {
                    "body": "Missing title"
                }

            return {
                "title": "Repaired Content",
                "body": "The repaired content.",
                "tags": ["test"],
            }

    llm = RepairLLM()

    result = generate_content_with_repair(
        llm=llm,
        initial_prompt="Create content.",
    )

    assert result.title == "Repaired Content"
    assert result.body == "The repaired content."
    assert result.tags == ["test"]

    assert llm.calls == 2