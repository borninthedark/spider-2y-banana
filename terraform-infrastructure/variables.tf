variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus"
}

variable "admin_username" {
  description = "Admin username for VMs"
  type        = string
  default     = "azureuser"
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
  sensitive   = true
}

variable "node_count" {
  description = "Number of k3s nodes (1 for single node, 3 for HA)"
  type        = number
  default     = 1

  validation {
    condition     = contains([1, 3], var.node_count)
    error_message = "Node count must be 1 or 3."
  }
}

variable "vm_size" {
  description = "Azure VM size"
  type        = string
  default     = "Standard_B2ms"
}

variable "disk_size_gb" {
  description = "OS disk size in GB"
  type        = number
  default     = 128

  validation {
    condition     = var.disk_size_gb >= 30 && var.disk_size_gb <= 1024
    error_message = "Disk size must be between 30 and 1024 GB."
  }
}

variable "domain_name" {
  description = "Base domain name for all services (e.g., princetonstrong.online)"
  type        = string
  default     = "princetonstrong.online"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "spider-2y-banana"
    ManagedBy = "Terraform"
  }
}
