from typing import List, Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class ContentLoadingSettings():
    def __init__(self):
        self.cosmos = CosmosSettings()
        self.openai = OpenAISettings()
        self.storage = StorageSettings()
        self.pii = PIISettings()
        self.image = ImageSettings()

class CosmosSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='CosmosDB', extra='ignore')
    endpoint: str
    key: Optional[str] = None
    database: str
    chunkContainer: str = Field(validation_alias='CosmosDBContainer')
    statusContainer: str = Field(validation_alias='CosmosDBDocumentStatusContainer')

class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='OpenAI', extra='ignore')
    apiKey: Optional[str] = None
    endpoint: str
    apiVersion: str
    modelName: str
    modelDeployment: str
    embeddingModelName: str
    embeddingModelDeployment: str

class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='StorageAccount', extra='ignore')
    accountName: str = Field(validation_alias='StorageAccountName')
    connectionString: Optional[str] = None

class PIISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='PII', extra='ignore')
    detectionSource: str = "AzureCognitiveServices"
    endpoint: Optional[str] = None
    apiKey: Optional[str] = None
    categories: str
    minimumConfidence: float

class ImageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='SupportedImage', extra='ignore')
    fileTypes: str


