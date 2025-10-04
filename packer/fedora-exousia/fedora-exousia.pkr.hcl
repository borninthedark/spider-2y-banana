// Fedora Exousia - Complete development environment
// Combines fedora-base, fedora-k8s, and fedora-sway into one comprehensive image
// Includes: base packages, Kubernetes tools, Sway desktop, and virtualization support

packer {
  required_plugins {
    docker = {
      version = ">= 1.0.8"
      source  = "github.com/hashicorp/docker"
    }
    ansible = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/ansible"
    }
  }
}

variable "fedora_version" {
  type    = string
  default = "42"
  validation {
    condition     = contains(["41", "42", "43", "rawhide"], var.fedora_version)
    error_message = "Fedora version must be one of: 41, 42, 43, rawhide."
  }
}

variable "image_name" {
  type    = string
  default = "fedora-exousia"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "registry" {
  type    = string
  default = "docker.io"
}

variable "registry_username" {
  type    = string
  default = ""
}

variable "registry_password" {
  type      = string
  default   = ""
  sensitive = true
}

source "docker" "fedora_exousia" {
  image  = "quay.io/fedora/fedora-bootc:${var.fedora_version}"
  commit = true

  // Run as root to avoid tmpdir permission errors
  run_command = ["-d", "-i", "-t", "--user", "root", "--entrypoint=/bin/sh", "--", "{{.Image}}"]

  changes = [
    "ENV CONTAINER=docker",
    "ENV K3S_VERSION=v1.30.5+k3s1",
    "ENV KUBECTL_VERSION=v1.30.0",
    "LABEL maintainer='spider-2y-banana'",
    "LABEL version='${var.fedora_version}'",
    "LABEL description='Fedora Exousia - Complete development environment with base packages, K8s tools, Sway desktop, and virtualization'"
  ]
}

build {
  name = "fedora-exousia-${var.fedora_version}"
  sources = ["source.docker.fedora_exousia"]

  provisioner "shell" {
    inline = [
    "microdnf install -y python3 python3-pip dnf5 sudo curl",
    "ln -sf /usr/bin/dnf /usr/bin/dnf5"
  ]
}

  // --- Ensure Python + dnf base tools installed
  provisioner "shell" {
    inline = [
      "dnf install -y python3 python3-pip sudo curl",
      "dnf clean all"
    ]
  }

  // --- FIX: precreate writable tmpdirs for Ansible (root user)
  provisioner "shell" {
    inline = [
      "mkdir -p /tmp/.ansible/tmp",
      "chmod -R 1777 /tmp"
    ]
  }

  // --- Run Ansible provisioning
  provisioner "ansible" {
    playbook_file = "../../ansible/playbooks/provision.yml"
    user          = "root"

    extra_arguments = [
      "--extra-vars",
      "ansible_connection=local enable_k8s_tools=true enable_sway_desktop=true enable_virtualization=true enable_plymouth=true",
      "--tags",
      "base,security,k8s,sway,services,virtualization"
    ]

    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_CONFIG=../../ansible/ansible.cfg"
    ]
  }

  // --- Cleanup to minimize image size
  provisioner "shell" {
    inline = [
      "dnf clean all",
      "rm -rf /tmp/* /var/tmp/* /var/cache/dnf"
    ]
  }

  // --- Tag and push image
  post-processor "docker-tag" {
    repository = "${var.registry}/${var.registry_username}/${var.image_name}"
    tags       = ["${var.image_tag}", "${var.fedora_version}", "${var.fedora_version}-{{timestamp}}"]
  }

  post-processor "docker-push" {
    login          = true
    login_username = var.registry_username
    login_password = var.registry_password
  }

  post-processor "manifest" {
    output     = "manifest-${var.fedora_version}.json"
    strip_path = true
  }
}
