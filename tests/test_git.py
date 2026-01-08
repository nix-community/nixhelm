from pathlib import Path
from unittest.mock import patch

import pytest

from helmupdater import git


class TestAddFile:
    @pytest.mark.parametrize(
        "file_path",
        [
            "charts/local/nginx/default.nix",
            Path("charts/local/nginx/default.nix"),
        ],
    )
    @patch("helmupdater.git.run_cmd")
    def test_add_file(self, mock_run_cmd, file_path):
        git.add_file(file_path)

        mock_run_cmd.assert_called_once_with(
            "git", "add", "charts/local/nginx/default.nix"
        )


class TestCommit:
    @patch("helmupdater.git.run_cmd")
    def test_commit_with_message(self, mock_run_cmd):
        git.commit("local/nginx: update to 1.0.1")

        mock_run_cmd.assert_called_once_with(
            "git", "commit", "-m", "local/nginx: update to 1.0.1"
        )


class TestAddAndCommit:
    @patch("helmupdater.git.commit")
    @patch("helmupdater.git.add_file")
    def test_add_and_commit(self, mock_add_file, mock_commit):
        git.add_and_commit("charts/local/nginx/default.nix", "Update nginx")

        mock_add_file.assert_called_once_with("charts/local/nginx/default.nix")
        mock_commit.assert_called_once_with("Update nginx")


class TestReset:
    @patch("helmupdater.git.run_cmd")
    def test_reset_all(self, mock_run_cmd):
        git.reset()

        mock_run_cmd.assert_called_once_with("git", "reset")

    @pytest.mark.parametrize(
        "file_path,expected_args",
        [
            (
                "charts/local/nginx/default.nix",
                ("git", "reset", "charts/local/nginx/default.nix"),
            ),
            (
                Path("charts/local/nginx/default.nix"),
                ("git", "reset", "charts/local/nginx/default.nix"),
            ),
        ],
    )
    @patch("helmupdater.git.run_cmd")
    def test_reset(self, mock_run_cmd, file_path, expected_args):
        git.reset(file_path)

        mock_run_cmd.assert_called_once_with(*expected_args)


class TestStagedFile:
    @pytest.mark.parametrize(
        "test_path",
        [
            "charts/local/nginx/default.nix",
            Path("charts/local/nginx/default.nix"),
        ],
    )
    @patch("helmupdater.git.reset")
    @patch("helmupdater.git.add_file")
    def test_staged_file_normal_operation(self, mock_add_file, mock_reset, test_path):
        with git.staged_file(test_path) as path:
            assert path == test_path
            mock_add_file.assert_called_once_with(test_path)
            mock_reset.assert_not_called()

        mock_reset.assert_called_once_with(test_path)

    @patch("helmupdater.git.reset")
    @patch("helmupdater.git.add_file")
    def test_staged_file_resets_on_exception(self, mock_add_file, mock_reset):
        test_path = "test.txt"

        with pytest.raises(ValueError):
            with git.staged_file(test_path):
                raise ValueError("Test exception")

        mock_add_file.assert_called_once()
        mock_reset.assert_called_once_with(test_path)
