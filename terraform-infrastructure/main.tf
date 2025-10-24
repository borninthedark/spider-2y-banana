terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    cloudinit = {
      source  = "hashicorp/cloudinit"
      version = "~> 2.3"
    }
  }

  # Terraform Cloud backend for remote state management
  # Authenticate using: terraform login
  # Or set TF_TOKEN_app_terraform_io environment variable
  cloud {
    organization = "DefiantEmissary"

    workspaces {
      name = "spider-2y-banana"
      # Project must exist in Terraform Cloud
      tags = ["DeepSpaceNine", "azure", "k3s"]
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-spider-2y-banana-${var.environment}"
  location = var.location

  tags = merge(var.tags, {
    Environment = var.environment
    Project     = "spider-2y-banana"
    ManagedBy   = "Terraform"
  })
}

# Network Module
module "network" {
  source = "./modules/network"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  tags                = var.tags
}

# Key Vault Module
module "keyvault" {
  source = "./modules/keyvault"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  tags                = var.tags
}

# Azure Container Registry Module
module "acr" {
  source = "./modules/acr"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  tags                = var.tags
}

# VM Module (supports 1 or 3 nodes)
module "vms" {
  source = "./modules/vm"
  count  = var.node_count

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  admin_username      = var.admin_username
  ssh_public_key      = var.ssh_public_key
  subnet_id           = module.network.subnet_id
  nsg_id              = module.network.nsg_id
  vm_size             = var.vm_size
  disk_size_gb        = var.disk_size_gb
  node_index          = count.index
  node_count          = var.node_count
  tags                = var.tags
}
