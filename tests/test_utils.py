"""Tests for scripts/utils.py shared utilities module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from utils import (  # noqa: E402
    Colors,
    check_command_exists,
    confirm_action,
    get_project_root,
    print_colored,
    print_error,
    print_success,
    print_warning,
    run_command,
)


class TestColors:
    """Test Colors class constants."""

    def test_colors_defined(self):
        """Test that all color constants are defined."""
        assert hasattr(Colors, "RED")
        assert hasattr(Colors, "GREEN")
        assert hasattr(Colors, "YELLOW")
        assert hasattr(Colors, "NC")

    def test_color_values(self):
        """Test that colors are ANSI escape codes."""
        assert Colors.RED.startswith("\033[")
        assert Colors.GREEN.startswith("\033[")
        assert Colors.NC == "\033[0m"


class TestPrintFunctions:
    """Test colored print functions."""

    @patch("builtins.print")
    def test_print_colored(self, mock_print):
        """Test print_colored function."""
        print_colored("Test message", Colors.GREEN)
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "Test message" in args
        assert Colors.GREEN in args

    @patch("builtins.print")
    def test_print_success(self, mock_print):
        """Test print_success includes checkmark."""
        print_success("Success message")
        args = mock_print.call_args[0][0]
        assert "✓" in args
        assert "Success message" in args

    @patch("builtins.print")
    def test_print_error(self, mock_print):
        """Test print_error includes X mark."""
        print_error("Error message")
        args = mock_print.call_args[0][0]
        assert "✗" in args
        assert "Error message" in args

    @patch("builtins.print")
    def test_print_warning(self, mock_print):
        """Test print_warning includes exclamation."""
        print_warning("Warning message")
        args = mock_print.call_args[0][0]
        assert "!" in args
        assert "Warning message" in args


class TestRunCommand:
    """Test run_command function."""

    def test_run_command_success(self):
        """Test successful command execution."""
        result = run_command("echo 'test'", capture_output=True)
        assert result is not None
        assert result.returncode == 0
        assert "test" in result.stdout

    def test_run_command_with_list(self):
        """Test command execution with list input."""
        result = run_command(["echo", "test"], capture_output=True)
        assert result is not None
        assert result.returncode == 0

    def test_run_command_failure_with_check(self):
        """Test command failure with check=True exits."""
        with pytest.raises(SystemExit):
            run_command("false", check=True)

    def test_run_command_failure_without_check(self):
        """Test command failure with check=False returns result."""
        result = run_command("false", check=False)
        assert result is not None
        assert result.returncode == 1

    def test_run_command_with_cwd(self, tmp_path):
        """Test command execution with custom working directory."""
        result = run_command("pwd", capture_output=True, cwd=tmp_path)
        assert str(tmp_path) in result.stdout


class TestCheckCommandExists:
    """Test check_command_exists function."""

    def test_existing_command(self):
        """Test that common commands are found."""
        assert check_command_exists("echo")
        assert check_command_exists("ls")

    def test_nonexistent_command(self):
        """Test that non-existent commands return False."""
        assert not check_command_exists("this_command_does_not_exist_12345")


class TestGetProjectRoot:
    """Test get_project_root function."""

    def test_get_project_root(self):
        """Test that project root is correctly identified."""
        root = get_project_root()
        assert root.exists()
        assert root.is_dir()
        # Check that scripts directory exists under root
        assert (root / "scripts").exists()


class TestConfirmAction:
    """Test confirm_action function."""

    @patch("builtins.input", return_value="y")
    def test_confirm_action_yes(self, mock_input):
        """Test confirmation with 'y' response."""
        assert confirm_action("Test prompt?")

    @patch("builtins.input", return_value="yes")
    def test_confirm_action_yes_full(self, mock_input):
        """Test confirmation with 'yes' response."""
        assert confirm_action("Test prompt?")

    @patch("builtins.input", return_value="n")
    def test_confirm_action_no(self, mock_input):
        """Test confirmation with 'n' response."""
        assert not confirm_action("Test prompt?")

    @patch("builtins.input", return_value="")
    def test_confirm_action_default_true(self, mock_input):
        """Test confirmation with empty response and default=True."""
        assert confirm_action("Test prompt?", default=True)

    @patch("builtins.input", return_value="")
    def test_confirm_action_default_false(self, mock_input):
        """Test confirmation with empty response and default=False."""
        assert not confirm_action("Test prompt?", default=False)
