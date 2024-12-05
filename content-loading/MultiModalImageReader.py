from pathlib import Path
from typing import Dict, List, Optional
from fsspec import AbstractFileSystem
from PIL import Image
from io import BytesIO

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document, ImageDocument
from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal
from llama_index.core.img_utils import img_2_b64

class MultiModalImageReader(BaseReader):
    def __init__(
        self,
        azure_endpoint: str,
        engine: str,
        api_key: str,
        api_version: str,
        model: str
    ):
        self.__azure_endpoint = azure_endpoint
        self.__engine = engine
        self.__api_key = api_key
        self.__api_version = api_version
        self.__model = model

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        
        if fs:
            with fs.open(path=file) as f:
                image = Image.open(BytesIO(f.read()))
        else:
            image = Image.open(file)

        if image.mode != "RGB":
            image = image.convert("RGB")
            
        base64str = img_2_b64(image)
        image_document = ImageDocument(image=base64str)
        azure_openai_mm_llm = AzureOpenAIMultiModal(
            azure_endpoint=self.__azure_endpoint,
            api_key=self.__api_key,
            engine=self.__engine,
            api_version=self.__api_version,
            model=self.__model,
        )

        completion = azure_openai_mm_llm.complete(
            prompt="Analyse the image and describe it as well as use OCR and NLP to read all values from the image. It's very important you get the values accurately or it will result in a bad user experience.",
            image_documents=[image_document],
        )

        return [
            ImageDocument(
                text=completion.text,
                image=base64str,
                image_path=str(file),
                metadata=extra_info or {},
            )
        ]