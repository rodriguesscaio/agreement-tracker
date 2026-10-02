import uuid
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


def test_resolve_agreement_marks_it_resolved(client, db_session):
    agreement = _make_agreement(db_session, status=AgreementStatus.open)

    response = client.post(f"/agreements/{agreement.id}/resolve")

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"

    db_session.refresh(agreement)
    assert agreement.status == AgreementStatus.resolved


def test_resolve_agreement_redirects_for_html_form_submission(client, db_session):
    agreement = _make_agreement(db_session, status=AgreementStatus.open)

    response = client.post(
        f"/agreements/{agreement.id}/resolve",
        headers={"accept": "text/html"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_resolve_agreement_404s_for_unknown_id(client):
    response = client.post(f"/agreements/{uuid.uuid4()}/resolve")

    assert response.status_code == 404


def test_remind_agreement_sets_reminder_sent_at(client, db_session):
    agreement = _make_agreement(db_session, status=AgreementStatus.open)
    assert agreement.reminder_sent_at is None

    response = client.post(f"/agreements/{agreement.id}/remind")

    assert response.status_code == 200
    assert response.json()["reminder_sent_at"] is not None

    db_session.refresh(agreement)
    assert agreement.reminder_sent_at is not None
    # Sending a reminder is purely a visual flag; it must not change status.
    assert agreement.status == AgreementStatus.open


def test_remind_agreement_redirects_for_html_form_submission(client, db_session):
    agreement = _make_agreement(db_session, status=AgreementStatus.open)

    response = client.post(
        f"/agreements/{agreement.id}/remind",
        headers={"accept": "text/html"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_remind_agreement_404s_for_unknown_id(client):
    response = client.post(f"/agreements/{uuid.uuid4()}/remind")

    assert response.status_code == 404
