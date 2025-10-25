# Python Scripts Quick Reference

This guide provides quick reference for all Python scripts in the project.

## Installation

```bash
# Install all dependencies
pip install -r requirements.txt
```

## Testing Scripts

### Test Docker Build & Container

```bash
cd osyraa/tests
python3 test_docker.py
```

**What it does:**
- Builds Docker image
- Starts container on port 8080
- Tests HTTP endpoints
- Checks security headers
- Cleans up resources

### Test Hugo Build

```bash
cd osyraa/tests
python3 test_build.py
```

**What it does:**
- Runs Hugo build in Docker
- Validates HTML structure
- Checks for required content
- Cleans up artifacts

## Infrastructure Scripts

### Deploy with Terraform

```bash
cd terraform-infrastructure/scripts
python3 deploy.py [environment]

# Options:
python3 deploy.py dev                    # Deploy dev environment
python3 deploy.py prod --auto-approve    # Auto-approve apply
python3 deploy.py dev --skip-plan        # Skip plan step
```

**What it does:**
- Validates prerequisites (Terraform, Azure CLI)
- Checks Azure authentication
- Runs terraform init/validate/plan/apply
- Displays deployment outputs
- Saves outputs to JSON

### Create Azure Service Principal

```bash
cd terraform-infrastructure/scripts
python3 create_service_principal.py [environment]

# Options:
python3 create_service_principal.py dev                           # Create for dev
python3 create_service_principal.py prod --no-keyvault           # Skip Key Vault
python3 create_service_principal.py dev --output-file ~/creds.json # Save to file
```

**What it does:**
- Creates Azure AD service principal
- Assigns Contributor role
- Stores credentials in Key Vault
- Saves credentials to file
- Displays next steps

## Utility Scripts

### Run Pre-commit in Podman Container

```bash
python3 scripts/run-precommit-podman.py [options] [precommit-args]

# Examples:
python3 scripts/run-precommit-podman.py                      # Run all hooks
python3 scripts/run-precommit-podman.py run trailing-whitespace  # Run specific hook
python3 scripts/run-precommit-podman.py --build run --all-files  # Force rebuild
python3 scripts/run-precommit-podman.py --clean              # Remove container image
python3 scripts/run-precommit-podman.py --verbose run --all-files  # Verbose output
```

**What it does:**
- Runs pre-commit hooks in an isolated container environment
- Auto-builds container image on first run
- Ensures consistent tool versions across systems
- Supports all pre-commit commands and options
- Handles missing system dependencies gracefully

**Benefits:**
- No need to install Ruby, Go, Terraform, etc. on host
- Isolated from system package conflicts
- Reproducible across different machines
- Easy to share with team members

### Check for Secrets

```bash
python3 scripts/check-secrets.py
```

**What it does:**
- Scans for sensitive files
- Checks for hardcoded passwords
- Detects AWS/Azure/GitHub tokens
- Validates .gitignore coverage
- Returns exit code 1 if secrets found

### Update Domain Name

```bash
python3 scripts/update-domain.py <new-domain>

# Example:
python3 scripts/update-domain.py example.com
python3 scripts/update-domain.py newdomain.com --old-domain princetonstrong.online
```

**What it does:**
- Updates domain across config files
- Modifies YAML manifests
- Updates documentation
- Displays next steps for rebuild

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_utils.py

# Run with coverage
pytest --cov=scripts --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=scripts --cov-report=html
open htmlcov/index.html
```

## Using Shared Utilities

Import common functions from `scripts/utils.py`:

```python
from scripts.utils import (
    Colors,
    print_success,
    print_error,
    print_warning,
    run_command,
    check_command_exists,
    get_project_root,
    confirm_action
)

# Print colored messages
print_success("Operation completed!")
print_error("Something went wrong")
print_warning("This is a warning")

# Run commands
result = run_command(["ls", "-la"], capture_output=True)
print(result.stdout)

# Check if command exists
if check_command_exists("docker"):
    print("Docker is installed")

# Get project root
root = get_project_root()
config_file = root / "config" / "settings.yaml"

# Confirm user action
if confirm_action("Delete all resources?"):
    delete_resources()
```

## Common Issues

### Import Error for utils module

```bash
# If you get "ModuleNotFoundError: No module named 'utils'"
# Make sure you're running from the project root:
cd /home/doom/Workspaces/spider-2y-banana
python3 scripts/check-secrets.py

# Or add scripts to PYTHONPATH:
export PYTHONPATH="${PYTHONPATH}:/home/doom/Workspaces/spider-2y-banana/scripts"
```

### Missing Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or install individually
pip install pytest pytest-cov requests
```

### Azure Authentication

```bash
# Login to Azure
az login

# Verify subscription
az account show

# Switch subscription if needed
az account set --subscription "Your Subscription Name"
```

### Terraform Cloud Authentication

```bash
# Option 1: Interactive login
terraform login

# Option 2: Environment variable
export TF_TOKEN_app_terraform_io="your-token-here"

# Option 3: Credentials file
cat > ~/.terraform.d/credentials.tfrc.json <<EOF
{
  "credentials": {
    "app.terraform.io": {
      "token": "your-token-here"
    }
  }
}
EOF
```

## Script Comparison: Shell vs Python

| Feature | Shell (.sh) | Python (.py) |
|---------|-------------|--------------|
| Error handling | Basic | Comprehensive |
| Type safety | None | Type hints |
| Testing | Difficult | Easy with pytest |
| Cross-platform | Limited | Excellent |
| Code reuse | Hard | Easy with imports |
| Documentation | Comments only | Docstrings + type hints |
| IDE support | Limited | Excellent |

## Best Practices

1. **Always run from project root** for correct relative paths
2. **Use --help flag** to see all options: `script.py --help`
3. **Check exit codes** in scripts: `echo $?` after running
4. **Run tests before committing**: `pytest && python3 scripts/check-secrets.py`
5. **Keep secrets out of git**: Use `.env` files (in .gitignore)

## Getting Help

```bash
# Every script supports --help
python3 scripts/update-domain.py --help
python3 terraform-infrastructure/scripts/deploy.py --help

# View script source (well-documented)
less scripts/check-secrets.py

# Read comprehensive guides
cat SECRETS.md
cat AUDIT_SUMMARY.md
```

## Quick Commands Cheat Sheet

```bash
# Test suite
pytest                                          # Run all tests
pytest -v --cov                                # Tests with coverage

# Secret scanning
python3 scripts/check-secrets.py              # Scan for secrets

# Infrastructure
python3 terraform-infrastructure/scripts/deploy.py dev    # Deploy
python3 terraform-infrastructure/scripts/create_service_principal.py dev  # Create SP

# Domain management
python3 scripts/update-domain.py newdomain.com # Update domain

# Testing
python3 osyraa/tests/test_docker.py           # Test Docker
python3 osyraa/tests/test_build.py            # Test build
```

## Documentation Links

- **SECRETS.md** - Complete secrets management guide
- **AUDIT_SUMMARY.md** - Project audit and improvements
- **requirements.txt** - Python dependencies
- **pytest.ini** - Test configuration

---

For more details, see the comprehensive documentation in `SECRETS.md` and `AUDIT_SUMMARY.md`.
