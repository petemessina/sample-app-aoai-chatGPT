import pytest
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from content_loading.image_model_reader import ImageModelReader

class Settings(BaseSettings):
    api_base:str = Field(validation_alias="AZURE_OPENAI_ENDPOINT")
    api_key:str = Field(validation_alias="AZURE_OPENAI_KEY")
    engine:str = Field(validation_alias="AZURE_OPENAI_MODEL_NAME")
    api_version:str=Field(validation_alias="AZURE_OPENAI_PREVIEW_API_VERSION")
    model_config = SettingsConfigDict()

@pytest.fixture
def settings():
    return Settings()

@pytest.fixture
def azure_openai_model(settings):
    from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal
    return AzureOpenAIMultiModal(
        model="gpt-4o",
        azure_endpoint=settings.api_base,
        api_key=settings.api_key,
        engine=settings.engine,
        azure_deployment=settings.engine,
        api_version=settings.api_version,      
    )

def test_multi_modal_reader_load_data(azure_openai_model):
    # Arrange
    filepath = "file://tests/unit_tests/dotenv_data/PasswordPhoto.png"
    model_reader = ImageModelReader(azure_openai_model)

    # Act
    documents = model_reader.load_data(
        file=filepath,
    )

    # Assert
    assert len(documents) == 1
    assert documents[0].text

