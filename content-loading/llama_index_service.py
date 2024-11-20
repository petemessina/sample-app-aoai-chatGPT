import logging

from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core import (StorageContext, VectorStoreIndex)
from llama_index.core.settings import Settings
from llama_index.core.vector_stores.types import VectorStore
from llama_index.readers.azstorage_blob import AzStorageBlobReader
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from azure.storage.blob import BlobClient
from azure.cosmos import ContainerProxy

class LlamaIndexService:

    # Index the documents
    def index_documents(self,
        aoai_model_name: str,
        aoai_api_key: str,
        aoai_endpoint: str,
        aoai_api_version: str,
        document_status_container_client: ContainerProxy,
        vector_store: VectorStore,
        embed_model: AzureOpenAIEmbedding,
        blob_loader: AzStorageBlobReader,
        blob_client: BlobClient
    ) -> VectorStoreIndex:

        blob_properties = blob_client.get_blob_properties()
        blob_meta = blob_loader._extract_blob_metadata(blob_properties)
        master_document_id = blob_meta["master_document_id"]
        user_principal_id = blob_meta["user_principal_id"]
        
        try:
            documents = blob_loader.load_data()
            llm = AzureOpenAI(
                model=aoai_model_name,
                deployment_name=aoai_model_name,
                api_key=aoai_api_key,
                azure_endpoint=aoai_endpoint,
                api_version=aoai_api_version,
            )
            
            self.__update_document_status__(master_document_id, user_principal_id, "Indexing", document_status_container_client)

            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            Settings.llm = llm
            Settings.embed_model = embed_model

            index = VectorStoreIndex.from_documents(
                documents, storage_context=storage_context
            )

            blob_client.delete_blob()
            self.__update_document_status__(master_document_id, user_principal_id, "Indexed", document_status_container_client)

            return index
        except Exception as e:
            logging.error(f"Error indexing blob: {e}")
            self.__update_document_status__(master_document_id, user_principal_id, "Failed", document_status_container_client)
    
    def __update_document_status__(self, document_id: str, user_id: str, status: str, container_client: ContainerProxy):
        patch_operations = [
            { 'op': 'replace', 'path': '/status', 'value': status }
        ]

        container_client.patch_item(
            item=document_id,
            partition_key=user_id,
            patch_operations=patch_operations
        )