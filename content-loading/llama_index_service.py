import logging

from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core import (StorageContext, VectorStoreIndex)
from llama_index.core.settings import Settings
from llama_index.core.vector_stores.types import VectorStore
from llama_index.core.readers.base import BaseReader
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

class LlamaIndexService:

    # Index the documents
    def index_documents(self,
        llm: AzureOpenAI, 
        vector_store: VectorStore,
        embed_model: AzureOpenAIEmbedding,
        loader: BaseReader
    ) -> VectorStoreIndex:
        
        documents = loader.load_data()
        #self.__update_document_status__(master_document_id, user_principal_id, "Indexing", document_status_container_client)

        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        Settings.llm = llm
        Settings.embed_model = embed_model

        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context
        )

        return index

            #self.__update_document_status__(master_document_id, user_principal_id, "Indexed", document_status_container_client)

        # except Exception as e:
        #     logging.error(f"Error indexing blob: {e}")
            #self.__update_document_status__(master_document_id, user_principal_id, "Failed", document_status_container_client)
    
    #def __update_document_status__(self, document_id: str, user_id: str, status: str, container_client: ContainerProxy):
    #    patch_operations = [
    #        { 'op': 'replace', 'path': '/status', 'value': status }
    #    ]

    #    container_client.patch_item(
    #        item=document_id,
    #        partition_key=user_id,
    #        patch_operations=patch_operations
    #    )
