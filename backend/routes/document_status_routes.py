from quart import (Blueprint, jsonify, request)
from backend.auth.auth_utils import get_authenticated_user_details
from backend.context.document_status_context import DocumentStatusContext

class DocumentStatusRoutes:
    def __init__(self, document_status_context: DocumentStatusContext):
        self.blueprint = Blueprint('document_status', __name__)
        self.document_status_context = document_status_context
        self.register_routes()

    def register_routes(self):
        @self.blueprint.route("/documents/statuses", methods=["POST"])
        async def get_document_statuses():        
            request_body = await request.get_json()
            authenticated_user = get_authenticated_user_details(request_headers=request.headers)
            user_id = authenticated_user["user_principal_id"]
            document_ids = request_body.get("documentIds", [])
            documents = await self.document_status_context.get_documents_statuses(
                user_id, document_ids
            )
            
            if not isinstance(documents, list):
                return jsonify({"error": f"No documents are uploaded for {user_id}"}), 404

            ## return the documents
            return jsonify(documents), 200