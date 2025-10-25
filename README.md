# Spider-2y-Banana: GitOps Infrastructure Platform

## Build and Deploy
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build and Push to GHCR](https://github.com/borninthedark/spider-2y-banana/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/borninthedark/spider-2y-banana/actions/workflows/build-and-push.yml)
[![Terraform Infrastructure](https://github.com/borninthedark/spider-2y-banana/actions/workflows/terraform.yml/badge.svg)](https://github.com/borninthedark/spider-2y-banana/actions/workflows/terraform.yml)
[![Azure](https://img.shields.io/badge/Azure-Cloud-0078D4?logo=microsoft-azure)](https://azure.microsoft.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-k3s-326CE5?logo=kubernetes)](https://k3s.io/)
[![GitOps](https://img.shields.io/badge/GitOps-ArgoCD-EF7B4D?logo=argo)](https://argo-cd.readthedocs.io/)

A comprehensive GitOps demonstration platform showcasing modern cloud-native infrastructure practices using Terraform, Ansible, Crossplane, ArgoCD, and Kubernetes.

## 🎯 Project Overview

This project demonstrates a complete GitOps workflow for managing cloud infrastructure and applications on Azure using:

- **Terraform**: Azure infrastructure provisioning (VMs, networking, Key Vault) with Terraform Cloud remote state
- **Ansible**: Automated k3s cluster bootstrapping and platform configuration
- **Crossplane**: Kubernetes-native Azure resource management
- **ArgoCD**: GitOps-based application and infrastructure delivery
- **External Secrets Operator**: Secure secrets management with Azure Key Vault
- **Monitoring**: Prometheus & Grafana for observability
- **Sample Application**: Hugo-based static resume site with CI/CD

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Repositories                         │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure     │  GitOps Repo     │  Application Repo  │
│  (Terraform + TF    │  (ArgoCD)        │  (Hugo + CI/CD)    │
│   Cloud)            │                  │                    │
└──────────┬──────────┴─────────┬────────┴──────────┬─────────┘
           │                    │                   │
           ▼                    ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│         Management Cluster (k3s on Azure VM)                │
├─────────────────────────────────────────────────────────────┤
│  Crossplane  │  ArgoCD  │  External Secrets  │  Monitoring  │
└──────────┬───────────────────┬────────────────────┬─────────┘
           │                   │                    │
           ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      Azure Cloud                            │
│  VMs │ SQL │ Storage │ Key Vault │ Networks                 │
└─────────────────────────────────────────────────────────────┘
           ▲
           │
┌──────────┴──────────────────────────────────────────────────┐
│             GitHub Container Registry (GHCR)                 │
│  Docker Images │ Build Attestations │ Provenance           │
└─────────────────────────────────────────────────────────────┘
```

## 💰 Cost Estimate

### Single VM Dev Setup (~$82/month)
- 1x Standard_B2ms VM: $65
- 128GB Standard SSD: $6
- Static Public IP: $3
- Key Vault: $1
- Azure SQL Basic: $5
- Storage Account: $2
- GitHub Container Registry: Free

### HA Production Setup (~$337/month)
- 3x Standard_B2ms VMs: $195
- 3x 128GB SSDs: $18
- Managed Azure services: ~$124

## 🚀 Quick Start

### Prerequisites

- Azure subscription
- Azure CLI installed and configured
- Terraform (>= 1.5.0)
- Terraform Cloud account (DefiantEmissary organization)
- SSH key pair
- Git
- Ansible (>= 2.14)

### 1. Authenticate to Terraform Cloud

```bash
# Interactive login (recommended)
terraform login

# Or set environment variable
export TF_TOKEN_app_terraform_io="your-token"
```

### 2. Deploy Infrastructure with Terraform

```bash
cd terraform-infrastructure

# Copy and update terraform.tfvars with your SSH public key
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

# Deploy using the automated script
cd scripts
./deploy.sh dev
```

This will create:
- Azure VMs for k3s cluster
- Virtual network and subnets
- Network security groups
- Azure Key Vault

### 3. Create Service Principal for Crossplane

```bash
cd terraform-infrastructure/scripts
./create-service-principal.sh dev
```

Save the credentials output - you'll need them for Ansible configuration.

### 4. Configure Ansible Variables

```bash
cd ansible
vim group_vars/all.yml
```

Update the following values with outputs from Terraform deployment:
- `azure_subscription_id`
- `azure_tenant_id`
- `azure_client_id`
- `azure_client_secret`
- `azure_key_vault_name`
- `acr_login_server`

### 5. Bootstrap k3s Cluster with Ansible

```bash
cd ansible

# Update inventory with your resource group
vim inventory/azure_rm.yml

# Run bootstrap playbook
ansible-playbook -i inventory/azure_rm.yml playbooks/bootstrap-all.yml
```

This will install:
- k3s Kubernetes cluster
- Crossplane with Azure providers
- ArgoCD for GitOps
- External Secrets Operator
- Helm and kubectl

### 6. Access the Cluster

```bash
# Get kubeconfig from the VM
VM_IP=$(az vm list-ip-addresses -g rg-spider-2y-banana-dev --query '[0].virtualMachine.network.publicIpAddresses[0].ipAddress' -o tsv)
scp azureuser@${VM_IP}:/home/azureuser/.kube/config ~/.kube/config

# Test access
kubectl get nodes
kubectl get pods -A
```

### 7. Access ArgoCD

```bash
# Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Or access via VM public IP
echo "ArgoCD URL: http://${VM_IP}:80"
```

### 8. Deploy GitOps Applications

```bash
# Apply the App of Apps pattern
kubectl apply -f gitops/bootstrap/app-of-apps.yaml

# Watch ArgoCD sync applications
kubectl get applications -n argocd -w
```

### 9. Configure DNS

Point your domain records to the cluster:
```
resume.princetonstrong.online   -> <VM_PUBLIC_IP>
grafana.princetonstrong.online  -> <VM_PUBLIC_IP>
```

### 10. Build and Deploy Resume App

```bash
cd osyraa

# Build container image locally (optional)
podman build -t osyraa:local .
# or with buildah
buildah bud -t osyraa:local .

# Or push to trigger GitHub Actions CI/CD
git add .
git commit -m "Deploy resume app"
git push
```

GitHub Actions will:
1. Build the container image with Buildah
2. Scan with Trivy for vulnerabilities
3. Push to GitHub Container Registry (GHCR) with Podman
4. Generate build attestation
5. ArgoCD will automatically sync and deploy

## 📂 Repository Structure

```
spider-2y-banana/
├── terraform-infrastructure/   # Azure infrastructure as code
│   ├── modules/                # Reusable Terraform modules
│   │   ├── network/
│   │   ├── vm/
│   │   └── keyvault/
│   ├── main.tf                 # Main orchestration
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Output values
│   ├── terraform.tfvars.example # Example variables
│   └── scripts/                # Deployment scripts
│       ├── deploy.sh
│       ├── deploy.py
│       ├── create-service-principal.sh
│       └── create_service_principal.py
│
├── ansible/                    # Configuration management
│   ├── inventory/              # Dynamic Azure inventory
│   ├── playbooks/              # Ansible playbooks
│   │   └── bootstrap-all.yml
│   ├── roles/                  # Ansible roles
│   │   ├── k3s/
│   │   ├── crossplane/
│   │   ├── argocd/
│   │   └── external-secrets/
│   └── group_vars/
│       └── all.yml
│
├── crossplane-infrastructure/  # Crossplane compositions
│   ├── providers/              # Provider configs
│   ├── definitions/            # XRDs
│   │   ├── database-xrd.yaml
│   │   └── storage-xrd.yaml
│   ├── compositions/           # Compositions
│   │   ├── azure-postgresql.yaml
│   │   └── azure-storage.yaml
│   └── claims/                 # Resource claims
│       ├── dev/
│       └── prod/
│
├── gitops/                     # GitOps manifests
│   ├── bootstrap/              # App of Apps
│   │   ├── app-of-apps.yaml
│   │   └── applications/
│   ├── infrastructure/         # Infrastructure apps
│   ├── platform/               # Platform services
│   │   ├── ingress-nginx/
│   │   ├── cert-manager/
│   │   └── monitoring/
│   └── applications/           # Application deployments
│       ├── dev/
│       └── prod/
│
└── osyraa/                 # Hugo resume application
    ├── content/
    ├── layouts/
    ├── Containerfile
    ├── tests/
    └── .github/workflows/
```

## 🔧 Key Components

### Terraform Infrastructure
- **Purpose**: Bootstrap Azure foundation with remote state management
- **Manages**: VMs, networking, Key Vault, service principals
- **Pattern**: Modular architecture with Terraform Cloud backend
- **State**: Remote state managed via Terraform Cloud (DefiantEmissary org)

### Container Registry
- **GHCR**: GitHub Container Registry for OCI container images
- **Tools**: Podman, Buildah, and Skopeo for building and pushing
- **Access**: Automatic via GitHub Actions GITHUB_TOKEN
- **Images**: Resume app and other containerized workloads

### Ansible Automation
- **Purpose**: Configure and bootstrap Kubernetes
- **Manages**: k3s installation, platform components
- **Pattern**: Role-based organization with dynamic inventory

### Crossplane
- **Purpose**: Kubernetes-native cloud resource management
- **Manages**: Azure SQL, Storage Accounts, Redis, etc.
- **Pattern**: Compositions and XRDs for self-service infrastructure

### ArgoCD GitOps
- **Purpose**: Declarative continuous delivery
- **Manages**: All Kubernetes resources
- **Pattern**: App of Apps for hierarchical management

### External Secrets Operator
- **Purpose**: Sync secrets from Azure Key Vault
- **Manages**: Database credentials, API keys
- **Pattern**: ClusterSecretStore with ExternalSecrets

### Monitoring Stack
- **Components**: Prometheus, Grafana, Node Exporter
- **Features**: Cluster metrics, application metrics, custom dashboards
- **Access**: grafana.princetonstrong.online

## 🧪 Testing

### Test Hugo Build
```bash
cd osyraa/tests
./test_build.sh
```

### Test Container Build
```bash
cd osyraa/tests
python3 test_docker.py  # Tests Podman build and container
```

### Test Crossplane Resources
```bash
# Check providers
kubectl get providers

# Check compositions
kubectl get compositions

# Check claims
kubectl get postgresqlinstances
kubectl get storageaccounts
```

### Test ArgoCD Sync
```bash
# Check application health
kubectl get applications -n argocd

# Sync manually if needed
argocd app sync app-of-apps
```

## 📊 Monitoring & Observability

### Access Grafana
- URL: https://grafana.princetonstrong.online
- Username: admin
- Password: (from Helm values or secret)

### Key Dashboards
1. **Kubernetes Cluster**: Overall cluster health
2. **Node Exporter**: VM-level metrics
3. **Resume Application**: Custom app metrics
4. **Nginx Ingress**: Ingress controller metrics

### Prometheus Queries
```promql
# Pod CPU usage
rate(container_cpu_usage_seconds_total{namespace="resume"}[5m])

# HTTP request rate
rate(nginx_http_requests_total{namespace="resume"}[5m])

# Active connections
nginx_connections_active{namespace="resume"}
```

## 🔒 Security Features

- **SSH-only access**: No password authentication
- **TLS certificates**: Automatic with cert-manager and Let's Encrypt
- **Secrets management**: Azure Key Vault integration
- **RBAC**: Kubernetes role-based access control
- **Network policies**: Namespace isolation
- **Image scanning**: Trivy in CI/CD pipeline
- **Security headers**: X-Frame-Options, CSP, etc.

## 🚨 Troubleshooting

### Terraform Deployment Fails
```bash
# Validate configuration
terraform validate

# Check plan before applying
terraform plan

# View Terraform Cloud run logs
# Visit: https://app.terraform.io/app/DefiantEmissary/workspaces/spider-2y-banana
```

### Ansible Playbook Fails
```bash
# Test connectivity
ansible all -i inventory/azure_rm.yml -m ping

# Run with verbose output
ansible-playbook -vvv -i inventory/azure_rm.yml playbooks/bootstrap-all.yml
```

### Crossplane Provider Not Healthy
```bash
# Check provider logs
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=provider-azure-sql

# Verify credentials
kubectl get secret azure-credentials -n crossplane-system -o yaml
```

### ArgoCD Application Out of Sync
```bash
# Check application details
kubectl describe application <app-name> -n argocd

# Force sync
argocd app sync <app-name> --force
```

### Resume App Not Accessible
```bash
# Check pod status
kubectl get pods -n resume

# Check ingress
kubectl get ingress -n resume
kubectl describe ingress resume -n resume

# Check certificate
kubectl get certificate -n resume
```

## 📚 Documentation

### Project Documentation

- **[CI/CD Pipeline Guide](CI_CD_GUIDE.md)** - Comprehensive GitHub Actions workflow documentation
- **[Workflow Integration Checklist](WORKFLOW_INTEGRATION_CHECKLIST.md)** - Integration verification and status
- **[Pre-commit Setup Guide](PRECOMMIT_SETUP.md)** - Pre-commit hooks configuration and containerized solution
- **[Python Scripts Guide](PYTHON_SCRIPTS_GUIDE.md)** - All Python utility scripts reference
- **[GitHub Secrets Setup](.github/SECRETS.md)** - Required secrets for GitHub Actions workflows
- **[Security Hardening Guide](docs/security-hardening.md)** - Comprehensive security hardening recommendations
- **[Deployment Guide](DEPLOYMENT.md)** - Complete step-by-step deployment instructions
- **[Quick Start Guide](QUICKSTART.md)** - Fast-track setup for getting started quickly
- **[Project Summary](PROJECT_SUMMARY.md)** - Detailed project overview and architecture
- **[Jsonnet Integration](JSONNET_INTEGRATION.md)** - Advanced configuration templating with Jsonnet
- **[Resume App Documentation](osyraa/README.md)** - Hugo-based resume application details
- **[Test Suite Documentation](osyraa/tests/README.md)** - Testing framework and guidelines

### External Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [Terraform Cloud Documentation](https://www.terraform.io/cloud-docs)
- [Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Ansible Documentation](https://docs.ansible.com/)
- [k3s Documentation](https://docs.k3s.io/)
- [Crossplane Documentation](https://docs.crossplane.io/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Hugo Documentation](https://gohugo.io/documentation/)

## 🤝 Contributing

This is a demonstration project. Feel free to fork and adapt for your own use cases!

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

**Princeton A. Strong**
- Email: info@princetonstrong.online
- GitHub: [@borninthedark](https://github.com/borninthedark)
- Resume: https://resume.princetonstrong.online

---

Built with ❤️ using GitOps best practices
