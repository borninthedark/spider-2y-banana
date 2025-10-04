# Migration from exousia to spider-2y-banana

Guide for transitioning from exousia bootc images to spider-2y-banana container-based provisioning.

## Why Migrate?

spider-2y-banana provides a more flexible, standardized approach:

- ✅ **Standard containers** - Works with any container runtime
- ✅ **Ansible-based** - Modular, reusable roles
- ✅ **Packer integration** - Build images for any platform
- ✅ **Better testing** - Comprehensive BATS test suite
- ✅ **DevSecOps pipeline** - Build, test, scan, sign workflow
- ✅ **Easier customization** - Edit role defaults, not Containerfiles

## What's Been Integrated

### From exousia → spider-2y-banana

| exousia Component | spider-2y-banana Equivalent | Status |
|-------------------|----------------------------|--------|
| `custom-pkgs/packages.add` | `ansible/roles/base_packages/defaults/main.yml` | ✅ Migrated |
| `custom-pkgs/packages.remove` | `ansible/roles/base_packages/defaults/main.yml` | ✅ Migrated |
| `custom-pkgs/packages.sway` | `ansible/roles/sway_desktop/defaults/main.yml` | ✅ Migrated |
| `custom-pkgs/packages.k8s` | `ansible/roles/kubernetes_tools/*` | ✅ Migrated |
| `custom-scripts/autotiling` | `ansible/roles/sway_desktop/files/autotiling` | ✅ Migrated |
| `custom-scripts/lid` | `ansible/roles/sway_desktop/files/lid` | ✅ Migrated |
| `custom-scripts/config-authselect` | `ansible/roles/security/tasks/main.yml` | ✅ Migrated |
| `custom-scripts/initramfs` | `ansible/roles/system_services/tasks/main.yml` | ✅ Migrated |
| `custom-tests/image_content.bats` | `tests/container/image_content.bats` | ✅ Refined |
| `.github/workflows/build.yaml` | `.github/workflows/packer-devsec-ci.yml` | ✅ Adapted |

### New Capabilities

spider-2y-banana adds:

- **Packer templates** - Build Docker containers, not just bootc images
- **Modular roles** - Reusable across projects
- **Tag-based execution** - Run only needed roles
- **Multi-target** - Provision containers or VMs
- **Better docs** - Comprehensive guides and examples

## Migration Steps

### Phase 1: Preparation (Week 1)

#### 1.1 Set Up spider-2y-banana

```bash
# Clone spider-2y-banana
git clone https://github.com/your-org/spider-2y-banana
cd spider-2y-banana

# Add Docker Hub secrets to repository
# Settings → Secrets → DOCKERHUB_USERNAME, DOCKERHUB_TOKEN
```

#### 1.2 Verify Configuration

```bash
# Check Ansible roles match your exousia config
diff ../exousia/custom-pkgs/packages.add \
     ansible/roles/base_packages/defaults/main.yml

# Update any custom packages
vim ansible/roles/base_packages/defaults/main.yml
```

#### 1.3 Test Builds Locally

```bash
# Build a test image
cd packer/fedora-base
packer init .

export REGISTRY_USERNAME="your-username"
export REGISTRY_PASSWORD="your-token"

packer build -except="docker-push" .

# Test it
docker run -it your-username/fedora-base:latest bash
```

### Phase 2: Parallel Operation (Week 2-4)

Run both exousia and spider-2y-banana in parallel:

#### 2.1 Deploy Test Instances

```bash
# exousia bootc (existing)
sudo bootc switch docker.io/your-username/exousia:latest
sudo bootc upgrade

# spider-2y-banana container (new)
docker run -d your-username/fedora-k8s:latest
```

#### 2.2 Validate Functionality

Test checklist:
- [ ] All packages installed
- [ ] Services running
- [ ] Configurations correct
- [ ] Scripts executable
- [ ] K8s tools working
- [ ] Sway desktop functional

#### 2.3 Monitor Issues

Track differences:
```bash
# Compare package lists
docker exec spider-container rpm -qa | sort > spider-pkgs.txt
ssh bootc-system "rpm -qa | sort" > exousia-pkgs.txt
diff spider-pkgs.txt exousia-pkgs.txt
```

### Phase 3: Gradual Rollout (Week 4-8)

#### 3.1 Update Documentation

Replace exousia references:

**Before:**
```bash
sudo bootc switch docker.io/your-username/exousia:latest
```

**After:**
```bash
docker pull your-username/fedora-k8s:latest
docker run -it your-username/fedora-k8s:latest
```

#### 3.2 Update CI/CD Pipelines

**Before (exousia):**
```yaml
- name: Deploy bootc image
  run: |
    ssh server "sudo bootc switch docker.io/your-username/exousia:latest"
    ssh server "sudo bootc upgrade"
```

**After (spider-2y-banana):**
```yaml
- name: Provision with Ansible
  run: |
    cd spider-2y-banana/ansible
    ansible-playbook -i inventory/hosts playbooks/provision.yml
```

#### 3.3 Migrate Workloads

Priority order:
1. Development environments
2. Staging systems
3. Production (after validation)

### Phase 4: Complete Migration (Week 8-12)

#### 4.1 Deprecate exousia

Add deprecation notice to exousia README:

