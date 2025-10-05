# spider-2y-banana

Ansible playbooks and ansible-bender for provisioning Fedora systems and building container images.

## 🎯 Purpose

This repository provides:
1. **Ansible playbooks** - Provision Fedora systems with modular, reusable roles
2. **ansible-bender** - Build custom Fedora container images using Ansible + buildah
3. **Integration with exousia** - Referenced by exousia bootc builds for consistent provisioning

## 📁 Repository Structure

```
.
├── ansible/                    # Ansible playbooks and roles
│   ├── playbooks/
│   │   ├── provision.yml      # Main provisioning playbook
│   │   ├── build-image.yml    # ansible-bender container build playbook
│   │   └── generate-readme.yml
│   ├── roles/                 # Modular Ansible roles
│   │   ├── base_packages/     # Core utilities and tools
│   │   ├── kubernetes_tools/  # k3s, kubectl, Helm, ArgoCD
│   │   ├── sway_desktop/      # Sway window manager
│   │   ├── security/          # U2F, PAM configuration
│   │   ├── system_services/   # systemd, Plymouth
│   │   └── virtualization/    # libvirt, virt-manager
│   ├── inventory/             # Inventory files
│   └── requirements.yml       # Ansible Galaxy dependencies
│
├── .github/workflows/        # GitHub Actions CI/CD
│   ├── ansible-lint.yml      # Lint Ansible playbooks
│   └── fedora-exousia-pipeline.yml  # Build container images with ansible-bender
│
└── tests/                    # Container image tests
    └── container/            # BATS integration tests
```

## 🚀 Quick Start

### Ansible Provisioning

```bash
# Install Ansible
pip install ansible

# Install dependencies
cd ansible
ansible-galaxy install -r requirements.yml

# Provision local system
ansible-playbook -i inventory/hosts playbooks/provision.yml --connection=local

# Provision remote systems
ansible-playbook -i inventory/hosts playbooks/provision.yml
```

### Container Image Builds

```bash
# Install dependencies
sudo dnf install buildah  # Fedora/RHEL
# or
sudo apt-get install buildah  # Ubuntu/Debian

pip install ansible-bender

# Build container image
ansible-bender build \
  --extra-vars "fedora_version=42 registry=docker.io registry_username=your-username" \
  ansible/playbooks/build-image.yml

# Push to registry
buildah push docker.io/your-username/fedora-exousia:latest
```

## 📦 Available Images

Built with ansible-bender, provisioned with Ansible:

| Image | Base | Includes | Use Case |
|-------|------|----------|----------|
| **fedora-exousia** | Fedora 42 bootc | Base packages, K8s tools, Sway desktop, virtualization | Complete development environment |

Pull from Docker Hub:
```bash
podman pull docker.io/your-username/fedora-exousia:latest
# or
docker pull docker.io/your-username/fedora-exousia:latest
```

## 🔧 Ansible Roles

### base_packages
Core system packages from exousia packages.add:
- Development tools (neovim, git, ripgrep, fzf)
- System utilities (htop, btop, fastfetch, glances)
- Security tools (lynis, pam-u2f, openssl)
- Cloud tools (awscli2)

**Tags:** `base`, `packages`

### kubernetes_tools
Full Kubernetes ecosystem:
- k3s v1.30.5+k3s1
- kubectl v1.30.0
- Helm v3.16.2
- ArgoCD CLI v2.12.3
- k3d v5.7.4

**Tags:** `k8s`, `kubernetes`

### sway_desktop
Complete Sway desktop environment:
- Sway window manager
- greetd/tuigreet display manager
- Desktop applications
- Autotiling and lid management scripts

**Tags:** `sway`, `desktop`

### security
Security hardening:
- U2F authentication
- PAM configuration with authselect

**Tags:** `security`, `auth`

### system_services
System configuration:
- systemd services
- Plymouth boot splash
- Flathub repository

**Tags:** `services`, `config`

### virtualization
Virtualization stack:
- libvirt, virt-manager
- QEMU/KVM

**Tags:** `virt`, `virtualization`

## 🎛️ Configuration

### Required Secrets (GitHub Actions)

For Packer container builds, set these in spider-2y-banana repository:
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for complete setup guide.

### Ansible Variables

Common variables in `ansible/playbooks/provision.yml`:

```yaml
enable_k8s_tools: true
enable_sway_desktop: false
enable_virtualization: true
enable_plymouth: true
plymouth_theme: bgrt-better-luks
```

Override at runtime:
```bash
ansible-playbook playbooks/provision.yml \
  -e "enable_k8s_tools=false" \
  -e "enable_sway_desktop=true"
```

## 🔄 Integration with exousia

The [exousia](https://github.com/borninthedark/exousia) project references this repository:

**exousia** → Builds bootc container images for bare metal/VM deployment
**spider-2y-banana** → Provides Ansible playbooks and builds standard containers

Both use identical Ansible roles for consistent provisioning.

## 🏗️ CI/CD Workflows

### Fedora Exousia DevSecOps CI
Comprehensive DevSecOps pipeline for container images:

**Stages:**
1. **Build** - ansible-bender builds with Ansible provisioning
2. **Test** - BATS integration tests
3. **Scan** - Trivy vulnerability scanning
4. **Push** - Publish to Docker Hub (non-PR only)
5. **Sign** - Cosign image signing with Sigstore
6. **Summary** - Build artifacts and reports

**Triggers:**
- **Automatic:** Push to main, nightly at 5:30 AM UTC
- **Manual:** Workflow dispatch (with push toggle)
- **PR:** Build and test without pushing

Trigger manually:
```
Actions → Fedora Sericea Bootc DevSec CI → Run workflow
```

### Ansible Lint
Runs on push/PR to `ansible/**`:
- Validates playbook syntax
- Checks best practices

## 📚 Documentation

- [Configuration Guide](docs/CONFIGURATION.md) - Variables, secrets, setup
- [Ansible README](ansible/README.md) - Ansible playbooks guide
- [ansible-bender Documentation](https://ansible-community.github.io/ansible-bender/) - Official docs

## 🛠️ Development

### Testing Ansible Locally

```bash
# Syntax check
ansible-playbook playbooks/provision.yml --syntax-check

# Dry run
ansible-playbook playbooks/provision.yml --check

# Run with specific tags
ansible-playbook playbooks/provision.yml --tags base,security
```

### Testing Container Builds Locally

```bash
# Build without pushing
ansible-bender build \
  --extra-vars "fedora_version=42 registry=docker.io registry_username=test" \
  ansible/playbooks/build-image.yml

# Build with no cache
ansible-bender build --no-cache \
  --extra-vars "fedora_version=42" \
  ansible/playbooks/build-image.yml

# List built images
buildah images
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Run linters: `ansible-lint` and test builds with `ansible-bender`
5. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Based on configuration from [exousia](https://github.com/borninthedark/exousia)
- Fedora Project and bootc maintainers
- Ansible and ansible-bender communities

---

**Built for Fedora systems with Ansible and ansible-bender**
