targetScope = 'resourceGroup'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('VM admin username')
param adminUsername string = 'azureuser'

@description('VM admin SSH public key')
@secure()
param sshPublicKey string

@description('Number of k3s nodes (1 for single node, 3 for HA)')
@allowed([
  1
  3
])
param nodeCount int = 1

@description('VM size for k3s nodes')
param vmSize string = 'Standard_B2ms'

@description('Disk size in GB')
param diskSizeGB int = 128

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'lavish-k3s'
  ManagedBy: 'Bicep'
  Purpose: 'GitOps-Demo'
}

// Network module
module network 'modules/network.bicep' = {
  name: 'networkDeployment'
  params: {
    location: location
    environment: environment
    tags: tags
  }
}

// Key Vault module
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyVaultDeployment'
  params: {
    location: location
    environment: environment
    tags: tags
  }
}

// Container Registry module
module acr 'modules/acr.bicep' = {
  name: 'acrDeployment'
  params: {
    location: location
    environment: environment
    tags: tags
  }
}

// VM module (supports 1 or 3 nodes)
module vms 'modules/vm.bicep' = [for i in range(0, nodeCount): {
  name: 'vmDeployment-${i}'
  params: {
    location: location
    environment: environment
    adminUsername: adminUsername
    sshPublicKey: sshPublicKey
    subnetId: network.outputs.subnetId
    nsgId: network.outputs.nsgId
    vmSize: vmSize
    diskSizeGB: diskSizeGB
    nodeIndex: i
    nodeCount: nodeCount
    tags: tags
  }
}]

// Service Principal for Crossplane (created separately via Azure CLI)
// See scripts/create-service-principal.sh

// Outputs
output resourceGroupName string = resourceGroup().name
output vnetName string = network.outputs.vnetName
output subnetName string = network.outputs.subnetName
output keyVaultName string = keyVault.outputs.keyVaultName
output keyVaultUri string = keyVault.outputs.keyVaultUri
output acrLoginServer string = acr.outputs.loginServer
output acrName string = acr.outputs.acrName
output vmPublicIps array = [for i in range(0, nodeCount): vms[i].outputs.publicIp]
output vmPrivateIps array = [for i in range(0, nodeCount): vms[i].outputs.privateIp]
output vmNames array = [for i in range(0, nodeCount): vms[i].outputs.vmName]
