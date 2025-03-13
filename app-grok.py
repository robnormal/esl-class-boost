import requests
from bs4 import BeautifulSoup
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

CORPUS_URLS = [
    "http://www.americanyawp.com/text/01-the-new-world"
    "http://www.americanyawp.com/text/02-colliding-cultures"
    "http://www.americanyawp.com/text/03-british-north-america"
    "http://www.americanyawp.com/text/04-colonial-society"
    "http://www.americanyawp.com/text/05-the-american-revolution/"
    "http://www.americanyawp.com/text/06-a-new-nation"
    "http://www.americanyawp.com/text/07-the-early-republic"
    "http://www.americanyawp.com/text/08-the-market-revolution"
    "http://www.americanyawp.com/text/09-democracy-in-america"
    "http://www.americanyawp.com/text/10-religion-and-reform"
    "http://www.americanyawp.com/text/11-the-cotton-revolution"
    "http://www.americanyawp.com/text/12-manifest-destiny"
    "http://www.americanyawp.com/text/13-the-sectional-crisis"
    "http://www.americanyawp.com/text/14-the-civil-war"
    "http://www.americanyawp.com/text/15-reconstruction/"
    "http://www.americanyawp.com/text/16-capital-and-labor"
    "http://www.americanyawp.com/text/17-conquering-the-west"
    "http://www.americanyawp.com/text/18-industrial-america"
    "http://www.americanyawp.com/text/19-american-empire"
    "http://www.americanyawp.com/text/20-the-progressive-era"
    "http://www.americanyawp.com/text/21-world-war-i"
    "http://www.americanyawp.com/text/22-the-twenties"
    "http://www.americanyawp.com/text/23-the-great-depression"
    "http://www.americanyawp.com/text/24-world-war-i"
    "http://www.americanyawp.com/text/25-the-cold-war"
    "http://www.americanyawp.com/text/26-the-affluent-society"
    "http://www.americanyawp.com/text/27-the-sixties"
    "http://www.americanyawp.com/text/28-the-unraveling"
    "http://www.americanyawp.com/text/29-the-triumph-of-the-right"
    "http://www.americanyawp.com/text/30-the-recent-past"
]

def fetch_text_from_url(url):
    """
    Fetches the webpage at the given URL and extracts the main text.
    Attempts to extract text from a div with class 'entry-content' if available;
    otherwise, falls back to the entire page text.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to get the main content if available
    main_content = soup.find('div', class_='entry-content')
    if main_content:
        text = main_content.get_text(separator=' ', strip=True)
    else:
        text = soup.get_text(separator=' ', strip=True)
    return text

def download_corpus():
    return [fetch_text_from_url(url) for url in CORPUS_URLS]


def main():
    nltk.download('averaged_perceptron_tagger')

    # Sample text
    chapter = "The troop marched to battle. Emancipation freed the slaves."
    general_corpus = ["The cat sat on the mat."]  # Replace with a larger corpus

    # Tokenize and tag
    words = nltk.word_tokenize(chapter.lower())
    tagged = nltk.pos_tag(words)

    # Filter by POS (nouns, verbs, adjectives)
    target_tags = ['NN', 'NNS', 'VB', 'VBD', 'VBG', 'JJ']
    content_words = [word for word, tag in tagged if tag in target_tags]

    # TF-IDF to rank importance
    corpus = [chapter] + general_corpus
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix[0].toarray()[0]
    word_scores = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)

# Top 15 words
core_words = word_scores[:15]

# Example usage:
if __name__ == '__main__':
    main()
