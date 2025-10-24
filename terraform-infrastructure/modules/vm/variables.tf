variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "admin_username" {
  description = "Admin username for the VM"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
  sensitive   = true
}

variable "subnet_id" {
  description = "ID of the subnet"
  type        = string
}

variable "nsg_id" {
  description = "ID of the network security group"
  type        = string
}

variable "vm_size" {
  description = "Azure VM size"
  type        = string
}

variable "disk_size_gb" {
  description = "OS disk size in GB"
  type        = number
}

variable "node_index" {
  description = "Index of this node (0-based)"
  type        = number
}

variable "node_count" {
  description = "Total number of nodes"
  type        = number
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
