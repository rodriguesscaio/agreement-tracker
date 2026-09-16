# Agreement Tracker

Agreements made in meetings, chats, and emails — who owns what, by when — quietly get lost the
moment the conversation ends. Agreement Tracker extracts structured commitments from pasted or
uploaded text so they end up in one place instead of buried in a transcript nobody rereads.

Paste a meeting transcript, chat export, or email thread in; get back a list of agreements —
owner, commitment, deadline, and how explicitly it was stated — saved to a database and shown on
a simple dashboard grouped by open vs. resolved.

## How it works

1. **`POST /extract`** accepts raw text (pasted, or an uploaded `.txt` file).
2. The text is cleaned locally (timestamps, "X joined the call" messages, signatures stripped)
   and split into chunks on natural paragraph/speaker-turn boundaries.
3. Each chunk is sent to **OpenAI** with a prompt that asks for *only* a JSON object matching the
   agreement schema below — no prose.
4. Extracted agreements are validated and saved to **PostgreSQL**.
5. **`GET /agreements`** returns them, optionally filtered by `status=open|resolved`.
6. **`/dashboard`** renders a minimal HTML page listing agreements grouped by status, with a form
   to submit new text.

## Tech stack

- **Python 3.11+**, **FastAPI** for the API
- **PostgreSQL** for storage, **SQLAlchemy 2.0** for models, **Alembic** for migrations
- **OpenAI API** (`gpt-4o-mini` by default, configurable) for extraction
- **Jinja2** for the minimal dashboard page (server-rendered, no build step)
- **pytest** for tests, with the OpenAI client faked out so the suite runs with no API key or
  live database beyond a local SQLite file

## MVP scope

This project deliberately does one thing: turn text into structured agreements and let you see
them. In scope:

- Extraction from pasted text or a single uploaded `.txt` file
- Structured storage in Postgres
- Listing agreements, filterable by status
- A read-oriented dashboard

See [Future Work](#future-work) for what's explicitly *not* built yet.

## Database schema

`agreements` table:

| Column                 | Type                         | Notes                                   |
|-------------------------|-------------------------------|------------------------------------------|
| `id`                    | UUID, primary key             |                                          |
| `source_text_excerpt`   | text                           | the snippet the agreement came from     |
| `owner`                 | text                           | who committed                           |
| `commitment`            | text                           | what they committed to                  |
| `deadline`               | date, nullable                | if a deadline was mentioned             |
| `confidence`            | enum: `high` / `medium` / `low` | how explicitly the agreement was stated |
| `status`                | enum: `open` / `resolved`     | defaults to `open`                      |
| `created_at`, `updated_at` | timestamps                 |                                          |

## Project layout

```
app/
  main.py              FastAPI app + router registration
  config.py             Settings (env vars via pydantic-settings)
  database.py           SQLAlchemy engine/session, declarative Base
  models.py              ORM model + enums
  schemas.py             Pydantic request/response schemas
  routers/
    extract.py           POST /extract
    agreements.py         GET /agreements
    dashboard.py           GET /dashboard (HTML)
  services/
    preprocessing.py       Noise stripping + paragraph-based chunking
    extraction.py           OpenAI prompt + call + JSON parsing
  templates/
    dashboard.html          Minimal Jinja dashboard
migrations/               Alembic environment + versions
tests/
  fixtures/sample_meeting.txt   Sample transcript with a few agreements
  fakes.py                       Fake OpenAI client used across tests
  test_extraction_service.py     Unit tests: cleaning, chunking, parsing
  test_extract_endpoint.py        End-to-end: text in -> agreements stored
  test_agreements_endpoint.py      GET /agreements + status filtering
```

## Setup

### 1. Prerequisites

- Python 3.11+
- A running PostgreSQL instance (local, Docker, or hosted)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 2. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configure

```bash
cp .env.example .env
# then edit .env with your OPENAI_API_KEY and DATABASE_URL
```

### 4. Create the database and run migrations

```bash
createdb agreement_tracker   # or create it however you normally do
alembic upgrade head
```

### 5. Run the app

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:8000/dashboard

### 6. Try it end to end

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@tests/fixtures/sample_meeting.txt"

curl http://localhost:8000/agreements?status=open
```

Or just paste text into the form on `/dashboard`.

### 7. Run the tests

```bash
pytest
```

Tests use an in-memory SQLite database and a fake OpenAI client, so they run without network
access, a real database, or an API key.

## Future Work

Explicitly out of scope for this MVP:

- **Live integrations** with Slack, Microsoft Teams, or Google Chat (webhook ingestion instead of
  copy/paste)
- **Auth / multi-user support** (workspaces, permissions, per-user agreement ownership)
- **Notifications** (reminders as a deadline approaches, digest emails)
- Editing/resolving agreements from the dashboard (currently read-only + extraction only)
- Re-extraction / deduplication when the same conversation is pasted twice
