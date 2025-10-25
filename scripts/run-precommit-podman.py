#!/usr/bin/env python3
"""Run pre-commit hooks in a podman container.

This script provides a containerized environment for running pre-commit hooks,
ensuring consistent tool versions and dependencies across different systems.

Usage:
    python scripts/run-precommit-podman.py [pre-commit args]

Examples:
    python scripts/run-precommit-podman.py run --all-files
    python scripts/run-precommit-podman.py run trailing-whitespace
    python scripts/run-precommit-podman.py install
"""

import argparse
import sys
from pathlib import Path

from utils import (
    Colors,
    check_command_exists,
    get_project_root,
    print_colored,
    print_error,
    print_info,
    print_success,
    print_warning,
    run_command,
)

IMAGE_NAME = "pre-commit-tools:local"
CONTAINER_FILE = "Containerfile.pre-commit"


def check_podman() -> bool:
    """Check if podman is installed and available.

    Returns:
        True if podman is available, False otherwise
    """
    if not check_command_exists("podman"):
        print_error("Podman is not installed or not in PATH")
        print_info("Install podman: https://podman.io/getting-started/installation")
        return False
    return True


def image_exists() -> bool:
    """Check if the pre-commit container image exists.

    Returns:
        True if image exists, False otherwise
    """
    result = run_command(
        ["podman", "image", "exists", IMAGE_NAME], capture_output=True, check=False
    )
    return result is not None and result.returncode == 0


def build_image(project_root: Path, force: bool = False) -> bool:
    """Build the pre-commit container image.

    Args:
        project_root: Path to project root directory
        force: Force rebuild even if image exists

    Returns:
        True if build successful, False otherwise
    """
    if image_exists() and not force:
        print_info(f"Container image '{IMAGE_NAME}' already exists")
        return True

    print_info(f"Building pre-commit container image: {IMAGE_NAME}")

    containerfile = project_root / CONTAINER_FILE
    if not containerfile.exists():
        print_error(f"Containerfile not found: {containerfile}")
        return False

    result = run_command(
        ["podman", "build", "-f", str(containerfile), "-t", IMAGE_NAME, "."],
        cwd=project_root,
        check=False,
    )

    if result and result.returncode == 0:
        print_success(f"Successfully built image: {IMAGE_NAME}")
        return True
    else:
        print_error("Failed to build container image")
        return False


def run_precommit_in_container(
    project_root: Path, args: list[str], verbose: bool = False
) -> int:
    """Run pre-commit in the container.

    Args:
        project_root: Path to project root directory
        args: Arguments to pass to pre-commit
        verbose: Enable verbose output

    Returns:
        Exit code from pre-commit
    """
    # Build command
    cmd = [
        "podman",
        "run",
        "--rm",
        "-v",
        f"{project_root}:/workspace:Z",
        "-w",
        "/workspace",
    ]

    # Mount git config if it exists
    gitconfig = Path.home() / ".gitconfig"
    if gitconfig.exists():
        cmd.extend(["-v", f"{gitconfig}:/root/.gitconfig:ro,Z"])

    cmd.append(IMAGE_NAME)
    cmd.extend(args)

    if verbose:
        print_colored(f"Running: {' '.join(cmd)}", Colors.CYAN)

    result = run_command(cmd, check=False)
    return result.returncode if result else 1


def clean_image() -> bool:
    """Remove the pre-commit container image.

    Returns:
        True if successful, False otherwise
    """
    if not image_exists():
        print_warning(f"Image '{IMAGE_NAME}' does not exist")
        return True

    print_info(f"Removing container image: {IMAGE_NAME}")
    result = run_command(
        ["podman", "rmi", IMAGE_NAME], capture_output=True, check=False
    )

    if result and result.returncode == 0:
        print_success("Container image removed")
        return True
    else:
        print_error("Failed to remove container image")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run pre-commit hooks in a podman container",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run --all-files
  %(prog)s run trailing-whitespace
  %(prog)s --build run --all-files
  %(prog)s --clean
        """,
    )

    parser.add_argument(
        "--build",
        action="store_true",
        help="Force rebuild the container image before running",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Remove the container image and exit"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "precommit_args",
        nargs="*",
        default=["run", "--all-files"],
        help="Arguments to pass to pre-commit (default: run --all-files)",
    )

    args = parser.parse_args()

    # Check podman availability
    if not check_podman():
        return 1

    project_root = get_project_root()

    # Handle clean command
    if args.clean:
        return 0 if clean_image() else 1

    # Build image if needed
    if not build_image(project_root, force=args.build):
        return 1

    # Run pre-commit
    print_info(f"Running pre-commit with args: {' '.join(args.precommit_args)}")
    exit_code = run_precommit_in_container(
        project_root, args.precommit_args, verbose=args.verbose
    )

    if exit_code == 0:
        print_success("Pre-commit checks passed")
    else:
        print_error(f"Pre-commit checks failed (exit code: {exit_code})")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
