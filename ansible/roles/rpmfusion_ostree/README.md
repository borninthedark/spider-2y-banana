# RPM Fusion for ostree-based Fedora Systems

This Ansible role enables RPM Fusion repositories on ostree-based Fedora systems (Silverblue, Kinoite, IoT) following the official Fedora documentation.

## Requirements

- ostree-based Fedora system
- `rpm-ostree` available
- Internet connectivity

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `rpmfusion_ostree_enable` | `true` | Whether to enable RPM Fusion repositories |
| `rpmfusion_ostree_mirror_url` | `https://mirrors.rpmfusion.org` | RPM Fusion mirror URL |
| `rpmfusion_ostree_skip_reboot` | `false` | Skip automatic reboots (for manual control) |

## How It Works

The role follows a two-stage process as per [Fedora documentation](https://docs.fedoraproject.org/en-US/quick-docs/rpmfusion-setup/):

### Stage 1: Install versioned repositories
- Installs Fedora version-specific RPM Fusion repo packages
- Reboots to activate the new ostree deployment

### Stage 2: Swap to unversioned repositories
- Replaces versioned repos with unversioned ones
- Provides flexibility across Fedora version upgrades
- Reboots to finalize changes

## Example Playbook

```yaml
- hosts: ostree_systems
  roles:
    - role: rpmfusion_ostree
```

### With custom variables:

```yaml
- hosts: ostree_systems
  roles:
    - role: rpmfusion_ostree
      vars:
        rpmfusion_ostree_skip_reboot: true  # Control reboots manually
```

## Idempotency

The role checks existing installations and skips completed stages, making it safe to run multiple times.

## License

MIT

## References

- [Fedora Quick Docs: RPM Fusion Setup](https://docs.fedoraproject.org/en-US/quick-docs/rpmfusion-setup/)
