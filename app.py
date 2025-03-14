import logging

from nlp_word_extraction import parse_text
from paragraph_extractor import fetch_paragraphs_from_url
from paragraph_summarizer import summarize_paragraph

logging.basicConfig(filename="openai_api.log", level=logging.WARNING)

def main() -> None:
    url = "http://www.americanyawp.com/text/18-industrial-america/"
    paragraphs = fetch_paragraphs_from_url(url, 'div.entry-content')

    text: str = "\n".join(paragraphs)

    # print("Extracted text snippet:")
    # print(text[:500])
    print("\nProcessing text...\n")
    results = parse_text(text)

    for word, data in results:
        print(f"{word}: {data['count']} times, language frequency: {data['lang_freq']:.6f}, first in: \"{data['first_sentence']}\"")

    print()
    print("Paragraph summaries:")
    print()
    for paragraph in paragraphs:
        print('# ' + paragraph[:30])
        print(summarize_paragraph(paragraph, subject="history"))
        print()

# Example usage:
if __name__ == '__main__':
    main()
