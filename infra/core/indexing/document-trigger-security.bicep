@description('The id of the function app.')
param functionAppId string

@description('The name of the function app.')
param functionAppName string

@description('The prinicpal id of the function app.')
param functionAppPricipalId string

resource documentStorageAccount 'Microsoft.Web/sites@2022-03-01' existing = {
  name: functionAppName
}

resource storageBlobDataContributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

resource storageQueueDataContributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
}

resource blobRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, functionAppId, documentStorageAccount.id, storageBlobDataContributorRoleDefinition.id)
  scope: documentStorageAccount
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleDefinition.id
    principalId: functionAppPricipalId
  }
}

resource queueDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, functionAppId, documentStorageAccount.id, storageQueueDataContributorRoleDefinition.id)
  scope: documentStorageAccount
  properties: {
    roleDefinitionId: storageQueueDataContributorRoleDefinition.id
    principalId: functionAppPricipalId
  }
}
