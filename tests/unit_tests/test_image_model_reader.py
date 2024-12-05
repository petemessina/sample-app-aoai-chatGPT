import pytest
from pydantic import Field
from pathlib import Path
from typing import Dict, List, Optional
from fsspec import AbstractFileSystem
import fsspec as fs
from PIL import Image
from io import BytesIO

from llama_index.core.readers.base import BaseReader 
from llama_index.core.schema import Document, ImageDocument
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.core.img_utils import img_2_b64
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_base:str = Field(validation_alias="AZURE_OPENAI_ENDPOINT")
    api_key:str = Field(validation_alias="AZURE_OPENAI_KEY")
    engine:str = Field(validation_alias="AZURE_OPENAI_MODEL_NAME")
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
    assert documents.count() == 1

class ImageModelReader(BaseReader):
    def __init__(self, model: MultiModalLLM):
        self.model = model

    def _get_image_document(
        self,
        file: Path,
        file_system: Optional[AbstractFileSystem] = None,
    ):
        if file_system is None:
            file_fs, _ = fs.url_to_fs(file)
            file_system = file_fs
        with file_system.open(file) as f:
            bytes = BytesIO(f.read())
            file_path = f.path
        image = Image.open(bytes)
        image = image.convert("RGB") if image.mode != "RGB" else image
        base64str = img_2_b64(image)
        return ImageDocument(
            image=base64str,
            image_url=str(file),
            image_path=file_path
        )

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        file_system: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        extra_info = extra_info or {}
        image_document = self._get_image_document(
            file=file,
            file_system=file_system
        )
        completion = self.model.complete(
            prompt="""
                Describe what is in this image as a summary of what you see.
                Also provide all of the exact text contained within or extracted from the image.
                Finally, provide a guess at what the image is attempting to communicate, using the information you've gathered.
                """,
            image_documents=[image_document],
        )

        return [
            ImageDocument(
                text=completion.text,
                image=image_document.image,
                image_path=image_document.image_path,
                image_url=image_document.image_url,
                metadata=extra_info,
            )
        ]
