from typing import Dict
import uuid
from datetime import datetime, timezone
from azure.core.credentials_async import AsyncTokenCredential

from backend.context.cosmos_db_context import CosmosDBContext
from backend.context.document_chunk_context import DocumentChunkContext

class DocumentStatusContext(CosmosDBContext):
    def __init__(self, cosmosdb_endpoint: str, credential: str | Dict[str, str] | AsyncTokenCredential, database_name: str, container_name: str, document_chunk_context: DocumentChunkContext):
        self.__document_chunk_context = document_chunk_context
        super().__init__(cosmosdb_endpoint, credential, database_name, container_name)
        
    async def get_documents_statuses(self, user_id: str, masterDocumentIds: list[str]):
        documents = []
        query = "SELECT c.id, c.status, c.conversation_id, c.file_name FROM c WHERE ARRAY_CONTAINS(@ids, c.id) AND c.user_principal_id = @userId"

        async for item in self.client_container.query_items(
                query=query,
                parameters=[
                    {"name": "@ids", "value": masterDocumentIds},
                    {"name": "@userId", "value": user_id}
                ]
            ):
            documents.append(item)

        return documents
    
    async def get_uploaded_documents(self, user_id, limit, offset = 0):
        query = f"SELECT c.id, c.file_name, c.conversation_id, c.status FROM c WHERE c.user_principal_id = @userId"

        if limit is not None:
            query += f" offset {offset} limit {limit}" 
        
        documents = []
        async for item in self.client_container.query_items(
                query=query,
                parameters=[{"name": "@userId", "value": user_id}]
            ):
            documents.append(item)
        
        return documents
    
    async def create_document_status(self, user_id: str, conversation_id: str, file_name: str):
        document_status = {
            'id': str(uuid.uuid4()),
            'user_principal_id': user_id,
            'conversation_id': conversation_id,
            'file_name': file_name,
            'status': 'Uploaded',
            'createdAt': datetime.now(timezone.utc).isoformat(),  
            'updatedAt': datetime.now(timezone.utc).isoformat()            
        }
        
        resp = await self.client_container.upsert_item(document_status)

        if resp:
            return resp
        else:
            return False
        
    async def delete_document_by_conversation_id(self, user_id, conversation_id):
        query = "SELECT * FROM c WHERE c.conversation_id = @conversation_id AND c.user_principal_id = @userId"
        response_list = []
        documents = self.client_container.query_items(
            query,
            parameters=[
                {"name": "@conversation_id", "value": conversation_id},
                {"name": "@userId", "value": user_id}
            ]
        )

        async for document in documents:
            response = await self.delete_document(user_id, document['id'])
            response_list.append(response)

        return response_list
    
    async def delete_document(self, user_id, document_id):
        response_list = []

        await self.client_container.delete_item(item=document_id, partition_key=user_id)
        response_list = await self.__document_chunk_context.delete_document_chunks(user_id, document_id)

        return response_list