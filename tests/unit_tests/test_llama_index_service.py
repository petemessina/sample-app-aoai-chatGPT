import pytest
from pydantic import Field
from content_loading import DocumentService
from content_loading.image_model_reader import ImageModelReader
from content_loading.Settings import AzureMultiModalModelSettings, StorageSettings
from content_loading.llama_index_service import LlamaIndexService
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.vector_stores.types import VectorStore
from llama_index.core.vector_stores.simple import SimpleVectorStore, SimpleVectorStoreData
from llama_index.readers.azstorage_blob import AzStorageBlobReader

@pytest.fixture
def settings():
    return AzureMultiModalModelSettings()

@pytest.fixture
def llm(settings):
    return AzureOpenAI(
        model=settings.modelName,
        deployment=settings.deploymentName,
        engine=settings.deploymentName,
        api_version=settings.apiVersion,
        api_key=settings.apiKey)

@pytest.fixture
def vector_store():
    data = SimpleVectorStoreData()
    return SimpleVectorStore(
        data=data,
    )

@pytest.fixture
def doc_service():
    return DocumentService(
        endpoint="https://test.documents.azure.com",
        key="test-key",
        database="test-db",
        chunkContainer="test-chunk-container",
        statusContainer="test-status-container"
    )
@pytest.fixture
def test_concern(doc_service, llm):
    return LlamaIndexService(
        document_service=doc_service,
        llm=llm,
        vector_store=VectorStore(),
        embed_model=None,
        deleteStagedDocuments=True
    )

@pytest.fixture
def az_storage_blob_reader():
    settings = StorageSettings()
    # todo: configure azurite connection.
    return AzStorageBlobReader(
        container_name=settings.key,

    )

def test_index_documents(test_concern, az_storage_blob_reader):
    # Arrange
    filepath = "file://dotenv_data/PasswordPhoto.png"

    # Act
    test_concern.index_documents(az_storage_blob_reader, filepath)

    # Assert
    # todo: assert that the document was indexed, but doesn't exist in the azure blob storage.
    assert True
