# Packer Templates for Fedora Container Images

Build custom Fedora container images using Packer and Ansible playbooks from spider-2y-banana.

## 📦 Available Templates

### fedora-base
Minimal Fedora container with core packages.

**Includes:**
- Core utilities (from ansible/roles/base_packages)
- Security hardening (U2F support)
- System services configuration

**Base:** `quay.io/fedora/fedora:43`

### fedora-k8s
Fedora container with full Kubernetes tooling.

**Includes:**
- Everything in fedora-base
- k3s v1.30.5+k3s1
- kubectl v1.30.0
- Helm v3.16.2
- ArgoCD CLI v2.12.3
- k3d v5.7.4
- Rootless k3s configuration

**Base:** `quay.io/fedora/fedora:43`

### fedora-sway
Fedora container with Sway desktop environment.

**Includes:**
- Everything in fedora-base
- Sway window manager
- greetd/tuigreet display manager
- Desktop applications (Firefox, Thunar, etc.)
- Autotiling and lid management scripts

**Base:** `quay.io/fedora/fedora:43`

## 🚀 Usage

### Prerequisites

```bash
# Install Packer
brew install packer  # macOS
# or
sudo dnf install packer  # Fedora

# Install Ansible
pip install ansible

# Install Docker or Podman
sudo dnf install docker  # or podman
sudo systemctl start docker
```

### Build Container Images Locally

```bash
# Build fedora-base
cd packer/fedora-base
packer init .
packer validate .

# Build without pushing to registry
packer build -except="docker-push" .

# Build and push to registry (requires credentials)
export REGISTRY_USERNAME="your-username"
export REGISTRY_PASSWORD="your-token"
packer build .
```

### Build Other Images

```bash
# Build fedora-k8s
cd packer/fedora-k8s
packer init .
packer build -except="docker-push" .

# Build fedora-sway
cd packer/fedora-sway
packer init .
packer build -except="docker-push" .
```

### Custom Variables

Override default variables:

```bash
cd packer/fedora-base
packer build \
  -var "fedora_version=43" \
  -var "image_name=my-fedora" \
  -var "image_tag=v1.0" \
  -var "registry=ghcr.io" \
  -var "registry_username=myuser" \
  -except="docker-push" \
  .
```

## 🔧 How It Works

### Packer + Ansible Integration

1. **Packer** pulls the base Fedora image from Quay
2. **Packer** starts a Docker container from the base image
3. **Ansible** provisioner runs playbooks from `ansible/playbooks/provision.yml`
4. **Packer** commits the container to a new image
5. **Packer** tags and pushes to container registry

### Ansible Provisioning

All images use the same modular Ansible roles:
- `base_packages` - Core system packages
- `kubernetes_tools` - K8s ecosystem (k8s image only)
- `sway_desktop` - Desktop environment (sway image only)
- `security` - Security hardening
- `system_services` - systemd services

Tags control which roles run for each image type.

## 🏗️ CI/CD Integration

### GitHub Actions

The repository includes `.github/workflows/packer-build.yml` for automated builds:

**Triggers:**
- Push to main (builds and pushes all images)
- Pull requests (builds without pushing)
- Manual workflow dispatch (choose image type)

**Usage:**
1. Set repository secrets:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
2. Push to main or trigger manually
3. Images are built and pushed to Docker Hub

**Manual Trigger:**
```
Actions → Build Container Images with Packer → Run workflow
- Select image type (fedora-base, fedora-k8s, fedora-sway, or all)
- Choose whether to push to registry
```

## 🐳 Using Built Images

### Pull and Run

```bash
# Pull from Docker Hub
docker pull your-username/fedora-base:latest
docker pull your-username/fedora-k8s:latest
docker pull your-username/fedora-sway:latest

# Run interactively
docker run -it your-username/fedora-base:latest /bin/bash

# Verify Kubernetes tools (k8s image)
docker run -it your-username/fedora-k8s:latest kubectl version --client
docker run -it your-username/fedora-k8s:latest helm version
```

### Use as Base Image

```dockerfile
FROM your-username/fedora-k8s:latest

# Add your application
COPY app /app
CMD ["/app/start.sh"]
```

## 📋 Image Tags

Each build creates multiple tags:
- `latest` - Latest build
- `43` - Fedora version
- `43-<timestamp>` - Specific build timestamp
- `k3s-v1.30.5` - Version-specific (k8s image only)

Example:
```bash
docker pull your-username/fedora-k8s:latest
docker pull your-username/fedora-k8s:43
docker pull your-username/fedora-k8s:k3s-v1.30.5
```

## 🔧 Customization

### Modify Package Lists

Edit Ansible role defaults:
```bash
# Core packages
vim ansible/roles/base_packages/defaults/main.yml

# Kubernetes versions
vim ansible/roles/kubernetes_tools/defaults/main.yml

# Sway desktop packages
vim ansible/roles/sway_desktop/defaults/main.yml
```

### Change Base Image

Edit the `source "docker"` block in any `.pkr.hcl`:
```hcl
source "docker" "fedora_base" {
  image  = "quay.io/fedora/fedora:44"  # Change version
  # or use different base
  image  = "registry.fedoraproject.org/fedora:latest"
  ...
}
```

### Add Custom Provisioners

Edit build blocks in `.pkr.hcl` files:
```hcl
build {
  # Add shell provisioner
  provisioner "shell" {
    inline = [
      "dnf install -y my-custom-package"
    ]
  }

  # Add file provisioner
  provisioner "file" {
    source      = "myfile.conf"
    destination = "/etc/myfile.conf"
  }
}
```

## 🧪 Testing Images

After building, test the image:

```bash
# Basic functionality
docker run -it your-username/fedora-base:latest bash -c "dnf --version && python3 --version"

# Kubernetes tools (k8s image)
docker run -it your-username/fedora-k8s:latest bash -c "
  kubectl version --client &&
  helm version &&
  k3s --version &&
  argocd version --client
"

# Sway desktop packages (sway image)
docker run -it your-username/fedora-sway:latest bash -c "
  swaymsg -v &&
  firefox --version
"
```

## 🔐 Security Notes

- Never commit registry credentials
- Use GitHub Secrets for CI/CD credentials
- Images are public by default (configure registry privacy)
- Review Ansible playbooks before building
- Scan images with Trivy or similar tools

## 📊 Build Output

Each build generates `manifest.json`:
```json
{
  "builds": [
    {
      "name": "fedora-base",
      "builder_type": "docker",
      "build_time": 1234567890,
      "artifact_id": "docker.io/username/fedora-base:latest"
    }
  ]
}
```

## 🔄 Integration with exousia

These Packer templates complement the exousia bootc image builder:

- **exousia**: Builds bootc container images for bare metal/VM deployment
- **spider-2y-banana**: Builds standard container images for containerized workloads

Both use the same Ansible playbooks for consistency.

## 📚 Resources

- [Packer Documentation](https://www.packer.io/docs)
- [Packer Docker Builder](https://www.packer.io/docs/builders/docker)
- [Ansible Provisioner](https://www.packer.io/docs/provisioners/ansible)
- [Fedora Container Images](https://quay.io/organization/fedora)

## 🤝 Contributing

To add a new template:
1. Create directory in `packer/my-image/`
2. Create `my-image.pkr.hcl` file
3. Reference appropriate Ansible tags
4. Add to GitHub Actions workflow
5. Update this README
6. Test the build locally
