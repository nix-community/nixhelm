"""HTTP-based Helm chart repository implementation."""

import requests
import yaml

from helmupdater.chart.chart_version import ChartVersion, parse_versions


class HTTPRegistry:
    """
    HTTP/HTTPS Helm chart repository (ChartMuseum style).

    This implements the standard Helm repository format using index.yaml
    for chart metadata and HTTP(S) URLs for chart downloads.
    """

    def __init__(self, base_url: str, name: str, timeout: int = 5) -> None:
        """
        Initialize HTTP registry.

        Args:
            base_url: Base URL of the Helm repository
            timeout: HTTP request timeout in seconds (default: 5)

        Examples:
            >>> registry = HTTPRegistry("https://prometheus-community.github.io/helm-charts")
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.name = name
        self.timeout = timeout

    def _fetch_raw_versions(self, chart_name: str) -> list[str]:
        """
        Fetch raw version strings from index.yaml.

        Args:
            chart_name: Name of the Helm chart

        Returns:
            List of raw version strings

        Raises:
            ValueError: If chart is not found in index.yaml
        """
        response = requests.get(
            f"{self.base_url}index.yaml",
            timeout=self.timeout,
        )
        response.encoding = "utf8"
        index = yaml.safe_load(response.text)

        chart_entries = index.get("entries", {}).get(chart_name)
        if chart_entries is None:
            raise ValueError(f"Chart {chart_name} is not found in the repo.")

        return [entry["version"] for entry in chart_entries]

    def get_versions(self, chart_name: str) -> list[ChartVersion]:
        """
        Fetch index.yaml and extract all versions for a chart.

        Args:
            chart_name: Name of the Helm chart

        Returns:
            List of available chart versions

        Raises:
            requests.exceptions.ConnectionError: If registry is unreachable
            ValueError: If chart is not found in index.yaml
            ValueError: If all version entries fail parsing
        """
        versions_raw = self._fetch_raw_versions(chart_name)
        versions = parse_versions(
            versions_raw,
            repo_name=self.name,
            chart_name=chart_name,
        )
        return [v for v in versions if v.is_stable]

    @property
    def registry_type(self) -> str:
        """Return registry type identifier."""
        return "http"

    @property
    def registry_url(self) -> str:
        return self.base_url
