import requests
from bs4 import BeautifulSoup
from typing import List


def naive_paragraph_extract(container) -> List[str]:
    paragraphs = []
    for paragraph in container.find_all('p'):
        # Get the text and strip whitespace
        text = paragraph.get_text(strip=True)
        if text:  # Only add non-empty paragraphs
            paragraphs.append(text)

    return paragraphs

def fetch_content_from_url(url: str, selector: str) -> BeautifulSoup:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    # Try to get the main content if available
    main = soup.select_one(selector)

    if main:
        return main
    else:
        return soup.select_one('body')

def fetch_paragraphs_from_url(url: str, selector: str) -> List[str]:
    """
    Fetches the webpage at the given URL and extracts the main text.
    Attempts to extract text from a div with class 'entry-content' if available;
    otherwise, falls back to the entire page text.
    """
    content = fetch_content_from_url(url, selector)
    return naive_paragraph_extract(content)
