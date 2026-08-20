from src.agent.nodes import style_critic_node
from src.schemas import StyleViolation


class FakeCriticLLM:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        return self.response


def test_style_critic_detects_violation():
    llm = FakeCriticLLM(
        {
            "passed": False,
            "violations": [
                {
                    "rule": "Avoid exaggerated claims",
                    "explanation": "The draft makes an unsupported claim.",
                    "severity": "high",
                }
            ],
        }
    )

    state = {
        "current_content": {
            "title": "Amazing Phone",
            "body": "The best phone in the world.",
            "tags": ["phone"],
        },
        "retrieved_context": {
            "style_rules": [
                "Avoid exaggerated claims."
            ]
        },
    }

    # Convert current_content to Content because ApprovalState
    # expects a Content object.
    from src.schemas import Content

    state["current_content"] = Content.model_validate(
        state["current_content"]
    )

    result = style_critic_node(
        state,
        llm,
    )

    violations = result["style_violations"]

    assert len(violations) == 1
    assert isinstance(violations[0], StyleViolation)

    assert violations[0].rule == (
        "Avoid exaggerated claims"
    )

    assert violations[0].severity == "high"

    assert llm.calls == 1


def test_style_critic_passes_clean_content():
    llm = FakeCriticLLM(
        {
            "passed": True,
            "violations": [],
        }
    )

    from src.schemas import Content

    content = Content(
        title="Everyday Smartphone",
        body="A smartphone designed for everyday use.",
        tags=["phone"],
    )

    state = {
        "current_content": content,
        "retrieved_context": {
            "style_rules": [
                "Use clear and simple language."
            ]
        },
    }

    result = style_critic_node(
        state,
        llm,
    )

    assert result["style_violations"] == []
    assert llm.calls == 1


def test_style_critic_can_return_multiple_violations():
    llm = FakeCriticLLM(
        {
            "passed": False,
            "violations": [
                {
                    "rule": "No exaggerated claims",
                    "explanation": "Unsupported superlative.",
                    "severity": "high",
                },
                {
                    "rule": "Keep language concise",
                    "explanation": "The sentence is unnecessarily long.",
                    "severity": "medium",
                },
            ],
        }
    )

    from src.schemas import Content

    content = Content(
        title="Phone",
        body="This phone is absolutely the greatest phone ever made.",
        tags=["phone"],
    )

    state = {
        "current_content": content,
        "retrieved_context": {},
    }

    result = style_critic_node(
        state,
        llm,
    )

    violations = result["style_violations"]

    assert len(violations) == 2
    assert violations[0].severity == "high"
    assert violations[1].severity == "medium"