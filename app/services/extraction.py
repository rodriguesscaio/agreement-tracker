"""Calls Claude to turn cleaned text into structured agreements."""

import json
import re

from anthropic import Anthropic

from app.config import get_settings
from app.schemas import ExtractedAgreement
from app.services.preprocessing import chunk_text, strip_noise

SYSTEM_PROMPT = """You are an expert at reading meeting transcripts, chat logs, and emails and \
extracting explicit agreements: commitments a specific person made to do something.

Return ONLY a JSON array. No prose, no markdown code fences, no explanation before or after it. \
If the text contains no agreements, return [].

Each element must be an object with exactly these keys:
- "source_text_excerpt": the exact snippet (as short as possible) the agreement was extracted from
- "owner": the name of the person who made the commitment
- "commitment": what they committed to do, in a short clear sentence
- "deadline": an ISO 8601 date (YYYY-MM-DD) if a deadline was mentioned, otherwise null
- "confidence": "high" if the commitment was stated explicitly and unambiguously, "medium" if it \
is implied but reasonably clear, "low" if it is a weak or uncertain signal

Only extract real commitments made by a named individual. Do not invent owners, deadlines, or \
commitments that are not supported by the text."""

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _parse_json_array(raw: str) -> list[dict]:
    """Claude is asked to return raw JSON; defensively unwrap a ```json
    code fence in case the model adds one anyway."""
    cleaned = raw.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    if not cleaned:
        return []
    data = json.loads(cleaned)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array from Claude")
    return data


def extract_from_chunk(chunk: str, client: Anthropic | None = None) -> list[ExtractedAgreement]:
    """Send a single chunk to Claude and parse the resulting agreements."""
    client = client or get_client()
    settings = get_settings()

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": chunk}],
    )
    raw_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    items = _parse_json_array(raw_text)
    return [ExtractedAgreement.model_validate(item) for item in items]


def extract_agreements_from_text(
    raw_text: str, client: Anthropic | None = None
) -> list[ExtractedAgreement]:
    """Full pipeline: strip noise, chunk on natural boundaries, call Claude
    per chunk, and aggregate the structured agreements."""
    cleaned = strip_noise(raw_text)
    chunks = chunk_text(cleaned)

    agreements: list[ExtractedAgreement] = []
    for chunk in chunks:
        agreements.extend(extract_from_chunk(chunk, client=client))
    return agreements
