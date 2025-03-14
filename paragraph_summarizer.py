import openai
import os

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

# Initialize OpenAI client
client = openai.OpenAI(api_key=API_KEY)

SYSTEM_PROMPT_TEMPLATE = """
You are a %(subject)s teacher in the US, with many immigrant and ESL students in your class.
Your task is to summarize a paragraph that your students have been assigned to read.
The summary should contain the most important information in the paragraph. The summary
is a study tool to help students learn the subject matter.
The paragraph may be from a textbook, or other sources.
Your summary should be understandable to the immigrant and ESL students.
Your summary should be exactly one sentence long.
"""

def summarize_paragraph(paragraph, subject="") -> str:
    # Don't summarize short paragraphs
    if len(paragraph) < 200:
        return paragraph

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE % {'subject': subject}},
            {"role": "user", "content": paragraph}
        ]
    )
    return response.choices[0].message.content
