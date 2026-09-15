from datetime import date

from app.models import Agreement, AgreementStatus, Confidence


def _make_agreement(db_session, **overrides):
    defaults = dict(
        source_text_excerpt="excerpt",
        owner="Priya",
        commitment="Do the thing",
        deadline=date(2025, 10, 3),
        confidence=Confidence.high,
        status=AgreementStatus.open,
    )
    defaults.update(overrides)
    agreement = Agreement(**defaults)
    db_session.add(agreement)
    db_session.commit()
    db_session.refresh(agreement)
    return agreement


def test_list_agreements_empty(client):
    response = client.get("/agreements")

    assert response.status_code == 200
    assert response.json() == []


def test_list_agreements_returns_all_by_default(client, db_session):
    _make_agreement(db_session, owner="Priya", status=AgreementStatus.open)
    _make_agreement(db_session, owner="Marcus", status=AgreementStatus.resolved)

    response = client.get("/agreements")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {a["owner"] for a in body} == {"Priya", "Marcus"}


def test_list_agreements_filters_by_status(client, db_session):
    _make_agreement(db_session, owner="Priya", status=AgreementStatus.open)
    _make_agreement(db_session, owner="Marcus", status=AgreementStatus.resolved)

    open_only = client.get("/agreements", params={"status": "open"}).json()
    resolved_only = client.get("/agreements", params={"status": "resolved"}).json()

    assert [a["owner"] for a in open_only] == ["Priya"]
    assert [a["owner"] for a in resolved_only] == ["Marcus"]


def test_list_agreements_rejects_invalid_status(client):
    response = client.get("/agreements", params={"status": "not-a-status"})

    assert response.status_code == 422
