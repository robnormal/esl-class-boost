"""
Google Cloud Document AI Paragraph Extractor

This script demonstrates how to use Google Cloud's Document AI
to process a document and extract paragraphs rather than fixed-size chunks.
"""

import pickle
import os
import re
from typing import List, Dict, Any, MutableSequence

from google.cloud import documentai, documentai_v1
from common.logger import logger

PROJECT_ID = "flash-spot-456815-c3"
LOCATION = "us"  # or "eu" depending on your processor location
PROCESSOR_ID = "59e7e67c38c56e39"
# FILE_PATH = '/home/rob/Downloads/Progressives Wynn.pdf'
FILE_PATH = '/home/rob/Downloads/KKK Americanism.pdf'
JSON_PATH = 'test-file-0.json'

PICKLE_DOC_PATH = 'my_document.pkl'

MID_SENTENCE_END_REGEX = re.compile('[a-z—\-]')
MID_WORD_END_REGEX = re.compile('[a-z]')
MID_SENTENCE_BEGIN_REGEX = re.compile('[a-z]')

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

def is_paragraph(text: str) -> bool:
    """
    Guess whether the given text is a paragraph.

    Args:
        text: The input text to evaluate.

    Returns:
        A boolean indicating if the text is a paragraph (True) or not (False).
    """
    text = text.strip()

    if not text:
        return False

    # Heuristic 1: Paragraphs are usually longer than headings or page numbers
    if len(text) < 40:
        return False

    # Heuristic 3: Paragraphs usually do not contain only uppercase letters
    if text.isupper():
        return False

    return True


def extract_text_from_blocks(blocks: MutableSequence[documentai_v1.types.Document.Page.Block], paragraphs = None) -> List[str]:
    if paragraphs is None:
        paragraphs = []
    for block in blocks:
        if block.layout.type_ == documentai.Document.Layout.Type.PARAGRAPH:
            paragraphs.append(block.layout.text)
        if block.layout.blocks:
            extract_text_from_blocks(block.layout.blocks, paragraphs)
    return paragraphs

def starts_mid_sentence(paragraph: str) -> bool:
    return bool(paragraph and MID_SENTENCE_END_REGEX.match(paragraph))

def fix_paragraphs(blocks_per_page: List[List[str]]) -> List[str]:
    output_paragraphs = []

    last_para_ends_mid_word = False
    last_para_ends_mid_sentence = False
    for page in blocks_per_page:
        is_top_of_page = True
        for paragraph in page:
            paragraph_already_added = False
            if not is_paragraph(paragraph):
                continue

            if is_top_of_page and output_paragraphs and MID_SENTENCE_BEGIN_REGEX.match(paragraph[0]):
                if last_para_ends_mid_word:
                    # add to previous paragraph without spaces
                    output_paragraphs[-1] = output_paragraphs[-1] + paragraph
                    paragraph_already_added = True
                elif last_para_ends_mid_sentence:
                    # add to previous paragraph with space between words
                    output_paragraphs[-1] = output_paragraphs[-1] + ' ' + paragraph
                    paragraph_already_added = True

            last_para_ends_mid_word = bool(MID_WORD_END_REGEX.match(paragraph[-1]))
            last_para_ends_mid_sentence = bool(MID_SENTENCE_END_REGEX.match(paragraph[-1]))

            if not paragraph_already_added:
                output_paragraphs.append(paragraph)

    return output_paragraphs

def extract_paragraphs(document: documentai.Document) -> List[str]:
    """
    Extract paragraphs from each page of the processed document.

    Args:
        document: The processed document from Document AI

    Returns:
        A list of strings, each representing a paragraph
    """
    print(len(document.pages))
    blocks_per_page = [extract_text_from_blocks(page.blocks) for page in document.pages]
    return fix_paragraphs(blocks_per_page)

def unpickle_document():
    if os.path.exists(PICKLE_DOC_PATH):
        with open(PICKLE_DOC_PATH, 'rb') as f:
            return pickle.load(f)
    else:
        return None

def main():
    """Main function to demonstrate Document AI paragraph extraction."""
    stored_doc = unpickle_document()

    if stored_doc:
        logger.info('Restoring saved document object')
        document = stored_doc
    elif os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r') as f:
            document = documentai.Document.from_json(f.read())
    else:
        # Process the document
        document = send_to_layout_processor(
            project_id=PROJECT_ID,
            location=LOCATION,
            processor_id=PROCESSOR_ID,
            file_path=FILE_PATH
        )
        with open(PICKLE_DOC_PATH, 'wb') as f:
            pickle.dump(document, f)
        with open(JSON_PATH, 'w') as f:
            f.write(documentai.Document.to_json(document))

    paragraphs = extract_paragraphs(document)
    # Try to identify headings (this is a heuristic approach)
    # mark_paragraph_headings(document, paragraphs)


    # Example: Save paragraphs to a structured format
    # This structured format can be used for various applications
    print("\nExample of structured paragraph data:")
    if paragraphs:
        import json
        example_para = paragraphs[0]
        print(json.dumps(example_para, indent=2))

if __name__ == "__main__":
    main()
