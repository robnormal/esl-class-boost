"""
NLP Word Extraction Module

This module provides functionality to extract and analyze uncommon words from text.
It uses NLTK for NLP tasks and wordfreq for language frequency analysis.
"""
import re
import functools
import logging
from typing import Dict, List, Tuple, Any, Set

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet, words
from wordfreq import word_frequency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Regular expression to filter non-letter characters
LETTERS_REGEX = re.compile(r'[^a-zA-ZÀ-ÿ]')

# Set of POS tags for proper nouns (to be filtered out)
PROPER_NOUN_TAGS: Set[str] = {'NNP', 'NNPS'}

# NLTK resources required
REQUIRED_NLTK_RESOURCES: List[str] = [
    'punkt', 'punkt_tab',
    'averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng',
    'wordnet', 'words', 'omw-1.4'
]

class Config:
    """Configuration settings for word extraction."""
    # Threshold for what is considered "common" in the language
    COMMON_THRESHOLD: float = 0.00002


def ensure_nltk_resources() -> None:
    """Download required NLTK resources if not already available."""
    for resource in REQUIRED_NLTK_RESOURCES:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            try:
                logger.info(f"Downloading NLTK resource: {resource}")
                nltk.download(resource, quiet=True)
            except Exception as e:
                logger.error(f"Failed to download NLTK resource '{resource}': {e}")
                raise

@functools.lru_cache(maxsize=1024)
def get_wordnet_pos(nltk_tag: str) -> Any:
    """
    Map NLTK POS tags to WordNet POS tags.

    Args:
        nltk_tag: The NLTK POS tag

    Returns:
        The corresponding WordNet POS tag
    """
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN  # Default to noun if uncertain

def expand_tokens(tokens: List[str]) -> List[str]:
    """
    Expand tokens that contain non-letter characters (like hyphens).

    Args:
        tokens: List of word tokens

    Returns:
        List of expanded tokens
    """
    expanded: List[str] = []
    for token in tokens:
        if LETTERS_REGEX.search(token):
            parts = [part for part in LETTERS_REGEX.split(token) if part]
            expanded.extend(parts)
        else:
            expanded.append(token)
    return expanded


class Language:
    """
    Represents the language and standards for processing text.
    """
    def __init__(self, lang: str, frequency_threshold: float):
        self.lang = lang
        self.frequency_threshold = frequency_threshold
        self.lemmatizer = WordNetLemmatizer()


class WordProcessor:
    """
    Class for processing and analyzing words in text.
    Encapsulates word-level NLP operations including POS tagging,
    lemmatization, and frequency analysis.
    """

    def __init__(self, text: str, language: Language):
        """
        Initialize the WordProcessor with the text to analyze.

        Args:
            text: The text to analyze
            language: The Language object according to which we will process the text
        """
        self.text = text
        self.lang = language.lang
        self.frequency_threshold = language.frequency_threshold
        self.lemmatizer = language.lemmatizer
        self.valid_words = set(words.words())
        # Output data structure - vocabulary words with associated information
        self.word_info: Dict[str, Dict[str, Any]] = {}

        ensure_nltk_resources()

    @functools.lru_cache(maxsize=1024)
    def get_word_frequency(self, lemma_word: str) -> float:
        """
        Get (and cache) the frequency of a word in the specified language.

        Args:
            lemma_word: The word to check

        Returns:
            The word frequency as a float
        """
        return word_frequency(lemma_word, self.lang)
        # return word_frequency(lemma_word, self.lang)

    def lemmatize_word(self, word: str, pos_tag: str) -> str:
        """
        Lemmatize a word using the appropriate POS tag.

        Args:
            word: The word to lemmatize
            pos_tag: The POS tag from NLTK

        Returns:
            The lemmatized word
        """
        return self.lemmatizer.lemmatize(word, pos=get_wordnet_pos(pos_tag))

    def is_uncommon_word(self, lemma_word: str) -> bool:
        """
        Check if a word is considered uncommon based on its frequency.

        Args:
            lemma_word: The lemmatized word to check

        Returns:
            True if the word is uncommon, False otherwise
        """
        return self.get_word_frequency(lemma_word) < self.frequency_threshold

    def is_valid_word(self, lemma_word: str) -> bool:
        return lemma_word in self.valid_words

    def process_sentence(self, sentence: str) -> None:
        """
        Process a single sentence to extract and analyze words.

        Args:
            sentence: The sentence to process
        """
        # Tokenize the sentence into words
        tokens = word_tokenize(sentence)

        # Expand hyphenated tokens
        expanded_tokens = expand_tokens(tokens)

        # Tag the tokens to identify parts of speech
        pos_tags = nltk.pos_tag(expanded_tokens)

        # Process each word
        for word, tag in pos_tags:
            # Skip proper nouns
            if tag in PROPER_NOUN_TAGS:
                continue

            # Clean the word
            cleaned = re.sub(r'\W+', '', word).lower()
            if not cleaned:
                continue

            # Lemmatize the word
            lemma_word = self.lemmatize_word(cleaned, tag)

            # Get word frequency and skip common words
            if not self.is_uncommon_word(lemma_word) or not self.is_valid_word(lemma_word):
                continue

            # Record or update word information
            if lemma_word not in self.word_info:
                self.word_info[lemma_word] = {
                    'count': 0,
                    'first_sentence': sentence,
                    'lang_freq': self.get_word_frequency(lemma_word)
                }
            self.word_info[lemma_word]['count'] += 1

    def parse_text(self) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse the text to extract and analyze uncommon words.

        Returns:
            List of tuples containing lemmas and their information,
            sorted by language frequency (highest first)
        """
        # Process each sentence
        for sentence in sent_tokenize(self.text):
            self.process_sentence(sentence)

        # Sort lemmas by their language frequency (most common first)
        sorted_words = sorted(
            self.word_info.items(),
            key=lambda item: item[1]['lang_freq'],
            reverse=True
        )

        return sorted_words


def parse_text(text: str, common_threshold = Config.COMMON_THRESHOLD) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Parse text to extract and analyze uncommon words.
    This function maintains backwards compatibility with the original API.

    Args:
        text: The text to analyze
        common_threshold: Words more frequent than this in their language will be ignored

    Returns:
        List of tuples containing lemmas and their information,
        sorted by language frequency (highest first)
    """
    language = Language('en', common_threshold)
    return WordProcessor(text, language).parse_text()
