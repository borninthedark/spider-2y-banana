# Fedora Provisioning Playbooks

Ansible playbooks for provisioning Fedora systems with a comprehensive DevSecOps approach.
Based on the exousia bootc image configuration.

## 📋 Current Configuration

- **Fedora Version:** 43
- **Build System:** Ansible-based provisioning
- **Source:** Converted from exousia custom-pkgs and Containerfile

## 🏗️ Architecture

This repository provides modular Ansible roles for provisioning Fedora systems, designed to be called from GitHub Actions workflows or run locally.

### Available Roles

- **base_packages** - Core utilities, tools, and system packages
- **kubernetes_tools** - k3s, kubectl, Helm, ArgoCD, k3d
- **sway_desktop** - Complete Sway window manager desktop environment
- **system_services** - systemd services, Plymouth boot splash configuration
- **virtualization** - libvirt, virt-manager, QEMU/KVM
- **security** - U2F authentication, PAM configuration with authselect

## 🚀 Getting Started

### Prerequisites

- Fedora 43 or compatible
- Ansible 2.14+
- Python 3.11+

### Local Execution

```bash
cd ansible

# Install dependencies
ansible-galaxy install -r requirements.yml

# Run full provisioning
ansible-playbook -i inventory/hosts playbooks/provision.yml

# Run specific components
ansible-playbook -i inventory/hosts playbooks/provision.yml --tags base
ansible-playbook -i inventory/hosts playbooks/provision.yml --tags k8s
ansible-playbook -i inventory/hosts playbooks/provision.yml --tags sway
ansible-playbook -i inventory/hosts playbooks/provision.yml --tags security
```

### GitHub Actions

This repository can be referenced from other GitHub Actions workflows:

```yaml
- name: Checkout provisioning playbooks
  uses: actions/checkout@v4
  with:
    repository: your-org/spider-2y-banana
    path: provisioning

- name: Install Ansible
  run: pip install ansible

- name: Run Ansible provisioning
  run: |
    cd provisioning/ansible
    ansible-galaxy install -r requirements.yml
    ansible-playbook playbooks/provision.yml
```

## 🔧 Customization

### Configuration Variables

Edit `playbooks/provision.yml` or override via command line:

```bash
ansible-playbook playbooks/provision.yml \
  -e "enable_k8s_tools=false" \
  -e "enable_sway_desktop=true" \
  -e "enable_plymouth=true"
```

Available variables:
- `enable_plymouth` - Enable Plymouth boot splash (default: true)
- `enable_k8s_tools` - Install Kubernetes tools (default: true)
- `enable_virtualization` - Install virtualization stack (default: true)
- `enable_sway_desktop` - Install Sway desktop environment (default: false)
- `plymouth_theme` - Plymouth theme name (default: bgrt-better-luks)

### Inventory

Define target systems in `inventory/hosts`:

```ini
[fedora_systems]
myserver ansible_host=192.168.1.100

[all:vars]
ansible_python_interpreter=/usr/bin/python3
```

### Package Lists

Customize package lists in role defaults:
- `roles/base_packages/defaults/main.yml`
- `roles/kubernetes_tools/defaults/main.yml`
- `roles/sway_desktop/defaults/main.yml`

## 📚 Role Documentation

### base_packages

Installs core system packages from exousia packages.add including:
- Development tools (neovim, git, ripgrep, fzf)
- System utilities (htop, btop, fastfetch, glances)
- Security tools (lynis, pam-u2f, openssl)
- Cloud tools (awscli2)
- Shell tools (zsh, zsh-autosuggestions, zsh-syntax-highlighting)

**Tags:** `base`, `packages`

### kubernetes_tools

Installs Kubernetes ecosystem from exousia packages.k8s:
- k3s v1.30.5+k3s1
- kubectl v1.30.0
- Helm v3.16.2
- ArgoCD CLI v2.12.3
- k3d v5.7.4
- Rootless k3s configuration
- cgroup v2 delegation

**Tags:** `k8s`, `kubernetes`

### sway_desktop

Complete Sway desktop environment from exousia packages.sway:
- Sway window manager with sway-config-upstream
- greetd/tuigreet display manager
- Plymouth boot splash
- Bluetooth support (bluez, blueman)
- Power management (tlp, powertop)
- File manager (Thunar), media viewers (imv, zathura)
- Autotiling script for dynamic layouts
- Lid management script

**Tags:** `sway`, `desktop`

### security

Security hardening from exousia config-authselect:
- U2F authentication support
- PAM configuration with authselect
- Custom authselect profile creation

**Tags:** `security`, `auth`

### system_services

System service configuration from exousia Containerfile:
- systemd-resolved
- NetworkManager
- Flathub repository
- greetd (when Sway enabled)
- libvirtd (when virtualization enabled)
- Plymouth theme configuration
- Dracut initramfs configuration

**Tags:** `services`, `config`

### virtualization

Virtualization stack:
- libvirt, virt-manager
- QEMU/KVM
- User group configuration

**Tags:** `virt`, `virtualization`

## 🔄 Migration from exousia custom-scripts

This Ansible approach replaces the following exousia custom-scripts:
- `autotiling` → `sway_desktop` role (deployed to /usr/local/bin)
- `config-authselect` → `security` role
- `lid` → `sway_desktop` role (deployed to /usr/local/bin)
- `initramfs` → `system_services` role (Plymouth configuration)

Benefits:
- ✅ Centralized configuration management
- ✅ Idempotent operations
- ✅ Better error handling
- ✅ Reusable across multiple systems
- ✅ Integration with CI/CD pipelines

## 🤝 Contributing

Contributions welcome! Please:
1. Test changes locally first
2. Run `ansible-lint` on playbooks
3. Update role documentation
4. Submit pull requests

## 📄 License

MIT License - See LICENSE file for details

---

**Built with Ansible for Fedora systems**
