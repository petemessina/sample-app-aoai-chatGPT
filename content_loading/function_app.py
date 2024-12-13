from typing import List
import azure.functions as func
import logging

from azure.cosmos import CosmosClient, ContainerProxy, PartitionKey
from azure.storage.blob import BlobClient
from llama_index.llms.azure_openai import AzureOpenAI as LlamaIndexAzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from openai import AzureOpenAI

from typing import List

from Settings import ContentLoadingSettings, CosmosSettings, OpenAISettings, StorageSettings, PIISettings, ImageSettings
from Credentials import ContentLoadingCredentials

from AzStorageBlobReader import AzStorageBlobReader
from AzureCosmosDBNoSqlVectorSearch import AzureCosmosDBNoSqlVectorSearch
from PIIServiceReaderFilter import PIIServiceReaderFilter, PIIDetectionError
from image_model_reader import ImageModelReader
from llama_index_service import LlamaIndexService
from DocumentService import DocumentService

app = func.FunctionApp()

@app.blob_trigger(arg_name="indexBlob", path="documents/{container_name}", connection="DOCUMENT_STORAGE_ACCOUNT")
def blob_trigger(indexBlob: func.InputStream):
    logging.info(f"Indexing blob: {indexBlob.name}")
    
    try:
        config = ContentLoadingSettings()
        auth = ContentLoadingCredentials(config)

        blob_name: str = indexBlob.name.split("/")[-1]
        container_name = ''.join(indexBlob.name.rsplit('/', 1)[:-1])
        blob_client = __create_blob_client__(container_name, blob_name, config.storage, auth)

        document_status_container_client = __create_status_container_proxy(config.cosmos, auth)
        document_service: DocumentService = DocumentService(document_status_container_client)
        vector_store = __create_vector_store__(config.cosmos, auth)

        llm = __create_llm__(config.openai, auth)
        openai_client = __create_openai_client(config.openai, auth)
        embed_model = __create_embedding_model__(config.openai, auth)
        llama_index_service: LlamaIndexService = LlamaIndexService(
            document_service=document_service,
            llm=llm,
            vector_store=vector_store,
            embed_model=embed_model,
            deleteStagedDocuments=config.storage.deleteStagedDocuments,
        )
        
        image_file_types: List[str] = config.image.fileTypes.split(",")
        loader = __create_composite_loader__(blob_client, openai_client, image_file_types, config.pii, auth)
        
        llama_index_service.index_documents(loader)
        
    except PIIDetectionError as e:
        document_service.update_document_status(e.document, "PII Detected")
        user = e.document.metadata.get("author", "Unknown")

        for entity in e.detected_entities:
            logging.error(f"PII Detected in document {blob_name} uploaded by {user}: {entity.category} with confidence {entity.confidence_score}")
    except Exception as e:
        logging.error(f"Error indexing blob: {e}")
        raise e
    else:
        logging.info(f"Blob {blob_name} indexed successfully.")
    finally:
        logging.info(f"Deleting blob {blob_name}.")
        blob_client.delete_blob()
        blob_client.close()
    
def __create_vector_store__(cosmosConfig: CosmosSettings, auth: ContentLoadingCredentials) -> AzureCosmosDBNoSqlVectorSearch:

    # Create the Cosmos client

    client = CosmosClient(cosmosConfig.endpoint, auth.cosmos_credential)
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
        database_name=cosmosConfig.database,
        container_name=cosmosConfig.chunkContainer,
        vector_embedding_policy=vector_embedding_policy,
        indexing_policy=indexing_policy,
        cosmos_container_properties=cosmos_container_properties,
        cosmos_database_properties=cosmos_database_properties,
        create_container=False
    )

