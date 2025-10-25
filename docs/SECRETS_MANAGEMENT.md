# Secrets Management Guide

This document provides a comprehensive guide for managing secrets across the spider-2y-banana infrastructure project.

## Table of Contents

- [Overview](#overview)
- [Code Coverage](#code-coverage)
- [GitHub Actions Secrets](#github-actions-secrets)
- [Terraform Cloud Configuration](#terraform-cloud-configuration)
- [Azure Secrets](#azure-secrets)
- [Local Development](#local-development)
- [Security Best Practices](#security-best-practices)

## Overview

This project requires secrets for several environments:

1. **GitHub Actions**: CI/CD pipeline automation
2. **Terraform Cloud**: Infrastructure provisioning
3. **Azure**: Cloud resource management
4. **Local Development**: Developer workstation configuration

## Code Coverage

### What is Code Coverage?

**Code coverage** is a metric that measures the percentage of your source code that is executed during automated tests. It helps identify:

- **Tested code**: Lines, branches, and functions that are covered by tests
- **Untested code**: Areas that may contain bugs because they lack test coverage
- **Test quality**: Whether tests actually exercise the code they're supposed to validate

### Coverage Metrics

Our project uses **pytest-cov** to track coverage:

```bash
# Run tests with coverage
pytest --cov=scripts --cov-report=term-missing

# Generate HTML report
pytest --cov=scripts --cov-report=html:htmlcov
```

### Current Coverage Status

- **scripts/utils.py**: 83% coverage (shared utilities)
- **Target**: Maintain >80% coverage for all Python modules

### Interpreting Coverage Reports

```
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
scripts/utils.py          53      9    83%   72, 120, 122-128
```

- **Stmts**: Total number of executable statements
- **Miss**: Number of statements not executed by tests
- **Cover**: Percentage of statements covered
- **Missing**: Line numbers of uncovered statements

High coverage (>80%) indicates well-tested code, but 100% coverage doesn't guarantee bug-free code. Focus on testing critical paths and edge cases.

## GitHub Actions Secrets

GitHub Actions requires the following secrets for CI/CD workflows.

### Required Secrets

Navigate to: **Repository Settings → Secrets and variables → Actions**

#### Azure Authentication

```
AZURE_CLIENT_ID
  Description: Service Principal Application ID
  How to get: Run scripts/create_service_principal.py
  Example: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

AZURE_CLIENT_SECRET
  Description: Service Principal Password
  How to get: Output from create_service_principal.py
  Security: Rotate every 90 days
  Note: This is sensitive - never commit to git

AZURE_SUBSCRIPTION_ID
  Description: Azure Subscription ID
  How to get: az account show --query id -o tsv
  Example: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

AZURE_TENANT_ID
  Description: Azure Active Directory Tenant ID
  How to get: az account show --query tenantId -o tsv
  Example: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### Container Registry

```
ACR_LOGIN_SERVER
  Description: Azure Container Registry URL
  How to get: Terraform output acr_login_server
  Example: myacr.azurecr.io

ACR_USERNAME
  Description: ACR admin username
  How to get: az acr credential show --name <acr-name> --query username

ACR_PASSWORD
  Description: ACR admin password
  How to get: az acr credential show --name <acr-name> --query passwords[0].value
  Security: Enable admin user only when needed
```

#### Kubernetes

```
KUBECONFIG_BASE64
  Description: Base64-encoded kubeconfig file
  How to get: base64 -w 0 < ~/.kube/config
  Security: Limit to specific namespace if possible
```

### Setting Up GitHub Secrets

```bash
# Example: Using GitHub CLI
gh secret set AZURE_CLIENT_ID --body "your-client-id"
gh secret set AZURE_CLIENT_SECRET --body "your-client-secret"
gh secret set AZURE_SUBSCRIPTION_ID --body "your-subscription-id"
gh secret set AZURE_TENANT_ID --body "your-tenant-id"
```

Or via the GitHub web interface:
1. Go to repository **Settings**
2. Click **Secrets and variables → Actions**
3. Click **New repository secret**
4. Enter name and value
5. Click **Add secret**

## Terraform Cloud Configuration

### Workspace Variables

Navigate to: **Terraform Cloud → Workspace → Variables**

#### Azure Provider Variables (Sensitive)

```
ARM_CLIENT_ID
  Description: Service Principal Application ID
  Category: Environment variable
  Sensitive: Yes
  Value: <same as AZURE_CLIENT_ID>

ARM_CLIENT_SECRET
  Description: Service Principal Password
  Category: Environment variable
  Sensitive: Yes
  Value: <same as AZURE_CLIENT_SECRET>

ARM_SUBSCRIPTION_ID
  Description: Azure Subscription ID
  Category: Environment variable
  Sensitive: Yes
  Value: <same as AZURE_SUBSCRIPTION_ID>

ARM_TENANT_ID
  Description: Azure Tenant ID
  Category: Environment variable
  Sensitive: Yes
  Value: <same as AZURE_TENANT_ID>
```

#### Terraform Variables

```
ssh_public_key
  Description: SSH public key for VM access
  Category: Terraform variable
  Sensitive: Yes
  How to get: cat ~/.ssh/id_rsa.pub
  Value: ssh-rsa AAAAB3NzaC1yc2E...

admin_username
  Description: Admin username for VMs
  Category: Terraform variable
  Sensitive: No
  Value: azureuser

environment
  Description: Deployment environment
  Category: Terraform variable
  Sensitive: No
  Value: dev | staging | prod

domain_name
  Description: Custom domain name
  Category: Terraform variable
  Sensitive: No
  Value: princetonstrong.online
```

### Authentication Token

Store your Terraform Cloud token locally:

```bash
# Option 1: Using terraform login
terraform login

# Option 2: Manual configuration
mkdir -p ~/.terraform.d
cat > ~/.terraform.d/credentials.tfrc.json <<EOF
{
  "credentials": {
    "app.terraform.io": {
      "token": "YOUR_TERRAFORM_CLOUD_TOKEN"
    }
  }
}
EOF

# Option 3: Environment variable
export TF_TOKEN_app_terraform_io="YOUR_TERRAFORM_CLOUD_TOKEN"
```

To generate a token:
1. Log in to Terraform Cloud
2. Click your avatar → **User Settings**
3. Go to **Tokens**
4. Click **Create an API token**
5. Save the token securely

## Azure Secrets

### Key Vault

Azure Key Vault stores secrets for runtime access:

```bash
# Create secrets in Key Vault
az keyvault secret set \
  --vault-name <keyvault-name> \
  --name "crossplane-client-id" \
  --value "<client-id>"

az keyvault secret set \
  --vault-name <keyvault-name> \
  --name "crossplane-client-secret" \
  --value "<client-secret>"

# Retrieve secrets
az keyvault secret show \
  --vault-name <keyvault-name> \
  --name "crossplane-client-id" \
  --query value -o tsv
```

### Service Principal Creation

Use our Python script to create a service principal:

```bash
# Create service principal for an environment
cd terraform-infrastructure/scripts
python3 create_service_principal.py dev

# With options
python3 create_service_principal.py prod --no-keyvault
python3 create_service_principal.py dev --output-file ~/sp-creds.json
```

This script will:
1. Create an Azure AD service principal
2. Assign Contributor role to your subscription
3. Store credentials in Key Vault (if available)
4. Save credentials to a JSON file
5. Display next steps for configuration

## Local Development

### Environment Variables

Create a `.env` file in the project root (DO NOT COMMIT):

```bash
# .env file (add to .gitignore)
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
export DOMAIN_NAME="princetonstrong.online"

# Load with:
source .env
```

### .gitignore Coverage

Ensure these patterns are in `.gitignore`:

```
# Secrets and credentials
*.env
.env*
*.pem
*.key
*_rsa
terraform.tfvars
sp-credentials.json
credentials.json
.vault_password
kubeconfig
*.kubeconfig
k3s.yaml
auth.json
service-account*.json

# Terraform
.terraform/
*.tfstate
*.tfstate.backup
.terraform.lock.hcl

# Python
__pycache__/
*.pyc
venv/
.pytest_cache/
htmlcov/
coverage.xml
```

## Security Best Practices

### 1. Never Commit Secrets

```bash
# Run secret scanner before committing
python3 scripts/check-secrets.py

# Add as pre-commit hook
cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
python3 scripts/check-secrets.py
EOF
chmod +x .git/hooks/pre-commit
```

### 2. Rotate Secrets Regularly

- **Service Principal Secrets**: Every 90 days
- **SSH Keys**: Every 180 days
- **ACR Passwords**: Every 90 days
- **Personal Access Tokens**: Every 180 days

```bash
# Rotate Azure service principal credentials
az ad sp credential reset --id <service-principal-id>
```

### 3. Use Least Privilege

- Grant minimum required permissions
- Use resource-scoped service principals when possible
- Enable RBAC on all resources

```bash
# Create limited-scope service principal
az ad sp create-for-rbac \
  --name "sp-limited-scope" \
  --role Reader \
  --scopes "/subscriptions/{subscription-id}/resourceGroups/{resource-group}"
```

### 4. Enable Audit Logging

- Azure Activity Log
- Key Vault logging
- Terraform Cloud audit trail
- GitHub Actions logs

### 5. Use Secret Scanning Tools

Recommended tools:
- **gitleaks**: https://github.com/gitleaks/gitleaks
- **trufflehog**: https://github.com/trufflesecurity/trufflehog
- **detect-secrets**: https://github.com/Yelp/detect-secrets

```bash
# Install gitleaks
brew install gitleaks  # macOS
# or
docker run -v $(pwd):/repo gitleaks/gitleaks:latest detect --source /repo

# Scan for secrets
gitleaks detect --source . --verbose
```

### 6. Emergency Response

If secrets are committed:

```bash
# 1. Revoke the compromised secret immediately
az ad sp credential reset --id <service-principal-id>

# 2. Remove from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret/file" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force push (coordinate with team)
git push origin --force --all

# 4. Rotate all related secrets

# 5. Review access logs for unauthorized use
az monitor activity-log list --max-events 100
```

## Python Scripts Self-Documentation

All Python scripts in this project include:

### Docstrings

Every module, class, and function has documentation:

```python
"""Module description.

Detailed explanation of what the module does.
"""

def function_name(param: str) -> bool:
    """Brief description.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Example:
        >>> function_name("test")
        True
    """
```

### Type Hints

All functions use type annotations:

```python
from pathlib import Path
from typing import Optional, Dict, List

def process_config(
    config_path: Path,
    options: Optional[Dict[str, str]] = None
) -> List[str]:
    """Process configuration file."""
    ...
```

### Usage Examples

Run any script with `--help`:

```bash
python3 scripts/update-domain.py --help
python3 terraform-infrastructure/scripts/deploy.py --help
python3 scripts/check-secrets.py  # No args needed
```

## Testing Your Scripts

Run the test suite:

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_utils.py -v

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html
```

## Additional Resources

- [Azure Key Vault Best Practices](https://docs.microsoft.com/azure/key-vault/general/best-practices)
- [GitHub Actions Security](https://docs.github.com/actions/security-guides/security-hardening-for-github-actions)
- [Terraform Cloud Variables](https://www.terraform.io/cloud-docs/workspaces/variables)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## Support

If you discover a security issue:
1. **DO NOT** create a public issue
2. Contact the security team directly
3. Follow responsible disclosure practices

For general questions about secrets management:
- Check this documentation first
- Review the scripts in `scripts/` directory
- Check existing issues on GitHub
