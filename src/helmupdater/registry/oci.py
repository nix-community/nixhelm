"""OCI-compliant container registry for Helm charts."""

import signal
from contextlib import contextmanager
from urllib.parse import urlparse

from oras.client import OrasClient

from helmupdater.chart.chart_version import ChartVersion


@contextmanager
def _timeout(seconds: int = 5):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class OCIRegistry:
    """
    OCI-compliant container registry for Helm charts.

    Implements the OCI Distribution Spec for listing and accessing Helm charts
    stored in OCI registries like Docker Hub, GitHub Container Registry (ghcr.io),
    Google Artifact Registry, etc. Uses the ORAS Python library for robust
    authentication and registry interaction.

    References:
        - https://github.com/opencontainers/distribution-spec
        - https://helm.sh/docs/topics/registries/
        - https://oras-project.github.io/oras-py/
    """

    def __init__(
        self, registry_url: str, name: str, timeout: int = 5, **options
    ) -> None:
        """
        Initialize OCI registry.

        Args:
            registry_url: OCI registry URL (oci://registry.example.com/charts/mychart)
            name: Name of the registry
            **options: various options passed to an underlying client (Oras)

        Example:
            >>> registry = OCIRegistry("oci://ghcr.io/myorg/charts", "myorg")
        """
        self.name = name

        # Parse URL components
        parsed = urlparse(registry_url)
        self.registry_host = parsed.netloc
        self.repository_path = parsed.path.lstrip("/")
        self.base_url = parsed._replace(path=self.repository_path)
        self.timeout = timeout

        self.options = options

    def get_versions(self, chart_name: str) -> list[ChartVersion]:
        """
        List tags (versions) from OCI registry.

        Args:
            chart_name: Name of the Helm chart

        Returns:
            List of available chart versions

        Raises:
            ValueError: If request fails or chart is not found
        """

        # Re-initializing client here since with "token" auth it needs to retrieve new
        # token for each repository individually.
        registry_client = OrasClient(hostname=self.registry_host, **self.options)

        repository = f"{self.repository_path}/{chart_name}"
        # Oras does not expose retries/timeout settings. It also uses exponential
        # backoff. Hardcoding timeout wrapper to have at least some control over it.
        with _timeout(self.timeout):
            tags = registry_client.get_tags(repository)

        return [
            ChartVersion(version=tag, repo=self.name, chart=chart_name) for tag in tags
        ]

    @property
    def registry_type(self) -> str:
        """Return registry type identifier."""
        return "oci"

    @property
    def registry_url(self) -> str:
        """Return normalized URL for the registry."""
        return self.base_url.geturl()
