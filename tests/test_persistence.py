from langgraph.types import Command

from src.agent.graph import build_graph
from src.agent.persistence import CHECKPOINT_DB


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)

    def invoke(self, prompt):
        return self.responses.pop(0)


def create_llms():
    drafter_llm = FakeLLM(
        [
            {
                "title": "Persistent Phone",
                "body": "A smartphone for everyday use.",
                "tags": ["phone"],
            }
        ]
    )

    critic_llm = FakeLLM(
        [
            {
                "passed": True,
                "violations": [],
            }
        ]
    )

    reviser_llm = FakeLLM([])

    return (
        drafter_llm,
        critic_llm,
        reviser_llm,
    )


def test_persistent_workflow_can_resume_after_interrupt():
    thread_id = "persistence-resume-test"

    (
        drafter_llm,
        critic_llm,
        reviser_llm,
    ) = create_llms()

    # First graph instance.
    graph1 = build_graph(
        drafter_llm,
        critic_llm,
        reviser_llm,
    )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    initial_state = {
        "brief": "Create smartphone content.",
        "retrieved_context": {
            "style_rules": [
                "Use clear and simple language."
            ]
        },
    }

    # Run until human review.
    result = graph1.invoke(
        initial_state,
        config,
    )

    assert "__interrupt__" in result

    # Confirm that a checkpoint exists.
    checkpoint = graph1.get_state(config)

    assert checkpoint.values
    assert checkpoint.next

    # Simulate application shutdown by creating
    # a completely new graph instance.
    (
        drafter_llm2,
        critic_llm2,
        reviser_llm2,
    ) = create_llms()

    graph2 = build_graph(
        drafter_llm2,
        critic_llm2,
        reviser_llm2,
    )

    # Resume the old workflow using the same thread_id.
    result = graph2.invoke(
        Command(
            resume={
                "decision": "approve",
                "feedback": [],
            }
        ),
        config,
    )

    content = result["current_content"]

    assert content.title == "Persistent Phone"

    assert content.status.value == "approved"

    # The workflow should be finished.
    assert result.get("__interrupt__") is None