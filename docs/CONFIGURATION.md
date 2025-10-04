# Configuration Guide

Required variables and secrets for spider-2y-banana provisioning and builds.

## GitHub Repository Secrets

Configure these in **Settings → Secrets and variables → Actions → Repository secrets**

### For Packer Container Builds

| Secret Name | Required | Description | How to Get |
|------------|----------|-------------|------------|
| `DOCKERHUB_USERNAME` | Yes | Docker Hub username | Your Docker Hub account name |
| `DOCKERHUB_TOKEN` | Yes | Docker Hub access token | Docker Hub → Account Settings → Security → New Access Token |

### For exousia Reference

No additional secrets required - the workflow checks out spider-2y-banana as public repository.

## Environment Variables

### Packer Builds (Local)

When building locally with Packer:

```bash
# Docker Hub
export REGISTRY_USERNAME="your-dockerhub-username"
export REGISTRY_PASSWORD="your-dockerhub-token"
```

### Ansible Playbooks (Local)

No secrets required for local Ansible runs. However, some roles have optional configuration:

```bash
# Optional: Override default versions
export K3S_VERSION="v1.30.5+k3s1"
export KUBECTL_VERSION="v1.30.0"
export HELM_VERSION="v3.16.2"
```

## Packer Variables

### Common Variables (All Templates)

Defined in `.pkr.hcl` files, can be overridden:

| Variable | Default | Description |
|----------|---------|-------------|
| `fedora_version` | `"43"` | Fedora version to use |
| `image_name` | Template-specific | Container image name |
| `image_tag` | `"latest"` | Image tag |
| `registry` | `"docker.io"` | Container registry |
| `registry_username` | `env("REGISTRY_USERNAME")` | Registry username from env |

### Override Variables

```bash
# Local build with custom variables
cd packer/fedora-base
packer build \
  -var "fedora_version=44" \
  -var "image_tag=custom" \
  -var "registry=ghcr.io" \
  .
```

### Variables File

Create `packer/variables.pkrvars.hcl`:

```hcl
fedora_version = "43"
registry       = "ghcr.io"
image_tag      = "v1.0.0"
```

Use it:
```bash
packer build -var-file=../variables.pkrvars.hcl .
```

## Ansible Variables

### Playbook Variables

Override in `ansible/playbooks/provision.yml` or via command line:

| Variable | Default | Description |
|----------|---------|-------------|
| `fedora_version` | `43` | Fedora version |
| `enable_plymouth` | `true` | Enable Plymouth boot splash |
| `enable_k8s_tools` | `true` | Install Kubernetes tools |
| `enable_virtualization` | `true` | Install libvirt/virt-manager |
| `enable_sway_desktop` | `false` | Install Sway desktop |
| `plymouth_theme` | `"bgrt-better-luks"` | Plymouth theme name |

### Override at Runtime

```bash
ansible-playbook playbooks/provision.yml \
  -e "enable_k8s_tools=false" \
  -e "enable_sway_desktop=true" \
  -e "fedora_version=44"
```

### Role-Specific Variables

#### base_packages

Located in `ansible/roles/base_packages/defaults/main.yml`:

- `upgrade_all_packages` (default: `true`)
- `core_utilities` - List of core packages
- `security_tools` - List of security packages
- `packages_to_remove` - Packages to remove

#### kubernetes_tools

Located in `ansible/roles/kubernetes_tools/defaults/main.yml`:

- `install_kubectl` (default: `true`)
- `install_helm` (default: `true`)
- `install_k3s` (default: `true`)
- `install_argocd` (default: `true`)
- `install_k3d` (default: `true`)
- `k3s_version` (default: `"v1.30.5+k3s1"`)
- `kubectl_version` (default: `"v1.30.0"`)
- `helm_version` (default: `"v3.16.2"`)
- `argocd_version` (default: `"v2.12.3"`)
- `k3d_version` (default: `"v5.7.4"`)

#### security

Located in `ansible/roles/security/defaults/main.yml`:

- `enable_u2f` (default: `false`)
- `authselect_profile` (default: `"custom/with-u2f"`)

#### system_services

Located in `ansible/roles/system_services/defaults/main.yml`:

- `enable_graphical_target` (default: `false`)
- `enable_greetd` (default: `false`)
- `enable_virtualization` (default: `false`)
- `enable_plymouth` (default: `false`)
- `plymouth_theme` (default: `"bgrt-better-luks"`)

## GitHub Actions Workflow Inputs

### Packer Build Workflow

Manual trigger inputs (workflow_dispatch):

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `image_type` | choice | `fedora-base` | Image to build (fedora-base, fedora-k8s, fedora-sway, all) |
| `registry` | string | `docker.io` | Container registry |
| `push_image` | boolean | `false` | Push to registry |

