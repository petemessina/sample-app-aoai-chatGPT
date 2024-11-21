import uuid
from quart import (Blueprint, jsonify, request)
from azure.storage.blob import BlobServiceClient

from backend.auth.auth_utils import get_authenticated_user_details
from backend.context.document_status_context import DocumentStatusContext
from backend.context.document_chunk_context import DocumentChunkContext

class DocumentChunkRoutes:
    def __init__(self, upload_container_client: BlobServiceClient, document_chunk_context: DocumentChunkContext, document_status_context: DocumentStatusContext):
        self.blueprint = Blueprint('document_chunks', __name__)
        self._upload_container_client = upload_container_client
        self.document_chunk_context = document_chunk_context
        self.document_status_context = document_status_context
        self.register_routes()

    def register_routes(self):
        @self.blueprint.route('/upload', methods=['POST'])
        async def upload_file():
            data = await request.files
            form = await request.form
            conversation_id = form.get('conversationId')

            if not conversation_id:
                return jsonify({'error': 'conversationId is required'}), 400
            
            if 'file' not in data:
                return jsonify({'error': 'No file part'}), 400
            
            file = data['file']

            if file.filename == '':
                return jsonify({'error': 'No selected file'})
            
            if file:
                authenticated_user = get_authenticated_user_details(request_headers=request.headers)
                user_principal_id = authenticated_user["user_principal_id"]
                user_name = authenticated_user["user_name"]
                metadata = {
                    'author': user_name,
                    'user_principal_id': user_principal_id,
                    'conversation_id': conversation_id,
                    'master_document_id': str(uuid.uuid4())
                }

                try:
                    document_status = await self.document_status_context.create_document_status(user_principal_id, conversation_id, file.filename)
                    blob_client = self._upload_container_client.get_blob_client(f"{conversation_id}/{file.filename}")
                    metadata = {
                        'author': user_name,
                        'user_principal_id': user_principal_id,
                        'conversation_id': conversation_id,
                        'master_document_id': document_status['id']
                    }

                    await blob_client.upload_blob(file, metadata=metadata, overwrite=True)
                    
                    return jsonify({
                        'message': 'File uploaded successfully', 
                        'isUploaded': True,
                        'document_status': {
                            'id': document_status['id'],
                            'conversation_id': document_status['conversation_id'],
                            'file_name': document_status['file_name'],
                            'status': document_status['status']
                        }
                        }), 200
                
                except Exception as e:
                    return jsonify({'message': str(e), 'isUploaded': False}), 500

        @self.blueprint.route('/document/delete', methods=["DELETE"])
        async def delete_document():
            offset = request.args.get("offset", 0)
            authenticated_user = get_authenticated_user_details(request_headers=request.headers)
            request_json = await request.get_json()

            user_id = authenticated_user["user_principal_id"]
            id = request_json.get("id", None)

            if not id:
                return jsonify({"error": "id is required"}), 400

            ## get the documents from cosmos
            documents = await self.document_status_context.delete_document(
                user_id, id
            )
            
            if not isinstance(documents, list):
                return jsonify({"error": f"No documents was deleted"}), 404

            ## return the documents
            return jsonify(documents), 200

        @self.blueprint.route("/documents/list", methods=["GET"])
        async def list_uploaded_documents():
            offset = request.args.get("offset", 0)
            authenticated_user = get_authenticated_user_details(request_headers=request.headers)
            user_id = authenticated_user["user_principal_id"]

            ## get the documents from cosmos
            documents = await self.document_status_context.get_uploaded_documents(
                user_id, offset=offset, limit=25
            )
            if not isinstance(documents, list):
                return jsonify({"error": f"No documents are uploaded for {user_id}"}), 404

            ## return the documents
            return jsonify(documents), 200