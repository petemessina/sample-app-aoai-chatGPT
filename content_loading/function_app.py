import os
from typing import List
import azure.functions as func
import logging
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from azure.cosmos import CosmosClient, ContainerProxy, PartitionKey
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient

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
        blob_name: str = indexBlob.name.split("/")[-1]
        container_name = ''.join(indexBlob.name.rsplit('/', 1)[:-1])
        blob_client = __create_blob_client__(container_name, blob_name)
        document_status_container_client = __create_status_container_proxy()
        document_service: DocumentService = DocumentService(document_status_container_client)
        vector_store = __create_vector_store__()
        llm = __create_llm__()
        llama_compat_llm = __create_llama_compat_llm()
        embed_model = __create_embedding_model__()
        llama_index_service: LlamaIndexService = LlamaIndexService(
            document_service=document_service,
            llm=llm,
            vector_store=vector_store,
            embed_model=embed_model
        )
        
        image_file_types: List[str] = os.environ["SupportedImageFileTypes"].split(",")
        loader = __create_composite_loader__(blob_client, llama_compat_llm, image_file_types)
        
        llama_index_service.index_documents(loader)
        
    except PIIDetectionError as e:
        document_service.update_document_status(e.document, "PII Detected")

        for entity in e.detected_entities:
            logging.error(f"PII Detected in document {blob_name}: {entity.category} with confidence {entity.confidence_score}")
    except Exception as e:
        logging.error(f"Error indexing blob: {e}")
        raise e
    else:
        logging.info(f"Blob {blob_name} indexed successfully.")
    finally:
        logging.info(f"Deleting blob {blob_name}.")
        blob_client.delete_blob()
        blob_client.close()
    
def __create_vector_store__() -> AzureCosmosDBNoSqlVectorSearch:
    endpoint = os.environ["CosmosDBEndpoint"]
    database_name = os.environ["CosmosDBDatabase"]
    container_name = os.environ["CosmosDBContainer"]
    credential = os.getenv("CosmosDBKey")

    # Create the Cosmos client

    if not credential:
        credential = DefaultAzureCredential()

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
def __create_composite_loader__(
    blob_client: BlobClient,
    model: MultiModalLLM,
    img_file_types: List[str]) -> AzStorageBlobReader:

    blob_properties = blob_client.get_blob_properties()
    logging.info(f"Creating Azure Blob Loader for container {blob_properties.container} and blob {blob_properties.name}.")

    image_model_reader = ImageModelReader(model=model)
    readers = dict(map(lambda type: (type, image_model_reader), img_file_types))
    blob_reader = AzStorageBlobReader(blob_client=blob_client)
    blob_reader.file_extractor = blob_reader.file_extractor or {}
    blob_reader.file_extractor.update(readers)
    pii_endpoint = os.environ["PIIEndpoint"]
    
    try:
        pii_categories = os.environ["PIICategories"].split(",")
    except KeyError:
        pii_categories = None

    DEFAULT_MIN_CONFIDENCE = 0.8
    try:
        min_confidence = float(os.environ["PIIMinimumConfidence"])
    except KeyError:
        min_confidence = DEFAULT_MIN_CONFIDENCE

    
    pii_filter = PIIServiceReaderFilter(
        reader=blob_reader, 
        endpoint=pii_endpoint,
        pii_categories=pii_categories, 
        min_confidence=min_confidence)

    return pii_filter

def __create_llm__() -> AzureOpenAI:
    model_name: str = os.environ["OpenAIModelName"]
    deployment_name: str = os.environ["OpenAIDeploymentName"]
    api_key: str = os.environ["OpenAIAPIKey"]
    endpoint: str = os.environ["OpenAIEndpoint"]
    api_version: str = os.environ["OpenAIAPIVersion"]

    return AzureOpenAI(
        model=model_name,
        deployment_name=deployment_name,
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version
    )

def __create_llama_compat_llm() -> MultiModalLLM:
    from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal

    model_name: str = os.environ["OpenAIModelName"]
    deployment_name: str = os.environ["OpenAIDeploymentName"]
    api_key: str = os.environ["OpenAIAPIKey"]
    endpoint: str = os.environ["OpenAIEndpoint"]
    api_version: str = os.environ["OpenAIAPIVersion"]

    return AzureOpenAIMultiModal(
        model=model_name,
        azure_endpoint=endpoint,
        api_key=api_key,
        engine=model_name,
        azure_deployment=deployment_name,
        api_version=api_version,      
    )

# Create the Azure OpenAI Embedding Model
def __create_embedding_model__() -> AzureOpenAIEmbedding:
    aoai_api_key: str = os.environ["OpenAIAPIKey"]
    aoai_endpoint: str = os.environ["OpenAIEndpoint"]
    aoai_api_version: str = os.environ["OpenAIAPIVersion"]
    aoai_embedding_model_name: str = os.environ["OpenAIEmbeddingModelName"]
    aoai_embedding_deployment_name: str = os.environ["OpenAIEmbeddingDeploymentName"]

    logging.info(f"Creating Azure OpenAI Embedding Model: {aoai_embedding_model_name}")

    embed_model = AzureOpenAIEmbedding(
        model=aoai_embedding_model_name,
        deployment_name=aoai_embedding_deployment_name,
        api_key=aoai_api_key,
        azure_endpoint=aoai_endpoint,
        api_version=aoai_api_version,
    )
    
    return embed_model

# Create Blob Client
def __create_blob_client__(container_name: str, blob_name: str) -> BlobClient:
    account_url: str = f"https://{os.environ['StorageAccountName']}.blob.core.windows.net"

    try:
        connection_string: str = os.environ["StorageAccountConnectionString"]
    except KeyError:
        connection_string = None

    logging.info(f"Creating Blob Client for container {container_name} and blob {blob_name}.")

    if (connection_string):
        return BlobClient.from_connection_string(
            conn_str=connection_string,
            container_name=container_name,
            blob_name=blob_name
        )
    else:
        return BlobClient(account_url=account_url, 
                          container_name=container_name, 
                          blob_name=blob_name, 
                          credential=DefaultAzureCredential())
    
def __create_status_container_proxy() -> ContainerProxy:
    endpoint = os.environ["CosmosDBEndpoint"]
    database_name = os.environ["CosmosDBDatabase"]
    container_name = os.environ["CosmosDBDocumentStatusContainer"]
    credential = DefaultAzureCredential()

    # Create the Cosmos client
    client = CosmosClient(endpoint, credential)
    database_proxy = client.get_database_client(database_name)
    container_proxy = database_proxy.get_container_client(container_name)

    return container_proxy
