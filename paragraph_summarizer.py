import openai
import os
import logging

# Configure logging to write errors to a file instead of CLI
LOG_FILE = "paragraph_summarizer_errors.log"
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode="a"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Retrieve API key from environment variable
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable. Please set it before running the script.")

# Initialize OpenAI client
client = openai.OpenAI(api_key=API_KEY)

# System prompt for contextualizing the AI's role
SYSTEM_PROMPT_TEMPLATE = """
You are a %(subject)s teacher in the US, with many immigrant and ESL students in your class.
Your task is to summarize a paragraph that your students have been assigned to read.
The summary should contain the most important information in the paragraph. The summary
is a study tool to help students learn the subject matter.
The paragraph may be from a textbook, or other sources.
Your summary should be understandable to the immigrant and ESL students.
Your summary should be exactly one sentence long.
"""

def summarize_paragraph(paragraph: str, subject: str = "") -> str:
    """
    Summarizes a given paragraph into a single sentence.

    Args:
        paragraph (str): The paragraph to be summarized.
        subject (str, optional): The subject matter of the text (e.g., "history", "science").
                                 Defaults to an empty string.

    Returns:
        str: The one-sentence summary.

    Raises:
        ValueError: If an invalid response is received.
        openai.OpenAIError: If an API-related error occurs.
        Exception: If any other unexpected issue happens.
    """

    # Do not summarize very short paragraphs
    if len(paragraph.strip()) < 200:
        return paragraph

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE % {'subject': subject}},
                {"role": "user", "content": paragraph}
            ]
        )

        # Ensure valid response structure
        if not response or not response.choices:
            raise ValueError("Invalid response structure received from OpenAI API.")

        return response.choices[0].message.content.strip()

    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise  # Reraise the OpenAI error to be handled by the caller
    except Exception as e:
        logger.error(f"Unexpected error while summarizing: {e}")
        raise  # Reraise any other exception
