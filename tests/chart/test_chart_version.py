import pytest
from pydantic import ValidationError

from helmupdater.chart.chart_version import ChartVersion, parse_versions


class TestChartVersion:
    """Test version parsing and comparison logic."""

    def test_parsing_semver(self):
        version_str = "1.2.3"

        chart_version = ChartVersion(version=version_str, repo="repo", chart="chart")
        assert chart_version.version == version_str
        assert str(chart_version) == version_str
        assert chart_version.version_info.major == 1
        assert chart_version.version_info.minor == 2
        assert chart_version.version_info.micro == 3

    def test_parsing_with_v_prefix(self):
        version_str = "v1.2.3"

        chart_version = ChartVersion(version=version_str, repo="repo", chart="chart")
        assert chart_version.version == version_str
        assert str(chart_version) == version_str
        assert chart_version.version_info.major == 1
        assert chart_version.version_info.minor == 2
        assert chart_version.version_info.micro == 3

    def test_comparison_compatibility(self):
        nginx_version = ChartVersion(version="1.0.0", repo="repo", chart="nginx")
        podinfo_version = ChartVersion(version="1.0.0", repo="repo", chart="podinfo")
        with pytest.raises(ValueError):
            _ = nginx_version == podinfo_version

    def test_comparison(self):
        v1 = ChartVersion(version="1.0.0", repo="repo", chart="nginx")
        v2 = ChartVersion(version="1.2.0", repo="repo", chart="nginx")
        assert v2 > v1

    def test_sort(self):
        versions = [
            ChartVersion(version="1.0.0", repo="repo", chart="nginx"),
            ChartVersion(version="1.2.0", repo="repo", chart="nginx"),
            ChartVersion(version="v3.0.0", repo="repo", chart="nginx"),
            ChartVersion(version="v2.3.0", repo="repo", chart="nginx"),
        ]
        latest = max(versions)
        assert str(latest) == "v3.0.0"

    def test_odd_versions(self):
        def parsed_version(version: str):
            return ChartVersion(
                version=version, repo="repo", chart="nginx"
            ).version_info

        assert str(parsed_version("0.42.00")) == "0.42.0"

    def test_invalid_version(self):
        with pytest.raises(ValidationError):
            ChartVersion(version="invalid", repo="repo", chart="chart")

    def test_is_stable_for_stable_versions(self):
        """Stable versions should return True."""
        stable_versions = [
            ChartVersion(version="1.0.0", repo="repo", chart="nginx"),
            ChartVersion(version="2.3.4", repo="repo", chart="nginx"),
            ChartVersion(version="v1.0.0", repo="repo", chart="nginx"),
        ]
        for v in stable_versions:
            assert v.is_stable is True

    def test_is_stable_for_prereleases(self):
        """Prerelease versions should return False."""
        prerelease_versions = [
            ChartVersion(version="1.0.0-alpha", repo="repo", chart="nginx"),
            ChartVersion(version="1.0.0-beta.1", repo="repo", chart="nginx"),
            ChartVersion(version="1.0.0-rc1", repo="repo", chart="nginx"),
            ChartVersion(version="2.0.0-alpha.2", repo="repo", chart="nginx"),
        ]
        for v in prerelease_versions:
            assert v.is_stable is False

    def test_is_stable_for_dev_releases(self):
        """Dev releases should return False."""
        dev_versions = [
            ChartVersion(version="1.0.0.dev1", repo="repo", chart="nginx"),
            ChartVersion(version="1.0.0.dev20", repo="repo", chart="nginx"),
        ]
        for v in dev_versions:
            assert v.is_stable is False


class TestParseVersions:
    """Test parse_versions function."""

    def test_parse_empty_list(self):
        """Empty list should return empty list."""
        result = parse_versions([], repo_name="repo", chart_name="chart")
        assert result == []

    def test_parse_valid_versions(self):
        versions_raw = [
            "1.0.0",
            "v1.0.0",
            "1.1.0-alpha",
            "2.0.0",
            "2.1.0-beta",
            "3.0.0-dev1",
            "4.0.0rc1",
        ]
        result = parse_versions(versions_raw, repo_name="repo", chart_name="chart")
        assert len(result) == len(versions_raw)

    def test_parse_all_invalid_version(self):
        versions_raw = ["invalid1", "invalid2"]
        with pytest.raises(ValueError):
            parse_versions(versions_raw, repo_name="repo", chart_name="chart")

    def test_parse_skip_invalid_versions(self):
        versions_raw = ["invalid1", "1.0.0", "invalid2"]
        result = parse_versions(versions_raw, repo_name="repo", chart_name="chart")

        assert len(result) == 1
        assert result[0].version == "1.0.0"
