from src.agent.prompts import (
    DRAFTER_SYSTEM_PROMPT,
    REVISER_SYSTEM_PROMPT,
    STYLE_CRITIC_SYSTEM_PROMPT,
)
from src.agent.state import ApprovalState
from src.schemas import (
    Content,
    ContentStatus,
    CriticResult,
    ContentVersion,
)


MAX_REVISIONS = 3
MAX_REPAIR_ATTEMPTS = 2


def build_drafter_prompt(
    brief: str,
    retrieved_context: dict,
) -> str:
    return f"""
{DRAFTER_SYSTEM_PROMPT}

USER BRIEF:
{brief}

RETRIEVED KNOWLEDGE:
{retrieved_context}

Create the requested content now.
Return only the structured content data.
"""


def build_critic_prompt(
    content: Content,
    retrieved_context: dict,
) -> str:
    return f"""
{STYLE_CRITIC_SYSTEM_PROMPT}

CURRENT CONTENT:
{content.model_dump()}

RETRIEVED STYLE KNOWLEDGE:
{retrieved_context}

Critique the current content.

Return:
- passed
- violations

Each violation must contain:
- rule
- explanation
- severity
"""


def build_reviser_prompt(
    brief: str,
    content: Content,
    retrieved_context: dict,
    violations: list,
    reviewer_feedback: list[str],
) -> str:
    return f"""
{REVISER_SYSTEM_PROMPT}

ORIGINAL BRIEF:
{brief}

CURRENT CONTENT:
{content.model_dump()}

RETRIEVED KNOWLEDGE:
{retrieved_context}

STYLE VIOLATIONS:
{violations}

HUMAN REVIEWER FEEDBACK:
{reviewer_feedback}

Create the revised content now.
Return only the structured content data.
"""


def build_repair_prompt(
    raw_output,
    validation_error: str,
) -> str:
    """
    Create a repair prompt when the model returns
    malformed or non-conforming structured output.
    """

    return f"""
The previous model output did not match the required Content schema.

PREVIOUS OUTPUT:
{raw_output}

VALIDATION ERROR:
{validation_error}

Repair the output.

The required fields are:
- title: string
- body: string
- tags: list of strings
- status: one of draft, in_review, revision_required,
  approved, published, escalated
- revision_count: non-negative integer
- reviewer_feedback: list of strings

Return ONLY valid structured Content data.
Do not add explanations.
"""


def repair_content_output(
    raw_output,
) -> Content:
    """
    Validate and normalize a raw model response into Content.

    This function performs the deterministic validation/repair
    part of the structured-output pipeline.

    LLM retry/repair is handled by generate_content_with_repair().
    """

    if isinstance(raw_output, Content):
        return raw_output

    if hasattr(raw_output, "model_dump"):
        raw_output = raw_output.model_dump()

    if not isinstance(raw_output, dict):
        raise ValueError(
            "Model output must be a dictionary or Content object."
        )

    repaired = dict(raw_output)

    # Required text fields
    if "title" not in repaired:
        raise ValueError(
            "Content output is missing the required 'title' field."
        )

    if "body" not in repaired:
        raise ValueError(
            "Content output is missing the required 'body' field."
        )

    # Normalize tags
    if "tags" not in repaired or repaired["tags"] is None:
        repaired["tags"] = []

    if isinstance(repaired["tags"], str):
        repaired["tags"] = [repaired["tags"]]

    # Normalize reviewer feedback
    if (
        "reviewer_feedback" not in repaired
        or repaired["reviewer_feedback"] is None
    ):
        repaired["reviewer_feedback"] = []

    if isinstance(repaired["reviewer_feedback"], str):
        repaired["reviewer_feedback"] = [
            repaired["reviewer_feedback"]
        ]

    # Defaults
    if "revision_count" not in repaired:
        repaired["revision_count"] = 0

    if "status" not in repaired:
        repaired["status"] = ContentStatus.DRAFT

    # Final Pydantic validation
    return Content.model_validate(repaired)


