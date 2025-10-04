# Quick Start Guide

Fast setup for spider-2y-banana Ansible playbooks and Packer container builds.

## ⚡ 5-Minute Setup

### 1. GitHub Secrets (Required for CI/CD)

Add these to spider-2y-banana repository:

```
Settings → Secrets and variables → Actions → New repository secret
```

| Secret Name | Value |
|-------------|-------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Token from Docker Hub → Account Settings → Security → New Access Token |

**That's it!** GitHub Actions will now automatically build and push images.

### 2. Test the Workflow

```
Actions → Build Container Images with Packer → Run workflow
```

Select:
- **Image type:** `fedora-base` (or `all` to build everything)
- **Push to registry:** ✅ (checked)

Click **Run workflow**

### 3. Pull Your Images

After ~10-15 minutes:

```bash
docker pull your-username/fedora-base:latest
docker pull your-username/fedora-k8s:latest
docker pull your-username/fedora-sway:latest
```

## 🔧 Local Development

### Ansible Only

```bash
# Install
pip install ansible

# Run
cd ansible
ansible-galaxy install -r requirements.yml
ansible-playbook -i inventory/hosts playbooks/provision.yml --connection=local
```

### Packer + Ansible

```bash
# Install tools
brew install packer  # or: sudo dnf install packer
pip install ansible

# Set credentials
export REGISTRY_USERNAME="your-dockerhub-username"
export REGISTRY_PASSWORD="your-dockerhub-token"

# Build
cd packer/fedora-base
packer init .
packer build .
```

## 📦 What Gets Built

| Image | Size | Build Time | Contents |
|-------|------|------------|----------|
| **fedora-base** | ~800MB | ~5 min | Core packages, security tools |
| **fedora-k8s** | ~1.2GB | ~8 min | Base + k3s, kubectl, Helm, ArgoCD |
| **fedora-sway** | ~1.5GB | ~12 min | Base + Sway desktop environment |

## 🎯 Common Use Cases

### Use Case 1: Build Custom Images

1. Fork spider-2y-banana
2. Add Docker Hub secrets
3. Modify `ansible/roles/*/defaults/main.yml` with your packages
4. Push to main → automatic builds
5. Pull `your-username/fedora-base:latest`

### Use Case 2: Provision Servers

1. Clone spider-2y-banana
2. Edit `ansible/inventory/hosts` with your servers
3. Run: `ansible-playbook -i inventory/hosts playbooks/provision.yml`

### Use Case 3: Test Locally

1. Clone spider-2y-banana
2. Run: `ansible-playbook playbooks/provision.yml --connection=local --tags base`
3. Verify: `which kubectl && helm version`

## 🔀 Integration with exousia

If you're using exousia for bootc images:

1. exousia automatically references spider-2y-banana
2. Both use the same Ansible roles
3. exousia builds bootc images, spider-2y-banana builds standard containers
4. Consistent configuration across both

No additional setup needed!

## ⚙️ Customization

### Change Packages

Edit package lists:
```bash
vim ansible/roles/base_packages/defaults/main.yml
vim ansible/roles/kubernetes_tools/defaults/main.yml
```

Commit and push → automatic rebuild.

### Change Versions

Edit Kubernetes versions:
```bash
vim ansible/roles/kubernetes_tools/defaults/main.yml
```

Change:
```yaml
k3s_version: v1.31.0+k3s1
kubectl_version: v1.31.0
```

### Add Custom Role

```bash
mkdir -p ansible/roles/my_role/{tasks,defaults}
echo "---" > ansible/roles/my_role/tasks/main.yml
```

Reference in `ansible/playbooks/provision.yml`:
```yaml
roles:
  - role: my_role
    tags: [custom]
```

## 🐛 Troubleshooting

### "Authentication required" in GitHub Actions

✅ **Fix:** Verify secrets are set in spider-2y-banana repository
- Settings → Secrets and variables → Actions
- Should see `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`

### "Permission denied" when building locally

✅ **Fix:** Export credentials:
```bash
export REGISTRY_USERNAME="your-username"
export REGISTRY_PASSWORD="your-token"
```

### Ansible playbook fails

✅ **Fix:** Check Python is installed:
```bash
which python3
pip install ansible
ansible --version
```

### Can't pull images

✅ **Fix:** Verify image was pushed:
- Check GitHub Actions logs
- Verify workflow completed successfully
- Check Docker Hub for your images

## 📚 Next Steps

- Read [CONFIGURATION.md](CONFIGURATION.md) for all variables
- Check [Ansible README](../ansible/README.md) for playbook details
- Check [Packer README](../packer/README.md) for template details
- Review [main README](../README.md) for full documentation

## 💡 Pro Tips

1. **Tag-based execution** - Run only what you need:
   ```bash
   ansible-playbook playbooks/provision.yml --tags k8s
   ```

2. **Dry run** - Test without changes:
   ```bash
   ansible-playbook playbooks/provision.yml --check
   ```

3. **Local testing** - Build without pushing:
   ```bash
   packer build -except="docker-push" .
   ```

4. **Parallel builds** - Use workflow dispatch with `all` to build all images at once

5. **Version pinning** - Images are tagged with timestamps for rollback:
   ```bash
   docker pull your-username/fedora-k8s:43-1696867200
   ```
