@description('Custom object type with name and value properties')
type NameValuePair = {
  name: string
  value: string
}

@description('The name of the function app that you wish to create.')
param name string

@description('Location for function.')
param location string = resourceGroup().location

@description('The language worker runtime to load in the function app.')
@allowed([
  'node'
  'dotnet'
  'java'
  'Python'
])
param runtime string = 'node'

@description('The version of the language worker runtime to load in the function app.')
param runtimeVersion string = '14'

@description('The name of the storage account that you want to use for the function app.')
param storageAccountName string

@description('The name of the application insights instance that you want to use for the function app.')
param applicationInsightsName string

@description('Whether to use a managed identity for the storage account.')
param useManagedIdentityForStorage bool = false

@description('The kind of hosting plan to use for the function app.')
@allowed([
  'windows'
  'linux'
])
param hostingPlanKind string = 'linux'

@description('The sku name for the hosting plan.')
@allowed([
  'Y1'
  'EP1'
  'EP2'
  'EP3'
  'P1V2'
  'P2V2'
  'P1V3'
])
param hostingPlanSkuName string = 'Y1'

@description('The sku tier for the hosting plan.')
@allowed([
  'Dynamic'
  'Premium'
  'PremiumV2'
  'PremiumV3'
])
param hostingPlanSkuTier string = 'Dynamic'

@description('Additional app settings to configure for the function app.')
param additionalAppSettings NameValuePair[] = []

var defaultAppSettings = [
  
  {
    name: 'FUNCTIONS_EXTENSION_VERSION'
    value: '~4'
  }
  {
    name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
    value: functionAppInsights.properties.ConnectionString
  }
  {
    name: 'FUNCTIONS_WORKER_RUNTIME'
    value: toLower(runtime)
  }
]

var concatenatedAppSettings = [
  ...defaultAppSettings
  ...additionalAppSettings
]

var appSettings = useManagedIdentityForStorage ? [
  ...concatenatedAppSettings
  {
    name: 'AzureWebJobsStorage__accountName'
    value: storageAccountName
  }
] : [
  ...concatenatedAppSettings
  {
    name: 'AzureWebJobsStorage'
    value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};EndpointSuffix=${environment().suffixes.storage};AccountKey=${functionStorageAccount.listKeys().keys[0].value}'
  }
  {
    name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
    value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};EndpointSuffix=${environment().suffixes.storage};AccountKey=${functionStorageAccount.listKeys().keys[0].value}'
  }
  {
    name: 'WEBSITE_CONTENTSHARE'
    value: toLower(name)
  }
]

resource functionAppInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource functionStorageAccount 'Microsoft.Storage/storageAccounts@2021-02-01' existing = {
  name: storageAccountName
}

resource hostingPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: name
  location: location
  kind: hostingPlanKind
  properties: {
    reserved: true
  }
  sku: {
    tier: hostingPlanSkuTier
    name: hostingPlanSkuName
  }
}

resource functionApp 'Microsoft.Web/sites@2022-03-01' = {
  name: name
  location: location
  kind: 'functionapp,${hostingPlanKind}'
  identity: hostingPlanSkuTier == 'Dynamic' ? null : {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      appSettings: appSettings
      ftpsState: 'FtpsOnly'
      minTlsVersion: '1.2'      
      linuxFxVersion: '${runtime}|${runtimeVersion}'
      alwaysOn: true
    }
    httpsOnly: true
  }
}

resource storageBlobDataContributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

resource storageBlobContributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: '17d1049b-9a84-46fb-8f53-869881c3d3ab'
}

resource storageQueueDataContributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
}

resource blobRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (useManagedIdentityForStorage) {
  name: guid(resourceGroup().id, functionApp.id, storageBlobDataContributorRoleDefinition.id)
  scope: functionStorageAccount
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleDefinition.id
    principalId: functionApp.identity.principalId
  }
}

resource blobContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (useManagedIdentityForStorage) {
  name: guid(resourceGroup().id, functionApp.id, storageBlobContributorRoleDefinition.id)
  scope: functionStorageAccount
  properties: {
    roleDefinitionId: storageBlobContributorRoleDefinition.id
    principalId: functionApp.identity.principalId
  }
}

resource queueDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (useManagedIdentityForStorage) {
  name: guid(resourceGroup().id, functionApp.id, storageQueueDataContributorRoleDefinition.id)
  scope: functionStorageAccount
  properties: {
    roleDefinitionId: storageQueueDataContributorRoleDefinition.id
    principalId: functionApp.identity.principalId
  }
}

output name string = functionApp.name
output principalId string = functionApp.identity.principalId
output id string = functionApp.id
