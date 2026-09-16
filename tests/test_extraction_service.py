import json

from app.schemas import ExtractedAgreement
from app.services.extraction import extract_agreements_from_text, extract_from_chunk
from app.services.preprocessing import chunk_text, strip_noise
from tests.fakes import FakeOpenAIClient


def test_strip_noise_removes_timestamps_system_messages_and_signature():
    raw = (
        "[10:02] Priya joined the call\n"
        "10:02:15 AM Priya: Morning everyone.\n"
        "\n"
        "Recording stopped\n"
        "\n"
        "Best regards,\n"
        "Priya\n"
        "Sent from my iPhone\n"
    )

    cleaned = strip_noise(raw)

    assert "joined the call" not in cleaned
    assert "Recording stopped" not in cleaned
    assert "Best regards" not in cleaned
    assert "Sent from my iPhone" not in cleaned
    assert "Priya: Morning everyone." in cleaned


def test_chunk_text_splits_on_paragraph_boundaries_and_respects_max_chars():
    paragraphs = ["Paragraph one is short.", "Paragraph two is also short.", "Paragraph three."]
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text, max_chars=40)

    assert len(chunks) > 1
    for paragraph in paragraphs:
        assert any(paragraph in chunk for chunk in chunks)
    for chunk in chunks:
        for piece in chunk.split("\n\n"):
            assert piece in paragraphs


def test_chunk_text_empty_input_returns_no_chunks():
    assert chunk_text("   \n\n  ") == []


def test_extract_from_chunk_parses_json_object_from_openai():
    payload = {
        "agreements": [
            {
                "source_text_excerpt": "I'll send the report by Friday.",
                "owner": "Priya",
                "commitment": "Send the report",
                "deadline": "2025-10-03",
                "confidence": "high",
            }
        ]
    }
    fake_client = FakeOpenAIClient(responses=[json.dumps(payload)])

    result = extract_from_chunk("some chunk", client=fake_client)

    assert len(result) == 1
    assert isinstance(result[0], ExtractedAgreement)
    assert result[0].owner == "Priya"
    assert result[0].deadline.isoformat() == "2025-10-03"
    assert result[0].confidence.value == "high"


def test_extract_from_chunk_accepts_bare_json_array():
    payload = [
        {
            "source_text_excerpt": "excerpt",
            "owner": "Marcus",
            "commitment": "Review contracts",
            "deadline": None,
            "confidence": "medium",
        }
    ]
    fake_client = FakeOpenAIClient(responses=[json.dumps(payload)])

    result = extract_from_chunk("some chunk", client=fake_client)

    assert len(result) == 1
    assert result[0].deadline is None


def test_extract_from_chunk_handles_markdown_fenced_json():
    payload = {
        "agreements": [
            {
                "source_text_excerpt": "excerpt",
                "owner": "Marcus",
                "commitment": "Review contracts",
                "deadline": None,
                "confidence": "medium",
            }
        ]
    }
    fenced = "```json\n" + json.dumps(payload) + "\n```"
    fake_client = FakeOpenAIClient(responses=[fenced])

    result = extract_from_chunk("some chunk", client=fake_client)

    assert len(result) == 1
    assert result[0].deadline is None


def test_extract_from_chunk_skips_malformed_items_and_keeps_valid_ones():
    payload = {
        "agreements": [
            {
                "source_text_excerpt": "missing confidence",
                "owner": "Rafael",
                "commitment": "Write a fix",
                "deadline": None,
                # "confidence" intentionally omitted, mirroring a real
                # OpenAI response that dropped a required field.
            },
            {
                "source_text_excerpt": "I'll post the incident notice.",
                "owner": "Yuki",
                "commitment": "Post an incident notice",
                "deadline": None,
                "confidence": "high",
            },
        ]
    }
    fake_client = FakeOpenAIClient(responses=[json.dumps(payload)])

    result = extract_from_chunk("some chunk", client=fake_client)

    assert len(result) == 1
    assert result[0].owner == "Yuki"


def test_extract_from_chunk_returns_empty_list_when_no_agreements_found():
    fake_client = FakeOpenAIClient(responses=['{"agreements": []}'])

    result = extract_from_chunk("just small talk, no commitments here", client=fake_client)

    assert result == []


def test_extract_agreements_from_text_sends_cleaned_text_to_openai():
    raw_text = (
        "[10:02] Priya joined the call\n"
        "Priya: I'll send the budget by Friday, October 3rd.\n"
        "\n"
        "Best regards,\nPriya\n"
    )
    payload = {
        "agreements": [
            {
                "source_text_excerpt": "I'll send the budget by Friday, October 3rd.",
                "owner": "Priya",
                "commitment": "Send the budget",
                "deadline": "2025-10-03",
                "confidence": "high",
            }
        ]
    }
    fake_client = FakeOpenAIClient(responses=[json.dumps(payload)])

    agreements = extract_agreements_from_text(raw_text, client=fake_client)

    assert len(agreements) == 1
    assert agreements[0].owner == "Priya"

    sent_content = fake_client.calls[0]["messages"][-1]["content"]
    assert "joined the call" not in sent_content
    assert "Best regards" not in sent_content
