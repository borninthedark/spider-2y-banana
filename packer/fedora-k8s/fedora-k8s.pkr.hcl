// Fedora Container Image with Kubernetes tools
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
  default = "fedora-k8s"
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

source "docker" "fedora_k8s" {
  image  = "quay.io/fedora/fedora:${var.fedora_version}"
  commit = true
  changes = [
    "ENV CONTAINER=docker",
    "ENV K3S_VERSION=v1.30.5+k3s1",
    "ENV KUBECTL_VERSION=v1.30.0",
    "LABEL maintainer='spider-2y-banana'",
    "LABEL version='${var.fedora_version}'",
    "LABEL description='Fedora image with Kubernetes tools'"
  ]
}

build {
  name = "fedora-k8s"
  sources = [
    "source.docker.fedora_k8s"
  ]

  // Install Python and Ansible requirements
  provisioner "shell" {
    inline = [
      "dnf install -y python3 python3-pip sudo curl",
      "dnf clean all"
    ]
  }

  // Run Ansible provisioning with Kubernetes
  provisioner "ansible" {
    playbook_file = "../../ansible/playbooks/provision.yml"
    user          = "root"

    extra_arguments = [
      "--extra-vars",
      "ansible_connection=docker enable_k8s_tools=true enable_sway_desktop=false enable_virtualization=false enable_plymouth=false",
      "--tags",
      "base,security,k8s"
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
      tags       = ["${var.image_tag}", "${var.fedora_version}", "${var.fedora_version}-{{timestamp}}", "k3s-v1.30.5"]
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
