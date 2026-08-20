from pathlib import Path
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


CHECKPOINT_DIR = Path("data")
CHECKPOINT_DB = CHECKPOINT_DIR / "workflow_checkpoints.sqlite"


def create_checkpointer() -> SqliteSaver:
    """
    Create a persistent SQLite checkpointer.

    The SQLite connection is kept open so the returned
    SqliteSaver can be passed directly to LangGraph.
    """

    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        str(CHECKPOINT_DB),
        check_same_thread=False,
    )

    checkpointer = SqliteSaver(
        connection
    )

    # Create the required checkpoint tables.
    checkpointer.setup()

    return checkpointer