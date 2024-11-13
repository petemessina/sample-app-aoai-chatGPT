from datetime import date
from typing import Any, List
from typing import Any, Optional, Dict, cast, List

from azure.cosmos import CosmosClient
from llama_index.core.schema import BaseNode, MetadataMode
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.vector_stores.utils import (node_to_metadata_dict)
from llama_index.vector_stores.azurecosmosnosql import AzureCosmosDBNoSqlVectorSearch

class TestAzureCosmosDBNoSqlSearch(AzureCosmosDBNoSqlVectorSearch):
    _metadata_columns: List[str] = PrivateAttr()
    
    def __init__(
        self,
        cosmos_client: CosmosClient,
        vector_embedding_policy: Dict[str, Any],
        indexing_policy: Dict[str, Any],
        cosmos_container_properties: Dict[str, Any],
        cosmos_database_properties: Optional[Dict[str, Any]] = None,
        database_name: str = "vectorSearchDB",
        container_name: str = "vectorSearchContainer",
        create_container: bool = True,
        id_key: str = "id",
        text_key: str = "text",
        metadata_key: str = "metadata",
        metadata_columns: List[str] = [],
        **kwargs: Any,
    ) -> None:
        super().__init__(
            cosmos_client=cosmos_client,
            vector_embedding_policy=vector_embedding_policy,
            indexing_policy=indexing_policy,
            cosmos_container_properties=cosmos_container_properties,
            cosmos_database_properties=cosmos_database_properties,
            database_name=database_name,
            container_name=container_name,
            create_container=create_container,
            id_key=id_key,
            text_key=text_key,
            metadata_key=metadata_key,
            **kwargs,
        )

        self._metadata_columns = metadata_columns

    def add(
        self,
        nodes: List[BaseNode],
        **add_kwargs: Any,
    ) -> List[str]:
        """Add nodes to index.

        Args:
            nodes: List[BaseNode]: list of nodes with embeddings

        Returns:
            A List of ids for successfully added nodes.

        """
        ids = []
        data_to_insert = []

        if not nodes:
            raise Exception("Texts can not be null or empty")

        for node in nodes:
            metadata = node_to_metadata_dict(
                node, remove_text=True, flat_metadata=self.flat_metadata
            )

            entry = {
                self._id_key: node.node_id,
                self._embedding_key: node.get_embedding(),
                self._text_key: node.get_content(metadata_mode=MetadataMode.NONE) or "",
                self._metadata_key: metadata,
                "timeStamp": date.today().isoformat(),
            }

#check for an existing name and do not override it
            for column in self._metadata_columns:
                entry[column] = metadata.get(column, "")

            data_to_insert.append(entry)
            ids.append(node.node_id)

        for item in data_to_insert:
            self._container.upsert_item(item)

        return ids