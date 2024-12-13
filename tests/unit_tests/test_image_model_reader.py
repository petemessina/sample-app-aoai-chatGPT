import pytest
from pydantic import Field
from content_loading.image_model_reader import ImageModelReader
from content_loading.Settings import AzureMultiModalModelSettings

@pytest.fixture
def settings():
    return AzureMultiModalModelSettings()

@pytest.fixture
def azure_openai_client(settings):
    from openai import AzureOpenAI
    return AzureOpenAI(
        azure_endpoint=settings.endpoint,
        azure_deployment=settings.deploymentName,
        api_version=settings.apiVersion,
        api_key=settings.apiKey    
    )

def test_multi_modal_reader_load_data(azure_openai_client):
    # Arrange
    filepath = "file://dotenv_data/PasswordPhoto.png"
    model_reader = ImageModelReader(azure_openai_client)

    # Act
    documents = model_reader.load_data(
        file=filepath,
    )

    # Assert
    assert len(documents) == 1
    assert documents[0].text

