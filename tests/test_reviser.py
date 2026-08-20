from src.agent.nodes import reviser_node, MAX_REVISIONS
from src.schemas import (
    Content,
    ContentStatus,
    ContentVersion,
    ReviewerDecision,
    ReviewDecision,
)


class FakeLLM:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        return self.response


def create_state():
    content = Content(
        title="Old Phone",
        body="A basic smartphone.",
        tags=["phone"],
        status=ContentStatus.DRAFT,
        revision_count=0,
    )

    return {
        "brief": "Create a short smartphone advertisement.",
        "current_content": content,
        "retrieved_context": {
            "style_rules": [
                "Use clear and simple language."
            ]
        },
        "style_violations": [],
        "reviewer_decision": ReviewDecision(
            decision=ReviewerDecision.REJECT,
            feedback=["Make the message more engaging."],
        ),
        "reviewer_feedback": [
            "Make the message more engaging."
        ],
        "revision_count": 0,
        "current_version": 1,
        "version_history": [
            ContentVersion(
                version=1,
                content=content,
                reason="Initial draft",
            )
        ],
    }


def test_reviser_creates_new_version():
    llm = FakeLLM(
        {
            "title": "Better Phone",
            "body": "A modern smartphone made for everyday life.",
            "tags": ["phone", "technology"],
        }
    )

    state = create_state()

    result = reviser_node(
        state,
        llm,
    )

    content = result["current_content"]

    assert content.title == "Better Phone"

    assert content.body == (
        "A modern smartphone made for everyday life."
    )

    assert content.status == ContentStatus.REVISION_REQUIRED

    assert content.revision_count == 1

    assert result["revision_count"] == 1

    assert result["current_version"] == 2

    assert len(result["version_history"]) == 2


def test_reviser_preserves_reviewer_feedback():
    llm = FakeLLM(
        {
            "title": "Revised Phone",
            "body": "A better smartphone for daily use.",
            "tags": ["phone"],
        }
    )

    state = create_state()

    result = reviser_node(
        state,
        llm,
    )

    content = result["current_content"]

    assert content.reviewer_feedback == [
        "Make the message more engaging."
    ]

    assert result["reviewer_feedback"] == [
        "Make the message more engaging."
    ]


def test_reviser_adds_version_history_entry():
    llm = FakeLLM(
        {
            "title": "Version Two",
            "body": "Updated smartphone content.",
            "tags": ["phone"],
        }
    )

    state = create_state()

    result = reviser_node(
        state,
        llm,
    )

    history = result["version_history"]

    assert len(history) == 2

    assert history[0].version == 1
    assert history[0].reason == "Initial draft"

    assert history[1].version == 2
    assert history[1].reason == (
        "Reviewer feedback and style revision"
    )


def test_reviser_increments_revision_count_multiple_times():
    llm = FakeLLM(
        {
            "title": "Another Version",
            "body": "Another revised smartphone description.",
            "tags": ["phone"],
        }
    )

    state = create_state()

    state["revision_count"] = 1
    state["current_version"] = 2

    result = reviser_node(
        state,
        llm,
    )

    assert result["revision_count"] == 2
    assert result["current_version"] == 3


def test_reviser_stops_at_maximum_revisions():
    llm = FakeLLM(
        {
            "title": "Should Not Be Created",
            "body": "This revision should never be generated.",
            "tags": [],
        }
    )

    state = create_state()

    state["revision_count"] = MAX_REVISIONS

    try:
        reviser_node(
            state,
            llm,
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as error:
        assert "Maximum revision count reached" in str(error)

    assert llm.calls == 0