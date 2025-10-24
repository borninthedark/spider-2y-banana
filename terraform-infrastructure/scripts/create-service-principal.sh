#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-dev}
SP_NAME="sp-crossplane-${ENVIRONMENT}"

echo -e "${GREEN}Creating Service Principal for Crossplane${NC}"
echo "Name: ${SP_NAME}"
echo ""

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription ID: ${SUBSCRIPTION_ID}"

# Create service principal with Contributor role
echo -e "${YELLOW}Creating service principal...${NC}"
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "${SP_NAME}" \
    --role Contributor \
    --scopes "/subscriptions/${SUBSCRIPTION_ID}")

CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.appId')
CLIENT_SECRET=$(echo $SP_OUTPUT | jq -r '.password')
TENANT_ID=$(echo $SP_OUTPUT | jq -r '.tenant')

echo ""
echo -e "${GREEN}Service Principal created successfully!${NC}"
echo ""
echo "Save these credentials securely:"
echo "CLIENT_ID: ${CLIENT_ID}"
echo "CLIENT_SECRET: ${CLIENT_SECRET}"
echo "TENANT_ID: ${TENANT_ID}"
echo "SUBSCRIPTION_ID: ${SUBSCRIPTION_ID}"
echo ""

# Get Key Vault name from Terraform output
cd ..
if [ -f "outputs.json" ]; then
    KEY_VAULT_NAME=$(jq -r '.key_vault_name.value' outputs.json)

    if [ -n "${KEY_VAULT_NAME}" ] && [ "${KEY_VAULT_NAME}" != "null" ]; then
        echo -e "${YELLOW}Storing credentials in Key Vault: ${KEY_VAULT_NAME}${NC}"

        az keyvault secret set --vault-name "${KEY_VAULT_NAME}" --name "crossplane-client-id" --value "${CLIENT_ID}"
        az keyvault secret set --vault-name "${KEY_VAULT_NAME}" --name "crossplane-client-secret" --value "${CLIENT_SECRET}"
        az keyvault secret set --vault-name "${KEY_VAULT_NAME}" --name "crossplane-tenant-id" --value "${TENANT_ID}"
        az keyvault secret set --vault-name "${KEY_VAULT_NAME}" --name "crossplane-subscription-id" --value "${SUBSCRIPTION_ID}"

        echo -e "${GREEN}Credentials stored in Key Vault${NC}"
    else
        echo -e "${YELLOW}Key Vault not found in Terraform outputs. Store these credentials manually.${NC}"
    fi
else
    echo -e "${YELLOW}Terraform outputs.json not found. Store these credentials manually.${NC}"
fi

echo ""
echo -e "${YELLOW}Next: Update ansible/group_vars/all.yml with these values${NC}"