# Create the Azure Blob Loader
def __create_composite_loader__(
    blob_client: BlobClient,
    openai_client: LlamaIndexAzureOpenAI,
    img_file_types: List[str],
    piiConfig: PIISettings,
    auth: ContentLoadingCredentials) -> AzStorageBlobReader:

    blob_properties = blob_client.get_blob_properties()
    logging.info(f"Creating Azure Blob Loader for container {blob_properties.container} and blob {blob_properties.name}.")

    image_model_reader = ImageModelReader(openai_client=openai_client)
    readers = dict(map(lambda type: (type, image_model_reader), img_file_types))
    blob_reader = AzStorageBlobReader(blob_client=blob_client)
    blob_reader.file_extractor = blob_reader.file_extractor or {}
    blob_reader.file_extractor.update(readers)
    pii_endpoint = piiConfig.endpoint
    
    try:
        pii_categories = piiConfig.categories.split(",")
    except KeyError:
        pii_categories = None

    DEFAULT_MIN_CONFIDENCE = 0.8
    try:
        min_confidence = float(piiConfig.minimumConfidence)
    except KeyError:
        min_confidence = DEFAULT_MIN_CONFIDENCE

    
    pii_filter = PIIServiceReaderFilter(
        reader=blob_reader, 
        endpoint=pii_endpoint,
        pii_categories=pii_categories, 
        min_confidence=min_confidence,
        credentials=auth)

    return pii_filter

def __create_llm__(openaiConfig: OpenAISettings, auth: ContentLoadingCredentials) -> LlamaIndexAzureOpenAI:
    logging.info(f"Creating Azure OpenAI Model: {openaiConfig.modelName}")

    kwargs = { "model": openaiConfig.modelName,
                "deployment_name": openaiConfig.deploymentName,
                "azure_endpoint": openaiConfig.endpoint,
                "api_version": openaiConfig.apiVersion }

    if (openaiConfig.apiKey):
        kwargs["api_key"] = openaiConfig.apiKey
    else:
        kwargs["azure_ad_token_provider"] = auth.openai_token_provider
        kwargs["use_azure_ad"] = True

    return LlamaIndexAzureOpenAI(**kwargs)

def __create_openai_client(openaiConfig: OpenAISettings, auth: ContentLoadingCredentials) -> AzureOpenAI:

    logging.info(f"Creating Azure OpenAI MultiModal Model: {openaiConfig.modelName}")
    kwargs = { 
            "azure_deployment": openaiConfig.deploymentName,
            "azure_endpoint": openaiConfig.endpoint,
            "api_version": openaiConfig.apiVersion }

    if (openaiConfig.apiKey):
        kwargs["api_key"] = openaiConfig.apiKey
    else:
        kwargs["azure_ad_token_provider"] = auth.openai_token_provider
        kwargs["use_azure_ad"] = True

    return AzureOpenAI(**kwargs)

# Create the Azure OpenAI Embedding Model
def __create_embedding_model__(openaiConfig: OpenAISettings, auth: ContentLoadingCredentials) -> AzureOpenAIEmbedding:
    logging.info(f"Creating Azure OpenAI Embedding Model: {openaiConfig.embeddingModelName}")

    kwargs = { 
        "model": openaiConfig.embeddingModelName,
        "deployment_name": openaiConfig.embeddingDeploymentName,
        "azure_endpoint": openaiConfig.endpoint,
        "api_version": openaiConfig.apiVersion }
    
    if (openaiConfig.apiKey):
        kwargs["api_key"] = openaiConfig.apiKey
    else:
        kwargs["azure_ad_token_provider"] = auth.openai_token_provider
        kwargs["use_azure_ad"] = True
    
    return AzureOpenAIEmbedding(**kwargs)

# Create Blob Client
def __create_blob_client__(container_name: str, blob_name: str, stgConfig: StorageSettings, auth: ContentLoadingCredentials) -> BlobClient:
    account_url: str = f"https://{stgConfig.accountName}.blob.core.windows.net"

    logging.info(f"Creating Blob Client for container {container_name} and blob {blob_name}.")

    return BlobClient(account_url=account_url, 
                        container_name=container_name, 
                        blob_name=blob_name, 
                        credential=auth.storage_credential)
    
def __create_status_container_proxy(cosmosConfig: CosmosSettings, auth: ContentLoadingCredentials) -> ContainerProxy:
    # Create the Cosmos client
    client = CosmosClient(cosmosConfig.endpoint, auth.cosmos_credential)
    database_proxy = client.get_database_client(cosmosConfig.database)
    container_proxy = database_proxy.get_container_client(cosmosConfig.statusContainer)

    return container_proxy
