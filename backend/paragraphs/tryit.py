import os
from paragraph_extractor import TextExtractor

here = os.path.dirname(__file__)
paragraphs = TextExtractor(f"{here}/tests/fixtures/Eloisa to Abelard _ The Poetry Foundation.html").extract()
for p in paragraphs:
    print(p)
    print()
