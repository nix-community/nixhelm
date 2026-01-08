import pytest

from helmupdater.registry import HTTPRegistry, OCIRegistry, create


class TestRegistryFactory:
    def test_http_scheme(self):
        registry = create("http://localhost:45010", "local")
        assert isinstance(registry, HTTPRegistry)

    def test_https_scheme(self):
        registry = create("https://localhost:45010", "local")
        assert isinstance(registry, HTTPRegistry)

    def test_oci_scheme(self):
        registry = create("oci://localhost:45020/charts", "local")
        assert isinstance(registry, OCIRegistry)

    def test_missing_scheme(self):
        with pytest.raises(ValueError, match="Unsupported registry scheme"):
            create("charts.example.com", "local")

    def test_invalid_scheme(self):
        with pytest.raises(ValueError, match="Unsupported registry scheme"):
            create("ftp://charts.example.com", "local")
