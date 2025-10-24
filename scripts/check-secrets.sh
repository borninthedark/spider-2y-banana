#!/bin/bash
set -euo pipefail

# Secret Detection Script
# Scans the repository for potential secrets before commit

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS_FOUND=0

echo "Scanning repository for secrets and sensitive data..."
echo "======================================================"

# Check for common secret files
echo -e "\n${YELLOW}Checking for sensitive files...${NC}"
SENSITIVE_FILES=(
    "*.env"
    ".env*"
    "*.pem"
    "*.key"
    "*_rsa"
    "*.pfx"
    "*.p12"
    "sp-credentials.json"
    "credentials.json"
    "terraform.tfvars"
    ".vault_password"
    "kubeconfig"
    "*.kubeconfig"
    "k3s.yaml"
    "auth.json"
    "service-account*.json"
)

for pattern in "${SENSITIVE_FILES[@]}"; do
    if git ls-files | grep -E "$pattern" > /dev/null 2>&1; then
        echo -e "${RED}✗ Found sensitive file matching: $pattern${NC}"
        git ls-files | grep -E "$pattern"
        ERRORS_FOUND=1
    fi
done

if [ $ERRORS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ No sensitive files found in git index${NC}"
fi

# Check for hardcoded passwords in Terraform
echo -e "\n${YELLOW}Checking Terraform files for hardcoded secrets...${NC}"
if find terraform-infrastructure -name "*.tf" -type f -exec grep -l 'password\s*=\s*"[^$]' {} \; 2>/dev/null | grep -v random_password | grep -v azurerm_key_vault_secret; then
    echo -e "${RED}✗ Found potential hardcoded passwords in Terraform files${NC}"
    ERRORS_FOUND=1
else
    echo -e "${GREEN}✓ No hardcoded passwords found in Terraform${NC}"
fi

# Check for hardcoded passwords in Ansible
echo -e "\n${YELLOW}Checking Ansible files for hardcoded secrets...${NC}"
if find ansible -name "*.yml" -o -name "*.yaml" -type f -exec grep -l 'password:' {} \; 2>/dev/null | xargs grep -v "ansible_become_password" | grep -v "vault" | grep -v "#"; then
    echo -e "${RED}✗ Found potential hardcoded passwords in Ansible files${NC}"
    ERRORS_FOUND=1
else
    echo -e "${GREEN}✓ No hardcoded passwords found in Ansible${NC}"
fi

# Check for AWS keys
echo -e "\n${YELLOW}Checking for AWS credentials...${NC}"
if git grep -E 'AKIA[0-9A-Z]{16}' -- ':(exclude).git' > /dev/null 2>&1; then
    echo -e "${RED}✗ Found potential AWS access keys${NC}"
    ERRORS_FOUND=1
else
    echo -e "${GREEN}✓ No AWS credentials found${NC}"
fi

# Check for Azure subscription IDs in plain text
echo -e "\n${YELLOW}Checking for exposed Azure subscription IDs...${NC}"
SUBSCRIPTION_COUNT=$(git grep -E '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' -- ':(exclude)*.md' ':(exclude).git' ':(exclude)scripts/' | wc -l || echo 0)
if [ "$SUBSCRIPTION_COUNT" -gt 5 ]; then
    echo -e "${YELLOW}! Warning: Found multiple UUID patterns (could be subscription IDs)${NC}"
    echo -e "${YELLOW}  Manual review recommended${NC}"
fi

# Check for private keys
echo -e "\n${YELLOW}Checking for private keys...${NC}"
if git grep -E '-----BEGIN.*PRIVATE KEY-----' -- ':(exclude).git' > /dev/null 2>&1; then
    echo -e "${RED}✗ Found private keys in repository${NC}"
    ERRORS_FOUND=1
else
    echo -e "${GREEN}✓ No private keys found${NC}"
fi

# Check for GitHub tokens
echo -e "\n${YELLOW}Checking for GitHub tokens...${NC}"
if git grep -E 'gh[pousr]_[a-zA-Z0-9]{36}' -- ':(exclude).git' > /dev/null 2>&1; then
    echo -e "${RED}✗ Found potential GitHub tokens${NC}"
    ERRORS_FOUND=1
else
    echo -e "${GREEN}✓ No GitHub tokens found${NC}"
fi

# Check for JWT tokens
echo -e "\n${YELLOW}Checking for JWT tokens...${NC}"
if git grep -E 'eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+' -- ':(exclude).git' ':(exclude)*.md' > /dev/null 2>&1; then
    echo -e "${YELLOW}! Warning: Found potential JWT tokens${NC}"
    echo -e "${YELLOW}  Manual review recommended${NC}"
fi

# Check for Slack tokens
echo -e "\n${YELLOW}Checking for Slack tokens...${NC}"
if git grep -E 'xox[baprs]-[0-9a-zA-Z]{10,48}' -- ':(exclude).git' > /dev/null 2>&1; then
    echo -e "${RED}✗ Found potential Slack tokens${NC}"
    ERRORS_FOUND=1
else
    echo -e "${GREEN}✓ No Slack tokens found${NC}"
fi

# Check .gitignore coverage
echo -e "\n${YELLOW}Verifying .gitignore coverage...${NC}"
REQUIRED_IGNORES=(
    "*.env"
    "*.pem"
    "*.key"
    "terraform.tfvars"
    ".vault_password"
    "kubeconfig"
    "sp-credentials.json"
)

MISSING_IGNORES=0
for ignore in "${REQUIRED_IGNORES[@]}"; do
    if ! grep -q "$ignore" .gitignore 2>/dev/null; then
        echo -e "${YELLOW}! Warning: '$ignore' not in .gitignore${NC}"
        MISSING_IGNORES=1
    fi
done

if [ $MISSING_IGNORES -eq 0 ]; then
    echo -e "${GREEN}✓ All critical patterns in .gitignore${NC}"
fi

# Summary
echo ""
echo "======================================================"
if [ $ERRORS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ No critical secrets detected!${NC}"
    echo ""
    echo "Note: This script provides basic checks."
    echo "For comprehensive scanning, use:"
    echo "  - gitleaks: https://github.com/gitleaks/gitleaks"
    echo "  - trufflehog: https://github.com/trufflesecurity/trufflehog"
    echo "  - pre-commit hooks: .pre-commit-config.yaml"
    exit 0
else
    echo -e "${RED}✗ Potential secrets detected!${NC}"
    echo ""
    echo "Please review the findings above and:"
    echo "1. Remove any hardcoded secrets"
    echo "2. Use Azure Key Vault or environment variables"
    echo "3. Ensure sensitive files are in .gitignore"
    echo "4. Run 'git reset' to unstage sensitive files"
    echo "5. Consider using git-filter-repo if secrets were committed"
    exit 1
fi
