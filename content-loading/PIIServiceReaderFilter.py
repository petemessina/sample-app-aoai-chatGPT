import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.identity import DefaultAzureCredential
from typing import Any, Dict, List, Optional, Union
from llama_index.core.schema import Document
from llama_index.core.readers.base import BaseReader, BasePydanticReader

class PIIServiceReaderFilter(BasePydanticReader):
    """Filter for ensuring that documents containing PII are not indexed.

    Args:
        reader (BaseReader): The reader to filter.
        min_confidence (float): The minimum confidence level for PII detection.
    """
    reader: BaseReader
    min_confidence: float = 0.8
    
    def load_data(self) -> List[Document]:
        """Load the data from the reader and filter out any documents containing PII.

        Returns:
            List[Document]: The list of documents with PII removed.
        """
        documents = self.reader.load_data()
        for doc in documents:
            if self.__contains_pii(doc):
                raise ValueError(f"Document contains PII: {doc.text}")

    def __contains_pii(self, document: Document) -> bool:
        """Check if a document contains PII.

        Args:
            document (Document): The document to check.

        Returns:
            bool: True if the document contains PII, False otherwise.
        """
        credential = DefaultAzureCredential()
        endpoint = os.environ["PIIEndpoint"]

        client = TextAnalyticsClient(endpoint=endpoint, credential=credential)
        response = client.recognize_pii_entities([document.text], language="en")
        
        result = [doc for doc in response if not doc.is_error]
        for doc in result:
            for entity in doc.entities:
                if entity.confidence_score > self.min_confidence:
                    return True

        return False



