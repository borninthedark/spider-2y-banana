#!/usr/bin/env bats
# Container image content tests for spider-2y-banana Packer-built images
# Based on exousia tests, refined for Ansible-provisioned containers

# Load Bats libraries
bats_load_library bats-support
bats_load_library bats-assert
bats_load_library bats-file

setup_file() {
    if [ -z "$TEST_IMAGE_TAG" ]; then
        echo "FATAL: TEST_IMAGE_TAG environment variable is not set." >&2
        echo "Example: export TEST_IMAGE_TAG=your-username/fedora-base:latest" >&2
        return 1
    fi
    echo "--- Using test image: $TEST_IMAGE_TAG ---"

    CONTAINER=$(buildah from --pull-never "$TEST_IMAGE_TAG")
    MOUNT_POINT=$(buildah mount "$CONTAINER")

    export CONTAINER MOUNT_POINT
    echo "--- Container filesystem mounted at $MOUNT_POINT ---"

    # Detect Fedora version
    if [ -f "$MOUNT_POINT/etc/os-release" ]; then
        FEDORA_VERSION=$(grep -oP 'VERSION_ID=\K\d+' "$MOUNT_POINT/etc/os-release" || echo "unknown")
        export FEDORA_VERSION
        echo "--- Detected Fedora version: $FEDORA_VERSION ---"
    fi
}

teardown_file() {
    echo "--- Cleaning up test resources ---"
    buildah umount "$CONTAINER"
    buildah rm "$CONTAINER"
}

# fedora-exousia includes all features: base, k8s, and sway

# --- OS / Fedora version checks ---

@test "OS should be Fedora Linux" {
    run grep 'ID=fedora' "$MOUNT_POINT/etc/os-release"
    assert_success "Should be running Fedora Linux"
}

@test "OS version should be Fedora 43" {
    run grep 'VERSION_ID=43' "$MOUNT_POINT/etc/os-release"
    assert_success "Should be Fedora 43"
}

# --- Base Packages (All Images) ---

@test "DNF should be installed" {
    run buildah run "$CONTAINER" -- rpm -q dnf5
    assert_success "dnf5 should be installed"
}

@test "Core utilities should be installed" {
    run buildah run "$CONTAINER" -- rpm -q neovim
    assert_success "neovim should be installed"

    run buildah run "$CONTAINER" -- rpm -q htop
    assert_success "htop should be installed"

    run buildah run "$CONTAINER" -- rpm -q git
    assert_success "git should be installed"
}

@test "Security tools should be installed" {
    run buildah run "$CONTAINER" -- rpm -q pam-u2f
    assert_success "pam-u2f should be installed"

    run buildah run "$CONTAINER" -- rpm -q lynis
    assert_success "lynis should be installed"
}

@test "Development tools should be installed" {
    run buildah run "$CONTAINER" -- rpm -q ripgrep
    assert_success "ripgrep should be installed"

    run buildah run "$CONTAINER" -- rpm -q fzf
    assert_success "fzf should be installed"
}

@test "Removed packages should NOT be installed" {
    run buildah run "$CONTAINER" -- rpm -q foot
    assert_failure "foot should be removed"

    run buildah run "$CONTAINER" -- rpm -q dunst
    assert_failure "dunst should be removed"

    run buildah run "$CONTAINER" -- rpm -q rofi-wayland
    assert_failure "rofi-wayland should be removed"
}

# --- Kubernetes Tools ---

@test "k3s should be installed" {
    run buildah run "$CONTAINER" -- k3s --version
    assert_success
    assert_output --partial "k3s version"
}

@test "kubectl should be installed" {
    run buildah run "$CONTAINER" -- kubectl version --client
    assert_success
}

@test "Helm should be installed" {
    run buildah run "$CONTAINER" -- helm version
    assert_success
}

@test "ArgoCD CLI should be installed" {
    run buildah run "$CONTAINER" -- argocd version --client
    assert_success
}

@test "k3d should be installed" {
    run buildah run "$CONTAINER" -- k3d version
    assert_success
}

@test "k3s-rootless systemd service should exist" {
    assert_file_exists "$MOUNT_POINT/etc/skel/.config/systemd/user/k3s-rootless.service"
}

@test "KUBECONFIG should be configured in .bashrc" {
    run grep "KUBECONFIG" "$MOUNT_POINT/etc/skel/.bashrc"
    assert_success
    assert_output --partial "~/.kube/k3s.yaml"
}

# --- Sway Desktop ---

