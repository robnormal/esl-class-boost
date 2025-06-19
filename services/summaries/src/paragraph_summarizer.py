import openai
import os
import logging
import json
from typing import List

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
Your task is to summarize paragraphs that your students have been assigned to read.
The paragraphs may be from a textbook, or other sources.
The paragraphs will be separated by paragraph markers, such as "---PARAGRAPH X---"
The summaries are a study tool to help students learn the subject matter.
Each summary should:
- contain the most important information in the paragraph
- include facts and truth claims put forward in the paragraph
- be understandable to ESL and immigrant students
- be exactly one sentence long
"""

# Define the JSON schema for structured output
def get_summaries_schema(paragraph_count: int) -> dict:
    """
    Generate a JSON schema for structured output with validation for exactly
    the specified number of paragraphs.

    Args:
        paragraph_count (int): The exact number of paragraphs to summarize

    Returns:
        dict: A JSON schema object
    """
    # POST /v1/chat/completions
    # {
    #     "model": "gpt-4o-2024-08-06",
    #     "messages": [
    #         {
    #             "role": "system",
    #             "content": "You are a helpful math tutor."
    #         },
    #         {
    #             "role": "user",
    #             "content": "solve 8x + 31 = 2"
    #         }
    #     ],
    #     "response_format": {
    #         "type": "json_schema",
    #         "json_schema": {
    #             "name": "math_response",
    #             "strict": true,
    #             "schema": {
    #                 "type": "object",
    #                 "properties": {
    #                     "steps": {
    #                         "type": "array",
    #                         "items": {
    #                             "type": "object",
    #                             "properties": {
    #                                 "explanation": {
    #                                     "type": "string"
    #                                 },
    #                                 "output": {
    #                                     "type": "string"
    #                                 }
    #                             },
    #                             "required": ["explanation", "output"],
    #                             "additionalProperties": false
    #                         }
    #                     },
    #                     "final_answer": {
    #                         "type": "string"
    #                     }
    #                 },
    #                 "required": ["steps", "final_answer"],
    #                 "additionalProperties": false
    #             }
    #         }
    #     }
    # }


    return {
        "type": "json_schema",
        "json_schema": {
            "name": "pargraph_summaries_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "summaries": {
                        "type": "array",
                        "description": f"An array of exactly {paragraph_count} paragraph summaries",
                        # "minItems": paragraph_count,
                        # "maxItems": paragraph_count,
                        "items": {
                            "type": "object",
                            "properties": {
                                "paragraph_number": {
                                    "type": "integer",
                                    "description": "The number of the paragraph being summarized",
                                    # "minimum": 1,
                                    # "maximum": paragraph_count
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "A single-sentence summary of the paragraph"
                                }
                            },
                            "required": ["paragraph_number", "summary"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["summaries"],
                "additionalProperties": False
            }
        }
    }

def summarize_paragraphs(paragraphs: List[str], subject: str = "", batch_size: int = 20) -> List[str]:
    """
    Summarizes a list of paragraphs into single sentences, processing them in batches.

    Args:
        paragraphs (List[str]): The list of paragraphs to be summarized.
        subject (str, optional): The subject matter of the text (e.g., "history", "science").
                                 Defaults to an empty string.
        batch_size (int, optional): Number of paragraphs to process in each API call.
                                   Defaults to 20.

    Returns:
        List[str]: A list of one-sentence summaries corresponding to each input paragraph.

    Raises:
        ValueError: If an invalid response is received.
        openai.OpenAIError: If an API-related error occurs.
        Exception: If any other unexpected issue happens.
    """
    # Create a copy of the paragraphs list to avoid modifying the original
    results = paragraphs.copy()

    # Filter out very short paragraphs that don't need summarization
    to_summarize = []
    indices_to_summarize = []

    for i, paragraph in enumerate(paragraphs):
        if len(paragraph.strip()) < 300:
            # Keep very short paragraphs as is
            continue
        else:
            to_summarize.append(paragraph)
            indices_to_summarize.append(i)

    # Process paragraphs in batches
    for i in range(0, len(to_summarize), batch_size):
        paragraph_batch = to_summarize[i:i+batch_size]
        batch_indices = indices_to_summarize[i:i+batch_size]
        batch_size_actual = len(paragraph_batch)

        try:
            # Format paragraphs for the API request
            template = "\n\n---PARAGRAPH {}---\n{}"
            paragraphs_text = "\n\n".join([template.format(j+1, p) for j, p in enumerate(paragraph_batch)])
            user_message = f"""
Please summarize the following {batch_size_actual} paragraphs, each with a single sentence:
---

{paragraphs_text}

---

For each paragraph, provide a one-sentence summary that captures the key information.
You MUST provide exactly {batch_size_actual} summaries, one for each paragraph.
""".strip()

            # Get a schema that enforces exactly the right number of summaries
            response_format = get_summaries_schema(batch_size_actual)

            # Create a properly typed response format object
            # response_format = {
            #     "type": "json_schema",
            #     "json_schema": batch_schema
            # }

            logger.info(f"Sending a batch of {batch_size_actual} paragraphs to API...")
            # Make the API call with the batch using structured output
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE % {'subject': subject}},
                    {"role": "user", "content": user_message}
                ],
                response_format=response_format
            )

            # Ensure valid response structure
            if not response or not response.choices:
                raise ValueError("Invalid response structure received from OpenAI API.")

            # Parse the JSON response
            response_content = response.choices[0].message.content.strip()
            response_data = json.loads(response_content)

            # Verify we have the correct number of summaries
            summaries = response_data.get("summaries", [])
            if len(summaries) != batch_size_actual:
                raise ValueError(f"Expected {batch_size_actual} summaries, but received {len(summaries)}")

            # Create a mapping to ensure we have all paragraph numbers represented exactly once
            summary_map = {}
            for summary_item in summaries:
                paragraph_number = summary_item.get("paragraph_number")
                summary = summary_item.get("summary")

                if paragraph_number and 1 <= paragraph_number <= batch_size_actual:
                    summary_map[paragraph_number] = summary

            # Verify all paragraph numbers are present
            if len(summary_map) != batch_size_actual:
                missing_numbers = set(range(1, batch_size_actual + 1)) - set(summary_map.keys())
                raise ValueError(f"Missing summaries for paragraphs: {missing_numbers}")

            # Update results using the verified mapping
            for paragraph_number, summary in summary_map.items():
                # Convert from 1-indexed (API response) to 0-indexed (batch array)
                batch_index = paragraph_number - 1
                results[batch_indices[batch_index]] = summary

        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise  # Reraise the OpenAI error to be handled by the caller
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while summarizing batch: {e}")
            raise  # Reraise any other exception

    return results

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
    summaries = summarize_paragraphs([paragraph], subject)
    return summaries[0]
