from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from helmupdater import chart


def _write_chart_file(
    tmp_path: Path,
    chart_info: chart.ChartMetadata,
    repo_name: str = "local",
    chart_name: str = "nginx",
) -> Path:
    """Helper method to create nix module file for a given chart metadata."""

    chart_path = tmp_path / "charts" / repo_name / chart_name / "default.nix"
    chart_path.parent.mkdir(parents=True)
    chart_path.touch()
    chart.write_chart_file(chart_path, chart_info)

    return chart_path

class TestChartUtils:
    def test_get_chart_path(self):
        result = chart.get_chart_path("local", "nginx")
        expected = Path.cwd() / "charts" / "local" / "nginx" / "default.nix"
        assert result == expected

    def test_create_chart_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        result = chart.create_chart_directory("local", "nginx")
        expected = tmp_path / "charts" / "local" / "nginx"

        assert result == expected
        assert result.exists()
        assert result.is_dir()

    def test_create_chart_directory_existing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        expected = tmp_path / "charts" / "local" / "nginx"
        expected.mkdir(parents=True)

        result = chart.create_chart_directory("local", "nginx")
        assert result.exists()

    def test_exists_returns_true(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        chart_path = tmp_path / "charts" / "local" / "nginx" / "default.nix"
        chart_path.parent.mkdir(parents=True)
        chart_path.touch()

        assert chart.exists("local", "nginx") is True
        assert chart.exists("unknown", "unknown") is False

    def test_write_chart_file(self, tmp_path, chart_metadata):
        chart_path = tmp_path / "default.nix"

        chart.write_chart_file(chart_path, chart_metadata)

        assert chart_path.exists()
        content = chart_path.read_text()
        assert f'repo = "{chart_metadata.repo}";' in content
        assert f'chart = "{chart_metadata.chart}";' in content
        assert f'version = "{chart_metadata.version}";' in content
        assert f'chartHash = "{chart_metadata.chartHash}";' in content

    def test_write_chart_file_existing(self, tmp_path, chart_metadata):
        chart_path = tmp_path / "default.nix"
        chart_path.write_text("old content")

        chart.write_chart_file(chart_path, chart_metadata)

        content = chart_path.read_text()
        assert "old content" not in content
        assert f'repo = "{chart_metadata.repo}";' in content


class TestChartCreate:
    def test_create_no_update(self, tmp_path, monkeypatch, chart_metadata):
        monkeypatch.chdir(tmp_path)

        result = chart.create(
            "local",
            chart_metadata.chart,
            chart_metadata.repo,
            update_to_latest=False,
        )

        assert result.repo == chart_metadata.repo
        assert result.chart == chart_metadata.chart
        assert result.version == chart.PLACEHOLDER_VERSION
        assert result.chartHash == chart.PLACEHOLDER_HASH

        chart_path = (
            tmp_path / "charts" / "local" / chart_metadata.chart / "default.nix"
        )
        assert chart_path.exists()

    def test_create_with_metadata_no_update(
        self, tmp_path, monkeypatch, chart_metadata
    ):
        monkeypatch.chdir(tmp_path)

        result = chart.create(
            "local",
            chart_metadata.chart,
            chart_info=chart_metadata,
            update_to_latest=False,
        )

        assert result == chart_metadata

        chart_path = (
            tmp_path / "charts" / "local" / chart_metadata.chart / "default.nix"
        )
        assert chart_path.exists()

    def test_create_conflict(self, tmp_path, monkeypatch, chart_metadata):
        monkeypatch.chdir(tmp_path)

        chart_path = (
            tmp_path / "charts" / "local" / chart_metadata.chart / "default.nix"
        )
        chart_path.parent.mkdir(parents=True)
        chart_path.touch()

        with pytest.raises(ValueError, match="already exists"):
            chart.create(
                "local",
                chart_metadata.chart,
                chart_info=chart_metadata,
                update_to_latest=False,
            )

    @patch("helmupdater.chart.update")
    @patch("helmupdater.chart.git.staged_file")
    def test_create_with_update_to_latest(
        self,
        mock_staged_file,
        mock_update,
        tmp_path,
        monkeypatch,
        local_chart_metadata_for,
    ):
        monkeypatch.chdir(tmp_path)

        mock_staged_file.return_value.__enter__ = MagicMock()
        mock_staged_file.return_value.__exit__ = MagicMock()

        old_chart_metadata = local_chart_metadata_for("nginx", "1.0.0")
        new_chart_metadata = local_chart_metadata_for("nginx", "1.0.1")

        mock_update.return_value = new_chart_metadata

        result = chart.create(
            "local",
            old_chart_metadata.chart,
            chart_info=old_chart_metadata,
            update_to_latest=True,
        )

        assert result == new_chart_metadata
        mock_update.assert_called_once()

    @patch("helmupdater.chart.update")
    @patch("helmupdater.chart.git.staged_file")
    def test_create_with_update_to_latest_failed(
        self,
        mock_staged_file,
        mock_update,
        tmp_path,
        monkeypatch,
        capsys,
        chart_metadata,
    ):
        monkeypatch.chdir(tmp_path)

        mock_staged_file.return_value.__enter__ = MagicMock()
        mock_staged_file.return_value.__exit__ = MagicMock()
        mock_update.side_effect = Exception("Update failed")

        result = chart.create(
            "local",
            chart_metadata.chart,
            chart_info=chart_metadata,
            update_to_latest=True,
        )

        assert result == chart_metadata
        captured = capsys.readouterr()
        assert "Failed to update chart" in captured.out


class TestChartUpdate:
    @patch("helmupdater.chart.nix.get_chart")
    @patch("helmupdater.chart.registry.create")
    @patch("helmupdater.chart.rehash")
    def test_update(
        self,
        mock_rehash,
        mock_registry_create,
        mock_get_chart,
        tmp_path,
        monkeypatch,
        local_chart_metadata_for,
    ):
        monkeypatch.chdir(tmp_path)

        old_chart_metadata = local_chart_metadata_for("nginx", "1.0.0")
        new_chart_metadata = local_chart_metadata_for("nginx", "1.0.1")

        _write_chart_file(tmp_path, old_chart_metadata)

        mock_get_chart.return_value = old_chart_metadata

        mock_repo = MagicMock()
        mock_repo.get_versions.return_value = [
            chart.ChartVersion(version="1.0.0", repo="local", chart="nginx"),
            chart.ChartVersion(version="1.0.1", repo="local", chart="nginx"),
        ]
        mock_registry_create.return_value = mock_repo
        mock_rehash.return_value = new_chart_metadata

        result = chart.update("local", "nginx")

        assert result == new_chart_metadata
        mock_get_chart.assert_called_once()
        mock_rehash.assert_called_once()

    @patch("helmupdater.chart.nix.get_chart")
    @patch("helmupdater.chart.registry.create")
    @patch("helmupdater.chart.rehash")
    def test_update_with_metadata(
        self,
        mock_rehash,
        mock_registry_create,
        mock_get_chart,
        tmp_path,
        monkeypatch,
        local_chart_metadata_for,
    ):
        monkeypatch.chdir(tmp_path)

        old_chart_metadata = local_chart_metadata_for("nginx", "1.0.0")
        new_chart_metadata = local_chart_metadata_for("nginx", "1.0.1")

        _write_chart_file(tmp_path, old_chart_metadata)

        mock_repo = MagicMock()
        mock_repo.get_versions.return_value = [
            chart.ChartVersion(version="1.0.0", repo="local", chart="nginx"),
            chart.ChartVersion(version="1.0.1", repo="local", chart="nginx"),
        ]
        mock_registry_create.return_value = mock_repo
        mock_rehash.return_value = new_chart_metadata

        result = chart.update("local", "nginx", chart_info=old_chart_metadata)

        assert result == new_chart_metadata
        mock_get_chart.assert_not_called()
        mock_rehash.assert_called_once()


    @patch("helmupdater.chart.nix.get_chart")
    @patch("helmupdater.chart.registry.create")
    @patch("helmupdater.chart.rehash")
    def test_update_already_latest_version(
        self,
        mock_rehash,
        mock_registry_create,
        mock_get_chart,
        tmp_path,
        monkeypatch,
        local_chart_metadata_for,
    ):
        monkeypatch.chdir(tmp_path)

        chart_metadata = local_chart_metadata_for("nginx", "1.0.0")
        _write_chart_file(tmp_path, chart_metadata)

        mock_repo = MagicMock()
        mock_repo.get_versions.return_value = [
            chart.ChartVersion(version="1.0.0", repo="local", chart="nginx"),
        ]
        mock_registry_create.return_value = mock_repo
        mock_rehash.return_value = chart_metadata

        result = chart.update("local", "nginx", chart_info=chart_metadata)

        assert result == chart_metadata


    @patch("helmupdater.chart.nix.get_chart")
    @patch("helmupdater.chart.registry.create")
    def test_update_no_versions(
        self,
        mock_registry_create,
        mock_get_chart,
        tmp_path,
        monkeypatch,
        local_chart_metadata_for,
    ):
        monkeypatch.chdir(tmp_path)

        chart_metadata = local_chart_metadata_for("nginx", "1.0.0")
        _write_chart_file(tmp_path, chart_metadata)

        mock_repo = MagicMock()
        mock_repo.get_versions.return_value = []
        mock_registry_create.return_value = mock_repo

        with pytest.raises(ValueError, match="No versions available"):
            chart.update("local", "nginx", chart_info=chart_metadata)


class TestRehash:
    """Test rehash function."""

    @patch("helmupdater.chart.nix.get_chart")
    @patch("helmupdater.chart.nix.get_hash")
    def test_rehash(
        self,
        mock_get_hash,
        mock_get_chart,
        tmp_path,
        monkeypatch,
        local_chart_metadata_for,
    ):
        monkeypatch.chdir(tmp_path)

        current_chart = local_chart_metadata_for("nginx")

        broken_chart: chart.ChartMetadata = current_chart.model_copy(
            update={"chartHash": chart.PLACEHOLDER_HASH}
        )

        _write_chart_file(tmp_path, broken_chart)

        mock_get_chart.return_value = broken_chart
        mock_get_hash.return_value = current_chart.chartHash

        result = chart.rehash("local", "nginx")

        assert result == current_chart
