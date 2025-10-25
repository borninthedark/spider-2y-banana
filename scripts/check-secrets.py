#!/usr/bin/env python3
"""Secret Detection Script - Scans for potential secrets before commit."""

import os
import sys

from utils import Colors, print_colored, run_command


def run_git_command(cmd):
    """Execute a git command and return result."""
    return run_command(cmd, capture_output=True, check=False, shell=True)


def check_sensitive_files():
    """Check for common secret files."""
    print_colored("\nChecking for sensitive files...", Colors.YELLOW)

    sensitive_files = [
        "*.env",
        ".env*",
        "*.pem",
        "*.key",
        "*_rsa",
        "*.pfx",
        "*.p12",
        "sp-credentials.json",
        "credentials.json",
        "terraform.tfvars",
        ".vault_password",
        "kubeconfig",
        "*.kubeconfig",
        "k3s.yaml",
        "auth.json",
        "service-account*.json",
    ]

    errors_found = False

    for pattern in sensitive_files:
        result = run_git_command(f"git ls-files | grep -E '{pattern}'")
        if result.returncode == 0 and result.stdout.strip():
            print_colored(f"✗ Found sensitive file matching: {pattern}", Colors.RED)
            print(result.stdout)
            errors_found = True

    if not errors_found:
        print_colored("✓ No sensitive files found in git index", Colors.GREEN)

    return errors_found


def check_terraform_passwords():
    """Check for hardcoded passwords in Terraform."""
    print(
        f"\n{Colors.YELLOW}Checking Terraform files for hardcoded secrets...{Colors.NC}"
    )

    if not os.path.exists("terraform-infrastructure"):
        print_colored("✓ No Terraform directory found", Colors.GREEN)
        return False

    result = run_git_command(
        "find terraform-infrastructure -name '*.tf' -type f "
        "-exec grep -l 'password\\s*=\\s*\"[^$]' {} \\; 2>/dev/null | "
        "grep -v random_password | grep -v azurerm_key_vault_secret"
    )

    if result.returncode == 0 and result.stdout.strip():
        print_colored(
            "✗ Found potential hardcoded passwords in Terraform files",
            Colors.RED,
        )
        print(result.stdout)
        return True
    else:
        print_colored("✓ No hardcoded passwords found in Terraform", Colors.GREEN)
        return False


def check_ansible_passwords():
    """Check for hardcoded passwords in Ansible."""
    print(
        f"\n{Colors.YELLOW}Checking Ansible files for hardcoded secrets...{Colors.NC}"
    )

    if not os.path.exists("ansible"):
        print_colored("✓ No Ansible directory found", Colors.GREEN)
        return False

    result = run_git_command(
        "find ansible -name '*.yml' -o -name '*.yaml' -type f "
        "-exec grep -l 'password:' {} \\; 2>/dev/null | "
        "xargs grep -v 'ansible_become_password' | grep -v 'vault' | grep -v '#'"
    )

    if result.returncode == 0 and result.stdout.strip():
        print_colored(
            "✗ Found potential hardcoded passwords in Ansible files",
            Colors.RED,
        )
        print(result.stdout)
        return True
    else:
        print_colored("✓ No hardcoded passwords found in Ansible", Colors.GREEN)
        return False


def check_aws_credentials():
    """Check for AWS credentials."""
    print(f"\n{Colors.YELLOW}Checking for AWS credentials...{Colors.NC}")

    result = run_git_command("git grep -E 'AKIA[0-9A-Z]{16}' -- ':(exclude).git'")

    if result.returncode == 0 and result.stdout.strip():
        print_colored("✗ Found potential AWS access keys", Colors.RED)
        return True
    else:
        print_colored("✓ No AWS credentials found", Colors.GREEN)
        return False


def check_azure_subscription_ids():
    """Check for exposed Azure subscription IDs."""
    print(
        f"\n{Colors.YELLOW}Checking for exposed Azure subscription IDs..."
        f"{Colors.NC}"
    )

    result = run_git_command(
        "git grep -E '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}"
        "-[0-9a-f]{12}' -- ':(exclude)*.md' ':(exclude).git' "
        "':(exclude)scripts/'"
    )

    if result.stdout.strip():
        uuid_count = len(result.stdout.strip().split("\n"))
        if uuid_count > 5:
            print_colored(
                "! Warning: Found multiple UUID patterns "
                "(could be subscription IDs)",
                Colors.YELLOW,
            )
            print_colored("  Manual review recommended", Colors.YELLOW)


