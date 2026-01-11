# # Used for a forward reference in ChartVersion
from __future__ import annotations

from functools import cached_property

from packaging.version import InvalidVersion, Version
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    model_validator,
)


class ChartVersion(BaseModel):
    """Information about a specific chart version from registry."""

    version: str
    repo: str
    chart: str

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    @model_validator(mode="after")
    def validate_version_parsable(self) -> ChartVersion:
        """Validate that version can be parsed at instantiation time."""
        try:
            # Access version_info to trigger parsing validation
            _ = self.version_info
        except InvalidVersion as e:
            raise ValueError(
                f"Invalid version string '{self.version}' for chart "
                f"{self.repo}/{self.chart}"
            ) from e
        return self

    @cached_property
    def version_info(self) -> Version:
        """Parse the semantic version, handling optional 'v' prefix."""
        return Version(self.version)

    def _ensure_comparable(self, other: object) -> ChartVersion:
        if not isinstance(other, ChartVersion):
            raise TypeError(f"Cannot compare ChartVersion with {type(other).__name__}")

        if self.repo != other.repo or self.chart != other.chart:
            raise ValueError(
                f"Cannot compare versions from different charts: "
                f"{self.repo}/{self.chart} vs {other.repo}/{other.chart}"
            )

        return other

    def __eq__(self, other: object) -> bool:
        other = self._ensure_comparable(other)
        return self.version_info == other.version_info

    def __lt__(self, other: object) -> bool:
        other = self._ensure_comparable(other)
        return self.version_info < other.version_info

    def __le__(self, other: object) -> bool:
        other = self._ensure_comparable(other)
        return self.version_info <= other.version_info

    def __gt__(self, other: object) -> bool:
        other = self._ensure_comparable(other)
        return self.version_info > other.version_info

    def __ge__(self, other: object) -> bool:
        other = self._ensure_comparable(other)
        return self.version_info >= other.version_info

    def __str__(self) -> str:
        """Return string representation."""
        return self.version


def parse_versions(
    versions_raw: list,
    repo_name: str,
    chart_name: str,
) -> list[ChartVersion]:
    if not versions_raw:
        return []

    result: list[ChartVersion] = []
    for version_raw in versions_raw:
        try:
            chart_version = ChartVersion(
                version=version_raw, repo=repo_name, chart=chart_name
            )
            result.append(chart_version)
        except ValidationError:
            pass

    if len(result) == 0:
        raise ValueError(
            f"All version entries failed parsing for chart {repo_name}/{chart_name}."
        )

    return result
