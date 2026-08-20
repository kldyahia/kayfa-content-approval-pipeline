from src.agent.graph import (
    MAX_REVISIONS,
    route_after_review,
    route_after_revision,
)
from src.schemas import (
    Content,
    ContentStatus,
    ReviewerDecision,
    ReviewDecision,
)


def create_review_state(
    decision,
    revision_count=0,
):
    content = Content(
        title="Test Content",
        body="Test body.",
        status=ContentStatus.DRAFT,
    )

    review = ReviewDecision(
        decision=decision,
        feedback=["Test feedback"],
    )

    return {
        "current_content": content,
        "reviewer_decision": review,
        "reviewer_feedback": [
            "Test feedback"
        ],
        "revision_count": revision_count,
        "current_version": 1,
        "version_history": [],
    }


def test_approve_routes_to_publish():
    state = create_review_state(
        ReviewerDecision.APPROVE
    )

    result = route_after_review(state)

    assert result == "publish"


def test_reject_routes_to_revise():
    state = create_review_state(
        ReviewerDecision.REJECT,
        revision_count=0,
    )

    result = route_after_review(state)

    assert result == "revise"


def test_edit_routes_to_edit():
    state = create_review_state(
        ReviewerDecision.EDIT
    )

    result = route_after_review(state)

    assert result == "edit"


def test_reject_at_max_revisions_routes_to_escalate():
    state = create_review_state(
        ReviewerDecision.REJECT,
        revision_count=MAX_REVISIONS,
    )

    result = route_after_review(state)

    assert result == "escalate"


def test_revision_under_limit_routes_to_critic():
    state = {
        "revision_count": 1,
    }

    result = route_after_revision(state)

    assert result == "critic"


def test_revision_at_limit_routes_to_escalate():
    state = {
        "revision_count": MAX_REVISIONS,
    }

    result = route_after_revision(state)

    assert result == "escalate"