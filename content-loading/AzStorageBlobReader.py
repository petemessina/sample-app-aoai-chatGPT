"""
Azure Storage Blob file and directory reader.

A loader that fetches a file or iterates through a directory from Azure Storage Blob.

"""
import logging
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List, Optional, Union

from azure.storage.blob import BlobClient
from azure.storage.blob._models import BlobProperties

from llama_index.core.bridge.pydantic import Field
from llama_index.core.readers.base import BaseReader, BasePydanticReader
from llama_index.core.schema import Document
from llama_index.core.readers import SimpleDirectoryReader, FileSystemReaderMixin
from llama_index.core.readers.base import (
    BaseReader,
    BasePydanticReader,
    ResourcesReaderMixin,
)

logger = logging.getLogger(__name__)

class AzStorageBlobReader(
    BasePydanticReader, ResourcesReaderMixin, FileSystemReaderMixin
):
    """
    General reader for any Azure Storage Blob file.

    Args:
        blob_client (BlobClient): The Azure Storage Blob client.
        file_extractor (Optional[Dict[str, Union[str, BaseReader]]]): A mapping of file
            extension to a BaseReader class that specifies how to convert that file
            to text. See `SimpleDirectoryReader` for more details, or call this path ```llama_index.readers.file.base.DEFAULT_FILE_READER_CLS```.
    """

    blob_client: BlobClient
    file_extractor: Optional[Dict[str, Union[str, BaseReader]]] = Field(
        default=None, exclude=True
    )
    is_remote: bool = True
    blob_properties: BlobProperties

    def __init__(self, blob_client, **kwargs: Any):
        blob_properties = blob_client.get_blob_properties()
        super().__init__(blob_client=blob_client, blob_properties=blob_properties, **kwargs)

    # Not in use. As part of the TODO below. Is part of the kwargs.
    # self.preloaded_data_path = kwargs.get('preloaded_data_path', None)

    @classmethod
    def class_name(cls) -> str:
        return "AzStorageBlobReader"

    def _sanitize_file_name(self, prop: str) -> str:
        return prop.replace("/", "-")
    
    def _download_blob_and_extract_metadata(self, temp_dir: str) -> Dict[str, Any]:
        """Download blob from Azure Storage and extract metadata."""
        blob_meta = {}

        sanitized_file_name = self._sanitize_file_name(self.blob_properties.name)

        download_file_path = os.path.join(temp_dir, sanitized_file_name)
        logger.info(f"Start download of {sanitized_file_name}")
        start_time = time.time()
        stream = self.blob_client.download_blob()
        with open(file=download_file_path, mode="wb") as download_file:
            stream.readinto(download_file)

        blob_meta[sanitized_file_name] = self.blob_properties.metadata
        end_time = time.time()
        logger.debug(
            f"{sanitized_file_name} downloaded in {end_time - start_time} seconds."
        )

        return blob_meta

    def _extract_blob_metadata(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        meta: dict = file_metadata

        creation_time = meta.get("creation_time")
        creation_time = creation_time.strftime("%Y-%m-%d") if creation_time else None

        last_modified = meta.get("last_modified")
        last_modified = last_modified.strftime("%Y-%m-%d") if last_modified else None

        last_accessed_on = meta.get("last_accessed_on")
        last_accessed_on = (
            last_accessed_on.strftime("%Y-%m-%d") if last_accessed_on else None
        )

        extracted_meta = {
            "file_name": meta.get("name"),
            "file_type": meta.get("content_settings", {}).get("content_type"),
            "file_size": meta.get("size"),
            "creation_date": creation_time,
            "last_modified_date": last_modified,
            "last_accessed_date": last_accessed_on,
            "container": meta.get("container"),
        }

        extracted_meta.update(meta.get("metadata") or {})
        extracted_meta.update(meta.get("tags") or {})

        return extracted_meta

    def _load_documents_with_metadata(
        self, files_metadata: Dict[str, Any], temp_dir: str
    ) -> List[Document]:
        """Load documents from a directory and extract metadata."""

        def get_metadata(file_name: str) -> Dict[str, Any]:
            file_name = file_name.split("\\")[-1]
            file_name = file_name.split("/")[-1]
            file_name = self._sanitize_file_name(file_name)

            return files_metadata.get(file_name, {})

        loader = SimpleDirectoryReader(
            temp_dir, 
            file_extractor=self.file_extractor, 
            input_files=[os.path.join(temp_dir, self.blob_properties.name)], 
            file_metadata=get_metadata
        )

        return loader.load_data()

    def list_resources(self, *args: Any, **kwargs: Any) -> List[str]:
        """There's only one blob, so return it."""
        return [self.blob_properties.name]

    def get_resource_info(self, resource_id: str, **kwargs: Any) -> Dict:
        """Get metadata for a specific blob."""
        info_dict = {
            **self._extract_blob_metadata(self.blob_properties),
            "file_path": str(resource_id).replace(":", "/"),
        }

        return {
            meta_key: meta_value
            for meta_key, meta_value in info_dict.items()
            if meta_value is not None
        }

    def load_resource(self, resource_id: str, **kwargs: Any) -> List[Document]:
        try:
            stream = self.blob_client.download_blob()
            with tempfile.TemporaryDirectory() as temp_dir:
                download_file_path = os.path.join(
                    temp_dir, resource_id.replace("/", "-")
                )
                with open(file=download_file_path, mode="wb") as download_file:
                    stream.readinto(download_file)
                return self._load_documents_with_metadata(
                    {resource_id: self.blob_properties}, temp_dir
                )
        except Exception as e:
            logger.error(
                f"Error loading resource {resource_id} from AzStorageBlob: {e}"
            )
            raise

    def read_file_content(self, input_file: Path, **kwargs) -> bytes:
        """Read the content of a file from Azure Storage Blob."""
        stream = self.blob_client.download_blob()
        return stream.readall()

    def load_data(self) -> List[Document]:
        """Load file(s) from Azure Storage Blob."""
        total_download_start_time = time.time()

        with tempfile.TemporaryDirectory() as temp_dir:
            files_metadata = self._download_blob_and_extract_metadata(temp_dir)

            total_download_end_time = time.time()

            total_elapsed_time = math.ceil(
                total_download_end_time - total_download_start_time
            )

            logger.info(
                f"Downloading completed in approximately {total_elapsed_time // 60}min"
                f" {total_elapsed_time % 60}s."
            )

            logger.info("Document creation starting")

            return self._load_documents_with_metadata(files_metadata, temp_dir)