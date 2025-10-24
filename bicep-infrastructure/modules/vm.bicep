param location string
param environment string
param adminUsername string
param sshPublicKey string
param subnetId string
param nsgId string
param vmSize string
param diskSizeGB int
param nodeIndex int
param nodeCount int
param tags object

var vmName = nodeCount == 1 ? 'vm-k3s-${environment}' : 'vm-k3s-${environment}-${nodeIndex}'
var nicName = '${vmName}-nic'
var pipName = '${vmName}-pip'
var osDiskName = '${vmName}-osdisk'

// Cloud-init configuration for k3s preparation
var cloudInitContent = base64('''
#cloud-config
package_update: true
package_upgrade: true
packages:
  - apt-transport-https
  - ca-certificates
  - curl
  - gnupg
  - lsb-release
  - python3
  - python3-pip

write_files:
  - path: /etc/sysctl.d/k3s.conf
    content: |
      net.ipv4.ip_forward = 1
      net.bridge.bridge-nf-call-iptables = 1
      net.bridge.bridge-nf-call-ip6tables = 1

runcmd:
  - sysctl -p /etc/sysctl.d/k3s.conf
  - systemctl disable --now ufw
  - echo "VM prepared for k3s installation via Ansible"
''')

// Public IP
resource publicIp 'Microsoft.Network/publicIPAddresses@2023-04-01' = {
  name: pipName
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
    dnsSettings: {
      domainNameLabel: toLower('${vmName}-${uniqueString(resourceGroup().id)}')
    }
  }
}

// Network Interface
resource nic 'Microsoft.Network/networkInterfaces@2023-04-01' = {
  name: nicName
  location: location
  tags: tags
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: {
            id: subnetId
          }
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: publicIp.id
          }
        }
      }
    ]
  }
}

// Virtual Machine
resource vm 'Microsoft.Compute/virtualMachines@2023-03-01' = {
  name: vmName
  location: location
  tags: union(tags, {
    Role: nodeIndex == 0 ? 'k3s-server' : 'k3s-agent'
    NodeIndex: string(nodeIndex)
  })
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: sshPublicKey
            }
          ]
        }
      }
      customData: cloudInitContent
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: '0001-com-ubuntu-server-jammy'
        sku: '22_04-lts-gen2'
        version: 'latest'
      }
      osDisk: {
        name: osDiskName
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'StandardSSD_LRS'
        }
        diskSizeGB: diskSizeGB
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
  }
}

output vmName string = vm.name
output vmId string = vm.id
output publicIp string = publicIp.properties.ipAddress
output privateIp string = nic.properties.ipConfigurations[0].properties.privateIPAddress
output fqdn string = publicIp.properties.dnsSettings.fqdn
