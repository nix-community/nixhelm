"""Command-line interface for helmupdater."""

import typer

from helmupdater import chart, git, nix, utils

app = typer.Typer(add_completion=False)


@app.command()
def init(
    repo_url: str,
    name: str,
    commit: bool = typer.Option(False),
) -> None:
    """
    Initialize a new chart in the repository.

    Args:
        repo_url: URL of the Helm repository
        name: Chart name in format "repo/chart"
        commit: Whether to create a git commit
    """
    repo_name, chart_name = utils.parse_chart_name(name)

    if chart.exists(repo_name, chart_name):
        print("chart already exists")
        exit(1)

    chart_info = chart.create(repo_name, chart_name, repo_url)

    if commit:
        git.add_and_commit(
            chart.get_chart_path(repo_name, chart_name),
            f"{repo_name}/{chart_name}: init at {chart_info.version}",
        )


@app.command()
def update(
    name: str,
    commit: bool = typer.Option(False),
    build: bool = typer.Option(False),
) -> None:
    """
    Update an existing chart version to latest.

    Args:
        name: Chart name in format "repo/chart"
        commit: Whether to create a git commit
        build: Whether to build a derivation with nix
    """

    repo_name, chart_name = utils.parse_chart_name(name)
    chart_info = chart.update(
        repo_name,
        chart_name,
    )
    if build:
        nix.build_chart(repo_name, chart_name)
    if commit:
        git.add_and_commit(
            chart.get_chart_path(repo_name, chart_name),
            f"{repo_name}/{chart_name}: update to {chart_info.version}",
        )


@app.command()
def update_all(
    commit: bool = typer.Option(False),
    build: bool = typer.Option(False),
) -> None:
    """
    Update all existing charts versions to latest.

    This sequentially updates every chart. If an error occurs while updating a chart,
    specific chart is skipped.

    Args:
        commit: Whether to create a git commit
        build: Whether to build a derivation with nix
    """

    charts = nix.get_charts()
    for repo_name, repo_charts in charts.items():
        for chart_name, current_chart_info in repo_charts.items():
            print(f"checking {repo_name}/{chart_name}")

            try:
                new_chart_info = chart.update(
                    repo_name,
                    chart_name,
                    chart_info=current_chart_info,
                )

                if build:
                    nix.build_chart(repo_name, chart_name)
                if commit:
                    git.add_and_commit(
                        chart.get_chart_path(repo_name, chart_name),
                        f"{repo_name}/{chart_name}: update to {new_chart_info.version}",
                    )

            except Exception as e:
                print(f"failed to update chart: {e}")


@app.command()
def rehash(
    name: str,
    commit: bool = typer.Option(False),
    build: bool = typer.Option(False),
) -> None:
    """
    Update a hash for an existing chart without changing the version.

    Args:
        name: Chart name in format "repo/chart"
        commit: Whether to create a git commit
        build: Whether to build a derivation with nix
    """

    repo_name, chart_name = utils.parse_chart_name(name)

    chart_info = chart.rehash(repo_name, chart_name)
    if build:
        nix.build_chart(repo_name, chart_name)
    if commit:
        git.add_and_commit(
            chart.get_chart_path(repo_name, chart_name),
            f"{repo_name}/{chart_name}: hash updated at {chart_info.version}",
        )


@app.command()
def build(name: str) -> None:
    """
    Build a nix derivation of an existing chart.

    Args:
        name: Chart name in format "repo/chart"
    """

    repo_name, chart_name = utils.parse_chart_name(name)
    nix.build_chart(repo_name, chart_name)
