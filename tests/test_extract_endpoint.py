"""End-to-end coverage: pasted/uploaded text goes in, structured agreements
come out of Claude (mocked) and land in the database."""

import json
from pathlib import Path

from tests.fakes import FakeAnthropicClient

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_meeting.txt"

SAMPLE_PAYLOAD = [
    {
        "source_text_excerpt": "I'll send the updated budget spreadsheet to the team by Friday, October 3rd.",
        "owner": "Priya",
        "commitment": "Send the updated budget spreadsheet to the team",
        "deadline": "2025-10-03",
        "confidence": "high",
    },
    {
        "source_text_excerpt": "I can review the vendor contracts and get back to you by end of next week.",
        "owner": "Marcus",
        "commitment": "Review the vendor contracts",
        "deadline": None,
        "confidence": "medium",
    },
    {
        "source_text_excerpt": "I think I can lock down the venue soon",
        "owner": "Alex",
        "commitment": "Lock down the venue",
        "deadline": None,
        "confidence": "low",
    },
]


def test_extract_endpoint_extracts_and_stores_agreements(client, monkeypatch):
    fake_client = FakeAnthropicClient(responses=[json.dumps(SAMPLE_PAYLOAD)])
    monkeypatch.setattr("app.services.extraction.get_client", lambda: fake_client)

    with FIXTURE_PATH.open("rb") as fixture_file:
        response = client.post(
            "/extract",
            files={"file": ("sample_meeting.txt", fixture_file, "text/plain")},
        )

    assert response.status_code == 201
    body = response.json()
    assert len(body["agreements"]) == 3
    assert {a["owner"] for a in body["agreements"]} == {"Priya", "Marcus", "Alex"}
    assert all(a["status"] == "open" for a in body["agreements"])

    listed = client.get("/agreements").json()
    assert len(listed) == 3


def test_extract_endpoint_accepts_pasted_text(client, monkeypatch):
    fake_client = FakeAnthropicClient(responses=[json.dumps([SAMPLE_PAYLOAD[0]])])
    monkeypatch.setattr("app.services.extraction.get_client", lambda: fake_client)

    response = client.post(
        "/extract", data={"text": "Priya: I'll send the budget by Friday, October 3rd."}
    )

    assert response.status_code == 201
    assert len(response.json()["agreements"]) == 1


def test_extract_endpoint_requires_text_or_file(client):
    response = client.post("/extract", data={})

    assert response.status_code == 400


def test_extract_endpoint_rejects_blank_text(client):
    response = client.post("/extract", data={"text": "   "})

    assert response.status_code == 400
