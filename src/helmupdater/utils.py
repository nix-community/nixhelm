"""Utility functions for helmupdater."""

import subprocess


def run_cmd(
    *args: str,
    raise_on_error: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a subprocess command with consistent defaults.

    This function always captures output as text (stdout and stderr).

    Args:
        *args: Command and arguments to run
        raise_on_error: If True, raise CalledProcessError on non-zero exit

    Returns:
        CompletedProcess result with stdout and stderr as strings

    Raises:
        CalledProcessError: If raise_on_error=True and command fails

    Examples:
        >>> run_cmd("git", "status")
        CompletedProcess(...)

        >>> run_cmd("nix", "build", "...", raise_on_error=False)
        CompletedProcess(...)
    """
    return subprocess.run(
        args,
        check=raise_on_error,
        capture_output=True,
        text=True,
    )

def parse_chart_name(name: str) -> tuple[str, str]:
    """
    Parse chart name in format "repo/chart".

    Args:
        name: Chart name in format "repo/chart"

    Returns:
        Tuple of (repo_name, chart_name)

    Raises:
        ValueError: If name is not in expected format
    """
    parts = name.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid chart name format: '{name}'. Expected format: 'repo/chart'"
        )
    return parts[0], parts[1]
