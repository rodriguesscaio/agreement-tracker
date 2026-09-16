"""Calls OpenAI to turn cleaned text into structured agreements."""

import json
import logging
import re

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import ValidationError

from app.config import get_settings
from app.schemas import ExtractedAgreement
from app.services.preprocessing import chunk_text, strip_noise

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert at reading meeting transcripts, chat logs, and emails and \
extracting explicit agreements: commitments a specific person made to do something.

Return ONLY a JSON object of the form {"agreements": [...]}. No prose, no markdown code fences, \
no explanation before or after it. If the text contains no agreements, return {"agreements": []}.

Each element of "agreements" must be an object with exactly these keys:
- "source_text_excerpt": the exact snippet (as short as possible) the agreement was extracted from
- "owner": the name of the person who made the commitment
- "commitment": what they committed to do, in a short clear sentence
- "deadline": an ISO 8601 date (YYYY-MM-DD) if a deadline was mentioned, otherwise null
- "confidence": "high" if the commitment was stated explicitly and unambiguously, "medium" if it \
is implied but reasonably clear, "low" if it is a weak or uncertain signal

Only extract real commitments made by a named individual. Do not invent owners, deadlines, or \
commitments that are not supported by the text."""

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _parse_json_array(raw: str) -> list[dict]:
    """OpenAI is asked (via JSON mode) to return {"agreements": [...]}; this
    defensively unwraps a ```json code fence and accepts a bare array too,
    in case the model returns one instead of the wrapper object."""
    cleaned = raw.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    if not cleaned:
        return []
    data = json.loads(cleaned)
    if isinstance(data, dict):
        data = data.get("agreements", [])
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array (or {'agreements': [...]}) from OpenAI")
    return data


def extract_from_chunk(chunk: str, client: OpenAI | None = None) -> list[ExtractedAgreement]:
    """Send a single chunk to OpenAI and parse the resulting agreements."""
    client = client or get_client()
    settings = get_settings()

    messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(role="system", content=SYSTEM_PROMPT),
        ChatCompletionUserMessageParam(role="user", content=chunk),
    ]
    response = client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=messages,
    )
    raw_text = response.choices[0].message.content or ""
    items = _parse_json_array(raw_text)

    agreements: list[ExtractedAgreement] = []
    for item in items:
        try:
            agreements.append(ExtractedAgreement.model_validate(item))
        except ValidationError:
            logger.warning("Skipping malformed agreement from OpenAI: %r", item)
    return agreements


def extract_agreements_from_text(
    raw_text: str, client: OpenAI | None = None
) -> list[ExtractedAgreement]:
    """Full pipeline: strip noise, chunk on natural boundaries, call OpenAI
    per chunk, and aggregate the structured agreements."""
    cleaned = strip_noise(raw_text)
    chunks = chunk_text(cleaned)

    agreements: list[ExtractedAgreement] = []
    for chunk in chunks:
        agreements.extend(extract_from_chunk(chunk, client=client))
    return agreements
