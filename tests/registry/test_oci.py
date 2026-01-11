"""
Integration tests for OCI registries.

Tests require the local registry to be running:
    tests/_infra/setup.sh
"""

from unittest.mock import patch

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

    @patch.object(OCIRegistry, "_fetch_raw_versions")
    def test_get_versions_filters_unstable(self, mock_fetch_raw_versions):
        """Test that get_versions returns only stable versions."""
        registry = OCIRegistry("oci://example.com/charts", "test")

        mixed_versions = [
            "1.0.0",
            "1.1.0-alpha",
            "1.2.0-beta.1",
            "2.0.0",
            "2.1.0-rc1",
            "3.0.0.dev1",
        ]
        mock_fetch_raw_versions.return_value = mixed_versions
        versions = registry.get_versions("testchart")

        assert len(versions) == 2
        version_strings = [v.version for v in versions]
        assert version_strings == ["1.0.0", "2.0.0"]
