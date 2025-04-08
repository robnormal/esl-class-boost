"""
NLP Word Extraction Module

This module provides functionality to extract and analyze uncommon words from text.
It uses NLTK for NLP tasks and wordfreq for language frequency analysis.
"""
import re
import functools
import logging
from typing import Dict, List, Any, Set

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

class WordFromText:
    """
    Represents a word extracted from text with its context and frequency information.

    This class stores information about a word found in text, including its occurrence count,
    the first sentence it appears in, which paragraph it was found in, and its frequency
    in the language.
    """
    def __init__(self, word: str, first_sentence: str, first_paragraph: int, language_frequency: float):
        """
        Initialize a WordFromText object.

        Args:
            word: The extracted word
            first_sentence: The first sentence containing this word
            first_paragraph: The index of the first paragraph containing this word
            language_frequency: The frequency of this word in the language
        """
        self.word = word
        self.count = 1
        self.first_sentence = first_sentence
        self.first_paragraph = first_paragraph
        self.language_frequency = language_frequency

    def increment(self):
        """
        Increment the occurrence count of this word.

        This method is called each time this word is found again in the text.
        """
        self.count += 1

class WordProcessor:
    """
    Class for processing and analyzing words in text.
    Encapsulates word-level NLP operations including POS tagging,
    lemmatization, and frequency analysis.
    """

    def __init__(self, paragraphs: List[str], language: Language):
        """
        Initialize the WordProcessor with multiple paragraphs.

        Args:
            paragraphs: List of text paragraphs to analyze
            language: The Language object according to which we will process the text
        """
        self.paragraphs = paragraphs  # Store paragraphs as a list
        self.lang = language.lang
        self.frequency_threshold = language.frequency_threshold
        self.lemmatizer = language.lemmatizer
        self.valid_words = set(words.words())
        self.word_info: Dict[str, WordFromText] = {}

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

    def process_sentence(self, sentence: str, paragraph_index: int) -> None:
        """
        Process a single sentence to extract and analyze words.

        Args:
            sentence: The sentence to process
            paragraph_index: The index of the paragraph this sentence belongs to
        """
        tokens = word_tokenize(sentence)
        expanded_tokens = expand_tokens(tokens)
        pos_tags = nltk.pos_tag(expanded_tokens)

        for word, tag in pos_tags:
            if tag in PROPER_NOUN_TAGS:
                continue

            cleaned = re.sub(r'\W+', '', word).lower()
            if not cleaned:
                continue

            lemma_word = self.lemmatize_word(cleaned, tag)

            if not self.is_uncommon_word(lemma_word) or not self.is_valid_word(lemma_word):
                continue

            if lemma_word not in self.word_info:
                self.word_info[lemma_word] = WordFromText(
                    lemma_word,
                    sentence,
                    paragraph_index,
                    self.get_word_frequency(lemma_word)
                )
            else:
                self.word_info[lemma_word].increment()

    def parse_text(self) -> List[WordFromText]:
        """
        Parse the paragraphs to extract and analyze uncommon words.

        Returns:
            List of tuples containing lemmas and their information,
            sorted by language frequency (highest first)
        """
        for i in range(len(self.paragraphs)):
            for sentence in sent_tokenize(self.paragraphs[i]):
                self.process_sentence(sentence, i)

        sorted_words = sorted(
            self.word_info.values(),
            key=lambda item: item.language_frequency,
            reverse=True
        )

        return sorted_words


def parse_paragraphs(paragraphs: List[str], common_threshold=Config.COMMON_THRESHOLD) -> List[WordFromText]:
    """
    Parse paragraphs to extract uncommon words.

    Args:
        paragraphs: List of text paragraphs
        common_threshold: Words more frequent than this in their language will be ignored

    Returns:
        List of tuples containing lemmas and their information,
        sorted by language frequency (highest first)
    """
    language = Language('en', common_threshold)
    return WordProcessor(paragraphs, language).parse_text()

def parse_text(text: str, common_threshold = Config.COMMON_THRESHOLD) -> List[WordFromText]:
    """
    Parse text to extract uncommon words.

    Args:
        text: The text to analyze
        common_threshold: Words more frequent than this in their language will be ignored

    Returns:
        List of tuples containing words and their information,
        sorted by language frequency (highest first)
    """
    return parse_paragraphs([text], common_threshold)
