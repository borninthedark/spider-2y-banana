output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "vnet_name" {
  description = "Name of the virtual network"
  value       = module.network.vnet_name
}

output "subnet_name" {
  description = "Name of the subnet"
  value       = module.network.subnet_name
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = module.keyvault.key_vault_name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = module.keyvault.key_vault_uri
}

output "acr_login_server" {
  description = "ACR login server URL"
  value       = module.acr.login_server
}

output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = module.acr.acr_name
}

output "vm_public_ips" {
  description = "Public IP addresses of VMs"
  value       = [for vm in module.vms : vm.public_ip]
}

output "vm_private_ips" {
  description = "Private IP addresses of VMs"
  value       = [for vm in module.vms : vm.private_ip]
}

output "vm_names" {
  description = "Names of VMs"
  value       = [for vm in module.vms : vm.vm_name]
}

output "vm_fqdns" {
  description = "FQDNs of VMs"
  value       = [for vm in module.vms : vm.fqdn]
}
