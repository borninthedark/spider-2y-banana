# Quick Start Guide

Get the Spider-2y-Banana platform up and running in under 45 minutes.

## Prerequisites Check

```bash
# Verify tools are installed
az --version          # Azure CLI
ansible --version     # Ansible
kubectl version       # kubectl (will work after cluster is ready)

# Login to Azure
az login
az account set --subscription "Your Subscription"
```

## 5-Step Deployment

### Step 1: Deploy Infrastructure (5 minutes)

```bash
cd bicep-infrastructure

# Add your SSH public key to parameters
vim parameters.dev.json
# Update: "sshPublicKey": "ssh-rsa AAAAB3..."

# Deploy
cd scripts
./deploy.sh dev eastus

# Save outputs
export VM_IP="<output-from-deploy>"
export KEY_VAULT="<output-from-deploy>"
export ACR_NAME="<output-from-deploy>"
```

### Step 2: Create Service Principal (2 minutes)

```bash
# Still in bicep-infrastructure/scripts
./create-service-principal.sh dev

# Save these values:
# - CLIENT_ID
# - CLIENT_SECRET
# - TENANT_ID
# - SUBSCRIPTION_ID
```

### Step 3: Configure Ansible (3 minutes)

```bash
cd ../../ansible

# Update variables
vim group_vars/all.yml
```

Required updates:
```yaml
azure_subscription_id: "YOUR_SUBSCRIPTION_ID"
azure_tenant_id: "YOUR_TENANT_ID"
azure_client_id: "YOUR_CLIENT_ID"
azure_client_secret: "YOUR_CLIENT_SECRET"
azure_key_vault_name: "YOUR_KEY_VAULT_NAME"
acr_login_server: "YOUR_ACR_LOGIN_SERVER.azurecr.io"
```

### Step 4: Bootstrap Cluster (15-20 minutes)

```bash
# Update inventory
vim inventory/azure_rm.yml
# Ensure resource group matches: rg-spider-2y-banana-dev

# Run bootstrap
ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml

# Get kubeconfig
scp azureuser@${VM_IP}:/home/azureuser/.kube/config ~/.kube/config-lavish

# Test
export KUBECONFIG=~/.kube/config-lavish
kubectl get nodes
```

### Step 5: Deploy GitOps (10 minutes)

```bash
cd ../gitops

# Deploy App of Apps
kubectl apply -f bootstrap/app-of-apps.yaml

# Watch deployment
watch kubectl get applications -n argocd

# Access ArgoCD
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
# Port forward: kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## Quick Access

```bash
# ArgoCD
kubectl port-forward -n argocd svc/argocd-server 8080:443
# https://localhost:8080
# Username: admin
# Password: <from secret above>

# Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# http://localhost:3000
# Username: admin
# Password: admin (change in production!)

# Resume App (after DNS configured)
# https://resume.princetonstrong.online
```

## DNS Setup

Point your domain to the VM:

```bash
# Get IP
echo $VM_IP

# Add DNS records:
# resume.princetonstrong.online  -> VM_IP
# grafana.princetonstrong.online -> VM_IP
```

## Deploy Resume App

```bash
# Configure GitHub secrets
# In your GitHub repo: Settings → Secrets → Actions
# Add:
# - ACR_NAME: acrk3sdev
# - ACR_USERNAME: <from: az acr credential show>
# - ACR_PASSWORD: <from: az acr credential show>

# Push code to trigger build
cd osyraa
git add .
git commit -m "Initial deployment"
git push
```

## Verification Commands

```bash
# Cluster
kubectl get nodes
kubectl get pods -A

# Crossplane
kubectl get providers
kubectl get compositions

# ArgoCD
kubectl get applications -n argocd

# Resume App
kubectl get pods -n resume
kubectl get ingress -n resume
kubectl get certificate -n resume

# Monitoring
kubectl get pods -n monitoring
kubectl top nodes
kubectl top pods -A
```

## Troubleshooting Quick Fixes

### Can't access cluster
```bash
# Re-fetch kubeconfig
scp azureuser@${VM_IP}:/home/azureuser/.kube/config ~/.kube/config-lavish
export KUBECONFIG=~/.kube/config-lavish
```

### Crossplane provider not healthy
```bash
# Check logs
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=provider-azure-sql

# Verify secret
kubectl get secret azure-credentials -n crossplane-system
```

### ArgoCD app stuck syncing
```bash
# Force sync
kubectl get applications -n argocd
kubectl patch application <app-name> -n argocd -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}' --type=merge
```

### Certificate not issuing
```bash
# Check cert-manager
kubectl get certificate -A
kubectl describe certificate <cert-name> -n <namespace>
kubectl logs -n cert-manager -l app=cert-manager
```

## Common Tasks

### Update resume content
```bash
cd osyraa/content
vim _index.md
git add .
git commit -m "Update resume"
git push  # GitHub Actions builds and deploys
```

### Scale application
```bash
kubectl scale deployment resume -n resume --replicas=3
```

### View logs
```bash
kubectl logs -n resume -l app=resume --tail=100 -f
```

### Check resource usage
```bash
kubectl top nodes
kubectl top pods -n resume
```

### Access Grafana dashboards
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# Open: http://localhost:3000
# Browse to: Resume Application Dashboard
```

## Next Steps

1. ✅ Read [README.md](README.md) for full documentation
2. ✅ Review [DEPLOYMENT.md](DEPLOYMENT.md) for detailed steps
3. ✅ Check [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for overview
4. ✅ Explore Crossplane compositions
5. ✅ Add more applications via GitOps
6. ✅ Configure monitoring alerts
7. ✅ Implement backup strategy

## Clean Up

```bash
# Delete everything
az group delete --name rg-spider-2y-banana-dev --yes --no-wait
```

## Estimated Costs

- **Dev (1 VM)**: ~$87/month
- **Prod (3 VMs)**: ~$337/month
- **Stopped VMs**: ~$10-15/month (storage only)

## Support

- 📖 Documentation: [README.md](README.md)
- 🐛 Issues: [GitHub Issues](https://github.com/borninthedark/spider-2y-banana/issues)
- 📧 Email: info@princetonstrong.online

---

**Time to Production**: ~45 minutes from start to finish!
