from typing import Any, Dict, List, Optional, Union
from llama_index.core.schema import Document
from llama_index.core.readers.base import BaseReader, BasePydanticReader
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from PIIDetection import PIIDetectionError, PIIDetectedEntity
import logging

class PresidioReaderFilter(BasePydanticReader):
    """Filter for ensuring that documents containing PII are not indexed, using Presidio.

    Args:
        reader (BaseReader): The reader to filter.
        min_confidence (float): The minimum confidence level for PII detection.
    """
    reader: BaseReader
    endpoint: str
    pii_categories: Optional[List[str]] = None
    min_confidence: float = 0.8
    analyzer: AnalyzerEngine = AnalyzerEngine()
    
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
                    detected_entities=map(lambda entity: PIIDetectedEntity(category=entity.entity_type, confidence_score=entity.score), detected_pii_entities),
                    document=doc, message=f"Document contains PII: {doc.text}")
            
        return documents

    def __detect_pii(self, document: Document) -> List[RecognizerResult]:
        """Check if a document contains PII.

        Args:
            document (Document): The document to check.

        Returns:
            A list of PII entities detected in the document.
        """       
        results = self.analyzer.analyze(text=document.text, entities=self.pii_categories, language='en')
        
        detected_pii = []
        for result in results:
            if result.score > self.min_confidence:
                detected_pii.append(result)

        return detected_pii
    



