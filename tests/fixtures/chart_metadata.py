from typing import Literal

import pytest

from helmupdater.chart import ChartMetadata


@pytest.fixture
def local_chart_metadata_for():
    local_charts = [
        {
            "chart": "nginx",
            "version": "1.0.0",
            "chartHash": "sha256-d0F6HCDggh3FWfR+LYim7iQr1E7X80Iwp8CCFRpZl3g=",
        },
        {
            "chart": "nginx",
            "version": "1.0.1",
            "chartHash": "sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY=",
        },
        {
            "chart": "podinfo",
            "version": "1.0.0",
            "chartHash": "sha256-xgHcBk8gDyemTiyncVrEUfvkzcxEfneqPlrQOnpQe7Y=",
        },
        {
            "chart": "podinfo",
            "version": "1.0.1",
            "chartHash": "sha256-J7vgcCue0nDvAgvUH8rKfqLv4qNYAZHESU/i2MyBhps=",
        },
    ]

    def _build_chart_metadata(
        name: str,
        version: str | None = None,
        repo_type: Literal["oci", "http"] = "http",
    ) -> ChartMetadata:
        chart_variants = [item for item in local_charts if item["chart"] == name]
        if version:
            data = next(
                (item for item in chart_variants if item["version"] == version), None
            )
        else:
            data = chart_variants[-1] if chart_variants else None

        if data is None:
            raise ValueError(f"Can't find requested local chart: {name} @ {version}")

        if repo_type == "http":
            data["repo"] = "http://localhost:45010"
        elif repo_type == "oci":
            data["repo"] = "oci://localhost:45020/charts"
        else:
            raise ValueError(f"Unknown repo type provided: {repo_type}")

        return ChartMetadata(**data)

    return _build_chart_metadata


@pytest.fixture
def chart_metadata(local_chart_metadata_for) -> ChartMetadata:
    return local_chart_metadata_for("nginx")


@pytest.fixture
def chart_metadata_dict(chart_metadata):
    return chart_metadata.model_dump()
