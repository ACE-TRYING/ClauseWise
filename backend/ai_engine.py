
import os
import re
import json
import time
import hashlib

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-120b"

client = Groq(api_key=API_KEY) if API_KEY else None

# Stores successful explanations while the backend is running.
EXPLANATION_CACHE = {}


JARGON = {
    "made and entered into": "agreed to",
    "pursuant to": "under",
    "hereinafter": "from now on",
    "prior to": "before",
    "commence": "start",
    "in accordance with": "as required by",
    "in the event that": "if",
    "for the purpose of": "to",
    "in the absence of": "if there is no",
}


def split_sentences(text):
    if not text:
        return []

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"(\d)\s+-\s+(\w)", r"\1-\2", text)

    parts = []

    for line in text.split("\n"):
        line = line.strip()

        if not line:
            continue

        sentences = re.split(
            r'(?<=[.!?;])\s+(?=[A-Z0-9"\'])',
            line
        )

        for sentence in sentences:
            sentence = sentence.strip()

            if len(sentence) > 25:
                parts.append(sentence)

    return parts


def basic_simplify(sentence):
    simplified = sentence
    changes = []

    for old, new in JARGON.items():
        pattern = re.compile(
            r"\b" + re.escape(old) + r"\b",
            flags=re.IGNORECASE
        )

        if pattern.search(simplified):
            simplified = pattern.sub(new, simplified)

            changes.append({
                "from": old,
                "to": new
            })

    return simplified, changes


def simplify_batch(clauses):
    """
    Explains all detected clauses using one Groq API request.

    Returns one explanation for each input clause.
    """

    if not clauses:
        return []

    results = [None] * len(clauses)
    pending = []

    # STEP 1: Check the explanation cache.
    for index, clause in enumerate(clauses):

        cache_key = hashlib.sha256(
            (
                clause.get("type", "General")
                + clause["sentence"]
            ).encode("utf-8")
        ).hexdigest()

        if cache_key in EXPLANATION_CACHE:
            results[index] = EXPLANATION_CACHE[cache_key]

        else:
            pending.append((index, cache_key, clause))

    if not pending:
        print("All explanations loaded from cache.")
        return results

    # STEP 2: Fallback if the API key is missing.
    if not client:
        print("Groq API key missing. Using basic fallback.")

        for index, _, clause in pending:
            simple, changes = basic_simplify(clause["sentence"])

            results[index] = {
                "simplified": simple,
                "why_it_matters": clause.get("why", ""),
                "example": "",
                "changes": changes,
            }

        return results

    # STEP 3: Prepare clauses for Groq.
    clause_input = [
        {
            "id": index,
            "clause_type": clause.get("type", "General"),
            "original_text": clause["sentence"],
        }
        for index, _, clause in pending
    ]

    system_prompt = """
You are a legal document explanation assistant.

Explain legal clauses in simple everyday English.

IMPORTANT RULES:

1. Preserve the original legal meaning.
2. Never remove conditions, exceptions, deadlines or obligations.
3. Never invent facts or legal consequences.
4. Do not provide legal advice.
5. Use short and understandable sentences.
6. Mention ambiguity rather than guessing.
7. Explain each clause independently.
8. Return every clause using its original numeric ID.

For every clause provide:

- id: Original numeric ID.
- simplified: Plain-English explanation.
- why_it_matters: Practical importance to the reader.
- example: A short everyday example, or an empty string.

Return the explanations as a JSON object.
"""

    user_prompt = (
        "Explain these legal clauses:\n\n"
        + json.dumps(clause_input, ensure_ascii=False)
    )

    # STEP 4: Define the expected JSON structure.
    response_schema = {
        "type": "object",
        "properties": {
            "explanations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "simplified": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                        "example": {"type": "string"},
                    },
                    "required": [
                        "id",
                        "simplified",
                        "why_it_matters",
                        "example",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["explanations"],
        "additionalProperties": False,
    }

    explanation_map = {}

    # STEP 5: Call Groq with one retry for temporary errors.
    for attempt in range(2):

        try:
            start_time = time.perf_counter()

            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "clause_explanations",
                        "strict": True,
                        "schema": response_schema,
                    },
                },
                reasoning_effort="low",
                max_completion_tokens=4000,
            )

            elapsed = time.perf_counter() - start_time

            print(f"Groq response time: {elapsed:.2f} seconds")

            content = response.choices[0].message.content

            if not content:
                raise ValueError("Groq returned an empty response.")

            parsed = json.loads(content)

            explanation_map = {
                item["id"]: item
                for item in parsed.get("explanations", [])
                if isinstance(item.get("id"), int)
            }

            print(
                f"Groq successfully explained "
                f"{len(explanation_map)} clauses."
            )

            break

        except Exception as error:

            status_code = getattr(error, "status_code", None)

            temporary_error = (
                status_code == 429
                or (
                    isinstance(status_code, int)
                    and status_code >= 500
                )
            )

            if temporary_error and attempt == 0:
                print(
                    f"Groq temporarily unavailable. "
                    f"Retrying once: {error}"
                )

                time.sleep(1)
                continue

            print(f"Groq simplification failed: {error}")
            break

    # STEP 6: Match explanations to original clauses.
    for index, cache_key, clause in pending:

        item = explanation_map.get(index)

        if item and item.get("simplified", "").strip():

            explanation = {
                "simplified": item["simplified"].strip(),
                "why_it_matters": item.get("why_it_matters", ""),
                "example": item.get("example", ""),
                "changes": [
                    {
                        "from": "Groq AI",
                        "to": "Plain-English explanation",
                    }
                ],
            }

            # Cache successful AI explanations only.
            EXPLANATION_CACHE[cache_key] = explanation
            results[index] = explanation

        else:
            # Fallback if a clause was not explained.
            simple, changes = basic_simplify(clause["sentence"])

            results[index] = {
                "simplified": simple,
                "why_it_matters": clause.get("why", ""),
                "example": "",
                "changes": changes,
            }

    return results


# Compatibility function for older code.
def simplify(sentence):

    result = simplify_batch([
        {
            "sentence": sentence,
            "type": "General",
            "why": "",
        }
    ])

    if result:
        return result[0]["simplified"], result[0]["changes"]

    return sentence, []


def make_summary(clauses, level):

    high = sum(
        c["severity"] == "high"
        for c in clauses
    )

    medium = sum(
        c["severity"] == "medium"
        for c in clauses
    )

    low = len(clauses) - high - medium

    important_types = sorted({
        c["type"]
        for c in clauses
        if c["severity"] in ("high", "medium")
    })

    if not clauses:
        return (
            "No clauses matching the current detection rules were found. "
            "This does not mean the document contains no important legal terms."
        )

    names = (
        ", ".join(important_types)
        if important_types
        else "the detected clauses"
    )

    return (
        f"We found {len(clauses)} potentially important clauses. "
        f"This includes {high} high-severity, "
        f"{medium} medium-severity, and {low} low-severity findings. "
        f"Pay particular attention to: {names}. "
        "These findings are based on keyword rules, not a legal assessment."
    )
