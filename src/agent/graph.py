from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from src.agent.nodes import (
    MAX_REVISIONS,
    drafter_node,
    publisher_node,
    reviser_node,
    style_critic_node,
)
from src.agent.persistence import create_checkpointer
from src.agent.state import ApprovalState
from src.schemas import (
    Content,
    ContentStatus,
    ContentVersion,
    ReviewDecision,
    ReviewerDecision,
)


def human_review_node(state: ApprovalState) -> ApprovalState:
    """
    Pause the workflow and wait for human review.

    The reviewer can:
    - approve
    - reject
    - edit
    """

    content = state.get("current_content")

    if content is None:
        raise ValueError("No current content available for review.")

    review_request = {
        "content": content.model_dump(),
        "style_violations": [
            violation.model_dump()
            for violation in state.get("style_violations", [])
        ],
        "revision_count": state.get("revision_count", 0),
        "version": state.get("current_version", 1),
        "message": (
            "Review the content and choose "
            "approve, reject, or edit."
        ),
    }

    reviewer_result = interrupt(review_request)

    if not isinstance(reviewer_result, dict):
        raise ValueError("Invalid human review response.")

    decision = reviewer_result.get("decision")
    feedback = reviewer_result.get("feedback", [])

    if decision not in {
        ReviewerDecision.APPROVE.value,
        ReviewerDecision.REJECT.value,
        ReviewerDecision.EDIT.value,
    }:
        raise ValueError(
            "Decision must be approve, reject, or edit."
        )

    if isinstance(feedback, str):
        feedback = [feedback]

    if not isinstance(feedback, list):
        raise ValueError("Reviewer feedback must be a list.")

    edited_content = None

    if decision == ReviewerDecision.EDIT.value:
        edited_content_data = reviewer_result.get("edited_content")

        if not edited_content_data:
            raise ValueError(
                "Edited content is required when decision is edit."
            )

        edited_content = Content.model_validate(
            edited_content_data
        )

    review = ReviewDecision(
        decision=ReviewerDecision(decision),
        feedback=feedback,
        edited_content=edited_content,
    )

    return {
        **state,
        "reviewer_decision": review,
        "reviewer_feedback": feedback,
    }


def apply_edit_node(state: ApprovalState) -> ApprovalState:
    """
    Apply content directly edited by the human reviewer.
    """

    review = state.get("reviewer_decision")

    if review is None:
        raise ValueError("No reviewer decision available.")

    if review.decision != ReviewerDecision.EDIT:
        raise ValueError("Current decision is not edit.")

    if review.edited_content is None:
        raise ValueError("No edited content provided.")

    current_version = state.get("current_version", 1)
    new_version = current_version + 1

    edited_content = review.edited_content

    edited_content.status = ContentStatus.IN_REVIEW
    edited_content.revision_count = state.get(
        "revision_count",
        0,
    )

    history = list(
        state.get(
            "version_history",
            [],
        )
    )

    history.append(
        ContentVersion(
            version=new_version,
            content=edited_content,
            reason="Human reviewer edit",
        )
    )

    return {
        **state,
        "current_content": edited_content,
        "current_version": new_version,
        "version_history": history,
    }


def route_after_review(state: ApprovalState) -> str:
    """
    Decide where the workflow goes after human review.

    approve -> publish
    reject  -> revise
    edit    -> apply edit
    max revisions -> escalate
    """

    review = state.get("reviewer_decision")

    if review is None:
        raise ValueError(
            "No reviewer decision available."
        )

    if review.decision == ReviewerDecision.APPROVE:
        return "publish"

    if review.decision == ReviewerDecision.EDIT:
        return "edit"

    if review.decision == ReviewerDecision.REJECT:
        revision_count = state.get(
            "revision_count",
            0,
        )

        if revision_count >= MAX_REVISIONS:
            return "escalate"

        return "revise"

    raise ValueError("Unknown reviewer decision.")


def route_after_revision(state: ApprovalState) -> str:
    """
    Prevent infinite revision loops.
    """

    revision_count = state.get(
        "revision_count",
        0,
    )

    if revision_count >= MAX_REVISIONS:
        return "escalate"

    return "critic"


def escalation_node(state: ApprovalState) -> ApprovalState:
    """
    Stop the workflow when the maximum number
    of revisions has been reached.
    """

    content = state.get("current_content")

    if content is not None:
        content.status = ContentStatus.ESCALATED

    return {
        **state,
        "current_content": content,
    }


def build_graph(
    drafter_llm,
    critic_llm,
    reviser_llm,
):
    """
    Build and compile the complete approval workflow.

    LLMs are injected from outside so the graph
    remains easy to test and independent from
    a specific model provider.
    """

    graph = StateGraph(ApprovalState)

    # -------------------------
    # Nodes
    # -------------------------

    graph.add_node(
        "drafter",
        lambda state: drafter_node(
            state,
            drafter_llm,
        ),
    )

    graph.add_node(
        "style_critic",
        lambda state: style_critic_node(
            state,
            critic_llm,
        ),
    )

    graph.add_node(
        "human_review",
        human_review_node,
    )

    graph.add_node(
        "reviser",
        lambda state: reviser_node(
            state,
            reviser_llm,
        ),
    )

    graph.add_node(
        "apply_edit",
        apply_edit_node,
    )

    graph.add_node(
        "publisher",
        publisher_node,
    )

    graph.add_node(
        "escalate",
        escalation_node,
    )

    # -------------------------
    # Initial workflow
    # -------------------------

    graph.add_edge(
        START,
        "drafter",
    )

    graph.add_edge(
        "drafter",
        "style_critic",
    )

    graph.add_edge(
        "style_critic",
        "human_review",
    )

    # -------------------------
    # Human review routing
    # -------------------------

    graph.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "publish": "publisher",
            "revise": "reviser",
            "edit": "apply_edit",
            "escalate": "escalate",
        },
    )

    # -------------------------
    #human edit
    # -------------------------

    graph.add_edge(
        "apply_edit",
        "style_critic",
    )

    #revision routing

    graph.add_conditional_edges(
        "reviser",
        route_after_revision,
        {
            "critic": "style_critic",
            "escalate": "escalate",
        },
    )

    #end states
    graph.add_edge(
        "publisher",
        END,
    )

    graph.add_edge(
        "escalate",
        END,
    )
    #persistent checkpointing
    checkpointer = create_checkpointer()
    return graph.compile(
        checkpointer=checkpointer,
    )