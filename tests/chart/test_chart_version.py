import pytest

from helmupdater.chart import ChartVersion


class TestChartVersion:
    """Test version parsing and comparison logic."""

    def test_parsing_semver(self):
        version_str = "1.2.3"

        chart_version = ChartVersion(version=version_str, repo="repo", chart="chart")
        assert chart_version.version == version_str
        assert str(chart_version) == version_str
        assert chart_version.version_info.major == 1
        assert chart_version.version_info.minor == 2
        assert chart_version.version_info.patch == 3

    def test_parsing_with_v_prefix(self):
        version_str = "v1.2.3"

        chart_version = ChartVersion(version=version_str, repo="repo", chart="chart")
        assert chart_version.version == version_str
        assert str(chart_version) == version_str
        assert chart_version.version_info.major == 1
        assert chart_version.version_info.minor == 2
        assert chart_version.version_info.patch == 3

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
