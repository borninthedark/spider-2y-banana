locals {
  vm_name  = var.node_count == 1 ? "vm-k3s-${var.environment}" : "vm-k3s-${var.environment}-${var.node_index}"
  nic_name = "${local.vm_name}-nic"
  pip_name = "${local.vm_name}-pip"
  disk_name = "${local.vm_name}-osdisk"
}

# Cloud-init configuration
data "cloudinit_config" "main" {
  gzip          = false
  base64_encode = true

  part {
    content_type = "text/cloud-config"
    content = yamlencode({
      package_update  = true
      package_upgrade = true
      packages = [
        "apt-transport-https",
        "ca-certificates",
        "curl",
        "gnupg",
        "lsb-release",
        "python3",
        "python3-pip"
      ]
      write_files = [{
        path    = "/etc/sysctl.d/k3s.conf"
        content = <<-EOT
          net.ipv4.ip_forward = 1
          net.bridge.bridge-nf-call-iptables = 1
          net.bridge.bridge-nf-call-ip6tables = 1
        EOT
      }]
      runcmd = [
        "sysctl -p /etc/sysctl.d/k3s.conf",
        "systemctl disable --now ufw",
        "echo 'VM prepared for k3s installation via Ansible'"
      ]
    })
  }
}

# Public IP
resource "azurerm_public_ip" "main" {
  name                = local.pip_name
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  domain_name_label   = lower("${local.vm_name}-${substr(md5(var.resource_group_name), 0, 8)}")
  tags                = var.tags
}

# Network Interface
resource "azurerm_network_interface" "main" {
  name                = local.nic_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  ip_configuration {
    name                          = "ipconfig1"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }
}

# Virtual Machine
resource "azurerm_linux_virtual_machine" "main" {
  name                = local.vm_name
  location            = var.location
  resource_group_name = var.resource_group_name
  size                = var.vm_size
  admin_username      = var.admin_username
  network_interface_ids = [
    azurerm_network_interface.main.id
  ]
  custom_data = data.cloudinit_config.main.rendered

  tags = merge(var.tags, {
    Role      = var.node_index == 0 ? "k3s-server" : "k3s-agent"
    NodeIndex = tostring(var.node_index)
  })

  admin_ssh_key {
    username   = var.admin_username
    public_key = var.ssh_public_key
  }

  os_disk {
    name                 = local.disk_name
    caching              = "ReadWrite"
    storage_account_type = "StandardSSD_LRS"
    disk_size_gb         = var.disk_size_gb
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  disable_password_authentication = true
}
