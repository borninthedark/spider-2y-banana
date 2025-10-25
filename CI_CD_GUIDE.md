# CI/CD Pipeline Guide

## Overview

This project uses GitHub Actions for continuous integration and delivery with two primary workflows:

1. **Build and Push to GHCR** - Container image builds for the resume application
2. **Terraform Infrastructure** - Infrastructure deployment and validation

## Workflows

### 1. Build and Push to GHCR

**File**: `.github/workflows/build-and-push.yml`

**Purpose**: Build, scan, and publish container images to GitHub Container Registry using Podman/Buildah/Skopeo

#### Triggers

- **Push to main**: When changes are pushed to the main branch
  - Only triggers if files in `osyraa/` directory change
  - Or if the workflow file itself changes
- **Pull Request to main**: On PR creation/update
  - Builds and scans but doesn't push images
- **Manual**: Via workflow_dispatch

#### Workflow Steps

| Step | Action | Description |
|------|--------|-------------|
| 1 | Checkout | Clone repository code |
| 2 | Install Tools | Install Podman, Buildah, and Skopeo |
| 3 | Lint Containerfile | Validate Containerfile with Hadolint |
| 4 | Generate Tags | Create image tags based on event type |
| 5 | Build with Buildah | Build container image using buildah bud |
| 6 | Scan with Trivy | Security vulnerability scanning |
| 7 | Tag Image | Apply all generated tags to image |
| 8 | Login to GHCR | Authenticate using GITHUB_TOKEN (main only) |
| 9 | Push with Podman | Push all tags to registry (main only) |
| 10 | Get Digest | Retrieve image digest using Skopeo |
| 11 | Generate Attestation | Create build provenance for supply chain security |

#### Image Tags Generated

```
ghcr.io/borninthedark/spider-2y-banana/osyraa:latest          # Latest from main
ghcr.io/borninthedark/spider-2y-banana/osyraa:main-abc1234    # SHA from main
ghcr.io/borninthedark/spider-2y-banana/osyraa:pr-42           # PR builds
ghcr.io/borninthedark/spider-2y-banana/osyraa:1.0.0           # Semantic version (if tagged)
```

#### Required Permissions

The workflow requires these permissions (automatically configured):

```yaml
permissions:
  contents: read       # Read repository
  packages: write      # Push to GHCR
  id-token: write      # Generate attestations
```

#### Environment Variables

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/osyraa
```

#### Build Args

```yaml
build-args: |
  DOMAIN_NAME=princetonstrong.online
```

#### Container Build Tools

- **Buildah**: OCI-compliant container image builder (no daemon required)
- **Podman**: Daemonless container engine for running and pushing images
- **Skopeo**: Tool for inspecting and copying container images
- **Format**: Docker-compatible multi-stage builds with layer caching

#### Security Features

1. **Containerfile Linting**: Hadolint validates best practices before build
2. **Vulnerability Scanning**: Trivy scans for CVEs in all layers
3. **Build Attestations**: Verifiable build provenance via GitHub attestations
4. **No Secrets Required**: Uses automatic GITHUB_TOKEN
5. **Daemonless Build**: Buildah/Podman eliminate daemon attack surface
6. **Supply Chain Security**: Attestations enable SLSA compliance

---

### 2. Terraform Infrastructure

**File**: `.github/workflows/terraform.yml`

**Purpose**: Validate and deploy Azure infrastructure

#### Triggers

- **Push to main**: When terraform files change
  - Only triggers if files in `terraform-infrastructure/` change
  - Or if the workflow file itself changes
- **Pull Request to main**: On PR creation/update
  - Runs plan and posts results to PR
- **Manual**: Via workflow_dispatch

#### Workflow Steps

| Step | Action | Description |
|------|--------|-------------|
| 1 | Checkout | Clone repository code |
| 2 | Setup Terraform | Install Terraform CLI (v1.5+) |
| 3 | Format Check | Verify Terraform formatting |
| 4 | Init | Initialize Terraform with remote backend |
| 5 | Validate | Validate configuration syntax |
| 6 | Plan | Generate execution plan |
| 7 | Update PR | Post plan to PR comments (PRs only) |
| 8 | Apply | Apply changes (main branch only) |

#### Required Secrets

Configure these in GitHub repository settings:

| Secret | Description | How to Get |
|--------|-------------|------------|
| `TF_API_TOKEN` | Terraform Cloud API token | https://app.terraform.io/app/settings/tokens |
| `ARM_CLIENT_ID` | Azure service principal ID | `az ad sp create-for-rbac` |
| `ARM_CLIENT_SECRET` | Azure SP secret | From SP creation |
| `ARM_SUBSCRIPTION_ID` | Azure subscription ID | `az account show --query id` |
| `ARM_TENANT_ID` | Azure tenant ID | `az account show --query tenantId` |

#### Environment Variables

```yaml
env:
  TF_CLOUD_ORGANIZATION: "DefiantEmissary"
  TF_WORKSPACE: "spider-2y-banana"
