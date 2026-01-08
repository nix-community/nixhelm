"""
Integration tests for OCI registries.

Tests require the local registry to be running:
    tests/_infra/setup.sh
"""

import pytest

from helmupdater.registry import OCIRegistry

REGISTRY_URL = "oci://localhost:45020/charts"
REGISTRY_NAME = "local"


class TestOCIRegistry:
    """Test OCI registry with local instance."""

    @pytest.fixture(scope="class")
    def oci_registry(self):
        return OCIRegistry(REGISTRY_URL, REGISTRY_NAME, insecure=True)

    def test_initialization(self, oci_registry):
        assert isinstance(oci_registry, OCIRegistry)
        assert oci_registry.registry_type == "oci"

    @pytest.mark.e2e
    def test_get_versions_nginx(self, oci_registry):
        versions = oci_registry.get_versions("nginx")

        assert len(versions) >= 2

        version_strings = [v.version for v in versions]
        assert "1.0.0" in version_strings
        assert "1.0.1" in version_strings

    @pytest.mark.e2e
    def test_get_versions_podinfo(self, oci_registry):
        versions = oci_registry.get_versions("podinfo")

        assert len(versions) >= 2

        version_strings = [v.version for v in versions]
        assert "v1.0.0" in version_strings
        assert "v1.0.1" in version_strings

    @pytest.mark.e2e
    def test_get_versions_nonexistent(self, oci_registry):
        with pytest.raises(ValueError):
            oci_registry.get_versions("nonexistent")
