output "vm_name" {
  description = "Name of the VM"
  value       = azurerm_linux_virtual_machine.main.name
}

output "vm_id" {
  description = "ID of the VM"
  value       = azurerm_linux_virtual_machine.main.id
}

output "public_ip" {
  description = "Public IP address of the VM"
  value       = azurerm_public_ip.main.ip_address
}

output "private_ip" {
  description = "Private IP address of the VM"
  value       = azurerm_network_interface.main.private_ip_address
}

output "fqdn" {
  description = "FQDN of the VM"
  value       = azurerm_public_ip.main.fqdn
}
