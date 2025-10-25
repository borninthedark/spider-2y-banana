"""Tests for scripts/run-precommit-podman.py."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Import after path is set
spec = importlib.util.spec_from_file_location(
    "run_precommit_podman",
    str(Path(__file__).parent.parent / "scripts" / "run-precommit-podman.py"),
)
if spec and spec.loader:
    run_precommit_podman = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_precommit_podman)
else:
    raise ImportError("Failed to load run-precommit-podman module")

IMAGE_NAME = run_precommit_podman.IMAGE_NAME
CONTAINER_FILE = run_precommit_podman.CONTAINER_FILE
check_podman = run_precommit_podman.check_podman
image_exists = run_precommit_podman.image_exists
build_image = run_precommit_podman.build_image
run_precommit_in_container = run_precommit_podman.run_precommit_in_container
clean_image = run_precommit_podman.clean_image


class TestCheckPodman:
    """Test check_podman function."""

    @patch("scripts.run-precommit-podman.check_command_exists")
    def test_podman_available(self, mock_check):
        """Test when podman is available."""
        mock_check.return_value = True
        assert check_podman() is True
        mock_check.assert_called_once_with("podman")

    @patch("scripts.run-precommit-podman.check_command_exists")
    @patch("scripts.run-precommit-podman.print_error")
    @patch("scripts.run-precommit-podman.print_info")
    def test_podman_not_available(self, mock_info, mock_error, mock_check):
        """Test when podman is not available."""
        mock_check.return_value = False
        assert check_podman() is False
        mock_error.assert_called_once()
        mock_info.assert_called_once()


class TestImageExists:
    """Test image_exists function."""

    @patch("run_precommit_podman.run_command")
    def test_image_exists_true(self, mock_run):
        """Test when image exists."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert image_exists() is True
        mock_run.assert_called_once_with(
            ["podman", "image", "exists", IMAGE_NAME], capture_output=True, check=False
        )

    @patch("run_precommit_podman.run_command")
    def test_image_exists_false(self, mock_run):
        """Test when image does not exist."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        assert image_exists() is False

    @patch("run_precommit_podman.run_command")
    def test_image_exists_command_failed(self, mock_run):
        """Test when command fails to run."""
        mock_run.return_value = None
        assert image_exists() is False


class TestBuildImage:
    """Test build_image function."""

    @patch("run_precommit_podman.image_exists")
    @patch("run_precommit_podman.print_info")
    def test_build_image_already_exists_no_force(self, mock_info, mock_exists):
        """Test that build is skipped when image exists and force=False."""
        mock_exists.return_value = True

        result = build_image(Path("/fake/path"), force=False)

        assert result is True
        mock_info.assert_called_once()

    @patch("run_precommit_podman.image_exists")
    @patch("run_precommit_podman.print_info")
    @patch("run_precommit_podman.print_error")
    def test_build_image_containerfile_missing(
        self, mock_error, mock_info, mock_exists
    ):
        """Test when Containerfile is missing."""
        mock_exists.return_value = False
        fake_root = Path("/nonexistent")

        result = build_image(fake_root, force=False)

        assert result is False
        mock_error.assert_called_once()

    @patch("run_precommit_podman.image_exists")
    @patch("run_precommit_podman.print_info")
    @patch("run_precommit_podman.print_success")
    @patch("run_precommit_podman.run_command")
    def test_build_image_success(
        self, mock_run, mock_success, mock_info, mock_exists, tmp_path
    ):
        """Test successful image build."""
        mock_exists.return_value = False

        # Create fake Containerfile
        containerfile = tmp_path / CONTAINER_FILE
        containerfile.write_text("FROM python:3.13-slim")

        # Mock successful build
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = build_image(tmp_path, force=False)

        assert result is True
        mock_success.assert_called_once()
        mock_run.assert_called_once()

    @patch("run_precommit_podman.image_exists")
    @patch("run_precommit_podman.print_info")
    @patch("run_precommit_podman.print_error")
    @patch("run_precommit_podman.run_command")
    def test_build_image_failure(
        self, mock_run, mock_error, mock_info, mock_exists, tmp_path
    ):
        """Test failed image build."""
        mock_exists.return_value = False

        # Create fake Containerfile
        containerfile = tmp_path / CONTAINER_FILE
        containerfile.write_text("FROM python:3.13-slim")

        # Mock failed build
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = build_image(tmp_path, force=False)

        assert result is False
        mock_error.assert_called_once()

    @patch("run_precommit_podman.image_exists")
    @patch("run_precommit_podman.print_info")
    @patch("run_precommit_podman.run_command")
    def test_build_image_with_force(self, mock_run, mock_info, mock_exists, tmp_path):
        """Test that force=True rebuilds even when image exists."""
        mock_exists.return_value = True

        # Create fake Containerfile
        containerfile = tmp_path / CONTAINER_FILE
        containerfile.write_text("FROM python:3.13-slim")

        # Mock successful build
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = build_image(tmp_path, force=True)

        assert result is True
        # Should call run_command even though image exists
        mock_run.assert_called_once()


class TestRunPrecommitInContainer:
    """Test run_precommit_in_container function."""

    @patch("run_precommit_podman.run_command")
    def test_run_precommit_basic(self, mock_run, tmp_path):
        """Test basic pre-commit execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        exit_code = run_precommit_in_container(tmp_path, ["run", "--all-files"])

        assert exit_code == 0
        mock_run.assert_called_once()

        # Verify command structure
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "podman"
        assert "run" in call_args
        assert "--rm" in call_args
        assert IMAGE_NAME in call_args

    @patch("run_precommit_podman.run_command")
    def test_run_precommit_with_gitconfig(self, mock_run, tmp_path, monkeypatch):
        """Test that gitconfig is mounted if it exists."""
        # Create fake gitconfig
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        gitconfig = fake_home / ".gitconfig"
        gitconfig.write_text("[user]\nname = Test")

        monkeypatch.setattr(Path, "home", lambda: fake_home)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        run_precommit_in_container(tmp_path, ["run"])

        call_args = mock_run.call_args[0][0]
        # Should contain gitconfig mount
        assert any(".gitconfig" in str(arg) for arg in call_args)

    @patch("run_precommit_podman.run_command")
    @patch("run_precommit_podman.print_colored")
    def test_run_precommit_verbose(self, mock_print, mock_run, tmp_path):
        """Test verbose output mode."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        run_precommit_in_container(tmp_path, ["run"], verbose=True)

        # Should print command in verbose mode
        mock_print.assert_called_once()

    @patch("run_precommit_podman.run_command")
    def test_run_precommit_failure(self, mock_run, tmp_path):
        """Test handling of pre-commit failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        exit_code = run_precommit_in_container(tmp_path, ["run"])

        assert exit_code == 1

    @patch("run_precommit_podman.run_command")
    def test_run_precommit_command_error(self, mock_run, tmp_path):
        """Test handling when command fails to execute."""
        mock_run.return_value = None

        exit_code = run_precommit_in_container(tmp_path, ["run"])

        assert exit_code == 1


