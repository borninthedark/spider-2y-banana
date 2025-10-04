# CI/CD Workflows

Complete guide to spider-2y-banana's GitHub Actions workflows.

## Overview

spider-2y-banana uses a comprehensive DevSecOps pipeline for Packer-built container images.

## Workflows

### 1. Packer DevSecOps CI

**File:** `.github/workflows/packer-devsec-ci.yml`

Complete Build → Test → Scan → Push → Sign pipeline for container images.

#### Pipeline Stages

```
┌─────────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌─────────┐
│  BUILD  │ → │ TEST │ → │ SCAN │ → │ PUSH │ → │ SIGN │ → │ SUMMARY │
└─────────┘   └──────┘   └──────┘   └──────┘   └──────┘   └─────────┘
```

##### Build Stage
- Validates Ansible role structure
- Initializes and validates Packer templates
- Lints Ansible playbooks with ansible-lint
- Builds container images with Packer + Ansible
- Creates images for: fedora-base, fedora-k8s, fedora-sway

##### Test Stage
- Runs BATS (Bash Automated Testing System) tests
- Validates package installations
- Checks configuration files
- Verifies scripts and services
- Tests role-specific functionality

##### Scan Stage
- **Trivy:** Scans for CRITICAL and HIGH vulnerabilities
- **Semgrep:** Static code analysis for security issues
- Results are non-blocking but reported

##### Push Stage
- Pushes images to Docker Hub
- Only runs on:
  - Push to main branch
  - Manual dispatch with push_image=true
  - Nightly scheduled builds
- Skipped for pull requests

##### Sign Stage
- Signs images with Cosign + Sigstore
- Provides cryptographic verification
- Enables supply chain security

##### Summary Stage
- Generates build artifacts
- Creates step summary
- Links to published images
- Provides resource documentation

#### Triggers

| Trigger | When | Behavior |
|---------|------|----------|
| **Push to main** | Code pushed to main branch | Full pipeline, push & sign images |
| **Pull request** | PR opened/updated | Build & test only, no push |
| **Manual dispatch** | User triggers workflow | Configurable: select image, push option |
| **Nightly** | 5:30 AM UTC daily | Full pipeline for all images |

#### Manual Dispatch Options

```yaml
image_type:
  - fedora-base   # Build base image only
  - fedora-k8s    # Build k8s image only
  - fedora-sway   # Build sway image only
  - all          # Build all images (default)

push_image: true/false  # Whether to push to Docker Hub
```

#### Job Matrix

Builds run in parallel:

| Job | Timeout | Includes |
|-----|---------|----------|
| `build-fedora-base` | 30 min | Core packages, security |
| `build-fedora-k8s` | 40 min | Base + Kubernetes tools |
| `build-fedora-sway` | 50 min | Base + Sway desktop |

### 2. Ansible Lint

**File:** `.github/workflows/ansible-lint.yml`

Validates Ansible playbooks for syntax and best practices.

#### What It Does

- Runs `ansible-lint` on all playbooks
- Checks YAML syntax
- Validates Ansible best practices
- Reports issues in PR checks

#### Triggers

- Push to `ansible/**` paths
- Pull requests affecting `ansible/**`

### 3. Exousia Integration

**File:** `exousia/.github/workflows/ansible.yml`

Exousia references spider-2y-banana for Ansible provisioning.

#### How It Works

1. Checks out exousia repository
2. Checks out spider-2y-banana repository
3. Runs spider-2y-banana Ansible playbooks
4. Validates playbook syntax

## Comparison: exousia vs spider-2y-banana

| Feature | exousia | spider-2y-banana |
|---------|---------|------------------|
| **Build Tool** | Buildah | Packer + Docker |
| **Image Type** | bootc (bare metal/VM) | Standard containers |
| **Base Image** | Fedora bootc/Atomic | Fedora container |
| **Provisioning** | Containerfile + scripts | Ansible playbooks |
| **Tests** | BATS on mounted filesystem | BATS on container |
| **Signing** | Cosign | Cosign |
| **Registry** | GHCR + Docker Hub | Docker Hub only |
| **Use Case** | Bootable systems | Containerized workloads |

## Security Features

### Vulnerability Scanning

**Trivy** scans for:
- OS package vulnerabilities
- Application dependencies
- Known CVEs rated CRITICAL or HIGH

**Severity Levels:**
```
CRITICAL: Immediate action required
HIGH:     Important to address
MEDIUM:   Should address when possible
LOW:      Nice to fix
```

### Static Analysis