### Ansible Lint Workflow

Triggers automatically on push/PR to `ansible/**` files.

### Ansible Provision Workflow (in exousia)

Manual trigger inputs:

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_k8s` | boolean | `true` | Enable Kubernetes tools |
| `enable_virt` | boolean | `true` | Enable virtualization |
| `ansible_tags` | string | `""` | Ansible tags (comma-separated) |

## Container Registry Setup

### Docker Hub

1. Create account at https://hub.docker.com
2. Create access token:
   - Account Settings → Security → New Access Token
   - Permissions: Read, Write, Delete
   - Copy token (shown once)
3. Add to GitHub secrets in spider-2y-banana repository:
   - `DOCKERHUB_USERNAME`: Your username
   - `DOCKERHUB_TOKEN`: The access token

## Inventory Configuration

For Ansible provisioning of remote systems, configure inventory:

### ansible/inventory/hosts

```ini
[fedora_systems]
server1 ansible_host=192.168.1.10 ansible_user=fedora
server2 ansible_host=192.168.1.11 ansible_user=fedora

[fedora_systems:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_become=true
ansible_become_method=sudo
```

### SSH Keys

For remote provisioning:

```bash
# Generate SSH key if needed
ssh-keygen -t ed25519 -f ~/.ssh/fedora_provisioning

# Copy to target systems
ssh-copy-id -i ~/.ssh/fedora_provisioning.pub fedora@192.168.1.10

# Use with Ansible
ansible-playbook -i inventory/hosts playbooks/provision.yml \
  --private-key ~/.ssh/fedora_provisioning
```

## Quick Setup Checklist

### For Packer Container Builds

- [ ] Create Docker Hub account at https://hub.docker.com
- [ ] Generate Docker Hub access token (Account Settings → Security → New Access Token)
- [ ] Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` to GitHub secrets in spider-2y-banana repository
- [ ] Test workflow: Actions → Build Container Images with Packer → Run workflow

### For Local Packer Builds

- [ ] Install Packer: `brew install packer` or `sudo dnf install packer`
- [ ] Install Ansible: `pip install ansible`
- [ ] Install Docker: `sudo dnf install docker && sudo systemctl start docker`
- [ ] Set environment variables:
  ```bash
  export REGISTRY_USERNAME="your-username"
  export REGISTRY_PASSWORD="your-token"
  ```
- [ ] Build: `cd packer/fedora-base && packer init . && packer build .`

### For Ansible Provisioning

- [ ] Install Ansible: `pip install ansible`
- [ ] Install dependencies: `cd ansible && ansible-galaxy install -r requirements.yml`
- [ ] Configure inventory: Edit `ansible/inventory/hosts`
- [ ] Run playbook: `ansible-playbook -i inventory/hosts playbooks/provision.yml`

## Security Best Practices

1. **Never commit secrets**
   - Add to `.gitignore`: `*.pkrvars.hcl`, `*.pem`, `*.key`
   - Use environment variables or GitHub secrets

2. **Use scoped tokens**
   - Docker Hub: Create token with minimal permissions
   - GitHub: Use PAT with only `write:packages` scope

3. **Rotate credentials**
   - Regularly regenerate access tokens
   - Update GitHub secrets when rotated

4. **Restrict access**
   - Use GitHub organization secrets for team access
   - Limit who can trigger workflows

5. **Review permissions**
   - Audit workflow permissions in `.github/workflows/*.yml`
   - Use `permissions:` blocks to limit scope

## Troubleshooting

### "Authentication required" during Packer build

```bash
# Verify credentials
echo $REGISTRY_USERNAME
echo $REGISTRY_PASSWORD  # Should show token

# Re-export if needed
export REGISTRY_USERNAME="your-username"
export REGISTRY_PASSWORD="your-token"
```

### GitHub Actions workflow fails to push

Check:
1. Secrets are set in spider-2y-banana: Settings → Secrets and variables → Actions
2. Secret names match exactly: `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
3. Docker Hub token has correct permissions (Read, Write, Delete)
4. Token hasn't expired

### Ansible fails to connect to remote hosts

```bash
# Test SSH connection
ssh -i ~/.ssh/your-key fedora@target-host

# Test Ansible ping
ansible -i inventory/hosts fedora_systems -m ping

# Verbose mode for debugging
ansible-playbook -i inventory/hosts playbooks/provision.yml -vvv
```

## Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Docker Hub Access Tokens](https://docs.docker.com/docker-hub/access-tokens/)
- [Packer Variables](https://www.packer.io/docs/templates/hcl_templates/variables)
- [Ansible Variables](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html)
