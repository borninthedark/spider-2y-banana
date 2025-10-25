#!/usr/bin/env python3
"""
Create Azure Service Principal for Crossplane.
Replaces create-service-principal.sh with Python implementation.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    NC = "\033[0m"


def print_colored(message: str, color: str = Colors.NC):
    """Print colored message to console."""
    print(f"{color}{message}{Colors.NC}")


def run_command(
    command: list[str], capture_output: bool = True
) -> subprocess.CompletedProcess:
    """Run shell command and return result."""
    try:
        result = subprocess.run(
            command, capture_output=capture_output, text=True, check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"Error running command: {' '.join(command)}", Colors.RED)
        print_colored(f"Error: {e.stderr if e.stderr else str(e)}", Colors.RED)
        sys.exit(1)


def get_subscription_id() -> str:
    """Get current Azure subscription ID."""
    result = run_command(["az", "account", "show", "--query", "id", "-o", "tsv"])
    return result.stdout.strip()


def create_service_principal(sp_name: str, subscription_id: str) -> Dict[str, str]:
    """Create Azure service principal with Contributor role."""
    print_colored("Creating service principal...", Colors.YELLOW)

    result = run_command(
        [
            "az",
            "ad",
            "sp",
            "create-for-rbac",
            "--name",
            sp_name,
            "--role",
            "Contributor",
            "--scopes",
            f"/subscriptions/{subscription_id}",
        ]
    )

    sp_data = json.loads(result.stdout)

    credentials = {
        "CLIENT_ID": sp_data["appId"],
        "CLIENT_SECRET": sp_data["password"],
        "TENANT_ID": sp_data["tenant"],
        "SUBSCRIPTION_ID": subscription_id,
    }

    print_colored("✓ Service principal created successfully", Colors.GREEN)
    return credentials


def get_key_vault_name(terraform_dir: Path) -> Optional[str]:
    """Get Key Vault name from Terraform outputs."""
    outputs_file = terraform_dir / "outputs.json"

    if not outputs_file.exists():
        return None

    try:
        outputs = json.loads(outputs_file.read_text())
        return outputs.get("key_vault_name", {}).get("value")
    except (json.JSONDecodeError, KeyError):
        return None


def store_credentials_in_keyvault(key_vault_name: str, credentials: Dict[str, str]):
    """Store service principal credentials in Azure Key Vault."""
    print_colored(
        f"\nStoring credentials in Key Vault: {key_vault_name}", Colors.YELLOW
    )

    secret_mapping = {
        "crossplane-client-id": credentials["CLIENT_ID"],
        "crossplane-client-secret": credentials["CLIENT_SECRET"],
        "crossplane-tenant-id": credentials["TENANT_ID"],
        "crossplane-subscription-id": credentials["SUBSCRIPTION_ID"],
    }

    for secret_name, secret_value in secret_mapping.items():
        run_command(
            [
                "az",
                "keyvault",
                "secret",
                "set",
                "--vault-name",
                key_vault_name,
                "--name",
                secret_name,
                "--value",
                secret_value,
            ],
            capture_output=True,
        )

    print_colored("✓ Credentials stored in Key Vault", Colors.GREEN)


def display_credentials(credentials: Dict[str, str]):
    """Display service principal credentials."""
    print_colored("\n=== Service Principal Credentials ===", Colors.GREEN)
    print("\nSave these credentials securely:")
    for key, value in credentials.items():
        print(f"{key}: {value}")


def save_credentials_to_file(credentials: Dict[str, str], output_file: Path):
    """Save credentials to a file for Ansible."""
    output_file.write_text(json.dumps(credentials, indent=2))
    print_colored(f"\n✓ Credentials saved to: {output_file}", Colors.GREEN)


def display_next_steps():
    """Display next steps for user."""
    print_colored("\n=== Next Steps ===", Colors.YELLOW)
    print("1. Update Ansible variables:")
    print("   cd ../ansible && vim group_vars/all.yml")
    print("\n2. Add these values to group_vars/all.yml:")
    print("   azure_subscription_id: <SUBSCRIPTION_ID>")
    print("   azure_tenant_id: <TENANT_ID>")
    print("   azure_client_id: <CLIENT_ID>")
    print("   azure_client_secret: <CLIENT_SECRET>")
    print("\n3. Or use the saved JSON file:")
    print("   ansible-playbook playbooks/bootstrap-all.yml \\")
    print("     -e @scripts/sp-credentials.json")


def main():
    parser = argparse.ArgumentParser(
        description="Create Azure Service Principal for Crossplane"
    )
    parser.add_argument(
        "environment", nargs="?", default="dev", help="Environment name (default: dev)"
    )
    parser.add_argument(
        "--no-keyvault", action="store_true", help="Skip storing in Key Vault"
    )
    parser.add_argument("--output-file", type=Path, help="Save credentials to file")
    args = parser.parse_args()

    sp_name = f"sp-crossplane-{args.environment}"

    print_colored("Creating Service Principal for Crossplane", Colors.GREEN)
    print(f"Name: {sp_name}\n")

    # Get subscription ID
    subscription_id = get_subscription_id()
    print(f"Subscription ID: {subscription_id}\n")

    # Create service principal
    credentials = create_service_principal(sp_name, subscription_id)

    # Display credentials
    display_credentials(credentials)

    # Get Terraform directory
    script_dir = Path(__file__).parent
    terraform_dir = script_dir.parent

    # Store in Key Vault if available and not disabled
    if not args.no_keyvault:
        key_vault_name = get_key_vault_name(terraform_dir)
        if key_vault_name:
            store_credentials_in_keyvault(key_vault_name, credentials)
        else:
            print_colored("\n⚠ Key Vault not found in Terraform outputs", Colors.YELLOW)
            print("Run Terraform deployment first, or use --no-keyvault flag")

    # Save to file if requested
    if args.output_file:
        save_credentials_to_file(credentials, args.output_file)
    else:
        # Save to default location
        default_file = script_dir / "sp-credentials.json"
        save_credentials_to_file(credentials, default_file)

    # Display next steps
    display_next_steps()


if __name__ == "__main__":
    main()