def generate_content_with_repair(
    llm,
    initial_prompt: str,
) -> Content:
    """
    Generate Content with a bounded validation-repair loop.

    Flow:

        LLM
         ↓
        Pydantic validation
         ↓
        invalid
         ↓
        repair prompt
         ↓
        LLM
         ↓
        Pydantic validation

    The loop is bounded by MAX_REPAIR_ATTEMPTS.
    """

    prompt = initial_prompt
    last_error = None
    raw_output = None

    for attempt in range(MAX_REPAIR_ATTEMPTS + 1):

        response = llm.invoke(prompt)
        raw_output = response

        try:
            return repair_content_output(response)

        except (ValueError, TypeError) as error:
            last_error = str(error)

            if attempt >= MAX_REPAIR_ATTEMPTS:
                break

            prompt = build_repair_prompt(
                raw_output=response,
                validation_error=last_error,
            )

    raise ValueError(
        "Unable to produce valid Content after "
        f"{MAX_REPAIR_ATTEMPTS + 1} attempts. "
        f"Last validation error: {last_error}"
    )


def drafter_node(
    state: ApprovalState,
    llm,
) -> ApprovalState:
    """
    Generate the initial structured Content draft.
    """

    brief = state.get("brief", "")
    retrieved_context = state.get(
        "retrieved_context",
        {},
    )

    prompt = build_drafter_prompt(
        brief=brief,
        retrieved_context=retrieved_context,
    )

    content = generate_content_with_repair(
        llm=llm,
        initial_prompt=prompt,
    )

    content.status = ContentStatus.DRAFT
    content.revision_count = 0
    content.reviewer_feedback = []

    return {
        **state,
        "current_content": content,
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


def style_critic_node(
    state: ApprovalState,
    llm,
) -> ApprovalState:
    """
    Check the current draft against the retrieved
    style knowledge.
    """

    content = state.get("current_content")

    if content is None:
        raise ValueError(
            "No current content available for style critic."
        )

    retrieved_context = state.get(
        "retrieved_context",
        {},
    )

    prompt = build_critic_prompt(
        content=content,
        retrieved_context=retrieved_context,
    )

    response = llm.invoke(prompt)

    if isinstance(response, CriticResult):
        result = response

    elif hasattr(response, "model_dump"):
        result = CriticResult.model_validate(
            response.model_dump()
        )

    elif isinstance(response, dict):
        result = CriticResult.model_validate(response)

    else:
        raise ValueError(
            "Style critic returned an invalid response."
        )

    return {
        **state,
        "style_violations": result.violations,
    }


def reviser_node(
    state: ApprovalState,
    llm,
) -> ApprovalState:
    """
    Create a new content version using:
    - original brief
    - retrieved knowledge
    - style violations
    - human reviewer feedback
    """

    content = state.get("current_content")

    if content is None:
        raise ValueError(
            "No current content available for revision."
        )

    revision_count = state.get(
        "revision_count",
        0,
    )

    if revision_count >= MAX_REVISIONS:
        raise RuntimeError(
            "Maximum revision count reached."
        )

    brief = state.get(
        "brief",
        "",
    )

    retrieved_context = state.get(
        "retrieved_context",
        {},
    )

    violations = state.get(
        "style_violations",
        [],
    )

    reviewer_feedback = state.get(
        "reviewer_feedback",
        [],
    )

    prompt = build_reviser_prompt(
        brief=brief,
        content=content,
        retrieved_context=retrieved_context,
        violations=violations,
        reviewer_feedback=reviewer_feedback,
    )

    revised_content = generate_content_with_repair(
        llm=llm,
        initial_prompt=prompt,
    )

    new_revision_count = revision_count + 1
    new_version = (
        state.get(
            "current_version",
            1,
        )
        + 1
    )

    revised_content.status = (
        ContentStatus.REVISION_REQUIRED
    )

    revised_content.revision_count = (
        new_revision_count
    )

    revised_content.reviewer_feedback = (
        reviewer_feedback
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
            content=revised_content,
            reason=(
                "Reviewer feedback and "
                "style revision"
            ),
        )
    )

    return {
        **state,
        "current_content": revised_content,
        "revision_count": new_revision_count,
        "current_version": new_version,
        "version_history": history,
    }


def publisher_node(
    state: ApprovalState,
) -> ApprovalState:
    """
    Mark the current content as approved.

    Actual Markdown file export is handled by
    src.agent.publisher.publish_content().
    """

    content = state.get("current_content")

    if content is None:
        raise ValueError(
            "No content available for publishing."
        )

    content.status = ContentStatus.APPROVED

    return {
        **state,
        "current_content": content,
    }