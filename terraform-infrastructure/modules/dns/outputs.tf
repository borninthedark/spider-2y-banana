output "dns_zone_id" {
  description = "ID of the DNS zone"
  value       = azurerm_dns_zone.main.id
}

output "dns_zone_name" {
  description = "Name of the DNS zone"
  value       = azurerm_dns_zone.main.name
}

output "name_servers" {
  description = "Azure DNS nameservers for this zone (configure these in Namecheap)"
  value       = azurerm_dns_zone.main.name_servers
}

output "resume_fqdn" {
  description = "Fully qualified domain name for resume"
  value       = "${azurerm_dns_a_record.resume.name}.${azurerm_dns_zone.main.name}"
}

output "grafana_fqdn" {
  description = "Fully qualified domain name for grafana"
  value       = "${azurerm_dns_a_record.grafana.name}.${azurerm_dns_zone.main.name}"
}

output "dns_records" {
  description = "Summary of DNS records created"
  value = {
    resume  = "${azurerm_dns_a_record.resume.name}.${azurerm_dns_zone.main.name} -> ${var.ingress_ip}"
    grafana = "${azurerm_dns_a_record.grafana.name}.${azurerm_dns_zone.main.name} -> ${var.ingress_ip}"
  }
}
