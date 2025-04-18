"""
Google Cloud Document AI Paragraph Extractor
"""
import re
from os.path import isfile
from typing import List, MutableSequence
from google.cloud import documentai, documentai_v1
from common.envvar import environment

cred_path = environment.require('GOOGLE_APPLICATION_CREDENTIALS', 'File path to GCP credentials')
if not isfile(cred_path):
    raise ValueError(f"GOOGLE_APPLICATION_CREDENTIALS file path {cred_path} does not exist")

MID_WORD_END_REGEX = re.compile('\\w[—\\-]$') # hyphenated
MID_SENTENCE_END_REGEX = re.compile('[a-z]$')
MID_SENTENCE_BEGIN_REGEX = re.compile('^[a-z]')

type DocAILayoutBlock = documentai_v1.types.Document.DocumentLayout.DocumentLayoutBlock
type DocAIPageBlock = documentai_v1.types.Document.Page.Block
type DocAIBlock = DocAILayoutBlock|DocAIPageBlock

def send_to_layout_processor(
        project_id: str,
        location: str,
        processor_id: str,
        file_path: str,
        mime_type: str = "application/pdf",
        processor_version: str = "latest",
) -> documentai.Document:
    """
    Process a document using Document AI optimized for paragraph extraction.
    """
    # Initialize Document AI client
    client_options = {"api_endpoint": f"{location}-documentai.googleapis.com"}
    client = documentai.DocumentProcessorServiceClient(client_options=client_options)

    # Construct processor resource name
    resource_name = client.processor_path(project_id, location, processor_id)
    if processor_version != "latest":
        resource_name = f"{resource_name}/processorVersions/{processor_version}"

    # Read file into memory
    with open(file_path, "rb") as file:
        file_content = file.read()

    # Create document object - without chunking configuration
    raw_document = documentai.RawDocument(
        content=file_content, # type: ignore
        mime_type=mime_type # type: ignore
    )

    # Use OCR config to ensure we get good paragraph detection
    process_options = documentai.ProcessOptions(
        ocr_config=documentai.OcrConfig( # type: ignore
            enable_native_pdf_parsing=True, # type: ignore
            enable_symbol=True, # type: ignore
        )
    )

    # Process the document
    request = documentai.ProcessRequest(
        name=resource_name, # type: ignore
        raw_document=raw_document, # type: ignore
        process_options=process_options # type: ignore
    )

    response = client.process_document(request=request)
    return response.document

def is_paragraph_block(block: DocAILayoutBlock) -> bool:
    """
    Guess whether the given block represents a paragraph.

    Args:
        block: The input text to evaluate.

    Returns:
        A boolean indicating if the text is a paragraph (True) or not (False).
    """
    if not block.text_block:
        return False

    text = block.text_block.text.strip()
    if not text:
        return False
    # Paragraphs are usually longer than headings or page numbers
    elif len(text) <= 40:
        return False
    # Paragraphs usually do not contain only uppercase letters
    elif len(text) <= 80 and text.isupper():
        return False
    else:
        return True


def paragraph_objects_from_blocks(blocks: MutableSequence[DocAILayoutBlock], paragraphs = None) -> List[DocAILayoutBlock]:
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
                # add to previous paragraph without spaces
                output_paragraphs[-1] = output_paragraphs[-1] + block_text
                paragraph_already_added = True
            elif last_para_ends_mid_sentence:
                # add to previous paragraph with space between words
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
    document = send_to_layout_processor(
        project_id=gcp_project_id,
        location=gcp_location,
        processor_id=gcp_processor_id,
        file_path=file_path
    )
    # documentai.Document.to_json(document)

    return extract_paragraphs_from_docai_output(document)
