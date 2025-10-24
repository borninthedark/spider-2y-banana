# Azure DNS Zone
resource "azurerm_dns_zone" "main" {
  name                = var.domain_name
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# A Record for resume subdomain
resource "azurerm_dns_a_record" "resume" {
  name                = "resume"
  zone_name           = azurerm_dns_zone.main.name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  records             = [var.ingress_ip]
  tags                = var.tags
}

# A Record for grafana subdomain
resource "azurerm_dns_a_record" "grafana" {
  name                = "grafana"
  zone_name           = azurerm_dns_zone.main.name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  records             = [var.ingress_ip]
  tags                = var.tags
}

# Optional: Wildcard A Record for any subdomain
resource "azurerm_dns_a_record" "wildcard" {
  name                = "*"
  zone_name           = azurerm_dns_zone.main.name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  records             = [var.ingress_ip]
  tags                = var.tags
}

# TXT Record for domain verification (useful for Let's Encrypt, etc.)
resource "azurerm_dns_txt_record" "verification" {
  name                = "@"
  zone_name           = azurerm_dns_zone.main.name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  tags                = var.tags

  record {
    value = "v=spf1 -all"  # SPF record to prevent email spoofing
  }
}

# CAA Record for certificate authority authorization
resource "azurerm_dns_caa_record" "letsencrypt" {
  name                = "@"
  zone_name           = azurerm_dns_zone.main.name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  tags                = var.tags

  record {
    flags = 0
    tag   = "issue"
    value = "letsencrypt.org"
  }

  record {
    flags = 0
    tag   = "issuewild"
    value = "letsencrypt.org"
  }
}
