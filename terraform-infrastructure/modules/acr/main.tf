resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

locals {
  acr_name = "acrk3s${var.environment}${random_string.suffix.result}"
}

resource "azurerm_container_registry" "main" {
  name                = local.acr_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Basic"
  admin_enabled       = true

  public_network_access_enabled = true
  network_rule_bypass_option    = "AzureServices"

  tags = var.tags
}
