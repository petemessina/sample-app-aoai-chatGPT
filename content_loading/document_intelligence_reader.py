import html
from typing import Dict, List, Optional
from fsspec import AbstractFileSystem
from pathlib import Path
import fsspec as fs

from azure.core import exceptions
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

MAX_SECTION_LENGTH = 1000
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 100

class DocumentIntelligenceReader(BaseReader):

    def __init__(self, documentintelligence_client: DocumentIntelligenceClient):
            self.docintelligence_client = documentintelligence_client

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        file_system: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        extra_info = extra_info or {}
        documents: List[Document] = []

        if file_system is None:
            file_fs, _ = fs.url_to_fs(file)
            file_system = file_fs

        with file_system.open(file, "rb") as image_file:
            blob_content = image_file.read()
            pages = self.parseFileWithDocumentIntelligence(blob_content)
    
            for i, (content, pagenum) in enumerate(self.split_text(pages)):
                documents.append(Document(
                    text=content,
                    extra_info=extra_info,
                ))

        return documents
    
    def parseFileWithDocumentIntelligence(self, fileAttachment):

        page_map = []
        offset = 0

        if not self.docintelligence_client:
            return "DocumentIntelligence client not initialized correctly. Cannot parse PDF file at this time."
        
        try:

            poller = self.docintelligence_client.begin_analyze_document("prebuilt-layout", analyze_request=fileAttachment, content_type="application/octet-stream")
            
            # document_intelligence_results: AnalyzeResult = await poller.result()
            document_intelligence_results = poller.result()

            if document_intelligence_results:

                for page_num, page in enumerate(document_intelligence_results.pages): #document_intelligence_results.documents
                    tables_on_page = [
                        table
                        for table in (document_intelligence_results.tables or [])
                        if table.bounding_regions and table.bounding_regions[0].page_number == page_num + 1
                    ]

                    # mark all positions of the table spans in the page
                    page_offset = page.spans[0].offset
                    page_length = page.spans[0].length
                    table_chars = [-1] * page_length
                    for table_id, table in enumerate(tables_on_page):
                        for span in table.spans:
                            # replace all table spans with "table_id" in table_chars array
                            for i in range(span.length):
                                idx = span.offset - page_offset + i
                                if idx >= 0 and idx < page_length:
                                    table_chars[idx] = table_id

                    # build page text by replacing characters in table spans with table html
                    page_text = ""
                    added_tables = set()
                    for idx, table_id in enumerate(table_chars):
                        if table_id == -1:
                            page_text += document_intelligence_results.content[page_offset + idx]
                        elif table_id not in added_tables:
                            page_text += self.table_to_html(tables_on_page[table_id])
                            added_tables.add(table_id)

                    page_text += " "
                    page_map.append((page_num, offset, page_text))
                    offset += len(page_text)
        except exceptions.HttpResponseError as e:
            raise ValueError("Error parsing PDF") from e
        except Exception as e:
            raise ValueError("Error parsing PDF") from e

        return page_map

    def table_to_html(self, table):
        table_html = "<table>"
        rows = [
            sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index)
            for i in range(table.row_count)
        ]
        for row_cells in rows:
            table_html += "<tr>"
            for cell in row_cells:
                tag = "th" if (cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
                cell_spans = ""
                if cell.column_span and cell.column_span > 1:
                    cell_spans += f" colSpan={cell.column_span}"
                if cell.row_span and cell.row_span > 1:
                    cell_spans += f" rowSpan={cell.row_span}"
                table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
            table_html += "</tr>"
        table_html += "</table>"
        return table_html

    def split_text(self, page_map):
        SENTENCE_ENDINGS = [".", "!", "?"]
        WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]

        def find_page(offset):
            num_pages = len(page_map)
            for i in range(num_pages - 1):
                if offset >= page_map[i][1] and offset < page_map[i + 1][1]:
                    return i
            return num_pages - 1
        
        all_text = "".join(p[2] for p in page_map)
        length = len(all_text)
        start = 0
        end = length
        while start + SECTION_OVERLAP < length:
            last_word = -1
            end = start + MAX_SECTION_LENGTH

            if end > length:
                end = length
            else:
                # Try to find the end of the sentence
                while (
                    end < length
                    and (end - start - MAX_SECTION_LENGTH) < SENTENCE_SEARCH_LIMIT
                    and all_text[end] not in SENTENCE_ENDINGS
                ):
                    if all_text[end] in WORDS_BREAKS:
                        last_word = end
                    end += 1
                if end < length and all_text[end] not in SENTENCE_ENDINGS and last_word > 0:
                    end = last_word  # Fall back to at least keeping a whole word
            if end < length:
                end += 1

            # Try to find the start of the sentence or at least a whole word boundary
            last_word = -1
            while (
                start > 0
                and start > end - MAX_SECTION_LENGTH - 2 * SENTENCE_SEARCH_LIMIT
                and all_text[start] not in SENTENCE_ENDINGS
            ):
                if all_text[start] in WORDS_BREAKS:
                    last_word = start
                start -= 1
            if all_text[start] not in SENTENCE_ENDINGS and last_word > 0:
                start = last_word
            if start > 0:
                start += 1

            section_text = all_text[start:end]
            yield (section_text, find_page(start))


            last_table_start = section_text.rfind("<table")
            if last_table_start > 2 * SENTENCE_SEARCH_LIMIT and last_table_start > section_text.rfind("</table"):
                # If the section ends with an unclosed table, we need to start the next section with the table.
                # If table starts inside SENTENCE_SEARCH_LIMIT, we ignore it, as that will cause an infinite loop for tables longer than MAX_SECTION_LENGTH
                # If last table starts inside SECTION_OVERLAP, keep overlapping

                # print(
                #     f"Section ends with unclosed table, starting next section with the table at page {find_page(start)} offset {start} table start {last_table_start}"
                # )
                start = min(end - SECTION_OVERLAP, start + last_table_start)
            else:
                start = end - SECTION_OVERLAP

        if start + SECTION_OVERLAP < end:
            yield (all_text[start:end], find_page(start))
            #return (all_text[start:end], find_page(start))