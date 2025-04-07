import os
from paragraph_extractor import extract_paragraphs

here = os.path.dirname(__file__)

def test_extract_text_txt():
    paragraph = """
    If still you think me mad, you will think so no longer when I describe the wise precautions I took for the concealment of the body. The night waned, and I worked hastily, but in silence. First of all I dismembered the corpse. I cut off the head and the arms and the legs.
    """.strip()

    result = extract_paragraphs(f"{here}/fixtures/the-tell-tale-heart.txt")
    assert isinstance(result, list)
    assert paragraph in result


def test_extract_text_pdf():
    paragraph = """
    This report outlines the launch strategy for our new SmartHome Hub, a central device designed to connect and control all smart home devices seamlessly. Our goal is to revolutionize home automation and establish ourselves as market leaders in this growing sector.
    """.strip()

    result = extract_paragraphs(f"{here}/fixtures/sample-5-page-pdf-a4-size.pdf")
    assert paragraph in result
