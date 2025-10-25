"""Shared utilities for Python scripts across the project.

This module provides common functionality used by multiple scripts to avoid
code duplication and ensure consistency.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Union


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


def print_colored(message: str, color: str = Colors.NC):
    """Print colored message to console.

    Args:
        message: The message to print
        color: ANSI color code (default: no color)

    Example:
        >>> print_colored("Success!", Colors.GREEN)
        Success! # (in green)
    """
    print(f"{color}{message}{Colors.NC}")


def print_success(message: str):
    """Print success message in green with checkmark.

    Args:
        message: The success message to print
    """
    print_colored(f"✓ {message}", Colors.GREEN)


def print_error(message: str):
    """Print error message in red with X mark.

    Args:
        message: The error message to print
    """
    print_colored(f"✗ {message}", Colors.RED)


def print_warning(message: str):
    """Print warning message in yellow with exclamation.

    Args:
        message: The warning message to print
    """
    print_colored(f"! {message}", Colors.YELLOW)


def print_info(message: str):
    """Print info message in cyan.

    Args:
        message: The info message to print
    """
    print_colored(message, Colors.CYAN)


def run_command(
    command: Union[str, list[str]],
    capture_output: bool = False,
    check: bool = True,
    cwd: Optional[Path] = None,
    shell: Optional[bool] = None,
) -> Optional[subprocess.CompletedProcess]:
    """Execute a command and handle errors.

    Args:
        command: Command to execute (string or list)
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise on non-zero exit code
        cwd: Working directory for command
        shell: Use shell execution (auto-detected if None)

    Returns:
        CompletedProcess object if successful, None on error (when check=False)

    Raises:
        SystemExit: If command fails and check=True

    Example:
        >>> result = run_command(["ls", "-la"], capture_output=True)
        >>> print(result.stdout)
    """
    # Auto-detect shell mode
    if shell is None:
        shell = isinstance(command, str)

    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=capture_output,
            text=True,
            check=check,
            cwd=cwd,
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            cmd_str = command if isinstance(command, str) else " ".join(command)
            print_error(f"Command failed: {cmd_str}")
            if e.stderr:
                print_colored(f"Error: {e.stderr}", Colors.RED)
            sys.exit(1)
        return None
    except FileNotFoundError:
        if check:
            cmd_str = command if isinstance(command, str) else command[0]
            print_error(f"Command not found: {cmd_str}")
            sys.exit(1)
        return None


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH.

    Args:
        command: Name of the command to check

    Returns:
        True if command exists, False otherwise

    Example:
        >>> if check_command_exists("docker"):
        ...     print("Docker is installed")
    """
    result = run_command(
        f"command -v {command}", capture_output=True, check=False, shell=True
    )
    return result is not None and result.returncode == 0


def get_project_root() -> Path:
    """Get the project root directory.

    Assumes the scripts/utils.py location and traverses up to find project root.

    Returns:
        Path object pointing to project root

    Example:
        >>> root = get_project_root()
        >>> print(root / "README.md")
    """
    # This file is in scripts/utils.py, so parent is scripts, parent.parent is root
    return Path(__file__).parent.parent


def confirm_action(prompt: str, default: bool = False) -> bool:
    """Prompt user for yes/no confirmation.

    Args:
        prompt: Question to ask the user
        default: Default response if user just presses Enter

    Returns:
        True if user confirms, False otherwise

    Example:
        >>> if confirm_action("Delete all files?"):
        ...     delete_files()
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").lower().strip()

    if not response:
        return default

    return response in ("y", "yes")
