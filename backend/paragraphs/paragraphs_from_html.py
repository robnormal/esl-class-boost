from typing import List
from bs4 import BeautifulSoup

def extract_paragraphs_from_html(file_handle, min_words=150) -> List[str]:
    soup = BeautifulSoup(file_handle, "html.parser")

    # TODO: Find a better guess
    return [p.text for p in soup.find_all('p')]