```

#### Working Directory

```yaml
defaults:
  run:
    working-directory: ./terraform-infrastructure
```

#### Required Permissions

```yaml
permissions:
  contents: read           # Read repository
  pull-requests: write     # Comment on PRs
  id-token: write          # OIDC for Azure
```

#### PR Comment Example

The workflow posts formatted Terraform plans to PRs:

```
#### Terraform Format and Style 🖌 success
#### Terraform Initialization ⚙️ success
#### Terraform Validation 🤖 success
#### Terraform Plan 📖 success

<details><summary>Show Plan</summary>

```terraform
Terraform will perform the following actions:
  # module.vm.azurerm_linux_virtual_machine.vm will be updated in-place
  ...
```

</details>

*Pusher: @username, Action: pull_request*
```

---

## GitHub Container Registry (GHCR)

### Advantages

1. **Free for public repos**: No cost for public container images
2. **Integrated**: Tightly coupled with GitHub workflows
3. **Secure**: Automatic token-based authentication
4. **Fast**: Co-located with CI runners
5. **Provenance**: Built-in attestation support

### Access Control

**Public Access** (default):
- Anyone can pull images
- Only authenticated users can push

**Private Access** (optional):
- Requires authentication for pulls
- Configure in package settings

### Pulling Images

```bash
# Public images (no auth needed)
podman pull ghcr.io/borninthedark/spider-2y-banana/osyraa:latest

# Private images (auth required)
echo $GITHUB_TOKEN | podman login ghcr.io -u USERNAME --password-stdin
podman pull ghcr.io/borninthedark/spider-2y-banana/osyraa:latest

# Using skopeo to inspect without pulling
skopeo inspect docker://ghcr.io/borninthedark/spider-2y-banana/osyraa:latest
```

### Pushing Images (Manual)

```bash
# Build with buildah
buildah bud -t osyraa:local -f Containerfile .

# Authenticate
echo $GITHUB_TOKEN | podman login ghcr.io -u USERNAME --password-stdin

# Tag image
podman tag osyraa:local ghcr.io/borninthedark/spider-2y-banana/osyraa:custom-tag

# Push with podman
podman push ghcr.io/borninthedark/spider-2y-banana/osyraa:custom-tag

# Alternative: Copy with skopeo (useful for multi-registry sync)
skopeo copy \
  containers-storage:osyraa:local \
  docker://ghcr.io/borninthedark/spider-2y-banana/osyraa:custom-tag
```

---

## GitOps Integration

### Automated Deployment Flow

```
1. Developer pushes code to main
        ↓
2. GitHub Actions builds Docker image
        ↓
3. Image pushed to GHCR with tags
        ↓
4. ArgoCD pulls latest image (via image updater or manual sync)
        ↓
5. Application deployed to Kubernetes
        ↓
6. Health checks verify deployment
```

### Image Update Strategies

#### Option 1: Manual Sync (Current)
- ArgoCD uses `:latest` tag
- Manual sync triggers pull of new image
- Simple but requires manual intervention

```bash
argocd app sync resume
```

#### Option 2: ArgoCD Image Updater (Recommended)
- Automatically detects new image versions
- Updates manifests with new tags
- Fully automated GitOps workflow

Install:
```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml
```

Configure annotation:
```yaml
metadata:
  annotations:
    argocd-image-updater.argoproj.io/image-list: ghcr.io/borninthedark/spider-2y-banana/osyraa:~1.0
    argocd-image-updater.argoproj.io/write-back-method: git
