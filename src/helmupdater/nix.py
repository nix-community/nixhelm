"""Nix operations for helmupdater."""

import functools
import json
import re
from subprocess import CompletedProcess

from helmupdater.chart.chart_metadata import ChartMetadata
from helmupdater.utils import run_cmd


@functools.cache
def current_system() -> str:
    """
    Get current Nix system architecture.

    Returns:
        System string (e.g., "x86_64-linux", "aarch64-darwin")

    Examples:
        >>> current_system()
        'aarch64-darwin'
    """
    result = run_cmd(
        "nix",
        "eval",
        "--impure",
        "--expr",
        "builtins.currentSystem",
    )
    # Strip quotes and whitespace from output like '"aarch64-darwin"\n'
    return result.stdout.strip().strip('"')


def build_chart(
    repo_name: str, chart_name: str, raise_on_error: bool = True
) -> CompletedProcess[str]:
    """
    Build Nix derivation for a Helm chart.

    Args:
        repo_name: Repository name
        chart_name: Chart name
        raise_on_error: If True, raise CalledProcessError on non-zero exit

    Returns:
        CompletedProcess with stdout and stderr

    Examples:
        >>> result = build_chart("local", "nginx", raise_on_error=False)
        >>> result.returncode
        1
    """
    return run_cmd(
        "nix",
        "build",
        f".#chartsDerivations.{current_system()}.{repo_name}.{chart_name}",
        raise_on_error=raise_on_error,
    )


def get_hash(repo_name: str, chart_name: str) -> str:
    """
    Extract correct hash from failed Nix build output.

    Args:
        repo_name: Repository name
        chart_name: Chart name

    Returns:
        SHA256 hash string (e.g., "sha256-abc123...")

    Raises:
        RuntimeError: If hash cannot be extracted from build output

    Examples:
        >>> get_hash("local", "nginx")
        "sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY="
    """
    build_result = build_chart(repo_name, chart_name, raise_on_error=False)

    # if build succeeded, look up derivation hash
    if build_result.returncode == 0:
        return get_hash_derivation(repo_name, chart_name)

    # Build failed, most likely due to hash mismatch.
    # Get a correct hash from the error message
    hash_value = _parse_build_mismatch_hash(build_result.stderr)
    if hash_value is None:
        raise RuntimeError(
            f"Failed to extract hash for {repo_name}/{chart_name}:\n"
            f"{build_result.stderr}"
        )

    return hash_value


def _parse_build_mismatch_hash(output: str) -> str | None:
    # ruff: disable[E501]
    # Error message looks like this:
    #
    # ❌ git+file:///.../src/nixhelm#chartsDerivations.aarch64-darwin.local.nginx
    # error: hash mismatch in fixed-output derivation \
    #   '/nix/store/2r72dg8...-nginx-1.0.1.drv':
    #          specified: sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
    #             got:    sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY=
    # ruff: enable[E501]
    if "hash mismatch" in output:
        match = re.search(r"got:\s+(?P<hash>sha256-\S+)", output)
        if match:
            hash_value = match.group("hash")
            return hash_value

    return None


def get_hash_derivation(repo_name: str, chart_name: str) -> str:
    result = run_cmd(
        "nix",
        "derivation",
        "show",
        f".#chartsDerivations.{current_system()}.{repo_name}.{chart_name}",
    )
    # Data structure with version:4 looks like this (trimmed for brevity):
    # {
    #   "derivations": {
    #     "bs30...-helm-chart-http-localhost-45010--nginx-1.0.1.drv": {
    #       ...
    #       "outputs": {
    #         "out": {
    #           "hash": "sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY=",
    #           ...
    data = json.loads(result.stdout)
    hash_value = list(data["derivations"].values())[0]["outputs"]["out"]["hash"]
    return hash_value


def get_charts() -> dict[str, dict[str, ChartMetadata]]:
    """
    Evaluate and return all chart metadata from Nix.

    Returns:
        Nested dict structure: {repo_name: {chart_name: ChartMetadata}}

    Examples:
        >>> charts = get_charts()
        >>> charts["local"]["nginx"]["version"]
        '1.0.0'
    """
    result = run_cmd(
        "nix",
        "eval",
        ".#chartsMetadata",
        "--json",
    )

    data = json.loads(result.stdout)
    return {
        repo_name: {
            chart_name: ChartMetadata(**chart_info)
            for chart_name, chart_info in repo_charts.items()
        }
        for repo_name, repo_charts in data.items()
    }


def get_chart(repo_name: str, chart_name: str) -> ChartMetadata:
    """
    Evaluate and return specific chart metadata from Nix.

    Returns:
        ChartMetadata
    """
    result = run_cmd(
        "nix",
        "eval",
        f".#chartsMetadata.{repo_name}.{chart_name}",
        "--json",
    )
    data = json.loads(result.stdout)
    return ChartMetadata(**data)
