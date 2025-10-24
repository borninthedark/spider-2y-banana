#!/usr/bin/env python3
"""
Terraform deployment script for Spider-2y-Banana infrastructure.
Replaces deploy.sh with a Python implementation.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = Colors.NC):
    """Print colored message to console."""
    print(f"{color}{message}{Colors.NC}")


def run_command(command: list[str], cwd: Optional[Path] = None, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Run shell command and handle errors."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"Error running command: {' '.join(command)}", Colors.RED)
        print_colored(f"Error: {e.stderr if e.stderr else str(e)}", Colors.RED)
        sys.exit(1)


def check_prerequisites():
    """Check if required tools are installed."""
    print_colored("Checking prerequisites...", Colors.YELLOW)

    tools = {
        'terraform': 'Terraform',
        'az': 'Azure CLI'
    }

    for cmd, name in tools.items():
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
            print_colored(f"✓ {name} is installed", Colors.GREEN)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_colored(f"✗ {name} is not installed", Colors.RED)
            if cmd == 'terraform':
                print("Install from: https://www.terraform.io/downloads")
            else:
                print("Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
            sys.exit(1)


def check_azure_login():
    """Check if logged into Azure and display subscription."""
    print_colored("\nChecking Azure login status...", Colors.YELLOW)

    try:
        result = run_command(['az', 'account', 'show'], capture_output=True)
        account = json.loads(result.stdout)
        print_colored(f"✓ Logged in to Azure", Colors.GREEN)
        print_colored(f"  Subscription: {account['name']}", Colors.GREEN)
        print_colored(f"  ID: {account['id']}", Colors.GREEN)
        return account
    except subprocess.CalledProcessError:
        print_colored("Not logged in to Azure. Running 'az login'...", Colors.YELLOW)
        run_command(['az', 'login'])
        return check_azure_login()


def check_tfvars(terraform_dir: Path) -> bool:
    """Check if terraform.tfvars exists."""
    tfvars_path = terraform_dir / 'terraform.tfvars'
    example_path = terraform_dir / 'terraform.tfvars.example'

    if not tfvars_path.exists():
        if example_path.exists():
            print_colored("terraform.tfvars not found. Creating from example...", Colors.YELLOW)
            example_path.read_text()
            tfvars_path.write_text(example_path.read_text())
            print_colored("Please edit terraform.tfvars with your SSH public key and re-run", Colors.RED)
            return False
        else:
            print_colored("Neither terraform.tfvars nor example file found", Colors.RED)
            return False

    return True


def terraform_init(terraform_dir: Path):
    """Initialize Terraform."""
    print_colored("\nInitializing Terraform...", Colors.YELLOW)
    run_command(['terraform', 'init'], cwd=terraform_dir)
    print_colored("✓ Terraform initialized", Colors.GREEN)


def terraform_validate(terraform_dir: Path):
    """Validate Terraform configuration."""
    print_colored("\nValidating Terraform configuration...", Colors.YELLOW)
    run_command(['terraform', 'validate'], cwd=terraform_dir)
    print_colored("✓ Configuration valid", Colors.GREEN)


def terraform_plan(terraform_dir: Path):
    """Create Terraform plan."""
    print_colored("\nCreating Terraform plan...", Colors.YELLOW)
    run_command(['terraform', 'plan', '-out=tfplan'], cwd=terraform_dir)
    print_colored("✓ Plan created", Colors.GREEN)


def terraform_apply(terraform_dir: Path):
    """Apply Terraform configuration."""
    print_colored("\nApplying Terraform configuration (this may take 5-10 minutes)...", Colors.YELLOW)
    run_command(['terraform', 'apply', 'tfplan'], cwd=terraform_dir)
    print_colored("✓ Infrastructure deployed", Colors.GREEN)


def get_terraform_outputs(terraform_dir: Path) -> Dict[str, Any]:
    """Retrieve Terraform outputs."""
    print_colored("\nRetrieving deployment outputs...", Colors.YELLOW)

    result = run_command(['terraform', 'output', '-json'], cwd=terraform_dir, capture_output=True)
    outputs = json.loads(result.stdout)

    # Save outputs to file
    outputs_file = terraform_dir / 'outputs.json'
    outputs_file.write_text(json.dumps(outputs, indent=2))
    print_colored(f"✓ Outputs saved to: {outputs_file}", Colors.GREEN)

    return outputs


def display_summary(outputs: Dict[str, Any]):
    """Display deployment summary."""
    print_colored("\n=== Deployment Summary ===", Colors.GREEN)

    summary_items = {
        'Resource Group': 'resource_group_name',
        'VM Public IPs': 'vm_public_ips',
        'Key Vault': 'key_vault_name',
        'Container Registry': 'acr_login_server'
    }

    for label, key in summary_items.items():
        if key in outputs:
            value = outputs[key]['value']
            if isinstance(value, list):
                value = ' '.join(value)
            print(f"{label}: {value}")


def display_next_steps():
    """Display next steps for user."""
    print_colored("\n=== Next Steps ===", Colors.YELLOW)
    print("1. Create service principal:")
    print("   cd scripts && python3 create_service_principal.py dev")
    print("\n2. Update Ansible variables:")
    print("   cd ../ansible && vim group_vars/all.yml")
    print("   Update with outputs from above")
    print("\n3. Bootstrap cluster:")
    print("   ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml")


def main():
    parser = argparse.ArgumentParser(description='Deploy Spider-2y-Banana infrastructure with Terraform')
    parser.add_argument('environment', nargs='?', default='dev', help='Environment name (default: dev)')
    parser.add_argument('--skip-plan', action='store_true', help='Skip terraform plan step')
    parser.add_argument('--auto-approve', action='store_true', help='Auto-approve terraform apply')
    args = parser.parse_args()

    # Get script directory and terraform directory
    script_dir = Path(__file__).parent
    terraform_dir = script_dir.parent

    print_colored(f"Deploying Spider-2y-Banana Infrastructure with Terraform", Colors.GREEN)
    print(f"Environment: {args.environment}\n")

    # Check prerequisites
    check_prerequisites()

    # Check Azure login
    check_azure_login()

    # Check terraform.tfvars
    if not check_tfvars(terraform_dir):
        sys.exit(1)

    # Terraform workflow
    terraform_init(terraform_dir)
    terraform_validate(terraform_dir)

    if not args.skip_plan:
        terraform_plan(terraform_dir)

    if args.auto_approve or input("\nApply this plan? (yes/no): ").lower() == 'yes':
        terraform_apply(terraform_dir)

        # Get and display outputs
        outputs = get_terraform_outputs(terraform_dir)
        display_summary(outputs)
        display_next_steps()

        print_colored("\n✓ Deployment complete!", Colors.GREEN)
    else:
        print_colored("Deployment cancelled", Colors.YELLOW)


if __name__ == '__main__':
    main()
