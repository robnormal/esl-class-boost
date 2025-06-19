import re
from pathlib import Path
from typing import List
import docx
import mammoth
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text

from common.envvar import environment
import document_ai_extract as document_ai

GCP_LOCATION = environment.require('GCP_LOCATION')
GCP_PROJECT_ID = environment.require('GCP_PROJECT_ID')
GCP_LAYOUT_PARSER_PROCESSOR_ID = environment.require('GCP_LAYOUT_PARSER_PROCESSOR_ID')

def paragraphs_from_string(text: str):
    """Extract paragraphs from a string."""
    # FIXME: naively dividing on empty lines
    return [p.strip() for p in text.split("\n\n") if p.strip()]

def paragraphs_from_text(file_path):
    """Extract text from plain text files."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        return paragraphs_from_string(file.read())

def paragraphs_from_html(file_handle) -> List[str]:
    soup = BeautifulSoup(file_handle, "html.parser")

    # TODO: Find a better guess
    return [p.text for p in soup.find_all('p')]

def paragraphs_from_word(file_path):
    """Extract paragraphs from Word (.docx) files."""
    doc = docx.Document(file_path)

    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:  # Only add non-empty paragraphs
            paragraphs.append(text)

    # If no paragraphs were found, try alternative method with mammoth
    if not paragraphs:
        with open(file_path, "rb") as docx_file:
            result = mammoth.extract_raw_text(docx_file)
            paragraphs = paragraphs_from_string(result.value)

    return paragraphs

def paragraphs_from_rtf(file_path):
    """Extract text from RTF files."""
    with open(file_path, 'rb') as file:
        return rtf_to_text(str(file.read()))

def paragraphs_from_pdf(file_path):
    """Extract text from PDF files using Document AI."""
    return document_ai.extract_paragraphs(
        file_path,
        gcp_project_id=GCP_PROJECT_ID,
        gcp_location=GCP_LOCATION,
        gcp_processor_id=GCP_LAYOUT_PARSER_PROCESSOR_ID,
    )

def paragraphs_from_file(file_path):
    """Extract text from various file types."""
    file_extension = Path(file_path).suffix.lower()

    # PDF files
    if file_extension == '.pdf':
        paragraphs = paragraphs_from_pdf(file_path)

    # Word documents
    elif file_extension in ['.docx', '.doc']:
        paragraphs = paragraphs_from_word(file_path)

    # HTML
    elif file_extension in ['.html', '.htm']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            paragraphs = paragraphs_from_html(file)

    # Plain text files
    elif file_extension in ['.txt', '.md', '.csv', '.json', '.xml']:
        paragraphs = paragraphs_from_text(file_path)

    # Excel files
    elif file_extension in ['.xlsx', '.xls']:
        # paragraphs = paragraphs_from_excel(file_path)
        raise NotImplementedError()

    # PowerPoint files
    elif file_extension in ['.pptx', '.ppt']:
        # paragraphs = paragraphs_from_powerpoint(file_path)
        raise NotImplementedError()

    # RTF files
    elif file_extension == '.rtf':
        paragraphs = paragraphs_from_rtf(file_path)

    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    one_line_paragraphs = [re.sub(r'[\n\r]+', ' ', p) for p in paragraphs]
    return one_line_paragraphs

def clean_paragraphs(raw_paragraphs: List[str], min_length: int):
    paragraphs = []
    for para in raw_paragraphs:
        # Replace single newlines with spaces
        clean_para = re.sub(r'\n', ' ', para)
        # Normalize whitespace
        clean_para = re.sub(r'\s+', ' ', clean_para).strip()

        # Add paragraph if it meets minimum length
        if len(clean_para) >= min_length:
            paragraphs.append(clean_para)

    return paragraphs

def extract_paragraphs(file_path: str, min_length: int = 100):
    return clean_paragraphs(paragraphs_from_file(file_path), min_length)
