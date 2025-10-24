#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
LOCATION=${2:-eastus}
RESOURCE_GROUP="rg-lavish-k3s-${ENVIRONMENT}"

echo -e "${GREEN}Deploying Lavish-k3s Infrastructure${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Location: ${LOCATION}"
echo "Resource Group: ${RESOURCE_GROUP}"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    echo "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Azure. Running 'az login'...${NC}"
    az login
fi

# Get current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${GREEN}Using subscription: ${SUBSCRIPTION}${NC}"
echo ""

# Create resource group if it doesn't exist
echo -e "${YELLOW}Creating resource group...${NC}"
az group create \
    --name "${RESOURCE_GROUP}" \
    --location "${LOCATION}" \
    --tags Environment="${ENVIRONMENT}" Project="lavish-k3s" ManagedBy="Bicep"

echo ""

# Validate Bicep template
echo -e "${YELLOW}Validating Bicep template...${NC}"
az deployment group validate \
    --resource-group "${RESOURCE_GROUP}" \
    --template-file ../main.bicep \
    --parameters "../parameters.${ENVIRONMENT}.json"

if [ $? -ne 0 ]; then
    echo -e "${RED}Template validation failed${NC}"
    exit 1
fi

echo -e "${GREEN}Template validation successful${NC}"
echo ""

# Deploy infrastructure
echo -e "${YELLOW}Deploying infrastructure (this may take 5-10 minutes)...${NC}"
DEPLOYMENT_NAME="lavish-k3s-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --template-file ../main.bicep \
    --parameters "../parameters.${ENVIRONMENT}.json" \
    --verbose

if [ $? -ne 0 ]; then
    echo -e "${RED}Deployment failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Deployment successful!${NC}"
echo ""

# Get outputs
echo -e "${YELLOW}Retrieving deployment outputs...${NC}"
VM_IPS=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query 'properties.outputs.vmPublicIps.value' \
    -o tsv)

KEY_VAULT_NAME=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query 'properties.outputs.keyVaultName.value' \
    -o tsv)

ACR_LOGIN_SERVER=$(az deployment group show \
    --name "${DEPLOYMENT_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query 'properties.outputs.acrLoginServer.value' \
    -o tsv)

echo ""
echo -e "${GREEN}=== Deployment Summary ===${NC}"
echo "VM Public IPs: ${VM_IPS}"
echo "Key Vault: ${KEY_VAULT_NAME}"
echo "Container Registry: ${ACR_LOGIN_SERVER}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update ansible/inventory/azure_rm.yml with resource group: ${RESOURCE_GROUP}"
echo "2. Run: cd ../ansible && ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml"
echo ""
