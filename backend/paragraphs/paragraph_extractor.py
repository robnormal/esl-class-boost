import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import List

try:
    from bs4 import BeautifulSoup
    import pdfplumber
    import docx
    import openpyxl
    from pptx import Presentation
    import mammoth
    from striprtf.striprtf import rtf_to_text
    from common.logger import logger
except ImportError:
    import traceback
    logging.error(traceback.format_exc())
    raise


def paragraphs_from_text(file_path):
    """Extract text from plain text files."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        # FIXME: naively dividing on empty lines
        return file.read().split("\n\n")

def paragraphs_from_word(file_path):
    """Extract text from Word documents."""
    if file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        return [para.text for para in doc.paragraphs if para.text.strip()]
    else:  # .doc format
        with open(file_path, 'rb') as docx_file:
            result = mammoth.extract_raw_text(docx_file)
            return paragraphs_from_text(result.value)

def paragraphs_from_html(file_path):
    """Extract text from HTML files. """
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

        # Get text with some structure preservation
        paragraphs = []

        # Extract paragraph content
        for para in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = para.get_text().strip()
            if text:
                # Add heading indicator
                if para.name.startswith('h'):
                    text = f"[{para.name.upper()}] {text}"
                paragraphs.append(text)

        # Extract table content
        for table in soup.find_all('table'):
            paragraphs.append("[TABLE]")
            for row in table.find_all('tr'):
                cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                if any(cells):
                    paragraphs.append(" | ".join(cells))

        return paragraphs

def paragraphs_from_rtf(file_path):
    """Extract text from RTF files."""
    with open(file_path, 'rb') as file:
        return rtf_to_text(str(file.read()))

# TODO: Review this (vibe coded)
def extract_paragraphs_from_pdf(pdf_path):
    all_paragraphs = []

    with pdfplumber.open(pdf_path) as pdf:
        # First pass: analyze the document to understand its structure
        line_heights = []
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                lines = text.split('\n')
                for i in range(1, len(lines)):
                    if lines[i-1].strip() and lines[i].strip():
                        chars_i = page.chars
                        if chars_i:
                            # Find line breaks and calculate heights
                            y_positions = sorted(set(char['top'] for char in chars_i))
                            for j in range(1, len(y_positions)):
                                line_heights.append(y_positions[j] - y_positions[j-1])

        # Calculate the most common line spacing (within paragraph)
        if line_heights:
            height_counts = defaultdict(int)
            for h in line_heights:
                # Round to nearest 0.5 to account for minor variations
                rounded_height = round(h * 2) / 2
                height_counts[rounded_height] += 1

            common_line_height = max(height_counts.items(), key=lambda x: x[1])[0]
            # Paragraph break threshold is typically 1.5x to 2x the common line height
            paragraph_threshold = common_line_height * 1.7
        else:
            # Fallback if we couldn't determine spacing
            paragraph_threshold = 15  # A reasonable default

        # Second pass: extract paragraphs using the calculated threshold
        for page in pdf.pages:
            current_paragraph = []
            last_y = None

            # Extract words with their positions
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=True
            )

            # Sort by vertical position then horizontal
            words = sorted(words, key=lambda w: (w['top'], w['x0']))

            for word in words:
                if last_y is not None and (word['top'] - last_y) > paragraph_threshold:
                    # We've hit a new paragraph
                    if current_paragraph:
                        paragraph_text = ' '.join(current_paragraph)
                        paragraph_text = re.sub(r'\s+', ' ', paragraph_text).strip()
                        if paragraph_text:
                            all_paragraphs.append(paragraph_text)
                        current_paragraph = []

                current_paragraph.append(word['text'])
                last_y = word['top']

            # Add the final paragraph from the page
            if current_paragraph:
                paragraph_text = ' '.join(current_paragraph)
                paragraph_text = re.sub(r'\s+', ' ', paragraph_text).strip()
                if paragraph_text:
                    all_paragraphs.append(paragraph_text)

    return all_paragraphs

# def paragraphs_from_excel(file_path):
#     """Extract text from Excel files."""
#     workbook = openpyxl.load_workbook(file_path, data_only=True)
#     paragraphs = []
#
#     for sheet_name in workbook.sheetnames:
#         sheet = workbook[sheet_name]
#         paragraphs.append(f"Sheet: {sheet_name}")
#
#         for row in sheet.iter_rows():
#             row_text = " | ".join(str(cell.value) if cell.value is not None else "" for cell in row)
#             if row_text.strip():
#                 paragraphs.append(row_text)
#
#     return paragraphs
#
# def paragraphs_from_powerpoint(file_path):
#     """Extract text from PowerPoint files."""
#     prs = Presentation(file_path)
#     paragraphs = []
#
#     for i, slide in enumerate(prs.slides):
#         paragraphs.append(f"Slide {i+1}:")
#         for shape in slide.shapes:
#             if hasattr(shape, "text") and shape.text.strip():
#                 paragraphs.append(shape.text)
#         paragraphs.append("")  # Empty line between slides
#
#     return paragraphs
#

def paragraphs_from_file(file_path):
    """Extract text from various file types."""
    file_extension = Path(file_path).suffix.lower()

    # PDF files
    if file_extension == '.pdf':
        paragraphs = extract_paragraphs_from_pdf(file_path)

    # Word documents
    elif file_extension in ['.docx', '.doc']:
        paragraphs = paragraphs_from_word(file_path)

    # HTML
    elif file_extension in ['.html', '.htm']:
        paragraphs = paragraphs_from_html(file_path)

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
