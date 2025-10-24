#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}

echo -e "${GREEN}Deploying Lavish-k3s Infrastructure with Terraform${NC}"
echo "Environment: ${ENVIRONMENT}"
echo ""

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    echo "Install from: https://www.terraform.io/downloads"
    exit 1
fi

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    echo "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check Terraform Cloud authentication
echo -e "${YELLOW}Checking Terraform Cloud authentication...${NC}"
if [ -z "$TF_TOKEN_app_terraform_io" ] && [ ! -f "$HOME/.terraform.d/credentials.tfrc.json" ]; then
    echo -e "${RED}Error: Not authenticated to Terraform Cloud${NC}"
    echo "Please run one of the following:"
    echo "  1. terraform login"
    echo "  2. export TF_TOKEN_app_terraform_io=\"your-token\""
    exit 1
fi
echo -e "${GREEN}Terraform Cloud authentication detected${NC}"
echo ""

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Azure. Running 'az login'...${NC}"
    az login
fi

# Get current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${GREEN}Using subscription: ${SUBSCRIPTION}${NC}"
echo ""

# Check for terraform.tfvars
if [ ! -f "../terraform.tfvars" ]; then
    echo -e "${YELLOW}terraform.tfvars not found. Creating from example...${NC}"
    cp ../terraform.tfvars.example ../terraform.tfvars
    echo -e "${RED}Please edit terraform.tfvars with your SSH public key and run again${NC}"
    exit 1
fi

# Initialize Terraform
echo -e "${YELLOW}Initializing Terraform...${NC}"
cd ..
terraform init

# Validate configuration
echo -e "${YELLOW}Validating Terraform configuration...${NC}"
terraform validate

if [ $? -ne 0 ]; then
    echo -e "${RED}Terraform validation failed${NC}"
    exit 1
fi

echo -e "${GREEN}Validation successful${NC}"
echo ""

# Plan
echo -e "${YELLOW}Creating Terraform plan...${NC}"
terraform plan -out=tfplan

# Apply
echo -e "${YELLOW}Applying Terraform configuration (this may take 5-10 minutes)...${NC}"
terraform apply tfplan

if [ $? -ne 0 ]; then
    echo -e "${RED}Terraform apply failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Deployment successful!${NC}"
echo ""

# Get outputs
echo -e "${YELLOW}Retrieving deployment outputs...${NC}"
VM_IPS=$(terraform output -json vm_public_ips | jq -r '.[]' | tr '\n' ' ')
KEY_VAULT_NAME=$(terraform output -raw key_vault_name)
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
RESOURCE_GROUP=$(terraform output -raw resource_group_name)

echo ""
echo -e "${GREEN}=== Deployment Summary ===${NC}"
echo "Resource Group: ${RESOURCE_GROUP}"
echo "VM Public IPs: ${VM_IPS}"
echo "Key Vault: ${KEY_VAULT_NAME}"
echo "Container Registry: ${ACR_LOGIN_SERVER}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update ansible/group_vars/all.yml with outputs above"
echo "2. Run: cd ../ansible && ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml"
echo ""

# Save outputs to JSON
terraform output -json > outputs.json
echo -e "${GREEN}Outputs saved to: terraform-infrastructure/outputs.json${NC}"