class TestCleanImage:
    """Test clean_image function."""

    @patch("run_precommit_podman.image_exists")
    @patch("run_precommit_podman.print_warning")
    def test_clean_image_not_exists(self, mock_warning, mock_exists):
        """Test cleaning when image doesn't exist."""
        mock_exists.return_value = False

        result = clean_image()

        assert result is True
        mock_warning.assert_called_once()

    @patch("run_precommit_podman.image_exists")
    @patch("run_precommit_podman.print_info")
    @patch("run_precommit_podman.print_success")
    @patch("run_precommit_podman.run_command")
    def test_clean_image_success(self, mock_run, mock_success, mock_info, mock_exists):
        """Test successful image removal."""
        mock_exists.return_value = True
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = clean_image()

        assert result is True
        mock_success.assert_called_once()
        mock_run.assert_called_once_with(
            ["podman", "rmi", IMAGE_NAME], capture_output=True, check=False
        )

    @patch("run_precommit_podman.image_exists")
    @patch("run_precommit_podman.print_info")
    @patch("run_precommit_podman.print_error")
    @patch("run_precommit_podman.run_command")
    def test_clean_image_failure(self, mock_run, mock_error, mock_info, mock_exists):
        """Test failed image removal."""
        mock_exists.return_value = True
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = clean_image()

        assert result is False
        mock_error.assert_called_once()


