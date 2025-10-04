# Packer Templates for Fedora Container Images

Build custom Fedora container images using Packer and Ansible playbooks from spider-2y-banana.

## 📦 Available Templates

### fedora-exousia
Complete Fedora development environment combining base packages, Kubernetes tools, Sway desktop, and virtualization support.

**Includes:**
- Core utilities (from ansible/roles/base_packages)
- Security hardening (U2F support)
- System services configuration
- k3s v1.30.5+k3s1
- kubectl v1.30.0
- Helm v3.16.2
- ArgoCD CLI v2.12.3
- k3d v5.7.4
- Rootless k3s configuration
- Sway window manager
- greetd/tuigreet display manager
- Desktop applications (Firefox, Thunar, etc.)
- Autotiling and lid management scripts
- Virtualization support (libvirt, virt-manager)

**Base:** `quay.io/fedora-bootc/fedora-bootc:43`

## 🚀 Usage

### Prerequisites

```bash
# Install Packer
brew install packer  # macOS
# or
sudo dnf install packer  # Fedora

# Install Ansible
pip install ansible

# Install container tools
sudo dnf install podman buildah skopeo
```

### Build Container Image Locally

```bash
# Build fedora-exousia
cd packer/fedora-exousia
packer init .
packer validate .

# Build without pushing to registry
packer build -except="docker-push" .

# Build and push to registry (requires credentials)
export REGISTRY_USERNAME="your-username"
export REGISTRY_PASSWORD="your-token"
packer build .
```

### Custom Variables

Override default variables:

```bash
cd packer/fedora-exousia
packer build \
  -var "fedora_version=43" \
  -var "image_name=my-fedora-exousia" \
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

The image uses modular Ansible roles:
- `base_packages` - Core system packages
- `kubernetes_tools` - K8s ecosystem
- `sway_desktop` - Desktop environment
- `security` - Security hardening
- `system_services` - systemd services
- `virtualization` - libvirt and virt-manager

Tags control which roles are applied during the build.

## 🏗️ CI/CD Integration

### GitHub Actions

The repository includes `.github/workflows/packer-devsec-ci.yml` for automated builds:

**Triggers:**
- Push to main (builds and pushes image)
- Pull requests (builds without pushing)
- Manual workflow dispatch
- Nightly builds at 5:30 AM UTC

**Usage:**
1. Set repository secrets:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
2. Push to main or trigger manually
3. Image is built and pushed to Docker Hub

**Manual Trigger:**
```
Actions → Packer DevSecOps CI → Run workflow
- Choose whether to push to registry
```

## 🐳 Using Built Images

### Pull and Run

```bash
# Pull from Docker Hub
podman pull your-username/fedora-exousia:latest

# Run interactively
podman run -it your-username/fedora-exousia:latest /bin/bash

# Verify Kubernetes tools
podman run -it your-username/fedora-exousia:latest kubectl version --client
podman run -it your-username/fedora-exousia:latest helm version
```

### Use as Base Image

```dockerfile
FROM your-username/fedora-exousia:latest

# Add your application
COPY app /app
CMD ["/app/start.sh"]
```

## 📋 Image Tags

Each build creates multiple tags:
- `latest` - Latest build
- `43` - Fedora version
- `43-<timestamp>` - Specific build timestamp

Example:
```bash
podman pull your-username/fedora-exousia:latest
podman pull your-username/fedora-exousia:43
podman pull your-username/fedora-exousia:43-1234567890
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

Edit the `source "docker"` block in the `.pkr.hcl`:
```hcl
source "docker" "fedora_exousia" {
  image  = "quay.io/fedora-bootc/fedora-bootc:44"  # Change version
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
podman run -it your-username/fedora-exousia:latest bash -c "dnf --version && python3 --version"

# Kubernetes tools
podman run -it your-username/fedora-exousia:latest bash -c "
  kubectl version --client &&
  helm version &&
  k3s --version &&
  argocd version --client
"

# Sway desktop packages
podman run -it your-username/fedora-exousia:latest bash -c "
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

Each build generates `manifest-<version>.json`:
```json
{
  "builds": [
    {
      "name": "fedora-exousia-43",
      "builder_type": "docker",
      "build_time": 1234567890,
      "artifact_id": "docker.io/username/fedora-exousia:latest"
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

To modify the template:
1. Edit `packer/fedora-exousia/fedora-exousia.pkr.hcl`
2. Reference appropriate Ansible tags
3. Update this README
4. Test the build locally
