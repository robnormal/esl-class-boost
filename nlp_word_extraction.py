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
from nltk.corpus import wordnet
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
    'wordnet', 'omw-1.4'
]

# Configuration
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


@functools.lru_cache(maxsize=1024)
def get_word_frequency(lemma: str, lang: str = 'en') -> float:
    """
    Get the frequency of a word in the specified language.

    Args:
        lemma: The word to check
        lang: Language code (default: 'en' for English)

    Returns:
        The word frequency as a float
    """
    try:
        return word_frequency(lemma, lang)
    except Exception as e:
        logger.warning(f"Error getting frequency for word '{lemma}': {e}")
        return 0.0


def process_sentence(sentence: str, word_info: Dict[str, Dict[str, Any]]) -> None:
    """
    Process a single sentence to extract and analyze words.

    Args:
        sentence: The sentence to process
        word_info: Dictionary to update with word information
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

        # Get appropriate WordNet POS tag and lemmatize
        wn_tag = get_wordnet_pos(tag)
        lemmatizer = WordNetLemmatizer()
        lemma = lemmatizer.lemmatize(cleaned, pos=wn_tag)

        # Get word frequency
        freq = get_word_frequency(lemma)

        # Skip common words
        if freq >= Config.COMMON_THRESHOLD:
            continue

        # Record or update word information
        if lemma not in word_info:
            word_info[lemma] = {
                'count': 0,
                'first_sentence': sentence,
                'lang_freq': freq
            }
        word_info[lemma]['count'] += 1


def parse_text(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Parse text to extract and analyze uncommon words.

    Args:
        text: The text to analyze

    Returns:
        List of tuples containing lemmas and their information,
        sorted by language frequency (highest first)
    """
    # Ensure NLTK resources are available
    ensure_nltk_resources()

    # Split the text into sentences
    sentences = sent_tokenize(text)

    # Dictionary to hold each word's data
    word_info: Dict[str, Dict[str, Any]] = {}

    # Process each sentence
    for sentence in sentences:
        process_sentence(sentence, word_info)

    # Sort lemmas by their language frequency (most common first)
    sorted_words = sorted(
        word_info.items(),
        key=lambda item: item[1]['lang_freq'],
        reverse=True
    )

    return sorted_words