```

#### Option 3: Tag-Based Deployment
- Use semantic versioning
- ArgoCD watches specific tags
- Controlled releases

```yaml
spec:
  template:
    spec:
      containers:
      - name: resume
        image: ghcr.io/borninthedark/spider-2y-banana/osyraa:1.2.3
```

---

## Monitoring Workflows

### GitHub Actions UI

View workflow runs:
1. Go to repository → Actions tab
2. Select workflow from sidebar
3. Click on specific run for details

### Workflow Badges

Add to README:
```markdown
[![Build and Push to GHCR](https://github.com/borninthedark/spider-2y-banana/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/borninthedark/spider-2y-banana/actions/workflows/build-and-push.yml)
```

### Notifications

Configure in repository Settings → Notifications:
- Email on workflow failure
- Slack/Discord webhooks
- GitHub mobile app notifications

---

## Troubleshooting

### Build Workflow Issues

#### Image Push Fails

**Symptom**: `denied: permission_denied: write_package`

**Solution**:
1. Check package visibility (Settings → Packages)
2. Verify GITHUB_TOKEN permissions in workflow
3. Ensure workflow has `packages: write` permission

#### Container Build Fails

**Symptom**: `ERROR: failed to solve: process "/bin/sh -c hugo --minify" did not complete successfully`

**Solution**:
```bash
# Test build locally with buildah
cd osyraa
buildah bud -t osyraa:test .

# Check Hugo syntax with podman
podman run --rm -v $(pwd):/src:Z klakegg/hugo:0.111.3-alpine hugo --minify

# Debug build step-by-step
buildah bud --layers -t osyraa:debug .
```

#### Trivy Scan Failures

**Symptom**: `Critical vulnerabilities found in image`

**Solution**:
```bash
# Run scan locally
podman pull aquasec/trivy:latest
podman run --rm -v /var/run/podman/podman.sock:/var/run/docker.sock \
  aquasec/trivy image osyraa:build

# Update base images in Containerfile
# Check for newer versions of hugo and nginx images
```

#### Attestation Generation Fails

**Symptom**: `Error: Unable to generate attestation`

**Solution**:
- Requires `id-token: write` permission
- Only works on main branch pushes (not PRs)
- Check GitHub Actions token permissions

### Terraform Workflow Issues

#### Authentication Failures

**Symptom**: `Error: authenticating using the Azure CLI: obtaining authorization token`

**Solution**:
1. Verify secrets are set correctly
2. Check service principal permissions
3. Test credentials locally:
```bash
az login --service-principal \
  -u $ARM_CLIENT_ID \
  -p $ARM_CLIENT_SECRET \
  --tenant $ARM_TENANT_ID
```

#### Terraform Cloud Issues

**Symptom**: `Error: Failed to get existing workspaces`

**Solution**:
1. Verify TF_API_TOKEN is correct
2. Check organization name: `DefiantEmissary`
3. Verify workspace exists: `spider-2y-banana`
4. Test token:
```bash
curl -H "Authorization: Bearer $TF_API_TOKEN" \
  https://app.terraform.io/api/v2/organizations/DefiantEmissary/workspaces
```

#### State Lock Issues

**Symptom**: `Error: Error acquiring the state lock`

**Solution**:
```bash
# Manually unlock (use with caution)
terraform force-unlock <LOCK_ID>

# Or via Terraform Cloud UI
# Settings → Locking → Force Unlock
```

---

## Best Practices

### Semantic Versioning

Use git tags for releases:
```bash
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

Workflow will automatically create:
- `ghcr.io/.../osyraa:1.2.3`
- `ghcr.io/.../osyraa:1.2`
- `ghcr.io/.../osyraa:1`

### Security

1. **Never commit secrets**: Use GitHub Secrets
2. **Rotate tokens**: Refresh service principal credentials periodically
3. **Least privilege**: Grant minimum required permissions
4. **Scan images**: Integrate Trivy or Snyk
5. **Review PRs**: Always review infrastructure changes

### Performance

1. **Use caching**: Enable Docker layer caching
2. **Parallel jobs**: Run independent steps concurrently
3. **Conditional execution**: Skip unnecessary steps
4. **Self-hosted runners**: For faster builds (optional)

### Documentation

1. **Comment workflows**: Explain complex steps
2. **Update README**: Keep badge status current
3. **Document secrets**: List required secrets
4. **Changelog**: Track workflow changes

---

## Local Testing

### Test Container Build Locally

```bash
cd osyraa

# Build with buildah (same as CI)
buildah bud \
  --format docker \
  --layers \
  --build-arg DOMAIN_NAME=princetonstrong.online \
  -t osyraa:local \
  .

# Lint Containerfile
wget -qO /tmp/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
chmod +x /tmp/hadolint
/tmp/hadolint Containerfile

# Scan with Trivy
podman run --rm -v /var/run/podman/podman.sock:/var/run/docker.sock \
  aquasec/trivy:latest image osyraa:local

# Run container with podman
podman run -p 8080:80 osyraa:local

# Test
curl http://localhost:8080

# Check logs
podman logs <container-id>

# Inspect image
skopeo inspect containers-storage:osyraa:local
```

### Test Terraform Locally

```bash
cd terraform-infrastructure

# Set Azure credentials
export ARM_CLIENT_ID="xxx"
export ARM_CLIENT_SECRET="xxx"
export ARM_SUBSCRIPTION_ID="xxx"
export ARM_TENANT_ID="xxx"

# Authenticate to Terraform Cloud
terraform login

# Test workflow steps
terraform fmt -check -recursive
terraform init
terraform validate
terraform plan
```

### Validate Workflows

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflows locally
act -l  # List workflows
act push  # Simulate push event
act pull_request  # Simulate PR event
```

---

## Migration from ACR to GHCR

**Completed**: The project has been migrated from Azure Container Registry (ACR) to GitHub Container Registry (GHCR).

### Changes Made

1. ✅ Updated workflow to push to GHCR
2. ✅ Removed ACR secrets requirements
3. ✅ Updated documentation (README, osyraa/README.md)
4. ✅ Added workflow badges
5. ✅ Updated architecture diagrams
6. ✅ Reduced cost estimate ($5/month savings)

### Benefits

- **Cost**: Free for public images (vs $5/month for ACR)
- **Simplicity**: No additional secrets needed
- **Integration**: Better GitHub ecosystem integration
- **Security**: Built-in attestation support

### Kubernetes Manifests

All manifests already reference GHCR:
- `gitops/applications/dev/resume-deployment.yaml:26`
- `jsonnet/environments/dev/main.jsonnet:9`
- `jsonnet/environments/prod/main.jsonnet:9`

---

## Future Enhancements

- [x] Add image vulnerability scanning (Trivy) ✅
- [x] Add Containerfile linting (Hadolint) ✅
- [ ] Implement multi-platform builds (arm64, amd64)
- [ ] Implement ArgoCD Image Updater
- [ ] Add performance testing in CI
- [ ] Create staging environment workflow
- [ ] Add automated rollback capability
- [ ] Implement canary deployments
- [ ] Add compliance scanning (OPA/Kyverno)
- [ ] Create workflow for disaster recovery testing
- [ ] Add SBOM generation (syft/cyclonedx)
- [ ] Implement image signing with cosign

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Podman Documentation](https://docs.podman.io/)
- [Buildah Documentation](https://buildah.io/)
- [Skopeo Documentation](https://github.com/containers/skopeo)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Hadolint Documentation](https://github.com/hadolint/hadolint)
- [Terraform Cloud Documentation](https://www.terraform.io/cloud-docs)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Build Attestations](https://docs.github.com/en/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds)

---

**Last Updated**: 2025-10-24
**Maintainer**: Princeton A. Strong
