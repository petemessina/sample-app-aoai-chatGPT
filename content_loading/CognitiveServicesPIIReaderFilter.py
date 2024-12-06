from azure.ai.textanalytics import TextAnalyticsClient, PiiEntity
from azure.identity import DefaultAzureCredential
from typing import Any, Dict, List, Optional, Union
from llama_index.core.schema import Document
from llama_index.core.readers.base import BaseReader, BasePydanticReader
from PIIDetection import PIIDetectionError, PIIDetectedEntity

class CognitiveServicesPIIReaderFilter(BasePydanticReader):
    """Filter for ensuring that documents containing PII are not indexed.

    Args:
        reader (BaseReader): The reader to filter.
        min_confidence (float): The minimum confidence level for PII detection.
    """
    reader: BaseReader
    endpoint: str
    pii_categories: Optional[List[str]] = None
    min_confidence: float = 0.8
    
    def load_data(self) -> List[Document]:
        """Load the data from the reader and filter out any documents containing PII.

        Returns:
            List[Document]: The list of documents with PII removed.
        """
        documents = self.reader.load_data()
        for doc in documents:
            detected_pii_entities = self.__detect_pii(doc)
            if detected_pii_entities:
                raise PIIDetectionError(
                    detected_entities=map(lambda entity: PIIDetectedEntity(category=entity.category, confidence_score=entity.confidence_score), detected_pii_entities), 
                    document=doc, message=f"Document contains PII: {doc.text}")
            
        return documents

    def __detect_pii(self, document: Document) -> List[PiiEntity]:
        """Check if a document contains PII.

        Args:
            document (Document): The document to check.

        Returns:
            list[PiiEntity]: A list of PII entities detected in the document.
        """
        credential = DefaultAzureCredential()

        client = TextAnalyticsClient(endpoint=self.endpoint, credential=credential)
        response = client.recognize_pii_entities([document.text], language="en", categories_filter=self.pii_categories)
        
        result = [doc for doc in response if not doc.is_error]
        detected_pii = []
        for doc in result:
            for entity in doc.entities:
                if entity.confidence_score > self.min_confidence:
                    detected_pii.append(entity)

        return detected_pii
    


