from typing import TypedDict

from src.schemas import (
    Content,
    ContentVersion,
    ReviewDecision,
    StyleViolation,
)


class ApprovalState(TypedDict, total=False):
    brief: str

    current_content: Content | None

    retrieved_context: dict

    style_violations: list[StyleViolation]

    reviewer_decision: ReviewDecision | None

    reviewer_feedback: list[str]

    revision_count: int

    version_history: list[ContentVersion]

    current_version: int