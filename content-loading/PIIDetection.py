from typing import List, Optional
from llama_index.core.schema import Document

class PIIDetectedEntity:
    """Class representing a PII entity detected in a document."""
    
    def __init__(self, category: str, confidence_score: float):
        self.category = category
        self.confidence_score = confidence_score

class PIIDetectionError(Exception):
    """Error raised when PII is detected in a document."""
    
    def __init__(self, detected_entities: List[PIIDetectedEntity], document: Document, message: Optional[str] = None):
        super().__init__(message)
        self.detected_entities = detected_entities
        self.document = document
