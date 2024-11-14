import os
import azure.functions as func
import logging
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.vector_stores.azurecosmosnosql import AzureCosmosDBNoSqlVectorSearch
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient

from AzStorageBlobReader import AzStorageBlobReader
from llama_index_service import LlamaIndexService

app = func.FunctionApp()

@app.blob_trigger(arg_name="indexBlob", path="documents/{container_name}", connection="stdocumentupload001_STORAGE")
def blob_trigger(indexBlob: func.InputStream):
    logging.info(f"Indexing blob: {indexBlob.name}")
    
    llama_index_service: LlamaIndexService = LlamaIndexService()
    blob_name: str = indexBlob.name.split("/")[-1]
    container_name = ''.join(indexBlob.name.rsplit('/', 1)[:-1])
    aoai_model_name: str = os.environ["OpenAIModelName"]
    aoai_api_key: str = os.environ["OpenAIAPIKey"]
    aoai_endpoint: str = os.environ["OpenAIEndpoint"]
    aoai_api_version: str = os.environ["OpenAIAPIVersion"]
    vector_store = __create_vector_store__()
    embed_model = __create_embedding_model__()
    blob_loader = __create_blob_loader__(container_name, blob_name)
    blob_client = __create_blob_client__(container_name, blob_name)

    llama_index_service.index_documents(
        aoai_model_name,
        aoai_api_key,
        aoai_endpoint,
        aoai_api_version,
        vector_store,
        embed_model,
        blob_loader,
        blob_client
    )

def __create_vector_store__() -> AzureCosmosDBNoSqlVectorSearch:
    endpoint = os.environ["CosmosDBEndpoint"]
    database_name = os.environ["CosmosDBDatabase"]
    container_name = os.environ["CosmosDBContainer"]
    credential = DefaultAzureCredential()

    # Create the Cosmos client
    client = CosmosClient(endpoint, credential)
    partition_key = PartitionKey(path="/userId")
    cosmos_database_properties = {}
    cosmos_container_properties = {"partition_key": partition_key}
    indexing_policy = {
        "indexingMode": "consistent",
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": '/"_etag"/?'}],
        "vectorIndexes": [{"path": "/embedding", "type": "quantizedFlat"}],
    }

    vector_embedding_policy = {
        "vectorEmbeddings": [
            {
                "path": "/contentVector",
                "dataType": "float32",
                "distanceFunction": "euclidean",
                "dimensions": 1531,
            }
        ]
    }

    return AzureCosmosDBNoSqlVectorSearch(
        cosmos_client=client,
        database_name=database_name,
        container_name=container_name,
        vector_embedding_policy=vector_embedding_policy,
        indexing_policy=indexing_policy,
        cosmos_container_properties=cosmos_container_properties,
        cosmos_database_properties=cosmos_database_properties,
        create_container=False
    )


# Create the Azure Blob Loader
def __create_blob_loader__(container_name: str, blob_name: str) -> AzStorageBlobReader:
    account_url: str = os.environ["StorageAccountUrl"]
    connection_string: str = os.environ["StorageAccountConnectionString"]
    
    logging.info(f"Creating Azure Blob Loader for container {container_name} and blob {blob_name}.")

    return AzStorageBlobReader(
        container_name=container_name,
        blob=blob_name,
        account_url=account_url,
        connection_string=connection_string
    )

# Create the Azure OpenAI Embedding Model
def __create_embedding_model__() -> AzureOpenAIEmbedding:
    aoai_api_key: str = os.environ["OpenAIAPIKey"]
    aoai_endpoint: str = os.environ["OpenAIEndpoint"]
    aoai_api_version: str = os.environ["OpenAIAPIVersion"]
    aoai_embedding_model_name: str = os.environ["OpenAIEmbeddingModelName"]

    logging.info(f"Creating Azure OpenAI Embedding Model: {aoai_embedding_model_name}")

    embed_model = AzureOpenAIEmbedding(
        model=aoai_embedding_model_name,
        deployment_name=aoai_embedding_model_name,
        api_key=aoai_api_key,
        azure_endpoint=aoai_endpoint,
        api_version=aoai_api_version,
    )
    
    return embed_model

# Create Blob Client
def __create_blob_client__(container_name: str, blob_name: str) -> BlobClient:
    connection_string: str = os.environ["StorageAccountConnectionString"]

    logging.info(f"Creating Blob Client for container {container_name} and blob {blob_name}.")

    return BlobClient.from_connection_string(
        conn_str=connection_string,
        container_name=container_name,
        blob_name=blob_name
    )