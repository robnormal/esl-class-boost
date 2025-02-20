import requests
from bs4 import BeautifulSoup
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from wordfreq import word_frequency

# Download required NLTK resources (if not already available)
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# Set a threshold for what is considered "common" in the language.
COMMON_THRESHOLD = 0.00002  # Adjust this threshold as desired
# Keep Latin letters (including accented), remove everything else
LETTERS_REGEX = re.compile('[^a-zA-ZÀ-ÿ]')

def fetch_text_from_url(url):
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

def parse_text(text):
    # Split the text into sentences.
    sentences = sent_tokenize(text)

    # Dictionary to hold each word's data:
    # word -> {'count': int, 'first_sentence': str, 'lang_freq': float}
    word_info = {}

    for sentence in sentences:
        # Tokenize the sentence into words.
        tokens = word_tokenize(sentence)

        # Expand tokens that are hyphenated.
        expanded_tokens = []
        for token in tokens:
            if LETTERS_REGEX.search(token):
                # Split on hyphen; you can further filter out empty parts.
                parts = [part for part in LETTERS_REGEX.split(token) if part]
                expanded_tokens.extend(parts)
            else:
                expanded_tokens.append(token)

        # Tag the tokens to identify proper nouns.
        pos_tags = nltk.pos_tag(expanded_tokens)

        for word, tag in pos_tags:
            # Clean the word: remove punctuation and lower-case it.
            cleaned = re.sub(r'\W+', '', word).lower()
            if not cleaned:
                continue

            # Skip proper nouns (e.g., names) if desired.
            if tag in ('NNP', 'NNPS'):
                continue

            # Use wordfreq to get the word's frequency in English.
            freq = word_frequency(cleaned, 'en')

            # Skip words that are too common.
            if freq >= COMMON_THRESHOLD:
                continue

            # Record the word's first occurrence and count.
            if cleaned not in word_info:
                word_info[cleaned] = {'count': 0, 'first_sentence': sentence, 'lang_freq': freq}
            word_info[cleaned]['count'] += 1

    # Sort words by their language frequency (from most common among the filtered words to least common).
    sorted_words = sorted(word_info.items(), key=lambda item: item[1]['lang_freq'], reverse=True)
    return sorted_words

def main():
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