class TestMainFunction:
    """Test main function and CLI integration."""

    @patch("run_precommit_podman.check_podman")
    def test_main_podman_not_available(self, mock_check):
        """Test main exits when podman not available."""
        from run_precommit_podman import main

        mock_check.return_value = False

        exit_code = main()
        assert exit_code == 1

    @patch("run_precommit_podman.check_podman")
    @patch("run_precommit_podman.clean_image")
    @patch("run_precommit_podman.get_project_root")
    @patch("sys.argv", ["script", "--clean"])
    def test_main_clean_mode(self, mock_root, mock_clean, mock_check, tmp_path):
        """Test main with --clean flag."""
        from run_precommit_podman import main

        mock_check.return_value = True
        mock_clean.return_value = True
        mock_root.return_value = tmp_path

        exit_code = main()

        assert exit_code == 0
        mock_clean.assert_called_once()

    @patch("run_precommit_podman.check_podman")
    @patch("run_precommit_podman.build_image")
    @patch("run_precommit_podman.run_precommit_in_container")
    @patch("run_precommit_podman.get_project_root")
    @patch("run_precommit_podman.print_info")
    @patch("run_precommit_podman.print_success")
    @patch("sys.argv", ["script", "run", "--all-files"])
    def test_main_successful_run(
        self,
        mock_success,
        mock_info,
        mock_root,
        mock_run,
        mock_build,
        mock_check,
        tmp_path,
    ):
        """Test successful main execution."""
        from run_precommit_podman import main

        mock_check.return_value = True
        mock_build.return_value = True
        mock_run.return_value = 0
        mock_root.return_value = tmp_path

        exit_code = main()

        assert exit_code == 0
        mock_build.assert_called_once()
        mock_run.assert_called_once()
        mock_success.assert_called_once()

    @patch("run_precommit_podman.check_podman")
    @patch("run_precommit_podman.build_image")
    @patch("run_precommit_podman.run_precommit_in_container")
    @patch("run_precommit_podman.get_project_root")
    @patch("run_precommit_podman.print_info")
    @patch("run_precommit_podman.print_error")
    @patch("sys.argv", ["script", "run", "--all-files"])
    def test_main_failed_run(
        self,
        mock_error,
        mock_info,
        mock_root,
        mock_run,
        mock_build,
        mock_check,
        tmp_path,
    ):
        """Test main with failed pre-commit."""
        from run_precommit_podman import main

        mock_check.return_value = True
        mock_build.return_value = True
        mock_run.return_value = 1
        mock_root.return_value = tmp_path

        exit_code = main()

        assert exit_code == 1
        mock_error.assert_called_once()

    @patch("run_precommit_podman.check_podman")
    @patch("run_precommit_podman.build_image")
    @patch("run_precommit_podman.get_project_root")
    @patch("sys.argv", ["script", "--build", "run"])
    def test_main_force_build(self, mock_root, mock_build, mock_check, tmp_path):
        """Test main with --build flag."""
        from run_precommit_podman import main

        mock_check.return_value = True
        mock_build.return_value = False  # Build fails
        mock_root.return_value = tmp_path

        exit_code = main()

        assert exit_code == 1
        # Verify force=True was passed
        assert mock_build.call_args[1]["force"] is True


class TestConstants:
    """Test module constants."""

    def test_image_name(self):
        """Test IMAGE_NAME constant is defined."""
        assert IMAGE_NAME == "pre-commit-tools:local"

    def test_container_file(self):
        """Test CONTAINER_FILE constant is defined."""
        assert CONTAINER_FILE == "Containerfile.pre-commit"
