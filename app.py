import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Download required resources (only need to do this once)
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')

# Use NLTK's English stopwords as a baseline for common words.
common_words = set(stopwords.words('english'))

def parse_text(text):
    # Split the text into sentences.
    sentences = sent_tokenize(text)

    # Dictionary to hold: word -> [count, first_sentence]
    word_info = {}

    for sentence in sentences:
        # Tokenize each sentence into words.
        words = word_tokenize(sentence)
        for word in words:
            # Remove punctuation and convert to lowercase.
            cleaned = re.sub(r'\W+', '', word).lower()
            if not cleaned:
                continue
            # Skip common words.
            if cleaned in common_words:
                continue
            # Record the first occurrence of the word.
            if cleaned not in word_info:
                word_info[cleaned] = [0, sentence]
            word_info[cleaned][0] += 1

    # Sort words by frequency (most common first)
    sorted_words = sorted(word_info.items(), key=lambda item: item[1][0], reverse=True)
    return sorted_words

def show_words(results):
    for word, (count, first_sentence) in results:
        print(f"{word}: {count} times, first in: \"{first_sentence}\"")

# Example usage:
if __name__ == '__main__':
    sample_text = (
        "The Revolution changed the structure of society. However, the impacts were not uniform. "
        "Revolutionary ideas took root slowly, challenging established norms. The change was revolutionary in nature."
    )

    show_words(parse_text(sample_text))
