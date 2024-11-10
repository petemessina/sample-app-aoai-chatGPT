from datetime import date
from typing import Any, List

from llama_index.core.schema import BaseNode, MetadataMode
from llama_index.core.vector_stores.utils import (node_to_metadata_dict)
from llama_index.vector_stores.azurecosmosnosql import AzureCosmosDBNoSqlVectorSearch

class TestAzureCosmosDBNoSqlSearch(AzureCosmosDBNoSqlVectorSearch):
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
                "timeStamp": date.today(),
            }
            data_to_insert.append(entry)
            ids.append(node.node_id)

        for item in data_to_insert:
            self._container.upsert_item(item)

        return ids