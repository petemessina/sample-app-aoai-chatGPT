from typing import Dict
from azure.core.credentials_async import AsyncTokenCredential
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions

class CosmosDBContext():
    def __init__(self, cosmosdb_endpoint: str, credential: str | Dict[str, str] | AsyncTokenCredential, database_name: str, container_name: str): 
        try:
            self.cosmosdb_client = CosmosClient(cosmosdb_endpoint, credential=credential)
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 401:
                raise ValueError("Invalid credentials") from e
            else:
                raise ValueError("Invalid CosmosDB endpoint") from e

        try:
            self.database_client = self.cosmosdb_client.get_database_client(database_name)
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError("Invalid CosmosDB database name")

        try:
            self.client_container = self.database_client.get_container_client(container_name)
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError("Invalid CosmosDB container name")