from typing import List

from azure.cosmos import ContainerProxy
from llama_index.core.schema import Document

class DocumentService:
    def __init__(self, container_proxy: ContainerProxy):
        self.__container_proxy = container_proxy

    def update_documents_status(self, documents: List[Document], status: str):
        master_documents = list({ (document.metadata['master_document_id'], document.metadata['user_principal_id']): document for document in documents }.values())
        
        for document in master_documents:
            self.update_document_status(document, status)

    def update_document_status(self, document: Document, status: str):
        document_id: str = document.metadata['master_document_id']
        user_id: str = document.metadata['user_principal_id']
        patch_operations = [
            { 'op': 'replace', 'path': '/status', 'value': status }
        ]

        self.__container_proxy.patch_item(
            item=document_id,
            partition_key=user_id,
            patch_operations=patch_operations
        )