"""Base registry interface for Helm chart registries."""

from typing import Protocol

from helmupdater.chart.chart_version import ChartVersion


class Registry(Protocol):
    """
    Protocol defining the interface for Helm chart registries.

    This protocol allows for different registry implementations (HTTP, OCI)
    while maintaining a consistent interface for chart operations.
    """

    def get_versions(self, chart_name: str) -> list[ChartVersion]:
        """
        Fetch all available versions for a chart.

        Args:
            chart_name: Name of the Helm chart

        Returns:
            List of available chart versions with metadata

        Raises:
            requests.exceptions.ConnectionError: If registry is unreachable
            ValueError: If chart is not found
        """
        ...

    @property
    def registry_type(self) -> str:
        """
        Return registry type identifier.

        Returns:
            Registry type ("http" or "oci")
        """
        ...

    @property
    def registry_url(self) -> str:
        """
        Return normalized URL for the registry
        """
        ...
