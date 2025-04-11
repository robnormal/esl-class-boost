from typing import List

from bs4 import BeautifulSoup
import re
from common.logger import logger

BLOCK_TAGS = {
    "p", "div", "section", "article", "blockquote", "pre", "li", "td", "main"
}

# Inline and non-visible tags to ignore
SKIP_TAGS = {"script", "style", "nav", "footer", "head", "meta", "title"}

def is_block(tag):
    return tag.name in BLOCK_TAGS

def is_visible(tag):
    return tag.name not in SKIP_TAGS and not tag.has_attr("hidden")

def get_text_word_count(tag):
    text = tag.get_text(separator=' ', strip=True)
    words = re.findall(r'\w+', text)
    return text, len(words)

def get_leaf_blocks(soup):
    """Return only leaf block elements (those without nested block children)."""
    blocks = []
    all = soup.find_all(BLOCK_TAGS)
    logger.info(f"Found {len(all)} blocks")
    for tag in all:
        if not any(is_block(child) for child in tag.find_all(recursive=True)):
            if is_visible(tag):
                _, wc = get_text_word_count(tag)
                if wc > 0:
                    blocks.append(tag)
    return blocks

def group_blocks(blocks, min_words=150, max_words=250):
    """Group block elements into paragraph-like chunks based on word count."""
    groups = []
    i = 0
    while i < len(blocks):
        group = []
        word_count = 0
        while i < len(blocks):
            text, wc = get_text_word_count(blocks[i])
            if word_count + wc > max_words and word_count >= min_words:
                break
            group.append(blocks[i])
            word_count += wc
            i += 1
        if group:
            groups.append(group)
    return groups

def extract_paragraphs_from_html(file_handle, min_words=150, max_words=250) -> List[str]:
    soup = BeautifulSoup(file_handle, "html.parser")

    # Clean soup by removing non-visible elements
    for tag in soup.find_all(SKIP_TAGS):
        tag.decompose()

    leaf_blocks = get_leaf_blocks(soup)
    block_groups = group_blocks(leaf_blocks, min_words=min_words, max_words=max_words)

    # Build final result with text and HTML for each paragraph group
    result = []
    for group in block_groups:
        text = ' '.join(get_text_word_count(tag)[0] for tag in group)
        result.append(text)

    return result
