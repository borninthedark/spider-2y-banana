#!/usr/bin/env python3
"""Update domain name across all configuration files.

This script replaces the old domain name with a new domain name across
multiple configuration files in the project.

Usage:
    python3 update-domain.py <new-domain>

Example:
    python3 update-domain.py example.com
"""

import argparse
from pathlib import Path
from typing import List


OLD_DOMAIN = "princetonstrong.online"


class Colors:
    """ANSI color codes."""

    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    NC = "\033[0m"  # No Color


def print_color(color, message):
    """Print colored message."""
    print(f"{color}{message}{Colors.NC}")


def update_file(file_path: Path, old_domain: str, new_domain: str) -> bool:
    """Update domain in a single file.

    Args:
        file_path: Path to the file to update
        old_domain: Domain to replace
        new_domain: New domain name

    Returns:
        True if file was updated, False if file not found
    """
    if not file_path.exists():
        print(f"Warning: {file_path} not found, skipping...")
        return False

    print(f"Updating {file_path}...")

    # Read the file content
    content = file_path.read_text()

    # Replace old domain with new domain
    updated_content = content.replace(old_domain, new_domain)

    # Write back to file
    file_path.write_text(updated_content)

    return True


def get_files_to_update() -> List[Path]:
    """Get list of files that need domain updates.

    Returns:
        List of Path objects for files to update
    """
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent

    files = [
        project_root / "gitops/platform/monitoring/kube-prometheus-stack.yaml",
        project_root / "gitops/platform/cert-manager/cert-manager.yaml",
        project_root / "gitops/applications/dev/resume-deployment.yaml",
        project_root / "docs/security-hardening.md",
    ]

    return files


def display_next_steps(new_domain: str):
    """Display next steps after domain update.

    Args:
        new_domain: The new domain name that was set
    """
    print()
    print_color(Colors.YELLOW, "Next steps:")
    print(f"1. Update .env file with DOMAIN_NAME={new_domain}")
    print("2. Rebuild Jsonnet manifests: cd jsonnet && make dev")
    print(
        f"3. Rebuild Docker images with: docker build --build-arg "
        f"DOMAIN_NAME={new_domain} osyraa/"
    )
    print(
        "4. Update Terraform variables in " "terraform-infrastructure/terraform.tfvars"
    )
    print("5. Review and commit the changes")


def main():
    """Main function to update domain names."""
    parser = argparse.ArgumentParser(
        description="Update domain name across all configuration files",
        epilog="Example: %(prog)s example.com",
    )
    parser.add_argument("new_domain", help="New domain name to use")
    parser.add_argument(
        "--old-domain",
        default=OLD_DOMAIN,
        help=f"Old domain to replace (default: {OLD_DOMAIN})",
    )

    args = parser.parse_args()

    new_domain = args.new_domain
    old_domain = args.old_domain

    print(f"Updating domain from {old_domain} to {new_domain}...\n")

    # Get files to update
    files = get_files_to_update()

    # Update each file
    updated_count = 0
    for file_path in files:
        if update_file(file_path, old_domain, new_domain):
            updated_count += 1

    print()
    print_color(Colors.GREEN, "Domain updated successfully!")
    print(f"Updated {updated_count} file(s)")

    # Display next steps
    display_next_steps(new_domain)


if __name__ == "__main__":
    main()
