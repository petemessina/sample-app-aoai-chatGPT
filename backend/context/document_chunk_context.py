from typing import Dict
from azure.core.credentials_async import AsyncTokenCredential

from backend.context.cosmos_db_context import CosmosDBContext

class DocumentChunkContext(CosmosDBContext):
    def __init__(self, cosmosdb_endpoint: str, credential: str | Dict[str, str] | AsyncTokenCredential, database_name: str, container_name: str):
        super().__init__(cosmosdb_endpoint, credential, database_name, container_name)

    async def get_documents_by_master_ids(self, user_id: str, ragMasterDocumentIds: list[str], embeddings: list[float]):
        documents = []
        query=f"""SELECT TOP 10 c.metadata.file_name as file_name, c.text, c.payload, VectorDistance(c.contentVector, @embedding) AS SimilarityScore FROM c WHERE ARRAY_CONTAINS(@ids, c.metadata.master_document_id) AND c.metadata.user_principal_id = @userId ORDER BY VectorDistance(c.contentVector, @embedding)"""

        async for item in self.client_container.query_items(
                query=query,
                parameters=[
                    {"name": "@userId", "value": user_id},
                    {"name": "@embedding", "value": embeddings},
                    {"name": "@ids", "value": ragMasterDocumentIds},
                ]
            ):
            documents.append(item)

        return documents
    
    async def get_documents_by_master_id(self, user_id, master_document_id):
        documents = []
        query = "SELECT * FROM c WHERE c.metadata.master_document_id = @master_document_id AND c.metadata.user_principal_id = @userId"
        async for item in self.client_container.query_items(
                query,
                parameters=[
                    {"name": "@master_document_id", "value": master_document_id},
                    {"name": "@userId", "value": user_id}
                ]
            ):
            documents.append(item)

        return documents

    async def delete_document_chunks(self, user_id, master_document_id):
        response_list = []
        documents = await self.get_documents_by_master_id(user_id, master_document_id)

        for document in documents:
            response = await self.delete_document_chunk(document["id"], user_id)
            response_list.append(response)
        
        return response_list

    async def delete_document_chunk(self, document_id, user_id):
        document = await self.client_container.read_item(item=document_id, partition_key=user_id)
        
        if document:
            await self.client_container.delete_item(item=document_id, partition_key=user_id)
            return document
        
        return None