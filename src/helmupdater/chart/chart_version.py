# # Used for a forward reference in ChartVersion
from __future__ import annotations

from packaging.version import Version
from pydantic import BaseModel, ConfigDict, computed_field


class ChartVersion(BaseModel):
    """Information about a specific chart version from registry."""

    version: str
    repo: str
    chart: str

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    @computed_field
    @property
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