def check_private_keys():
    """Check for private keys."""
    print(f"\n{Colors.YELLOW}Checking for private keys...{Colors.NC}")

    result = run_git_command(
        "git grep -E '-----BEGIN.*PRIVATE KEY-----' -- ':(exclude).git'"
    )

    if result.returncode == 0 and result.stdout.strip():
        print_colored("✗ Found private keys in repository", Colors.RED)
        return True
    else:
        print_colored("✓ No private keys found", Colors.GREEN)
        return False


def check_github_tokens():
    """Check for GitHub tokens."""
    print(f"\n{Colors.YELLOW}Checking for GitHub tokens...{Colors.NC}")

    result = run_git_command(
        "git grep -E 'gh[pousr]_[a-zA-Z0-9]{36}' -- ':(exclude).git'"
    )

    if result.returncode == 0 and result.stdout.strip():
        print_colored("✗ Found potential GitHub tokens", Colors.RED)
        return True
    else:
        print_colored("✓ No GitHub tokens found", Colors.GREEN)
        return False


def check_jwt_tokens():
    """Check for JWT tokens."""
    print(f"\n{Colors.YELLOW}Checking for JWT tokens...{Colors.NC}")

    result = run_git_command(
        "git grep -E 'eyJ[a-zA-Z0-9_\\-]+\\.eyJ[a-zA-Z0-9_\\-]+\\."
        "[a-zA-Z0-9_\\-]+' -- ':(exclude).git' ':(exclude)*.md'"
    )

    if result.returncode == 0 and result.stdout.strip():
        print_colored("! Warning: Found potential JWT tokens", Colors.YELLOW)
        print_colored("  Manual review recommended", Colors.YELLOW)


def check_slack_tokens():
    """Check for Slack tokens."""
    print(f"\n{Colors.YELLOW}Checking for Slack tokens...{Colors.NC}")

    result = run_git_command(
        "git grep -E 'xox[baprs]-[0-9a-zA-Z]{10,48}' -- ':(exclude).git'"
    )

    if result.returncode == 0 and result.stdout.strip():
        print_colored("✗ Found potential Slack tokens", Colors.RED)
        return True
    else:
        print_colored("✓ No Slack tokens found", Colors.GREEN)
        return False


def check_gitignore_coverage():
    """Check .gitignore coverage."""
    print(f"\n{Colors.YELLOW}Verifying .gitignore coverage...{Colors.NC}")

    required_ignores = [
        "*.env",
        "*.pem",
        "*.key",
        "terraform.tfvars",
        ".vault_password",
        "kubeconfig",
        "sp-credentials.json",
    ]

    if not os.path.exists(".gitignore"):
        print_colored("! Warning: .gitignore not found", Colors.YELLOW)
        return

    with open(".gitignore", "r") as f:
        gitignore_content = f.read()

    missing_ignores = False
    for pattern in required_ignores:
        if pattern not in gitignore_content:
            print_colored(f"! Warning: '{pattern}' not in .gitignore", Colors.YELLOW)
            missing_ignores = True

    if not missing_ignores:
        print_colored("✓ All critical patterns in .gitignore", Colors.GREEN)


def main():
    """Run all secret detection checks."""
    print("Scanning repository for secrets and sensitive data...")
    print("=" * 54)

    errors_found = 0

    # Run all checks
    if check_sensitive_files():
        errors_found += 1

    if check_terraform_passwords():
        errors_found += 1

    if check_ansible_passwords():
        errors_found += 1

    if check_aws_credentials():
        errors_found += 1

    check_azure_subscription_ids()

    if check_private_keys():
        errors_found += 1

    if check_github_tokens():
        errors_found += 1

    check_jwt_tokens()

    if check_slack_tokens():
        errors_found += 1

    check_gitignore_coverage()

    # Summary
    print("\n" + "=" * 54)
    if errors_found == 0:
        print_colored("✓ No critical secrets detected!", Colors.GREEN)
        print("\nNote: This script provides basic checks.")
        print("For comprehensive scanning, use:")
        print("  - gitleaks: https://github.com/gitleaks/gitleaks")
        print("  - trufflehog: https://github.com/trufflesecurity/trufflehog")
        print("  - pre-commit hooks: .pre-commit-config.yaml")
        sys.exit(0)
    else:
        print_colored("✗ Potential secrets detected!", Colors.RED)
        print("\nPlease review the findings above and:")
        print("1. Remove any hardcoded secrets")
        print("2. Use Azure Key Vault or environment variables")
        print("3. Ensure sensitive files are in .gitignore")
        print("4. Run 'git reset' to unstage sensitive files")
        print("5. Consider using git-filter-repo if secrets were committed")
        sys.exit(1)


if __name__ == "__main__":
    main()
