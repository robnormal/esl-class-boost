from vocabulary.nlp_word_extraction import parse_text
from paragraphs.paragraph_extractor import fetch_paragraphs_from_url
from summaries.paragraph_summarizer import summarize_paragraph

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
        try:
            print(summarize_paragraph(paragraph, subject="history"))
        except Exception:
            print("No summary available")
        print()

# Example usage:
if __name__ == '__main__':
    main()
