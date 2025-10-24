output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = azurerm_container_registry.main.name
}

output "acr_id" {
  description = "ID of the Azure Container Registry"
  value       = azurerm_container_registry.main.id
}

output "login_server" {
  description = "Login server URL for the ACR"
  value       = azurerm_container_registry.main.login_server
}
