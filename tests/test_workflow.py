from langgraph.types import Command

from src.agent.graph import (
    MAX_REVISIONS,
    build_graph,
)
from src.schemas import ContentStatus


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def invoke(self, prompt):
        if not self.responses:
            raise RuntimeError(
                "FakeLLM has no more responses."
            )

        response = self.responses.pop(0)
        self.calls += 1

        return response


def create_llms():
    drafter_llm = FakeLLM(
        [
            {
                "title": "Phone X",
                "body": "A modern smartphone for everyday use.",
                "tags": ["phone", "technology"],
            }
        ]
    )

    critic_llm = FakeLLM(
        [
            {
                "passed": True,
                "violations": [],
            },
            {
                "passed": True,
                "violations": [],
            },
        ]
    )

    reviser_llm = FakeLLM(
        [
            {
                "title": "Phone X Revised",
                "body": "A better smartphone for everyday life.",
                "tags": ["phone", "technology"],
            }
        ]
    )

    return (
        drafter_llm,
        critic_llm,
        reviser_llm,
    )


def create_config(thread_id):
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def test_workflow_approve_and_publish():
    (
        drafter_llm,
        critic_llm,
        reviser_llm,
    ) = create_llms()

    graph = build_graph(
        drafter_llm,
        critic_llm,
        reviser_llm,
    )

    config = create_config(
        "test-approve-workflow"
    )

    initial_state = {
        "brief": (
            "Create a short advertisement "
            "for a smartphone."
        ),
        "retrieved_context": {
            "style_rules": [
                "Use clear and simple language."
            ]
        },
    }

    result = graph.invoke(
        initial_state,
        config,
    )

    # The workflow must stop at human review.
    assert "__interrupt__" in result

    interrupt_data = result["__interrupt__"][0].value

    assert (
        interrupt_data["message"]
        == "Review the content and choose "
        "approve, reject, or edit."
    )

    # Resume with human approval.
    result = graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "feedback": [],
            }
        ),
        config,
    )

    content = result["current_content"]

    assert content.status == ContentStatus.APPROVED
    assert content.title == "Phone X"


def test_workflow_reject_then_revise_then_approve():
    (
        drafter_llm,
        critic_llm,
        reviser_llm,
    ) = create_llms()

    graph = build_graph(
        drafter_llm,
        critic_llm,
        reviser_llm,
    )

    config = create_config(
        "test-reject-revise-approve"
    )

    initial_state = {
        "brief": (
            "Create a short advertisement "
            "for a smartphone."
        ),
        "retrieved_context": {
            "style_rules": [
                "Use clear and simple language."
            ]
        },
    }

    # First run stops at human review.
    result = graph.invoke(
        initial_state,
        config,
    )

    assert "__interrupt__" in result

    # Human rejects the first draft.
    result = graph.invoke(
        Command(
            resume={
                "decision": "reject",
                "feedback": [
                    "Make the advertisement more engaging."
                ],
            }
        ),
        config,
    )

    # The graph should revise, run the critic again,
    # then stop at human review again.
    assert "__interrupt__" in result

    content = result["current_content"]

    assert content.title == "Phone X Revised"
    assert content.revision_count == 1

    assert result["current_version"] == 2

    assert len(result["version_history"]) == 2

    # Approve the revised version.
    result = graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "feedback": [],
            }
        ),
        config,
    )

    content = result["current_content"]

    assert content.status == ContentStatus.APPROVED
    assert content.title == "Phone X Revised"
    assert content.revision_count == 1


def test_workflow_human_edit():
    (
        drafter_llm,
        critic_llm,
        reviser_llm,
    ) = create_llms()

    graph = build_graph(
        drafter_llm,
        critic_llm,
        reviser_llm,
    )

    config = create_config(
        "test-human-edit"
    )

    initial_state = {
        "brief": "Create smartphone content.",
        "retrieved_context": {},
    }

    # Reach human review.
    result = graph.invoke(
        initial_state,
        config,
    )

    assert "__interrupt__" in result

    edited_content = {
        "title": "Human Edited Phone",
        "body": (
            "A smartphone edited and approved "
            "by the human reviewer."
        ),
        "tags": [
            "phone",
            "edited",
        ],
    }

    # Human chooses EDIT.
    result = graph.invoke(
        Command(
            resume={
                "decision": "edit",
                "feedback": [
                    "I changed the wording."
                ],
                "edited_content": edited_content,
            }
        ),
        config,
    )

    # apply_edit -> critic -> human review
    assert "__interrupt__" in result

    content = result["current_content"]

    assert content.title == "Human Edited Phone"

    assert content.body == (
        "A smartphone edited and approved "
        "by the human reviewer."
    )

    assert result["current_version"] == 2

    assert len(result["version_history"]) == 2

    # Approve the human-edited version.
    result = graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "feedback": [],
            }
        ),
        config,
    )

    content = result["current_content"]

    assert content.status == ContentStatus.APPROVED


def test_workflow_escalates_after_max_revisions():
    (
        drafter_llm,
        critic_llm,
        reviser_llm,
    ) = create_llms()

    graph = build_graph(
        drafter_llm,
        critic_llm,
        reviser_llm,
    )

    config = create_config(
        "test-max-revisions"
    )

    initial_state = {
        "brief": "Create smartphone content.",
        "retrieved_context": {},
    }

    # Start the workflow.
    result = graph.invoke(
        initial_state,
        config,
    )

    assert "__interrupt__" in result

    # Simulate a workflow that has already reached
    # the maximum revision count.
    checkpoint = graph.get_state(config)

    current_values = dict(checkpoint.values)

    current_values["revision_count"] = MAX_REVISIONS

    # Update the persisted state before continuing.
    graph.update_state(
        config,
        current_values,
    )

    # Reject the content at the maximum revision limit.
    result = graph.invoke(
        Command(
            resume={
                "decision": "reject",
                "feedback": [
                    "The content still needs changes."
                ],
            }
        ),
        config,
    )

    content = result["current_content"]

    assert content.status == ContentStatus.ESCALATED

    assert "__interrupt__" not in result