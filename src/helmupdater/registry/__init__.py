"""Registry module for Helm chart repository abstractions."""

from urllib.parse import urlparse

from .base import Registry
from .http import HTTPRegistry
from .oci import OCIRegistry

__all__ = ["Registry", "HTTPRegistry", "OCIRegistry", "create"]


def create(url: str, name: str, **kwargs) -> Registry:
    """
    Create appropriate registry instance based on URL scheme.

    Args:
        url: Repository URL (http://, https://, or oci://)
        name: Repository name (e.g. "local")
        **kwargs: Additional arguments passed to registry constructor

    Returns:
        Registry instance (HTTPRegistry or OCIRegistry)

    Raises:
        ValueError: If URL scheme is not supported

    Examples:
        >>> registry = create_registry("https://prometheus-community.github.io/helm-charts")
        >>> isinstance(registry, HTTPRegistry)
        True

        >>> registry = create_registry("oci://ghcr.io/prometheus-community/charts")
        >>> registry.registry_type
        'oci'
    """
    parsed = urlparse(url)

    if parsed.scheme == "oci":
        return OCIRegistry(url, name, **kwargs)
    elif parsed.scheme in ("http", "https"):
        return HTTPRegistry(url, name, **kwargs)
    else:
        raise ValueError(f"Unsupported registry scheme: {parsed.scheme}")
