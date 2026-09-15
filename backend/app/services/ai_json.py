import json
import re


def extract_json(text: str) -> dict | None:
    """Best-effort JSON extraction from an LLM's raw text reply — models
    sometimes wrap JSON in prose or markdown fences despite instructions not
    to. Shared by every service that asks the model for structured output."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
