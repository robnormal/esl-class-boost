import pytest
import nltk
from nlp_word_extraction import (
    expand_tokens, get_wordnet_pos, WordProcessor, Language, parse_text
)
from unittest.mock import patch, MagicMock

def test_expand_tokens():
    assert expand_tokens(["well-known", "high-quality"]) == ["well", "known", "high", "quality"]
    assert expand_tokens(["hello", "world"]) == ["hello", "world"]
    assert expand_tokens(["co-op", "e-mail"]) == ["co", "op", "e", "mail"]

def test_get_wordnet_pos():
    assert get_wordnet_pos("JJ") == nltk.corpus.wordnet.ADJ
    assert get_wordnet_pos("VB") == nltk.corpus.wordnet.VERB
    assert get_wordnet_pos("NN") == nltk.corpus.wordnet.NOUN
    assert get_wordnet_pos("RB") == nltk.corpus.wordnet.ADV
    assert get_wordnet_pos("XYZ") == nltk.corpus.wordnet.NOUN  # Default case

@pytest.fixture
def mock_lemmatizer():
    lemmatizer = MagicMock()
    lemmatizer.lemmatize.side_effect = lambda word, pos: "run" if word == "running" else word
    return lemmatizer

@pytest.fixture
def language(mock_lemmatizer):
    my_language = Language("en", 0.00002)
    my_language.lemmatizer = mock_lemmatizer
    return my_language

@pytest.fixture
def word_processor(language):
    return WordProcessor("This is a simple test sentence.", language)

@patch("nlp_word_extraction.word_frequency", return_value=0.00001)
def test_is_uncommon_word(_mock_word_frequency, word_processor):
    assert word_processor.is_uncommon_word("test") is True

@patch("nlp_word_extraction.words.words", return_value={"test", "sentence", "simple"})
def test_is_valid_word(_mock_words, word_processor):
    assert word_processor.is_valid_word("test") is True
    assert word_processor.is_valid_word("xyzabc") is False

def test_lemmatize_word(word_processor):
    assert word_processor.lemmatize_word("running", "VB") == "run" # Mocked
    assert word_processor.lemmatize_word("better", "JJ") == "better" # Mocked generically

def test_process_sentence(word_processor):
    word_processor.process_sentence("The scientist discovered a new element.")
    # Ensure it processed the sentence without relying on internals
    assert isinstance(word_processor.parse_text(), list)

def test_parse_text():
    text = "The astronaut walked on the moon. The scientist discovered a new element."
    results = parse_text(text)
    assert isinstance(results, list)
    assert all(isinstance(entry, tuple) and len(entry) == 2 for entry in results)
    assert all("count" in entry[1] for entry in results)
