variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the DNS zone"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "ingress_ip" {
  description = "IP address for ingress (for A records)"
  type        = string
}

variable "tags" {
  description = "Tags to apply to DNS resources"
  type        = map(string)
  default     = {}
}
