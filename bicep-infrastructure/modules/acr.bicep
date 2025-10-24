param location string
param environment string
param tags object

var acrName = 'acrk3s${environment}${uniqueString(resourceGroup().id)}'

// Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}

output acrName string = acr.name
output acrId string = acr.id
output loginServer string = acr.properties.loginServer
