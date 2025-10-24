# Namecheap DNS Setup with Azure DNS

This guide walks you through setting up your Namecheap domain to work with Azure DNS, allowing Terraform to automatically manage all your DNS records.

## Overview

**Architecture:**
- **Domain Registration**: Namecheap (where you purchased the domain)
- **DNS Management**: Azure DNS (managed by Terraform)
- **One-time Setup**: Update nameservers in Namecheap to point to Azure

**Benefits:**
- ✅ All DNS records managed via Terraform (infrastructure-as-code)
- ✅ Automatic DNS updates when infrastructure changes
- ✅ No manual DNS record management
- ✅ Free Azure DNS for first 25 zones
- ✅ Keep domain registration at Namecheap

## Prerequisites

- Domain registered at Namecheap
- Terraform infrastructure deployed (creates Azure DNS zone)
- Access to Namecheap account dashboard

## Step-by-Step Setup

### Step 1: Deploy Terraform Infrastructure

First, deploy your infrastructure which creates the Azure DNS zone:

```bash
cd terraform-infrastructure

# Initialize Terraform
terraform init

# Review the plan (check DNS module is included)
terraform plan

# Apply the configuration
terraform apply
```

### Step 2: Get Azure DNS Nameservers

After Terraform completes, it will output the Azure DNS nameservers:

```bash
# View all outputs
terraform output

# Or specifically get nameservers
terraform output dns_nameservers
```

You'll see output like:
```
dns_nameservers = [
  "ns1-01.azure-dns.com",
  "ns2-01.azure-dns.net",
  "ns3-01.azure-dns.org",
  "ns4-01.azure-dns.info",
]
```

**📋 Copy these four nameservers - you'll need them for Namecheap.**

### Step 3: Update Nameservers in Namecheap

1. **Log in to Namecheap**
   - Go to https://www.namecheap.com
   - Sign in to your account

2. **Navigate to Domain List**
   - Click on "Domain List" in the left sidebar
   - Find your domain (e.g., `princetonstrong.online`)
   - Click "Manage" button

3. **Change Nameservers**
   - Scroll down to the "NAMESERVERS" section
   - Change dropdown from "Namecheap BasicDNS" to "Custom DNS"

4. **Enter Azure Nameservers**
   - You'll see fields for nameservers
   - Enter the four Azure nameservers from Step 2:
     ```
     Nameserver 1: ns1-01.azure-dns.com
     Nameserver 2: ns2-01.azure-dns.net
     Nameserver 3: ns3-01.azure-dns.org
     Nameserver 4: ns4-01.azure-dns.info
     ```
   - Replace the example values with your actual Azure nameservers

5. **Save Changes**
   - Click the green checkmark (✓) to save
   - Namecheap will show a confirmation message

### Step 4: Wait for DNS Propagation

DNS changes take time to propagate globally:

- **Namecheap propagation**: 0-30 minutes (usually 5-10 minutes)
- **Global DNS propagation**: Up to 48 hours (usually 2-4 hours)

**Check propagation status:**

```bash
# Check if nameservers have updated
dig NS yourdomain.com +short

# Expected output (your Azure nameservers):
# ns1-01.azure-dns.com
# ns2-01.azure-dns.net
# ns3-01.azure-dns.org
# ns4-01.azure-dns.info
```

Or use online tools:
- https://www.whatsmydns.net/
- https://dnschecker.org/

### Step 5: Verify DNS Records

Once nameservers have propagated, verify your DNS records are working:

```bash
# Check resume subdomain
dig resume.yourdomain.com +short
# Should return your VM's public IP

# Check grafana subdomain
dig grafana.yourdomain.com +short
# Should return your VM's public IP

# Check with curl (after cert-manager issues certificates)
curl -I https://resume.yourdomain.com
curl -I https://grafana.yourdomain.com
```

## What Terraform Manages

Once nameservers are updated, Terraform automatically manages:

### DNS Records Created:
1. **resume.yourdomain.com** → VM Public IP (A Record)
2. **grafana.yourdomain.com** → VM Public IP (A Record)
3. **\*.yourdomain.com** → VM Public IP (Wildcard A Record)

### Additional Records:
4. **SPF Record** (TXT) - Prevents email spoofing
5. **CAA Record** - Authorizes Let's Encrypt for SSL certificates

### Future Updates:

When you need to change DNS records:

```bash
# Edit terraform-infrastructure/modules/dns/main.tf
# Add new DNS records as needed

# Apply changes
terraform apply

# DNS updates automatically in Azure (no Namecheap changes needed!)
```

## Troubleshooting

### Issue: Nameservers not updating

**Check:**
```bash
dig NS yourdomain.com +short
```

**Solutions:**
- Wait longer (can take up to 48 hours)
- Clear DNS cache: `sudo dnsmasq -k` or flush browser DNS
- Verify you entered nameservers correctly in Namecheap
- Check you saved the changes in Namecheap

### Issue: DNS records not resolving

**Check:**
```bash
# Check if Azure has the records
terraform output dns_records_summary

# Check DNS resolution
dig resume.yourdomain.com +short
```

**Solutions:**
- Verify nameservers have fully propagated first
- Check Terraform applied successfully: `terraform apply`
- Verify VM has a public IP: `terraform output vm_public_ips`

### Issue: HTTPS not working

**Note:** HTTPS certificates are issued by cert-manager after DNS is working.

**Steps:**
1. First, ensure DNS resolves correctly (HTTP works)
2. cert-manager will automatically request Let's Encrypt certificates
3. This can take 5-10 minutes after DNS propagation
4. Check cert-manager logs: `kubectl logs -n cert-manager -l app=cert-manager`

### Issue: Want to add more subdomains

**Add to Terraform:**

Edit `terraform-infrastructure/modules/dns/main.tf`:

```hcl
# Add new subdomain
resource "azurerm_dns_a_record" "newsubdomain" {
  name                = "newsubdomain"
  zone_name           = azurerm_dns_zone.main.name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  records             = [var.ingress_ip]
  tags                = var.tags
}
```

Then apply:
```bash
terraform apply
```

## Cost Information

**Azure DNS Pricing (as of 2024):**
- First 25 hosted zones: **FREE**
- First 1 billion DNS queries/month: **FREE**
- Beyond that: ~$0.50/zone/month, $0.40/million queries

**For this project:** Effectively **FREE** unless you have massive traffic.

**Namecheap:** Continue paying annual domain registration fee (no extra costs).

## Reverting to Namecheap DNS

If you want to go back to Namecheap DNS:

1. In Namecheap, change nameservers back to "Namecheap BasicDNS"
2. Manually add DNS records in Namecheap dashboard
3. Optionally remove DNS module from Terraform

## Summary

✅ **One-time setup** (15 minutes):
   - Run `terraform apply`
   - Update nameservers in Namecheap
   - Wait for propagation

✅ **Future changes** (automatic):
   - Edit Terraform
   - Run `terraform apply`
   - DNS updates automatically

✅ **No ongoing maintenance** in Namecheap DNS dashboard

## Next Steps

After DNS is configured:

1. **SSL Certificates**: cert-manager will automatically issue Let's Encrypt certificates
2. **Test Services**:
   - Visit https://resume.yourdomain.com
   - Visit https://grafana.yourdomain.com
3. **Monitor**: Check Grafana dashboards for application health

## Support

- **Namecheap Support**: https://www.namecheap.com/support/
- **Azure DNS Docs**: https://learn.microsoft.com/en-us/azure/dns/
- **Project Issues**: Check the main README.md

---

**Last Updated**: 2025-10-23
