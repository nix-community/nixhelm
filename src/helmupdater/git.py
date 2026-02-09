"""Git operations for helmupdater."""

from contextlib import contextmanager
from pathlib import Path

from helmupdater.logging import get_logger
from helmupdater.utils import run_cmd

log = get_logger()


def add_file(file_path: Path | str) -> None:
    """
    Stage a file for commit.

    Args:
        file_path: Path to file to stage

    Examples:
        >>> add_file("charts/local/nginx/default.nix")
    """
    run_cmd("git", "add", str(file_path))


def commit(message: str) -> None:
    """
    Create git commit with message.

    Args:
        message: Commit message

    Raises:
        CalledProcessError: If git commit fails

    Examples:
        >>> commit("local/nginx: update to 1.0.1")
    """
    run_cmd("git", "commit", "-m", message)


def add_and_commit(file_path: Path | str, message: str) -> None:
    """
    Stage and commit file in one operation.
    Only commits if file has changes.

    Args:
        file_path: Path to file to stage
        message: Commit message

    Raises:
        CalledProcessError: If git add or commit fails

    Examples:
        >>> add_and_commit(
        ...     "charts/local/nginx/default.nix",
        ...     "local/nginx: update to 1.0.1"
        ... )
    """
    if not has_changes(file_path):
        log.debug(f"no changes in file {file_path}")
        return
    add_file(file_path)
    commit(message)


def reset(file_path: Path | str | None = None) -> None:
    """
    Reset currently staged changes.

    Args:
        file_path: Optional path to specific file to unstage.
            If None, unstages all files.

    Examples:
        >>> reset()  # Unstage all files
        >>> reset("charts/local/nginx/default.nix")  # Unstage specific file
    """
    if file_path is None:
        run_cmd("git", "reset")
    else:
        run_cmd("git", "reset", str(file_path))


@contextmanager
def staged_file(file_path: Path | str):
    """
    Context manager to temporarily stage a file.

    Args:
        file_path: Path to file to stage

    Yields:
        Path to the staged file

    Examples:
        >>> with staged_file("charts/local/nginx/default.nix") as path:
        ...     # File is staged here
        ...     perform_operations()
        ...     # File is automatically unstaged after the block
    """
    add_file(file_path)
    try:
        yield file_path
    finally:
        reset(file_path)


def has_changes(file_path: Path | str) -> bool:
    """
    Check if file has unstaged changes.

    Args:
        file_path: Path to file to check

    Returns:
        True if file has changes, False otherwise

    Examples:
        >>> has_changes("charts/local/nginx/default.nix")
        True
    """
    result = run_cmd(
        "git", "status", "--porcelain", str(file_path)
    )
    return result.stdout.strip() != ""
