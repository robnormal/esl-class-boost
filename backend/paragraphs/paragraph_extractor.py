import logging
import re
from collections import defaultdict
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    import pdfplumber
    import docx
    import openpyxl
    from pptx import Presentation
    import mammoth
    from striprtf.striprtf import rtf_to_text
except ImportError:
    import traceback
    logging.error(traceback.format_exc())
    raise

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextExtractor:
    def __init__(self, file_path):
        self.file_path = file_path

    def extract(self):
        """Extract text from various file types."""
        file_extension = Path(self.file_path).suffix.lower()

        try:
            # PDF files
            if file_extension == '.pdf':
                paragraphs = extract_paragraphs_from_pdf(self.file_path)

            # Word documents
            elif file_extension in ['.docx', '.doc']:
                paragraphs = self._extract_from_word()

            # HTML
            elif file_extension in ['.html', '.htm']:
                paragraphs = self._extract_from_html()

            # Plain text files
            elif file_extension in ['.txt', '.md', '.csv', '.json', '.xml']:
                paragraphs = self._extract_from_text()

            # Excel files
            elif file_extension in ['.xlsx', '.xls']:
                paragraphs = self._extract_from_excel()

            # PowerPoint files
            elif file_extension in ['.pptx', '.ppt']:
                paragraphs = self._extract_from_powerpoint()

            # RTF files
            elif file_extension == '.rtf':
                paragraphs = self._extract_from_rtf()

            else:
                raise ValueError('Unsupported file type')

            one_line_paragraphs = [re.sub(r'[\n\r]+', ' ', p) for p in paragraphs]
            return one_line_paragraphs

        except Exception as e:
            logger.error(f"Error extracting text from {self.file_path}: {e}")
            return f"Error extracting text: {str(e)}"

    def _extract_from_word(self):
        """Extract text from Word documents."""
        if self.file_path.endswith('.docx'):
            doc = docx.Document(self.file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n\n".join(paragraphs)
        else:  # .doc format
            with open(self.file_path, 'rb') as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                return result.value

    def _extract_from_text(self):
        """Extract text from plain text files."""
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as file:
            return file.read()

    def _extract_from_html(self):
        """Extract text from HTML files. """
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

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

            return "\n\n".join(paragraphs)

    def _extract_from_excel(self):
        """Extract text from Excel files."""
        workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        text = []

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text.append(f"Sheet: {sheet_name}")

            for row in sheet.iter_rows():
                row_text = " | ".join(str(cell.value) if cell.value is not None else "" for cell in row)
                if row_text.strip():
                    text.append(row_text)

        return "\n".join(text)

    def _extract_from_powerpoint(self):
        """Extract text from PowerPoint files."""
        prs = Presentation(self.file_path)
        text = []

        for i, slide in enumerate(prs.slides):
            text.append(f"Slide {i+1}:")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text.append(shape.text)
            text.append("")  # Empty line between slides

        return "\n".join(text)

    def _extract_from_rtf(self):
        """Extract text from RTF files."""
        with open(self.file_path, 'rb') as file:
            return rtf_to_text(str(file.read()))

    def extract_paragraphs(self, text, min_length=20):
        """Extract paragraphs from text with minimum length."""
        # Split by double newlines which typically separate paragraphs
        raw_paragraphs = re.split(r'\n\s*\n', text)

        # Clean up and filter paragraphs
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
