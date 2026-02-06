"""Chart operations for version management and file I/O."""

from pathlib import Path

import chevron

from helmupdater import git, nix, registry
from helmupdater.logging import get_logger

from .chart_metadata import ChartMetadata
from .chart_version import ChartVersion

log = get_logger()

CHART_TEMPLATE = """{
  repo = "{{ repo }}";
  chart = "{{ chart }}";
  version = "{{ version }}";
  chartHash = "{{ hash }}";
}
"""

PLACEHOLDER_HASH = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
PLACEHOLDER_VERSION = "0.0.0"


def get_chart_path(repo_name: str, chart_name: str) -> Path:
    """
    Get path to chart's default.nix file.

    Args:
        repo_name: Repository name
        chart_name: Chart name

    Returns:
        Path to chart's default.nix file

    Examples:
        >>> get_chart_path("local", "nginx")
        PosixPath('charts/local/nginx/default.nix')
    """
    return Path.cwd() / "charts" / repo_name / chart_name / "default.nix"


def create_chart_directory(repo_name: str, chart_name: str) -> Path:
    """
    Create chart directory structure if it doesn't exist.

    Args:
        repo_name: Repository name
        chart_name: Chart name

    Returns:
        Path to created chart directory

    Examples:
        >>> create_chart_directory("local", "nginx")
        PosixPath('charts/local/nginx')
    """
    repo_dir = Path.cwd() / "charts" / repo_name
    repo_dir.mkdir(parents=True, exist_ok=True)

    chart_dir = repo_dir / chart_name
    chart_dir.mkdir(exist_ok=True)

    return chart_dir


def exists(repo_name: str, chart_name: str) -> bool:
    """
    Check if the provided chart exists.

    Args:
        repo_name: Repository name
        chart_name: Chart name

    Returns:
        True if chart exists, False otherwise.
    """
    return Path.exists(get_chart_path(repo_name, chart_name))


def write_chart_file(
    chart_path: Path | str,
    chart_info: ChartMetadata,
) -> None:
    """
    Write chart metadata to Nix file using template.

    Args:
        chart_path: Path to chart's default.nix file
        chart_info: Chart metadata dict

    Examples:
        >>> chart_info = {
        ...     "repo": "http://localhost:45010/",
        ...     "chart": "nginx",
        ...     "version": "1.0.0",
        ...     "chartHash": "sha256-abc123...",
        ... }
        >>> write_chart_file("charts/local/nginx/default.nix", chart_info)
    """
    chart_path = Path(chart_path)

    content = chevron.render(
        CHART_TEMPLATE,
        data=dict(
            repo=chart_info.repo,
            chart=chart_info.chart,
            version=chart_info.version,
            hash=chart_info.chartHash,
        ),
    )

    chart_path.write_text(content)


def create(
    repo_name: str,
    chart_name: str,
    repo_url: str | None = None,
    update_to_latest: bool = True,
    chart_info: ChartMetadata | None = None,
) -> ChartMetadata:
    """
    Create a new chart entry in the charts registry.

    If chart_info is provided, use provided metadata (repo, version, hash) to write
    chart definition. Otherwise if repo_url is provided add a dummy (version "0.0.0"
    and dummy hash).

    Args:
        repo_name: Repository name (e.g., "local")
        chart_name: Chart name (e.g., "nginx")
        repo_url: Repository URL (required if chart_info is not provided)
        update_to_latest: If True, update chart to latest version after creation
        chart_info: Pre-populated chart metadata (required if repo_url is not provided)

    Returns:
        ChartMetadata: The created (and possibly updated) chart metadata

    Examples:
        >>> create("local", "nginx", repo_url="http://localhost:45010/")
        ChartMetadata(repo='http://localhost:45010/', chart='nginx', ...)
    """

    if exists(repo_name, chart_name):
        raise ValueError(f"chart {repo_name}/{chart_name} already exists")

    chart_path = create_chart_directory(repo_name, chart_name) / "default.nix"

    if chart_info:
        write_chart_file(chart_path, chart_info)
    elif repo_url:
        chart_info = ChartMetadata(
            repo=repo_url,
            chart=chart_name,
            version=PLACEHOLDER_VERSION,
            chartHash=PLACEHOLDER_HASH,
        )
        write_chart_file(chart_path, chart_info)
    else:
        raise ValueError("either repo_url or chart_info should be specified")

    if update_to_latest:
        with git.staged_file(chart_path):
            try:
                chart_info = update(
                    repo_name,
                    chart_name,
                    chart_info=chart_info,
                )
            except Exception as e:
                log.warning(
                    f"{repo_name}/{chart_name}: "
                    "failed to update chart to latest version",
                    error=str(e),
                )

    return chart_info


def update(
    repo_name: str,
    chart_name: str,
    chart_info: ChartMetadata | None = None,
) -> ChartMetadata:
    """
    Update a single chart to the latest version.

    Args:
        repo_name: Repository name
        chart_name: Chart name
        chart_info: Current chart metadata

    Returns:
        ChartMetadata: The updated chart metadata
    """
    if not chart_info:
        chart_info = nix.get_chart(repo_name, chart_name)

    repo_url = chart_info.repo
    current_version = ChartVersion(
        version=chart_info.version, repo=repo_name, chart=chart_name
    )

    repo = registry.create(repo_url, repo_name)
    available_versions = repo.get_versions(chart_name)
    if len(available_versions) == 0:
        raise ValueError(f"No versions available for {repo_name}/{chart_name}.")

    latest_version = max(available_versions)

    if current_version == latest_version:
        return chart_info

    if current_version > latest_version:
        log.warning(f"{repo_name}/{chart_name}: performing version downgrade")

    log.info(
        f"{repo_name}/{chart_name}: updating chart version "
        f"{current_version} -> {latest_version}"
    )

    chart_path = get_chart_path(repo_name, chart_name)
    placeholder_chart_info = chart_info.model_copy(
        update={"version": latest_version.version, "chartHash": PLACEHOLDER_HASH}
    )
    write_chart_file(chart_path, placeholder_chart_info)
    updated_chart_info = rehash(repo_name, chart_name)

    return updated_chart_info


def rehash(
    repo_name: str,
    chart_name: str,
) -> ChartMetadata:
    """
    Recalculate and update the hash for an existing chart.

    This function triggers a Nix build with a placeholder hash to extract
    the correct hash from the build output, then updates the chart file
    with the correct hash value.

    Args:
        repo_name: Repository name
        chart_name: Chart name

    Returns:
        ChartMetadata: Updated chart metadata with correct hash

    Examples:
        >>> rehash("local", "nginx")
        ChartMetadata(repo='...', chart='nginx', version='1.0.0', chartHash='sha256-...'
        )
    """
    current_chart = nix.get_chart(repo_name, chart_name)
    correct_hash = nix.get_hash(repo_name, chart_name)

    corrected_chart = current_chart.model_copy(update={"chartHash": correct_hash})

    chart_path = get_chart_path(repo_name, chart_name)
    write_chart_file(chart_path, corrected_chart)

    return corrected_chart
