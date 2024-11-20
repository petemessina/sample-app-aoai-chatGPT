import uuid
from typing import List
from datetime import datetime
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions
from backend.context.document_status_context import DocumentStatusContext

class CosmosConversationClient():
    
    def __init__(self,
        document_status_context: DocumentStatusContext,
        cosmosdb_endpoint: str,
        credential: any,
        database_name: str,
        chat_container_name: str,
        document_chunks_container_name: str,
        document_status_container_name: str,
        enable_message_feedback: bool = False
    ):
        self.document_status_context = document_status_context
        self.cosmosdb_endpoint = cosmosdb_endpoint
        self.credential = credential
        self.database_name = database_name
        self.chat_container_name = chat_container_name
        self.document_chunks_container_name = document_chunks_container_name
        self.document_status_container_name = document_status_container_name

        self.enable_message_feedback = enable_message_feedback
        try:
            self.cosmosdb_client = CosmosClient(self.cosmosdb_endpoint, credential=credential)
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 401:
                raise ValueError("Invalid credentials") from e
            else:
                raise ValueError("Invalid CosmosDB endpoint") from e

        try:
            self.database_client = self.cosmosdb_client.get_database_client(database_name)
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError("Invalid CosmosDB database name") 
        
    async def ensure(self):
        chat_container_client = self.create_chat_container_client()
        if not self.cosmosdb_client or not self.database_client or not chat_container_client:
            return False, "CosmosDB client not initialized correctly"
        try:
            database_info = await self.database_client.read()
        except:
            return False, f"CosmosDB database {self.database_name} on account {self.cosmosdb_endpoint} not found"
        
        try:
            container_info = await chat_container_client.read()
        except:
            return False, f"CosmosDB container {self.chat_container_name} not found"
            
        return True, "CosmosDB client initialized successfully"

    async def create_conversation(self, user_id, title = ''):
        chat_container_client = self.create_chat_container_client()
        conversation = {
            'id': str(uuid.uuid4()),  
            'type': 'conversation',
            'createdAt': datetime.utcnow().isoformat(),  
            'updatedAt': datetime.utcnow().isoformat(),  
            'userId': user_id,
            'title': title
        }
        ## TODO: add some error handling based on the output of the upsert_item call
        resp = await chat_container_client.upsert_item(conversation)  
        if resp:
            return resp
        else:
            return False
    
    async def upsert_conversation(self, conversation):
        chat_container_client = self.create_chat_container_client()
        resp = await chat_container_client.upsert_item(conversation)
        if resp:
            return resp
        else:
            return False

    async def delete_conversation(self, user_id, conversation_id):
        chat_container_client = self.create_chat_container_client()
        conversation = await chat_container_client.read_item(item=conversation_id, partition_key=user_id)        
        if conversation:
            resp = await chat_container_client.delete_item(item=conversation_id, partition_key=user_id)
            await self.document_status_context.delete_document_by_conversation_id(user_id, conversation_id)           

            return resp
        else:
            return True

        
    async def delete_messages(self, conversation_id, user_id):
        ## get a list of all the messages in the conversation
        chat_container_client = self.create_chat_container_client()
        messages = await self.get_messages(user_id, conversation_id)
        response_list = []
        if messages:
            for message in messages:
                resp = await chat_container_client.delete_item(item=message['id'], partition_key=user_id)
                response_list.append(resp)

            await self.document_status_context.delete_document_by_conversation_id(user_id, conversation_id)
            return response_list


    async def get_conversations(self, user_id, limit, sort_order = 'DESC', offset = 0):
        chat_container_client = self.create_chat_container_client()
        parameters = [
            {
                'name': '@userId',
                'value': user_id
            }
        ]
        query = f"SELECT * FROM c where c.userId = @userId and c.type='conversation' order by c.updatedAt {sort_order}"
        if limit is not None:
            query += f" offset {offset} limit {limit}" 
        
        conversations = []
        async for item in chat_container_client.query_items(query=query, parameters=parameters):
            conversations.append(item)
        
        return conversations

    async def get_conversation(self, user_id, conversation_id):
        chat_container_client = self.create_chat_container_client()
        parameters = [
            {
                'name': '@conversationId',
                'value': conversation_id
            },
            {
                'name': '@userId',
                'value': user_id
            }
        ]
        query = f"SELECT * FROM c where c.id = @conversationId and c.type='conversation' and c.userId = @userId"
        conversations = []
        async for item in chat_container_client.query_items(query=query, parameters=parameters):
            conversations.append(item)

        ## if no conversations are found, return None
        if len(conversations) == 0:
            return None
        else:
            return conversations[0]
 
    async def create_message(self, uuid, conversation_id, user_id, input_message: dict):
        chat_container_client = self.create_chat_container_client()
        message = {
            'id': uuid,
            'type': 'message',
            'userId' : user_id,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            'conversationId' : conversation_id,
            'role': input_message['role'],
            'content': input_message['content']
        }

        if self.enable_message_feedback:
            message['feedback'] = ''
        
        resp = await chat_container_client.upsert_item(message)  
        if resp:
            ## update the parent conversations's updatedAt field with the current message's createdAt datetime value
            conversation = await self.get_conversation(user_id, conversation_id)
            if not conversation:
                return "Conversation not found"
            conversation['updatedAt'] = message['createdAt']
            await self.upsert_conversation(conversation)
            return resp
        else:
            return False
    
    async def update_message_feedback(self, user_id, message_id, feedback):
        chat_container_client = self.create_chat_container_client()
        message = await chat_container_client.read_item(item=message_id, partition_key=user_id)
        if message:
            message['feedback'] = feedback
            resp = await chat_container_client.upsert_item(message)
            return resp
        else:
            return False

    async def get_messages(self, user_id, conversation_id):
        chat_container_client = self.create_chat_container_client()
        parameters = [
            {
                'name': '@conversationId',
                'value': conversation_id
            },
            {
                'name': '@userId',
                'value': user_id
            }
        ]
        query = f"SELECT * FROM c WHERE c.conversationId = @conversationId AND c.type='message' AND c.userId = @userId ORDER BY c.timestamp ASC"
        messages = []
        async for item in chat_container_client.query_items(query=query, parameters=parameters):
            messages.append(item)

        return messages

    

    
    
    
    
    def create_chat_container_client(self):
        try:
            return self.database_client.get_container_client(self.chat_container_name)
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError("Invalid CosmosDB container name")
        
    def create_document_chunk_container_client(self):
        try:
            return self.database_client.get_container_client(self.document_chunks_container_name)
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError("Invalid CosmosDB container name") 
        
    def create_document_status_container_client(self):
        try:
            return self.database_client.get_container_client(self.document_status_container_name)
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError("Invalid CosmosDB container name") 
        
    