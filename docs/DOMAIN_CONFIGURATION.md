# Domain Configuration Guide

This guide explains how to configure your custom domain for the spider-2y-banana project.

## Overview

The domain name is now configurable through environment variables and can be easily changed from the default `princetonstrong.online` to your own domain.

## Configuration Locations

The domain is used in the following components:

1. **Terraform Infrastructure** - DNS and infrastructure resources
2. **Kubernetes Manifests** - Ingress configurations (generated via Jsonnet)
3. **Hugo Resume Site** - Base URL and contact information
4. **GitOps Platform YAML** - Static Kubernetes configurations

## Quick Start

### 1. Set Environment Variable

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and set your domain:

```bash
DOMAIN_NAME=yourdomain.com
```

Source the environment file:

```bash
source .env
```

### 2. Update Terraform Configuration

Edit `terraform-infrastructure/terraform.tfvars`:

```hcl
domain_name = "yourdomain.com"
```

### 3. Update Static GitOps Files

Use the provided script to update all static YAML files:

```bash
./scripts/update-domain.sh yourdomain.com
```

This will update:
- `gitops/platform/monitoring/kube-prometheus-stack.yaml`
- `gitops/platform/cert-manager/cert-manager.yaml`
- `gitops/applications/dev/resume-deployment.yaml`
- `docs/security-hardening.md`

### 4. Build Jsonnet Manifests

The Jsonnet build will automatically use the `DOMAIN_NAME` environment variable:

```bash
cd jsonnet
make dev   # or make prod
```

This generates Kubernetes manifests with your domain in `jsonnet/output/`.

### 5. Build Docker Images

When building the resume Docker image, pass the domain as a build argument:

```bash
cd osyraa
docker build --build-arg DOMAIN_NAME=${DOMAIN_NAME} -t resume:latest .
```

## Component Details

### Terraform

The domain is defined as a variable in `terraform-infrastructure/variables.tf`:

```hcl
variable "domain_name" {
  description = "Base domain name for all services"
  type        = string
  default     = "princetonstrong.online"
}
```

### Jsonnet

The Jsonnet templates use the `DOMAIN_NAME` external variable:

- `jsonnet/components/resume.libsonnet` - Accepts domain as a parameter
- `jsonnet/environments/dev/main.jsonnet` - Reads `DOMAIN_NAME` from environment
- `jsonnet/environments/prod/main.jsonnet` - Reads `DOMAIN_NAME` from environment

The Makefile automatically passes the environment variable to jsonnet:

```bash
jsonnet --ext-str DOMAIN_NAME="${DOMAIN_NAME:-princetonstrong.online}" ...
```

### Hugo (Resume Site)

The Hugo configuration uses a template file:

- `osyraa/config.toml.template` - Template with `${DOMAIN_NAME}` placeholder
- `osyraa/Dockerfile` - Substitutes the domain during build

The Dockerfile automatically generates `config.toml` from the template during the build process.

## Subdomains

The following subdomains are configured:

- `resume.${DOMAIN_NAME}` - Resume website
- `grafana.${DOMAIN_NAME}` - Grafana monitoring dashboard
- Additional subdomains can be added in the respective configuration files

## DNS Configuration

### Automated DNS with Azure DNS (Recommended)

Terraform automatically creates and manages DNS records via Azure DNS:

1. Deploy Terraform: `cd terraform-infrastructure && terraform apply`
2. Get Azure nameservers: `terraform output dns_nameservers`
3. Update nameservers in your registrar (Namecheap, GoDaddy, etc.)
4. Done! All DNS records managed automatically

**See [NAMECHEAP_DNS_SETUP.md](./NAMECHEAP_DNS_SETUP.md) for detailed Namecheap configuration.**

### Manual DNS Configuration (Alternative)

If you prefer not to use Azure DNS, manually configure these records at your registrar:

```
resume.yourdomain.com   A  <your-vm-public-ip>
grafana.yourdomain.com  A  <your-vm-public-ip>
```

Get your VM IP: `terraform output vm_public_ips`

## Troubleshooting

### Issue: Jsonnet build fails with "Field does not exist: DOMAIN_NAME"

**Solution**: Make sure you've set and sourced the `DOMAIN_NAME` environment variable:

```bash
export DOMAIN_NAME=yourdomain.com
cd jsonnet && make dev
```

### Issue: Hugo site shows wrong domain after building

**Solution**: Rebuild the Docker image with the correct build argument:

```bash
docker build --build-arg DOMAIN_NAME=yourdomain.com osyraa/
```

### Issue: Grafana ingress still shows old domain

**Solution**: Make sure you ran the update script and applied the changes:

```bash
./scripts/update-domain.sh yourdomain.com
kubectl apply -f gitops/platform/monitoring/kube-prometheus-stack.yaml
```

## Reverting to Default

To revert to the default domain:

```bash
./scripts/update-domain.sh princetonstrong.online
export DOMAIN_NAME=princetonstrong.online
# Rebuild manifests and images as needed
```

## See Also

- [Main README](../README.md) - Overall project documentation
- [Deployment Guide](../DEPLOYMENT.md) - Deployment instructions
- [Quickstart Guide](../QUICKSTART.md) - Quick setup guide
