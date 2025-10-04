// Fedora Base Container Image with core packages
// Uses spider-2y-banana Ansible playbooks for provisioning

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
  default = "43"
}

variable "image_name" {
  type    = string
  default = "fedora-base"
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
  default = env("REGISTRY_USERNAME")
}

source "docker" "fedora_base" {
  image  = "quay.io/fedora/fedora:${var.fedora_version}"
  commit = true
  changes = [
    "ENV CONTAINER=docker",
    "LABEL maintainer='spider-2y-banana'",
    "LABEL version='${var.fedora_version}'",
    "LABEL description='Fedora base image with core packages'"
  ]
}

build {
  name = "fedora-base"
  sources = [
    "source.docker.fedora_base"
  ]

  // Install Python and Ansible requirements
  provisioner "shell" {
    inline = [
      "dnf install -y python3 python3-pip sudo",
      "dnf clean all"
    ]
  }

  // Run Ansible provisioning
  provisioner "ansible" {
    playbook_file = "../../ansible/playbooks/provision.yml"
    user          = "root"

    extra_arguments = [
      "--extra-vars",
      "ansible_connection=docker enable_k8s_tools=false enable_sway_desktop=false enable_virtualization=false enable_plymouth=false",
      "--tags",
      "base,security"
    ]

    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False"
    ]
  }

  // Clean up
  provisioner "shell" {
    inline = [
      "dnf clean all",
      "rm -rf /tmp/*",
      "rm -rf /var/tmp/*",
      "rm -rf /var/cache/dnf"
    ]
  }

  // Tag and push to registry
  post-processors {
    post-processor "docker-tag" {
      repository = "${var.registry}/${var.registry_username}/${var.image_name}"
      tags       = ["${var.image_tag}", "${var.fedora_version}", "${var.fedora_version}-{{timestamp}}"]
    }

    post-processor "docker-push" {
      login          = true
      login_username = var.registry_username
      login_password = env("REGISTRY_PASSWORD")
    }
  }

  post-processor "manifest" {
    output     = "manifest.json"
    strip_path = true
  }
}
