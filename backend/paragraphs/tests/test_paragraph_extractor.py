import os
from paragraph_extractor import TextExtractor

here = os.path.dirname(__file__)

def test_extract_paragraphs_filters_short_and_formats():
    text = """
    This is a short paragraph.

    This is a longer paragraph that should be included because it's longer than 20 characters.

    Another good one!
    """
    extractor = TextExtractor("dummy.txt")
    result = extractor.extract_paragraphs(text, min_length=30)

    assert len(result) == 1
    assert result[0].startswith("This is a longer paragraph")


def test_extract_paragraphs_removes_extra_newlines():
    text = """
    This is a paragraph
    that was broken into lines.

    Another one here,
    still continuing.

    Short

    Final valid paragraph that is long enough to be kept.
    """
    extractor = TextExtractor("dummy.txt")
    result = extractor.extract_paragraphs(text, min_length=40)

    assert len(result) == 2
    assert all("\n" not in para for para in result)
    assert all(len(para) >= 40 for para in result)


def test_extract_paragraphs_whitespace_normalization():
    text = """
    This    is    spaced      out.

    Lots\n\n\n\n\n of blank space
    """
    extractor = TextExtractor("dummy.txt")
    result = extractor.extract_paragraphs(text, min_length=10)

    assert all("  " not in para for para in result)
    assert all("\n" not in para for para in result)


def test_extract_text_txt():
    paragraph = """
    If still you think me mad, you will think so no longer when I describe the wise precautions I took for the concealment of the body. The night waned, and I worked hastily, but in silence. First of all I dismembered the corpse. I cut off the head and the arms and the legs.
    """.strip()

    extractor = TextExtractor(f"{here}/fixtures/the-tell-tale-heart.txt")
    result = extractor.extract()
    assert isinstance(result, list)
    assert paragraph in result


def test_extract_text_pdf():
    paragraph = """
    This report outlines the launch strategy for our new SmartHome Hub, a central device designed to connect and control all smart home devices seamlessly. Our goal is to revolutionize home automation and establish ourselves as market leaders in this growing sector.
    """.strip()

    extractor = TextExtractor(f"{here}/fixtures/sample-5-page-pdf-a4-size.pdf")
    result = extractor.extract()
    assert paragraph in result
