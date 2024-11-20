from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core import (StorageContext, VectorStoreIndex)
from llama_index.core.settings import Settings
from llama_index.core.vector_stores.types import VectorStore
from llama_index.readers.azstorage_blob import AzStorageBlobReader
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
        
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        Settings.llm = llm
        Settings.embed_model = embed_model

        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context
        )

        return index