"""
Google Cloud Document AI Paragraph Extractor
"""
import json
import re
from typing import List, MutableSequence

from google.oauth2 import service_account
from google.cloud import documentai, documentai_v1
from common.envvar import environment

MID_WORD_END_REGEX = re.compile('\\w[—\\-]$') # hyphenated
MID_SENTENCE_END_REGEX = re.compile('[a-z]$')
MID_SENTENCE_BEGIN_REGEX = re.compile('^[a-z]')

type DocAILayoutBlock = documentai_v1.types.Document.DocumentLayout.DocumentLayoutBlock
type DocAIPageBlock = documentai_v1.types.Document.Page.Block
type DocAIBlock = DocAILayoutBlock|DocAIPageBlock

class GoogleDocumentProcessor:
    def __init__(self, project_id: str, location: str, processor_id: str, processor_version: str = "latest"):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.processor_version = processor_version
        self.client = self._build_client()
        self.resource_name = self.client.processor_path(self.project_id, self.location, self.processor_id)
        if self.processor_version != "latest":
            self.resource_name = f"{self.resource_name}/processorVersions/{self.processor_version}"

    def send_to_layout_processor(self, file_path: str, mime_type: str = "application/pdf") -> documentai.Document:
        with open(file_path, "rb") as file:
            file_content = file.read()
        raw_document = documentai.RawDocument(
            content=file_content, # type: ignore
            mime_type=mime_type # type: ignore
        )
        request = documentai.ProcessRequest(
            name=self.resource_name, # type: ignore
            raw_document=raw_document, # type: ignore
            process_options=documentai.ProcessOptions( # type: ignore
                ocr_config=documentai.OcrConfig( # type: ignore
                    enable_native_pdf_parsing=True, # type: ignore
                    enable_symbol=True, # type: ignore
                )
            ) # type: ignore
        )
        return self.client.process_document(request=request).document

    def _build_client(self) -> documentai.DocumentProcessorServiceClient:
        credentials = None
        if environment.has('GCP_DOCUMENTAI_CREDENTIALS'):
            key_data = json.loads(environment.require('GCP_DOCUMENTAI_CREDENTIALS').strip())
            credentials = service_account.Credentials.from_service_account_info(key_data)
        client_options = {"api_endpoint": f"{self.location}-documentai.googleapis.com"}
        return documentai.DocumentProcessorServiceClient(credentials=credentials, client_options=client_options)


def is_paragraph_block(block: DocAILayoutBlock) -> bool:
    if not block.text_block:
        return False
    text = block.text_block.text.strip()
    if not text:
        return False
    elif len(text) <= 40:
        return False
    elif len(text) <= 80 and text.isupper():
        return False
    else:
        return True

def paragraph_objects_from_blocks(blocks: MutableSequence[DocAILayoutBlock], paragraphs=None) -> List[DocAILayoutBlock]:
    if paragraphs is None:
        paragraphs = []
    for block in blocks:
        if block.text_block:
            if block.text_block.type_ == 'paragraph':
                paragraphs.append(block)
            if block.text_block.blocks:
                paragraph_objects_from_blocks(block.text_block.blocks, paragraphs)
    return paragraphs

def fix_paragraphs(paragraph_blocks: List[DocAILayoutBlock]) -> List[str]:
    output_paragraphs: List[str] = []
    last_para_ends_mid_word = False
    last_para_ends_mid_sentence = False
    current_page = None
    for block in paragraph_blocks:
        if not is_paragraph_block(block):
            continue
        paragraph_already_added = False
        block_text = block.text_block.text.strip()
        at_top_of_page = block.page_span.page_start != current_page
        starts_mid_sentence = MID_SENTENCE_BEGIN_REGEX.match(block_text)
        if output_paragraphs and at_top_of_page and starts_mid_sentence:
            if last_para_ends_mid_word:
                output_paragraphs[-1] = output_paragraphs[-1] + block_text
                paragraph_already_added = True
            elif last_para_ends_mid_sentence:
                output_paragraphs[-1] = output_paragraphs[-1] + ' ' + block_text
                paragraph_already_added = True
        last_para_ends_mid_word = bool(MID_WORD_END_REGEX.search(block_text))
        last_para_ends_mid_sentence = bool(MID_SENTENCE_END_REGEX.search(block_text))
        current_page = block.page_span.page_end
        if not paragraph_already_added:
            output_paragraphs.append(block_text)
    return output_paragraphs

def extract_paragraphs_from_docai_output(document: documentai.Document) -> List[str]:
    paragraph_blocks = paragraph_objects_from_blocks(document.document_layout.blocks)
    return fix_paragraphs(paragraph_blocks)

def extract_paragraphs(file_path, gcp_project_id, gcp_location, gcp_processor_id) -> List[str]:
    doc_processor = GoogleDocumentProcessor(gcp_project_id, gcp_location, gcp_processor_id)
    document = doc_processor.send_to_layout_processor(file_path=file_path)
    return extract_paragraphs_from_docai_output(document)
