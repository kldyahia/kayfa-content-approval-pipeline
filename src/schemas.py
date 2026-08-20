from enum import Enum

from pydantic import BaseModel, Field


class ContentStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    REVISION_REQUIRED = "revision_required"
    APPROVED = "approved"
    PUBLISHED = "published"
    ESCALATED = "escalated"


class ReviewerDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class Content(BaseModel):
    title: str
    body: str
    tags: list[str] = Field(default_factory=list)
    status: ContentStatus = ContentStatus.DRAFT
    revision_count: int = Field(default=0, ge=0)
    reviewer_feedback: list[str] = Field(default_factory=list)


class StyleViolation(BaseModel):
    rule: str
    explanation: str
    severity: str = "medium"


class CriticResult(BaseModel):
    passed: bool
    violations: list[StyleViolation] = Field(default_factory=list)


class ReviewDecision(BaseModel):
    decision: ReviewerDecision
    feedback: list[str] = Field(default_factory=list)
    edited_content: Content | None = None


class ContentVersion(BaseModel):
    version: int = Field(ge=1)
    content: Content
    reason: str = ""