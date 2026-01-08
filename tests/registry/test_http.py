"""
Integration tests for HTTP registries.

Tests require the local registry to be running:
    tests/_infra/setup.sh
"""

import pytest

from helmupdater.registry import HTTPRegistry

REGISTRY_URL = "http://localhost:45010/"
REGISTRY_NAME = "local"


class TestHTTPRegistry:
    """Test HTTP registry with local instance."""

    @pytest.fixture(scope="class")
    def http_registry(self):
        return HTTPRegistry(REGISTRY_URL, REGISTRY_NAME)

    def test_initialization(self, http_registry):
        assert isinstance(http_registry, HTTPRegistry)
        assert http_registry.registry_type == "http"

    @pytest.mark.e2e
    def test_get_versions_nginx(self, http_registry):
        versions = http_registry.get_versions("nginx")

        assert len(versions) >= 2

        version_strings = [v.version for v in versions]
        assert "1.0.0" in version_strings
        assert "1.0.1" in version_strings

    @pytest.mark.e2e
    def test_get_versions_podinfo(self, http_registry):
        versions = http_registry.get_versions("podinfo")

        assert len(versions) >= 2

        version_strings = [v.version for v in versions]
        assert "v1.0.0" in version_strings
        assert "v1.0.1" in version_strings

    @pytest.mark.e2e
    def test_get_versions_nonexistent(self, http_registry):
        with pytest.raises(ValueError):
            http_registry.get_versions("nonexistent")
