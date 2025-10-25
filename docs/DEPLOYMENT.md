# Deployment Guide

Complete step-by-step guide for deploying the Spider-2y-Banana platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Infrastructure Deployment](#phase-1-infrastructure-deployment)
3. [Phase 2: Cluster Bootstrap](#phase-2-cluster-bootstrap)
4. [Phase 3: GitOps Configuration](#phase-3-gitops-configuration)
5. [Phase 4: Application Deployment](#phase-4-application-deployment)
6. [Phase 5: DNS and TLS](#phase-5-dns-and-tls)
7. [Verification](#verification)
8. [Post-Deployment](#post-deployment)

## Prerequisites

### Required Tools

```bash
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Ansible
sudo apt update
sudo apt install ansible

# Python dependencies for Azure inventory
pip3 install azure-cli azure-identity

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# ArgoCD CLI (optional)
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -o root -g root -m 0755 argocd /usr/local/bin/argocd
```

### Azure Setup

```bash
# Login to Azure
az login

# Set default subscription
az account set --subscription "Your Subscription Name"

# Verify
az account show
```

### SSH Key Generation

```bash
# Generate SSH key pair if you don't have one
ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/spider-2y-banana

# Get public key for Bicep parameters
cat ~/.ssh/spider-2y-banana.pub
```

## Phase 1: Infrastructure Deployment

### 1.1 Configure Bicep Parameters

```bash
cd bicep-infrastructure

# Copy and edit dev parameters
cp parameters.dev.json parameters.dev.json.backup
vim parameters.dev.json
```

Update the following:
```json
{
  "sshPublicKey": {
    "value": "ssh-rsa AAAAB3... your-public-key"
  },
  "nodeCount": {
    "value": 1  # or 3 for HA
  }
}
```

### 1.2 Deploy Infrastructure

```bash
cd scripts

# Deploy to dev environment
./deploy.sh dev eastus

# For production (3-node HA cluster)
./deploy.sh prod eastus
```

Expected output:
- Resource Group created
- Virtual Network and Subnets created
- Network Security Group configured
- Virtual Machine(s) provisioned
- Key Vault created
- Container Registry created

### 1.3 Save Deployment Outputs

```bash
# Save outputs to file
RESOURCE_GROUP="rg-spider-2y-banana-dev"
az deployment group show -g $RESOURCE_GROUP -n <deployment-name> --query properties.outputs > ../outputs.json

# Extract key values
export VM_PUBLIC_IP=$(cat ../outputs.json | jq -r '.vmPublicIps.value[0]')
export KEY_VAULT_NAME=$(cat ../outputs.json | jq -r '.keyVaultName.value')
export ACR_LOGIN_SERVER=$(cat ../outputs.json | jq -r '.acrLoginServer.value')

echo "VM IP: $VM_PUBLIC_IP"
echo "Key Vault: $KEY_VAULT_NAME"
echo "ACR: $ACR_LOGIN_SERVER"
```

### 1.4 Create Service Principal

```bash
./create-service-principal.sh dev
```

Save the output:
- `CLIENT_ID`
- `CLIENT_SECRET`
- `TENANT_ID`
- `SUBSCRIPTION_ID`

## Phase 2: Cluster Bootstrap

### 2.1 Configure Ansible Variables

```bash
cd ../../ansible

# Edit variables
vim group_vars/all.yml
```

Update these values:
```yaml
azure_subscription_id: "YOUR_SUBSCRIPTION_ID"
azure_tenant_id: "YOUR_TENANT_ID"
azure_client_id: "YOUR_CLIENT_ID"
azure_client_secret: "YOUR_CLIENT_SECRET"
azure_key_vault_name: "YOUR_KEY_VAULT_NAME"
acr_login_server: "YOUR_ACR_LOGIN_SERVER"
```

### 2.2 Update Inventory

```bash
# Edit inventory to match your resource group
vim inventory/azure_rm.yml
```

Update resource group names:
```yaml
include_vm_resource_groups:
  - rg-spider-2y-banana-dev  # Update this
```

### 2.3 Test Connectivity

```bash
# Test SSH access
ssh -i ~/.ssh/spider-2y-banana azureuser@$VM_PUBLIC_IP

# Test Ansible connectivity
ansible all -i inventory/azure_rm.yml -m ping
```

### 2.4 Run Bootstrap Playbook

```bash
# Bootstrap the entire cluster
ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml

# Or run roles individually
ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml --tags k3s
ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml --tags crossplane
ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml --tags argocd
```

Expected duration: 15-20 minutes

### 2.5 Retrieve kubeconfig

```bash
# Copy kubeconfig from VM
scp -i ~/.ssh/spider-2y-banana azureuser@$VM_PUBLIC_IP:/home/azureuser/.kube/config ~/.kube/config-spider-2y-banana

# Merge with existing config or set directly
export KUBECONFIG=~/.kube/config-spider-2y-banana

# Test access
kubectl get nodes
kubectl get pods -A
```

## Phase 3: GitOps Configuration

### 3.1 Verify Crossplane

```bash
# Check Crossplane installation
kubectl get providers

# Should see:
# provider-azure-sql
# provider-azure-storage
# provider-azure-network

# Check provider health
kubectl get providers -o wide

# Check ProviderConfig
kubectl get providerconfig
```

### 3.2 Verify ArgoCD

```bash
# Check ArgoCD pods
kubectl get pods -n argocd

# Get admin password
export ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "ArgoCD Password: $ARGOCD_PASSWORD"

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Login with CLI
argocd login localhost:8080 --username admin --password $ARGOCD_PASSWORD --insecure
```

### 3.3 Deploy App of Apps

```bash
cd ../gitops

# Update repository URL if forked
vim bootstrap/app-of-apps.yaml
# Update: repoURL: https://github.com/borninthedark/spider-2y-banana.git

# Apply App of Apps
kubectl apply -f bootstrap/app-of-apps.yaml

# Watch applications sync
watch kubectl get applications -n argocd
```

Applications that will be created:
- `infrastructure`: Crossplane resources
- `platform`: Ingress, cert-manager, monitoring
- `applications-dev`: Application deployments

### 3.4 Wait for Platform Sync

```bash
# Monitor application sync status
argocd app list

# Watch specific application
argocd app get infrastructure
argocd app get platform

# Force sync if needed
argocd app sync infrastructure
argocd app sync platform
```

## Phase 4: Application Deployment

### 4.1 Configure GitHub Secrets

In your GitHub repository, add these secrets:

```
Settings → Secrets and variables → Actions → New repository secret
```

Add:
- `ACR_NAME`: (e.g., acrk3sdev)
- `ACR_USERNAME`: Get from: `az acr credential show -n <acr-name> --query username -o tsv`
- `ACR_PASSWORD`: Get from: `az acr credential show -n <acr-name> --query passwords[0].value -o tsv`

### 4.2 Trigger Resume App Build

```bash
cd osyraa

# Make a change to trigger build
git add .
git commit -m "Deploy resume application"
git push origin main
```

Monitor in GitHub Actions:
- Build and push Docker image
- Scan with Trivy
- Update GitOps manifest
- ArgoCD auto-sync

### 4.3 Verify Application Deployment

```bash
# Check resume namespace
kubectl get pods -n resume

# Check deployment status
kubectl get deployment -n resume

# Check service
kubectl get svc -n resume

# Check ingress
kubectl get ingress -n resume
```

## Phase 5: DNS and TLS

### 5.1 Get Ingress IP

```bash
# Get ingress controller external IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# If using LoadBalancer
export INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# If using NodePort (k3s default)
export INGRESS_IP=$VM_PUBLIC_IP

echo "Ingress IP: $INGRESS_IP"
```

### 5.2 Configure DNS Records

Add these DNS records to your domain (princetonstrong.online):

```
Type   Name      Value           TTL
----   ----      -----           ---
A      resume    <INGRESS_IP>    300
A      grafana   <INGRESS_IP>    300
```

Using Azure DNS:
```bash
RESOURCE_GROUP="rg-spider-2y-banana-dev"
ZONE_NAME="princetonstrong.online"

# Create A records
az network dns record-set a add-record \
  -g $RESOURCE_GROUP \
  -z $ZONE_NAME \
  -n resume \
  -a $INGRESS_IP

az network dns record-set a add-record \
  -g $RESOURCE_GROUP \
  -z $ZONE_NAME \
  -n grafana \
  -a $INGRESS_IP
```

### 5.3 Wait for Certificate Issuance

```bash
# Check certificate status
kubectl get certificate -A

# Watch certificate issuance
kubectl describe certificate resume-tls -n resume
kubectl describe certificate grafana-tls -n monitoring

# Check cert-manager logs if issues
kubectl logs -n cert-manager -l app=cert-manager
```

Certificate states:
- `Issuing`: Certificate request in progress
- `Ready`: Certificate issued successfully

## Verification

### Complete System Check

```bash
# 1. Cluster Health
kubectl get nodes
kubectl get pods -A | grep -v Running

# 2. Crossplane
kubectl get providers
kubectl get compositions
kubectl get postgresqlinstances -A
kubectl get storageaccounts -A

# 3. ArgoCD
argocd app list
argocd app get applications-dev

# 4. Monitoring
kubectl get pods -n monitoring
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# 5. Application
curl -I https://resume.princetonstrong.online
kubectl get pods -n resume

# 6. Certificates
kubectl get certificate -A
```

### Test Resume Website

```bash
# Test HTTP redirect
curl -I http://resume.princetonstrong.online

# Test HTTPS
curl -I https://resume.princetonstrong.online

# Check content
curl -s https://resume.princetonstrong.online | grep "Princeton A. Strong"
```

### Test Grafana

```bash
# Access Grafana
# URL: https://grafana.princetonstrong.online
# Username: admin
# Password: admin (change in production!)

# Or port forward
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# Access: http://localhost:3000
```

## Post-Deployment

### Security Hardening

```bash
# 1. Change ArgoCD admin password
argocd account update-password

# 2. Change Grafana admin password
kubectl exec -n monitoring -it $(kubectl get pod -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}') -- grafana-cli admin reset-admin-password <new-password>

# 3. Store credentials in Key Vault
az keyvault secret set --vault-name $KEY_VAULT_NAME --name argocd-admin-password --value "<new-password>"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name grafana-admin-password --value "<new-password>"

# 4. Enable RBAC in ArgoCD
# Edit ArgoCD ConfigMap to add RBAC policies
```

### Backup Configuration

```bash
# 1. Backup kubeconfig
cp ~/.kube/config-spider-2y-banana ~/.kube/config-spider-2y-banana.backup

# 2. Backup Ansible variables
cp ansible/group_vars/all.yml ansible/group_vars/all.yml.backup

# 3. Export ArgoCD applications
argocd app list -o yaml > argocd-apps-backup.yaml

# 4. Backup Crossplane resources
kubectl get compositions -o yaml > crossplane-compositions-backup.yaml
kubectl get xrds -o yaml > crossplane-xrds-backup.yaml
```

### Monitoring Setup

```bash
# 1. Import Grafana dashboards
# Access Grafana → Dashboards → Import
# Import dashboard IDs: 7249, 1860, 9614

# 2. Configure alerts (optional)
# Edit kube-prometheus-stack values to add AlertManager routes

# 3. Set up Prometheus retention
# Default: 30 days (configured in values)
```

### Documentation

```bash
# Document your deployment
cat > DEPLOYMENT_NOTES.md << EOF
# Deployment Notes

## Date: $(date)
## Environment: dev

### Infrastructure
- Resource Group: $RESOURCE_GROUP
- VM IPs: $VM_PUBLIC_IP
- Key Vault: $KEY_VAULT_NAME
- ACR: $ACR_LOGIN_SERVER

### Credentials
- ArgoCD: Stored in Key Vault
- Grafana: Stored in Key Vault
- Service Principal: Stored in Key Vault

### DNS
- resume.princetonstrong.online → $INGRESS_IP
- grafana.princetonstrong.online → $INGRESS_IP

### Access
- ArgoCD: https://$VM_PUBLIC_IP/argocd
- Grafana: https://grafana.princetonstrong.online
- Resume: https://resume.princetonstrong.online
EOF
```

## Troubleshooting Deployment

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting steps.

## Next Steps

1. ✅ Review [README.md](README.md) for full documentation
2. ✅ Configure additional Crossplane resources
3. ✅ Deploy more applications via GitOps
4. ✅ Set up backup strategy
5. ✅ Configure monitoring alerts
6. ✅ Implement CI/CD for other applications

## Cleanup

To delete all resources:

```bash
# Delete resource group (includes all resources)
az group delete --name rg-spider-2y-banana-dev --yes --no-wait
```

---

**Need help?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or open an issue.
