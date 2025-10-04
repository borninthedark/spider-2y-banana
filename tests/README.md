# Test Suite

Comprehensive tests for spider-2y-banana Ansible playbooks and Packer-built container images.

## Test Categories

### Container Tests (`tests/container/`)
Tests for Packer-built container images using BATS (Bash Automated Testing System).

- `image_content.bats` - Validates container image contents
- Tests packages, configuration files, scripts
- Runs against Docker images built by Packer

### Ansible Tests (`tests/ansible/`)
Tests for Ansible playbook provisioning.

- `playbook_syntax.bats` - Syntax validation
- `role_tests.bats` - Individual role tests
- Can test local or remote provisioning

### Common Tests (`tests/common/`)
Shared test utilities and helpers.

## Prerequisites

```bash
# Install BATS
sudo dnf install bats

# Install BATS libraries
git clone https://github.com/bats-core/bats-support test/test_helper/bats-support
git clone https://github.com/bats-core/bats-assert test/test_helper/bats-assert
git clone https://github.com/bats-core/bats-file test/test_helper/bats-file

# Or use npm
npm install -g bats bats-support bats-assert bats-file
```

## Running Tests

### Test Container Images

```bash
# Test a specific image
export TEST_IMAGE_TAG="your-username/fedora-base:latest"
bats tests/container/image_content.bats

# Test all built images
./tests/run-container-tests.sh
```

### Test Ansible Playbooks

```bash
# Syntax check
bats tests/ansible/playbook_syntax.bats

# Role tests
bats tests/ansible/role_tests.bats
```

### Run All Tests

```bash
# All tests
bats tests/

# Specific test file
bats tests/container/image_content.bats
```

## CI/CD Integration

Tests run automatically in GitHub Actions:
- Container tests run after Packer builds
- Ansible tests run on playbook changes
- All tests run on PRs

## Writing Tests

### Container Test Example

```bash
@test "Package should be installed" {
    run buildah run "$CONTAINER" -- rpm -q neovim
    assert_success
}
```

### Ansible Test Example

```bash
@test "Playbook syntax is valid" {
    run ansible-playbook playbooks/provision.yml --syntax-check
    assert_success
}
```

## Test Reports

Test results are:
- Displayed in GitHub Actions logs
- Saved as artifacts
- Reported in PR checks
