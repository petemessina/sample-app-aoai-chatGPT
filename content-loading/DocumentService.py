from azure.cosmos import ContainerProxy

class DocumentService:
    def __init__(self, container_proxy: ContainerProxy):
        self.__container_proxy = container_proxy

    def update_document_status(self, document_id: str, user_id: str, status: str):
        patch_operations = [
            { 'op': 'replace', 'path': '/status', 'value': status }
        ]

        self.__container_proxy.patch_item(
            item=document_id,
            partition_key=user_id,
            patch_operations=patch_operations
        )