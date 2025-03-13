import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from wordfreq import word_frequency
from typing import Dict, List, Tuple, Any

# Download required NLTK resources (if not already available)
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('wordnet')
nltk.download('omw-1.4')

# Set a threshold for what is considered "common" in the language.
COMMON_THRESHOLD: float = 0.00002  # Adjust this threshold as desired
# Keep Latin letters (including accented), remove everything else
LETTERS_REGEX = re.compile('[^a-zA-ZÀ-ÿ]')

# Initialize the lemmatizer.
lemmatizer = WordNetLemmatizer()

# Function to map NLTK POS tags to WordNet POS tags.
def get_wordnet_pos(nltk_tag: str) -> Any:
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN  # Default to noun if uncertain.

def parse_text(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    # Split the text into sentences.
    sentences = sent_tokenize(text)

    # Dictionary to hold each word's data:
    # lemma -> {'count': int, 'first_sentence': str, 'lang_freq': float}
    word_info: Dict[str, Dict[str, Any]] = {}

    for sentence in sentences:
        # Tokenize the sentence into words.
        tokens = word_tokenize(sentence)

        # Expand tokens that are hyphenated.
        expanded_tokens: List[str] = []
        for token in tokens:
            if LETTERS_REGEX.search(token):
                parts = [part for part in LETTERS_REGEX.split(token) if part]
                expanded_tokens.extend(parts)
            else:
                expanded_tokens.append(token)

        # Tag the tokens to identify proper nouns and determine POS.
        pos_tags = nltk.pos_tag(expanded_tokens)

        for word, tag in pos_tags:
            # Clean the word: remove punctuation and lower-case it.
            cleaned = re.sub(r'\W+', '', word).lower()
            if not cleaned:
                continue

            # Skip proper nouns (e.g., names) if desired.
            if tag in ('NNP', 'NNPS'):
                continue

            # Map the tag for lemmatization.
            wn_tag = get_wordnet_pos(tag)
            # Lemmatize the word.
            lemma = lemmatizer.lemmatize(cleaned, pos=wn_tag)

            # Use wordfreq to get the lemma's frequency in English.
            freq = word_frequency(lemma, 'en')

            # Skip words that are too common.
            if freq >= COMMON_THRESHOLD:
                continue

            # Record the lemma's first occurrence and count.
            if lemma not in word_info:
                word_info[lemma] = {'count': 0, 'first_sentence': sentence, 'lang_freq': freq}
            word_info[lemma]['count'] += 1

    # Sort lemmas by their language frequency (most common among the filtered ones first).
    sorted_words = sorted(word_info.items(), key=lambda item: item[1]['lang_freq'], reverse=True)
    return sorted_words