```markdown
# ⚠️ DEPRECATED

This repository is deprecated in favor of [spider-2y-banana](https://github.com/your-org/spider-2y-banana).

**Migration Guide:** [MIGRATION_FROM_EXOUSIA.md](https://github.com/your-org/spider-2y-banana/blob/main/MIGRATION_FROM_EXOUSIA.md)
```

#### 4.2 Archive exousia

```bash
# GitHub Settings → Archive this repository
# Add final commit
git add README.md
git commit -m "docs: deprecate in favor of spider-2y-banana"
git push
```

#### 4.3 Cleanup

- Remove exousia workflows
- Delete old bootc images (after grace period)
- Update all documentation
- Notify team of completion

## Configuration Mapping

### Package Lists

**exousia:**
```
custom-pkgs/packages.add
```

**spider-2y-banana:**
```
ansible/roles/base_packages/defaults/main.yml
ansible/roles/kubernetes_tools/defaults/main.yml
ansible/roles/sway_desktop/defaults/main.yml
```

### Scripts

**exousia:**
```
custom-scripts/
├── autotiling
├── config-authselect
├── lid
└── initramfs
```

**spider-2y-banana:**
```
ansible/roles/sway_desktop/files/
├── autotiling
└── lid

ansible/roles/security/tasks/main.yml (authselect)
ansible/roles/system_services/tasks/main.yml (Plymouth/initramfs)
```

### Tests

**exousia:**
```
custom-tests/image_content.bats
```

**spider-2y-banana:**
```
tests/container/image_content.bats
```

### Workflows

**exousia:**
```
.github/workflows/build.yaml
```

**spider-2y-banana:**
```
.github/workflows/packer-devsec-ci.yml
.github/workflows/ansible-lint.yml
```

## Use Case Mapping

| exousia Use Case | spider-2y-banana Solution |
|------------------|--------------------------|
| Bootable bare metal system | Use Ansible to provision existing system |
| Immutable VM | Use Packer to build VM images (future) |
| Container base image | Use Packer to build Docker images |
| Development environment | Use Ansible playbook locally |
| CI/CD image | Pull spider-2y-banana images |

## Advantages of spider-2y-banana

### 1. Flexibility

**exousia:** Locked to bootc workflow
**spider-2y-banana:** Works with:
- Docker/Podman containers
- Ansible on bare metal
- Future: AMIs, VM images, etc.

### 2. Modularity

**exousia:** Monolithic Containerfile
**spider-2y-banana:** Modular Ansible roles
- Reuse roles in other projects
- Mix and match components
- Tag-based execution

### 3. Testing

**exousia:** Single test file
**spider-2y-banana:**
- Role-specific tests
- Container tests
- Ansible playbook tests
- CI/CD integration

### 4. Customization

**exousia:** Edit Containerfile, rebuild everything
**spider-2y-banana:** Edit role defaults, rebuild only changed roles

### 5. Documentation

**exousia:** README
**spider-2y-banana:**
- Comprehensive docs/
- Per-role documentation
- Examples and guides
- Workflow documentation

## Common Migration Issues

### Issue 1: Missing Packages

**Problem:** Some packages not installed

**Solution:** Check role defaults match exousia
```bash
cd ansible/roles/base_packages
vim defaults/main.yml
```

### Issue 2: Scripts Not Executable

**Problem:** Custom scripts not found

**Solution:** Verify script deployment
```bash
# Check Ansible task
cat ansible/roles/sway_desktop/tasks/main.yml | grep autotiling
```

### Issue 3: Services Not Starting

**Problem:** systemd services not enabled

**Solution:** Update system_services role
```yaml
- name: Enable my-service
  ansible.builtin.systemd:
    name: my-service
    enabled: true
```

### Issue 4: Configuration Missing

**Problem:** Custom configs not present

**Solution:** Add to appropriate role
```bash
mkdir -p ansible/roles/my_role/files
cp my-config ansible/roles/my_role/files/
```

## Support During Migration

### Documentation

- [CONFIGURATION.md](docs/CONFIGURATION.md) - All variables and secrets
- [WORKFLOWS.md](docs/WORKFLOWS.md) - CI/CD pipeline guide
- [QUICK_START.md](docs/QUICK_START.md) - Fast setup guide

### Testing

Run tests before deploying:
```bash
# Syntax check
ansible-playbook playbooks/provision.yml --syntax-check

# Dry run
ansible-playbook playbooks/provision.yml --check

# Container tests
export TEST_IMAGE_TAG="your-username/fedora-base:latest"
bats tests/container/
```

### Rollback Plan

If issues arise:
```bash
# Keep exousia images available
# Document rollback procedure
# Have backups ready
```

## Timeline Example

**Week 1-2:** Setup and testing
**Week 3-4:** Parallel operation
**Week 5-8:** Gradual rollout
**Week 9-12:** Complete migration
**Week 13+:** exousia deprecated

## Success Criteria

Migration is complete when:
- [ ] All workloads running on spider-2y-banana
- [ ] Documentation updated
- [ ] Team trained on new workflow
- [ ] exousia archived
- [ ] No active exousia deployments

## Questions?

Open an issue in spider-2y-banana repository with:
- Migration phase
- Specific problem
- Error messages
- What you've tried

---

**🎉 Welcome to spider-2y-banana!**
