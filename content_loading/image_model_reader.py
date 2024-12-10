import base64
import fsspec as fs

from mimetypes import guess_type
from typing import Dict, List, Optional
from pathlib import Path
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document, ImageDocument
from openai import AzureOpenAI

class ImageModelReader(BaseReader):
    def __init__(self, openai_client: AzureOpenAI):
        self.openai_client = openai_client

    def _get_image_document(
        self,
        file: Path,
        file_system: Optional[AbstractFileSystem] = None
    ):

        if file_system is None:
            file_fs, _ = fs.url_to_fs(file)
            file_system = file_fs

        with file_system.open(file, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

        mime_type, _ = guess_type(file)

        return ImageDocument(
            image=base64_encoded_data,
            image_url=f"data:{mime_type};base64,{base64_encoded_data}",
            image_mimetype=mime_type
        )

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        file_system: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        extra_info = extra_info or {}
        system_prompt = "You are a helpful assistant."
        prompt= """
                Describe what is in this image as a summary of what you see.
                Also provide all of the exact text contained within or extracted from the image.
                Finally, provide a guess at what the image is attempting to communicate, using the information you've gathered.
                """
        image_document = self._get_image_document(
            file=file,
            file_system=file_system
        )

        completion = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                { "role": "system", "content": system_prompt },
                { 
                    "role": "user", "content": 
                    [
                        {
                            "type": "text", 
                            "text": prompt 
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_document.image_url
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        return [
            ImageDocument(
                text=completion.choices[0].message.content,
                image=image_document.image,
                image_path=image_document.image_path,
                image_url=image_document.image_url,
                metadata=extra_info,
            )
        ]
