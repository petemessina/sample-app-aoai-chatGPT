@description('Location for application insights.')
param location string = resourceGroup().location

@description('The name of the application insights instance that you want to create.')
param applicationInsightsName string

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
  }
}

output name string = applicationInsights.name
