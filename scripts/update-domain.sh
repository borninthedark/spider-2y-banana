#!/bin/bash
# Script to update domain name across all configuration files
# Usage: ./scripts/update-domain.sh <new-domain>
# Example: ./scripts/update-domain.sh example.com

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <new-domain>"
    echo "Example: $0 example.com"
    exit 1
fi

NEW_DOMAIN="$1"
OLD_DOMAIN="princetonstrong.online"

echo "Updating domain from ${OLD_DOMAIN} to ${NEW_DOMAIN}..."
echo

# Files to update
FILES=(
    "gitops/platform/monitoring/kube-prometheus-stack.yaml"
    "gitops/platform/cert-manager/cert-manager.yaml"
    "gitops/applications/dev/resume-deployment.yaml"
    "docs/security-hardening.md"
)

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED_INPLACE="sed -i ''"
else
    SED_INPLACE="sed -i"
fi

# Update each file
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Updating $file..."
        sed -i.bak "s/${OLD_DOMAIN}/${NEW_DOMAIN}/g" "$file"
        rm -f "${file}.bak"
    else
        echo "Warning: $file not found, skipping..."
    fi
done

echo
echo "Domain updated successfully!"
echo
echo "Next steps:"
echo "1. Update .env file with DOMAIN_NAME=${NEW_DOMAIN}"
echo "2. Rebuild Jsonnet manifests: cd jsonnet && make dev"
echo "3. Rebuild Docker images with: docker build --build-arg DOMAIN_NAME=${NEW_DOMAIN} osyraa/"
echo "4. Update Terraform variables in terraform-infrastructure/terraform.tfvars"
echo "5. Review and commit the changes"
