## Terraform Infrastructure

Azure infrastructure provisioning using Terraform for the Spider-2y-Banana GitOps platform.

## Overview

This Terraform configuration deploys the foundation infrastructure for running k3s Kubernetes clusters on Azure with:

- Virtual Machines for k3s nodes (1 for dev, 3 for HA prod)
- Virtual Network and subnets
- Network Security Groups with required firewall rules
- Azure Key Vault for secrets management
- Azure Container Registry for container images
- Cloud-init configuration for VM preparation

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.5.0
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Azure subscription
- SSH key pair
- [Terraform Cloud](https://app.terraform.io) account (for remote state management)

## Terraform Cloud Setup

This project uses Terraform Cloud for remote state management and collaboration.

### Authentication (Choose One Method)

**Method 1: Interactive Login (Recommended for local development)**
```bash
terraform login
```
This will open a browser to authenticate and store credentials securely in `~/.terraform.d/credentials.tfrc.json`.

**Method 2: Environment Variable (Recommended for CI/CD)**
```bash
export TF_TOKEN_app_terraform_io="your-terraform-cloud-token"
```

**IMPORTANT: Never commit Terraform Cloud tokens to Git!**
- Credentials are automatically ignored via `.gitignore`
- Use GitHub Secrets or environment variables in CI/CD pipelines
- The `.gitignore` includes:
  - `.terraform.d/`
  - `credentials.tfrc.json`
  - `.terraformrc`

### Workspace Configuration

The configuration is set up for:
- **Organization**: `DefiantEmissary`
- **Workspace**: `spider-2y-banana`
- **Project**: `DeepSpaceNine` (via tags)

Ensure the workspace exists in Terraform Cloud before running `terraform init`.

## Quick Start

### 1. Login to Azure

```bash
az login
az account set --subscription "Your Subscription Name"
```

### 2. Configure Variables

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

Required values:
- `ssh_public_key`: Your SSH public key (contents of ~/.ssh/id_rsa.pub)
- `environment`: dev, staging, or prod
- `node_count`: 1 for dev, 3 for HA

### 3. Deploy Infrastructure

```bash
cd scripts
./deploy.sh dev
```

Or manually:

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

### 4. Create Service Principal

```bash
cd scripts
./create-service-principal.sh dev
```

Save the output credentials for Ansible configuration.

## Module Structure

```
terraform-infrastructure/
├── main.tf                    # Root module
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example variables
├── scripts/
│   ├── deploy.sh             # Automated deployment
│   └── create-service-principal.sh
└── modules/
    ├── network/              # VNet, subnet, NSG
    ├── vm/                   # Virtual machines
    ├── keyvault/             # Azure Key Vault
    └── acr/                  # Container Registry
```

## Resources Created

### Network Module
- **Virtual Network**: 10.0.0.0/16 address space
- **Subnet**: 10.0.1.0/24 for k3s nodes
- **Network Security Group**:
  - SSH (22)
  - Kubernetes API (6443)
  - HTTP (80)
  - HTTPS (443)
  - Internal cluster communication

### VM Module (per node)
- **Public IP**: Static, Standard SKU
- **Network Interface**: Connected to subnet
- **Linux VM**:
  - Ubuntu 22.04 LTS
  - Cloud-init configured
  - SSH key authentication
  - Tags: Role, NodeIndex

### Key Vault Module
- **Azure Key Vault**:
  - RBAC authorization
  - Soft delete enabled (7 days)
  - Public access enabled

### ACR Module
- **Container Registry**:
  - Basic SKU
  - Admin user enabled
  - Public access enabled

## Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `environment` | Environment name | dev | No |
| `location` | Azure region | eastus | No |
| `admin_username` | VM admin username | azureuser | No |
| `ssh_public_key` | SSH public key | - | Yes |
| `node_count` | Number of nodes (1 or 3) | 1 | No |
| `vm_size` | Azure VM size | Standard_B2ms | No |
| `disk_size_gb` | OS disk size in GB | 128 | No |
| `tags` | Resource tags | {} | No |

## Outputs

| Output | Description |
|--------|-------------|
| `resource_group_name` | Name of the resource group |
| `vnet_name` | Virtual network name |
| `subnet_name` | Subnet name |
| `key_vault_name` | Key Vault name |
| `key_vault_uri` | Key Vault URI |
| `acr_login_server` | ACR login server URL |
| `acr_name` | ACR name |
| `vm_public_ips` | Array of VM public IPs |
| `vm_private_ips` | Array of VM private IPs |
| `vm_names` | Array of VM names |
| `vm_fqdns` | Array of VM FQDNs |

## Environments

### Development (Single Node)

```hcl
environment  = "dev"
node_count   = 1
vm_size      = "Standard_B2ms"
disk_size_gb = 128
```

**Cost**: ~$87/month

### Production (HA - 3 Nodes)

```hcl
environment  = "prod"
node_count   = 3
vm_size      = "Standard_B2ms"
disk_size_gb = 128
```

**Cost**: ~$337/month

## Cost Estimation

Use `terraform plan` to see resource counts, or:

```bash
# Install cost estimation tool
terraform init
terraform plan -out=tfplan
terraform show -json tfplan | jq > plan.json

# Use Infracost (optional)
infracost breakdown --path .
```

### Estimated Monthly Costs (East US)

| Component | Dev (1 node) | Prod (3 nodes) |
|-----------|--------------|----------------|
| VMs (B2ms) | $65 | $195 |
| Managed Disks | $6 | $18 |
| Public IPs | $3 | $9 |
| Key Vault | $1 | $1 |
| ACR Basic | $5 | $5 |
| **Subtotal** | **~$80** | **~$228** |
| + Azure services | +$7-10 | +$109-120 |
| **Total** | **~$87-90** | **~$337-348** |

## State Management

### Local State (Default)

State is stored locally in `terraform.tfstate`. **Do not commit this file to git.**

### Remote State (Recommended for Teams)

Configure Azure Storage backend:

```hcl
# backend.tf
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "sttfstate<unique>"
    container_name       = "tfstate"
    key                  = "spider-2y-banana-${var.environment}.tfstate"
  }
}
```

Initialize with backend:

```bash
terraform init -backend-config="key=spider-2y-banana-dev.tfstate"
```

## Workspaces

Use Terraform workspaces for multiple environments:

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select dev

# Deploy to current workspace
terraform apply -var="environment=dev"
```

## Outputs Usage

### Save Outputs

```bash
# Save all outputs to JSON
terraform output -json > outputs.json

# Get specific output
terraform output -raw vm_public_ips
terraform output -raw key_vault_name
```

### Use in Ansible

```bash
# Extract outputs for Ansible
export VM_IP=$(terraform output -json vm_public_ips | jq -r '.[0]')
export KEY_VAULT=$(terraform output -raw key_vault_name)
export ACR_SERVER=$(terraform output -raw acr_login_server)

# Update Ansible variables
cat > ../ansible/group_vars/all.yml <<EOF
azure_key_vault_name: "${KEY_VAULT}"
acr_login_server: "${ACR_SERVER}"
EOF
```

## Advanced Usage

### Targeting Specific Resources

```bash
# Only recreate VMs
terraform apply -target=module.vms

# Only update network
terraform apply -target=module.network
```

### Import Existing Resources

```bash
# Import existing resource group
terraform import azurerm_resource_group.main /subscriptions/SUB_ID/resourceGroups/rg-name

# Import existing VM
terraform import 'module.vms[0].azurerm_linux_virtual_machine.main' /subscriptions/SUB_ID/resourceGroups/rg-name/providers/Microsoft.Compute/virtualMachines/vm-name
```

### Conditional Resources

Create resources conditionally:

```hcl
# Only create NAT Gateway in prod
resource "azurerm_nat_gateway" "main" {
  count = var.environment == "prod" ? 1 : 0
  # ...
}
```

## Troubleshooting

### Terraform Init Fails

```bash
# Clear cache and reinitialize
rm -rf .terraform .terraform.lock.hcl
terraform init
```

### State Lock Issues

```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

### VM Creation Fails

Check quotas:
```bash
az vm list-usage --location eastus -o table
```

### Key Vault Name Conflicts

Key Vault names must be globally unique. The module uses a random suffix, but if deployment fails:

```bash
# Destroy and recreate
terraform destroy -target=module.keyvault
terraform apply
```

## Validation

### Pre-deployment Validation

```bash
# Format check
terraform fmt -check -recursive

# Validation
terraform validate

# Security scan (optional)
tfsec .
```

### Post-deployment Verification

```bash
# List resources
az resource list -g $(terraform output -raw resource_group_name) -o table

# Test VM SSH access
ssh azureuser@$(terraform output -json vm_public_ips | jq -r '.[0]')

# Test ACR access
az acr login --name $(terraform output -raw acr_name)
```

## Cleanup

### Destroy All Resources

```bash
terraform destroy
```

Or delete resource group:

```bash
az group delete --name $(terraform output -raw resource_group_name) --yes
```

### Destroy Specific Resources

```bash
# Only destroy VMs
terraform destroy -target=module.vms
```

## Migration from Bicep

If migrating from the Bicep version:

1. Export Bicep outputs
2. Create `terraform.tfvars` with same values
3. Run `terraform import` for existing resources (if keeping them)
4. Or destroy Bicep resources and create fresh with Terraform

## Best Practices

1. **Always run `terraform plan` before apply**
2. **Use remote state for team collaboration**
3. **Enable state locking with Azure Storage backend**
4. **Tag all resources for cost tracking**
5. **Use workspaces for multiple environments**
6. **Never commit `terraform.tfvars` or state files**
7. **Use `-out=tfplan` to review plans before applying**
8. **Implement CI/CD with Terraform Cloud or Azure DevOps**

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Terraform

on:
  push:
    branches: [main]
    paths: ['terraform-infrastructure/**']

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -out=tfplan

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: terraform apply tfplan
```

## Next Steps

After infrastructure deployment:

1. Update `ansible/group_vars/all.yml` with Terraform outputs
2. Run `create-service-principal.sh` for Crossplane credentials
3. Execute Ansible bootstrap: `ansible-playbook playbooks/bootstrap-all.yml`
4. Deploy GitOps applications with ArgoCD

## Support

- Terraform Documentation: https://www.terraform.io/docs
- Azure Provider Docs: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
- Project README: [../README.md](../README.md)

---

**Managed by**: Terraform >= 1.5.0
**Azure Provider**: ~> 3.80
