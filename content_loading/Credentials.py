from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential
from Settings import ContentLoadingSettings

class ContentLoadingCredentials():
    def __init__(self, settings: ContentLoadingSettings):
        self.settings = settings

        if (settings.cosmos.key):
            self.cosmos_credential = settings.cosmos.key
        else:
            self.cosmos_credential = DefaultAzureCredential()

        if (settings.openai.apiKey):
            self.openai_credential = settings.openai.apiKey
        else:
            self.openai_credential = DefaultAzureCredential()
            self.openai_token_provider = get_bearer_token_provider(self.openai_credential, "https://cognitiveservices.azure.com/.default")

        if (settings.storage.key):
            self.storage_credential = settings.storage.key
        else:
            self.storage_credential = DefaultAzureCredential()

        if (settings.pii.apiKey):
            self.pii_credential = AzureKeyCredential(settings.pii.apiKey)
        else:
            self.pii_credential = DefaultAzureCredential()