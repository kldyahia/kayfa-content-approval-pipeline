from pathlib import Path

from src.schemas import Content, ContentStatus


PUBLISHED_DIR = Path("data") / "published"


def content_to_markdown(content: Content) -> str:
    """
    Convert approved content to Markdown format.
    """

    tags = ""

    if content.tags:
        tags = " ".join(
            f"`{tag}`"
            for tag in content.tags
        )

    markdown = f"""# {content.title}

{content.body}

"""

    if tags:
        markdown += f"**Tags:** {tags}\n"

    markdown += f"""
**Status:** {content.status.value}
**Revision:** {content.revision_count}
"""

    return markdown


def publish_content(
    content: Content,
    output_dir: Path = PUBLISHED_DIR,
) -> Path:
    """
    Export approved content as a Markdown file.
    """

    if content.status != ContentStatus.APPROVED:
        raise ValueError(
            "Only approved content can be published."
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_title = "".join(
        character
        if character.isalnum() or character in " -_"
        else "_"
        for character in content.title
    )

    safe_title = safe_title.strip().replace(" ", "_")

    if not safe_title:
        safe_title = "published_content"

    output_path = output_dir / f"{safe_title}.md"

    markdown = content_to_markdown(content)

    output_path.write_text(
        markdown,
        encoding="utf-8",
    )

    return output_path