import json
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import patch

import pytest

from helmupdater import nix
from helmupdater.chart.chart_metadata import ChartMetadata


class TestCurrentSystem:
    @pytest.mark.parametrize(
        "stdout,expected",
        [
            ('"aarch64-darwin"\n', "aarch64-darwin"),
            ('"x86_64-linux"\n', "x86_64-linux"),
        ],
    )
    @patch("helmupdater.nix.run_cmd")
    def test_current_system(self, mock_run_cmd, stdout, expected):
        nix.current_system.cache_clear()
        mock_run_cmd.return_value = CompletedProcess(
            args=[], returncode=0, stdout=stdout, stderr=""
        )

        result = nix.current_system()

        assert result == expected
        mock_run_cmd.assert_called_once_with(
            "nix", "eval", "--impure", "--expr", "builtins.currentSystem"
        )
        nix.current_system.cache_clear()

    @patch("helmupdater.nix.run_cmd")
    def test_current_system_caching(self, mock_run_cmd):
        nix.current_system.cache_clear()
        mock_run_cmd.return_value = CompletedProcess(
            args=[], returncode=0, stdout='"aarch64-darwin"\n', stderr=""
        )

        result1 = nix.current_system()
        result2 = nix.current_system()

        assert result1 == result2 == "aarch64-darwin"
        mock_run_cmd.assert_called_once()
        nix.current_system.cache_clear()


class TestBuildChart:
    @patch("helmupdater.nix.current_system")
    @patch("helmupdater.nix.run_cmd")
    def test_build_chart_success(self, mock_run_cmd, mock_current_system):
        system = "aarch64-darwin"
        mock_current_system.return_value = system
        mock_run_cmd.return_value = CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        nix.build_chart("local", "nginx")

        mock_run_cmd.assert_called_once_with(
            "nix",
            "build",
            f".#chartsDerivations.{system}.local.nginx",
            raise_on_error=True,
        )

    @patch("helmupdater.nix.current_system")
    @patch("helmupdater.nix.run_cmd")
    def test_build_chart_failure(self, mock_run_cmd, mock_current_system):
        mock_run_cmd.side_effect = CalledProcessError(1, "nix build ...")
        with pytest.raises(CalledProcessError):
            nix.build_chart("local", "nginx")

    @patch("helmupdater.nix.current_system")
    @patch("helmupdater.nix.run_cmd")
    def test_build_chart_capture_failure(self, mock_run_cmd, mock_current_system):
        mock_run_cmd.return_value = CompletedProcess(
            args=[], returncode=1, stdout="info message", stderr="error message"
        )
        result = nix.build_chart("local", "nginx", raise_on_error=False)
        assert result.stderr == "error message"


class TestGetHash:
    @patch("helmupdater.nix.build_chart")
    def test_get_hash_raises_when_not_found(self, mock_build_chart):
        mock_build_chart.return_value = CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="flake 'git+file:///.../src/nixhelm' does not provide attribute ...",
        )

        with pytest.raises(
            RuntimeError, match="Failed to extract hash for local/nginx"
        ):
            nix.get_hash("local", "nginx")

    @patch("helmupdater.nix.current_system")
    @patch("helmupdater.nix.run_cmd")
    def test_get_hash_derivation(self, mock_run_cmd, mock_current_system):
        derivation_json = """
        {
            "derivations": {
                "abcd-helm-chart-http-localhost-45010--nginx-1.0.1.drv": {
                    "outputs": {
                        "out": {
                            "hash": "sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY=",
                            "method": "nar"
                        }
                    },
                    "system": "aarch64-darwin",
                    "version": 4
                }
            },
            "version": 4
        }
        """ # noqa: E501

        system = "aarch64-darwin"
        mock_current_system.return_value = system
        mock_run_cmd.return_value = CompletedProcess(
            args=[], returncode=0, stdout=derivation_json, stderr=""
        )

        result = nix.get_hash_derivation("local", "nginx")

        assert result == "sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY="
        mock_run_cmd.assert_called_once_with(
            "nix",
            "derivation",
            "show",
            f".#chartsDerivations.{system}.local.nginx",
        )

    @patch("helmupdater.nix.build_chart")
    def test_get_hash_build_mismatch(self, mock_build_chart):
        err_msg = (
            "❌ git+file:///.../src/nixhelm#chartsDerivations.aarch64-darwin.local.nginx\n"
            "error: hash mismatch in fixed-output derivation '/nix/store/2r72dg...-nginx-1.0.1.drv':\n"  # noqa: E501
            "         specified: sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n"
            "            got:    sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY="
        )
        mock_build_chart.return_value = CompletedProcess(
            args=[], returncode=1, stdout="", stderr=err_msg
        )

        result = nix.get_hash("local", "nginx")

        assert result == "sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY="
        mock_build_chart.assert_called_once_with("local", "nginx", raise_on_error=False)

    @patch("helmupdater.nix.get_hash_derivation")
    @patch("helmupdater.nix.build_chart")
    def test_get_hash_build_matches(self, mock_build_chart, mock_get_hash_derivation):
        mock_get_hash_derivation.return_value = (
            "sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY="
        )
        mock_build_chart.return_value = CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        result = nix.get_hash("local", "nginx")

        assert result == "sha256-2Wu51wd842yLn8ZRO9NunjzJhIqGkqEsU4qHzKKXjFY="
        mock_build_chart.assert_called_once_with("local", "nginx", raise_on_error=False)
        mock_get_hash_derivation.assert_called_once_with("local", "nginx")


class TestGetCharts:
    @patch("helmupdater.nix.run_cmd")
    def test_get_charts_single_repo(self, mock_run_cmd, local_chart_metadata_for):
        nginx_chart = local_chart_metadata_for("nginx")
        podinfo_chart = local_chart_metadata_for("podinfo")
        remote_chart = ChartMetadata(
            repo="https://example.org/charts",
            chart="dummy",
            version="2.0.0",
            chartHash="sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        )
        chart_data = {
            "local": {
                "nginx": nginx_chart.model_dump(),
                "podinfo": podinfo_chart.model_dump(),
            },
            "remote": {"dummy": remote_chart.model_dump()},
        }

        mock_run_cmd.return_value = CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(chart_data), stderr=""
        )
        result = nix.get_charts()

        assert "local" in result
        assert "nginx" in result["local"]
        assert "podinfo" in result["local"]
        assert result["local"]["nginx"] == nginx_chart
        assert result["local"]["podinfo"] == podinfo_chart
        assert "remote" in result
        assert "dummy" in result["remote"]
        assert result["remote"]["dummy"] == remote_chart

        mock_run_cmd.assert_called_once_with(
            "nix", "eval", ".#chartsMetadata", "--json"
        )

    @patch("helmupdater.nix.run_cmd")
    def test_get_charts_empty(self, mock_run_cmd):
        mock_run_cmd.return_value = CompletedProcess(
            args=[], returncode=0, stdout="{}", stderr=""
        )

        result = nix.get_charts()

        assert result == {}


class TestGetChart:
    @patch("helmupdater.nix.run_cmd")
    def test_get_chart(self, mock_run_cmd, local_chart_metadata_for):
        chart = local_chart_metadata_for("nginx")
        chart_json = json.dumps(chart.model_dump())

        mock_run_cmd.return_value = CompletedProcess(
            args=[], returncode=0, stdout=chart_json, stderr=""
        )

        result = nix.get_chart("local", "nginx")

        assert result == chart
        mock_run_cmd.assert_called_once_with(
            "nix", "eval", ".#chartsMetadata.local.nginx", "--json"
        )