@test "Sway should be installed" {
    run buildah run "$CONTAINER" -- rpm -q sway-config-upstream
    assert_success "sway-config-upstream should be installed"
}

@test "Greetd should be installed" {
    run buildah run "$CONTAINER" -- rpm -q greetd
    assert_success "greetd should be installed"

    run buildah run "$CONTAINER" -- rpm -q tuigreet
    assert_success "tuigreet should be installed"
}

@test "Desktop applications should be installed" {
    run buildah run "$CONTAINER" -- rpm -q firefox
    assert_success "firefox should be installed"

    run buildah run "$CONTAINER" -- rpm -q thunar
    assert_success "thunar should be installed"
}

@test "Autotiling script should be present" {
    assert_file_executable "$MOUNT_POINT/usr/local/bin/autotiling"
}

@test "Lid management script should be present" {
    assert_file_executable "$MOUNT_POINT/usr/local/bin/lid"
}

@test "Python i3ipc should be installed" {
    run buildah run "$CONTAINER" -- rpm -q python3-i3ipc
    assert_success "python3-i3ipc should be installed for autotiling"
}

# --- System Services ---

@test "Flathub remote should be configured" {
    run buildah run "$CONTAINER" -- flatpak remotes --show-details
    assert_output --partial 'flathub'
}

@test "Systemd should be present" {
    run buildah run "$CONTAINER" -- rpm -q systemd
    assert_success
}

@test "NetworkManager should be installed" {
    run buildah run "$CONTAINER" -- rpm -q NetworkManager
    assert_success
}

# --- RPM Fusion (ostree-based) ---

@test "System should be ostree-based (bootc)" {
    assert_file_exists "$MOUNT_POINT/run/ostree-booted" "System should be ostree-based"
}

@test "RPM Fusion free repository should be installed" {
    run buildah run "$CONTAINER" -- rpm -q rpmfusion-free-release
    assert_success "rpmfusion-free-release should be installed"
}

@test "RPM Fusion nonfree repository should be installed" {
    run buildah run "$CONTAINER" -- rpm -q rpmfusion-nonfree-release
    assert_success "rpmfusion-nonfree-release should be installed"
}

@test "RPM Fusion repos should be unversioned (not tied to specific Fedora release)" {
    # Check that the installed packages are the unversioned variants
    # Unversioned packages don't have fedora version in their release string
    run buildah run "$CONTAINER" -- sh -c "rpm -q rpmfusion-free-release | grep -v 'fc[0-9]'"
    assert_success "RPM Fusion should use unversioned repositories"

    run buildah run "$CONTAINER" -- sh -c "rpm -q rpmfusion-nonfree-release | grep -v 'fc[0-9]'"
    assert_success "RPM Fusion nonfree should use unversioned repositories"
}

@test "RPM Fusion repo files should exist" {
    assert_file_exists "$MOUNT_POINT/etc/yum.repos.d/rpmfusion-free.repo"
    assert_file_exists "$MOUNT_POINT/etc/yum.repos.d/rpmfusion-nonfree.repo"
}

@test "RPM Fusion repos should be enabled" {
    run grep "enabled=1" "$MOUNT_POINT/etc/yum.repos.d/rpmfusion-free.repo"
    assert_success "RPM Fusion free repo should be enabled"

    run grep "enabled=1" "$MOUNT_POINT/etc/yum.repos.d/rpmfusion-nonfree.repo"
    assert_success "RPM Fusion nonfree repo should be enabled"
}

# --- Virtualization ---

@test "Podman should be installed" {
    run buildah run "$CONTAINER" -- rpm -q podman
    assert_success
}

# --- Container Metadata ---

@test "Container should have proper labels" {
    run buildah inspect --format '{{.Docker.Config.Labels}}' "$CONTAINER"
    assert_success
    assert_output --partial "maintainer"
}

@test "Container ENV should be set" {
    run buildah run "$CONTAINER" -- printenv CONTAINER
    assert_success
    assert_output "docker"
}

# --- Cloud Tools ---

@test "AWS CLI v2 should be installed" {
    run buildah run "$CONTAINER" -- rpm -q awscli2
    assert_success
}

@test "Node.js should be installed" {
    run buildah run "$CONTAINER" -- rpm -q nodejs
    assert_success
}

# --- Final Validation ---

@test "Python3 should be installed" {
    run buildah run "$CONTAINER" -- python3 --version
    assert_success
}

@test "No critical errors in package installation" {
    # Verify no broken dependencies
    run buildah run "$CONTAINER" -- dnf check
    assert_success
}
