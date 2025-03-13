import requests
from bs4 import BeautifulSoup
from nlp_word_extraction import parse_text

def fetch_text_from_url(url: str) -> str:
    """
    Fetches the webpage at the given URL and extracts the main text.
    Attempts to extract text from a div with class 'entry-content' if available;
    otherwise, falls back to the entire page text.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to get the main content if available
    main_content = soup.find('div', class_='entry-content')
    if main_content:
        text = main_content.get_text(separator=' ', strip=True)
    else:
        text = soup.get_text(separator=' ', strip=True)
    return text

def main() -> None:
    url = "http://www.americanyawp.com/text/18-industrial-america/"
    text = fetch_text_from_url(url)

    # Optionally, print a snippet of the extracted text to verify it's correct
    print("Extracted text snippet:")
    print(text[:500])
    print("\nProcessing text...\n")

    results = parse_text(text)

    for word, data in results:
        print(f"{word}: {data['count']} times, language frequency: {data['lang_freq']:.6f}, first in: \"{data['first_sentence']}\"")

# Example usage:
if __name__ == '__main__':
    main()