**Semgrep** checks for:
- Security anti-patterns
- Code quality issues
- Best practice violations
- Common bugs

### Image Signing

**Cosign + Sigstore** provides:
- Cryptographic signatures
- Supply chain verification
- Transparency logs
- Keyless signing (OIDC)

**Verify signed images:**
```bash
cosign verify \
  --certificate-identity-regexp=".*" \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  docker.io/your-username/fedora-base:latest
```

## Build Artifacts

Each workflow run produces:

### Manifests

**Location:** Artifacts → `fedora-*-manifest`

**Contents:**
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

### Test Results

**Location:** Workflow logs → Test stage

**Format:** BATS test output
```
✓ OS should be Fedora Linux
✓ Core utilities should be installed
✓ k3s should be installed in k8s image
```

### Scan Reports

**Location:** Workflow logs → Scan stage

**Trivy Output:** Table format with vulnerabilities
**Semgrep Output:** Security findings and recommendations

## Workflow Outputs

### Step Summary

Automatically generated after each run:

```markdown
## 🚀 Packer Container Build Summary

**Configuration:**
- Fedora Version: `43`
- Registry: `docker.io`

### 📦 Published Images

- **Base:** `docker.io/username/fedora-base:latest`
- **K8s:** `docker.io/username/fedora-k8s:latest`
- **Sway:** `docker.io/username/fedora-sway:latest`

### 📚 Resources

- [Packer Documentation](https://www.packer.io/docs)
- [Ansible Playbooks](ansible/README.md)
- [Test Results](tests/README.md)
```

### PR Checks

Pull requests show:
- ✅ Build fedora-base
- ✅ Build fedora-k8s
- ✅ Build fedora-sway
- ✅ Ansible lint
- ⚠️  Trivy scan (warnings allowed)
- ⚠️  Semgrep analysis (warnings allowed)

## Troubleshooting

### Build Fails: "Missing role"

**Problem:** Ansible role not found

**Solution:** Verify role structure:
```bash
ls ansible/roles/
# Should show: base_packages, kubernetes_tools, etc.
```

### Test Fails: "Container not found"

**Problem:** Image wasn't built properly

**Solution:** Check Packer build logs:
```
Build Stage → Build image → View logs
```

### Push Fails: "Authentication required"

**Problem:** Docker Hub credentials not set

**Solution:** Verify secrets:
```
Settings → Secrets → DOCKERHUB_USERNAME, DOCKERHUB_TOKEN
```

### Signing Fails: "Cosign error"

**Problem:** OIDC token issue

**Solution:** Check workflow permissions:
```yaml
permissions:
  id-token: write  # Required for Cosign
```

## Best Practices

### For Pull Requests

1. **Always run tests:** Ensure tests pass before requesting review
2. **Check lint output:** Address ansible-lint warnings
3. **Review scan results:** Look at Trivy/Semgrep findings
4. **Keep changes focused:** One feature/fix per PR

### For Main Branch

1. **Merge when green:** All checks must pass
2. **Monitor builds:** Watch automated builds after merge
3. **Verify images:** Test pulled images after push
4. **Check signatures:** Validate Cosign signatures

### For Scheduled Builds

1. **Review nightly results:** Check daily build status
2. **Update dependencies:** Keep Packer/Ansible current
3. **Address CVEs:** Act on Trivy findings
4. **Rotate secrets:** Update Docker Hub tokens periodically

## Advanced Usage

### Custom Test Suites

Add tests to `tests/container/`:

```bash
@test "My custom package is installed" {
    run buildah run "$CONTAINER" -- rpm -q my-package
    assert_success
}
```

### Conditional Builds

Skip stages with workflow inputs:

```bash
# Build without tests
skip_tests: true

# Build without security scans
skip_scans: true
```

### Multi-Registry Push

Extend workflow to push to multiple registries:

```yaml
- name: Push to GHCR
  run: |
    docker tag $LOCAL_IMAGE ghcr.io/${{ github.repository }}
    docker push ghcr.io/${{ github.repository }}
```

## Migration from exousia

When deprecating exousia in favor of spider-2y-banana:

1. **Update references:** Change bootc image references to standard containers
2. **Adapt inventory:** Configure Ansible inventory for target systems
3. **Test thoroughly:** Validate all use cases work with new images
4. **Document changes:** Update deployment documentation
5. **Gradual rollout:** Deploy spider-2y-banana images incrementally

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Packer CI/CD Guide](https://www.packer.io/guides/continuous-integration)
- [BATS Testing](https://bats-core.readthedocs.io/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Cosign Documentation](https://docs.sigstore.dev/cosign/)
