"""Cheap, local text cleanup that runs before anything is sent to OpenAI.

Stripping obvious noise in Python (instead of asking the model to ignore it)
keeps extraction prompts shorter and cheaper.
"""

import re

TIMESTAMP_PATTERNS = [
    re.compile(r"^\[?\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm)?\]?\s*[-–—]?\s*"),
    re.compile(r"^\(\d{1,2}:\d{2}(:\d{2})?\)\s*"),
]

SYSTEM_MESSAGE_PATTERN = re.compile(
    r"^.{0,60}\b(joined|left|has joined|has left)\b.{0,20}\b(the call|the meeting|the chat|the room)\b.*$",
    re.IGNORECASE,
)

CALL_LIFECYCLE_PATTERN = re.compile(
    r"^(recording (started|stopped)|meeting (started|ended)|call (started|ended))\.?\s*$",
    re.IGNORECASE,
)

SIGNATURE_STARTERS = re.compile(
    r"^(--\s*$|best regards,?$|kind regards,?$|regards,?$|best,?$|thanks,?$|"
    r"thank you,?$|cheers,?$|sent from my (iphone|android|mobile).*$)",
    re.IGNORECASE,
)


def strip_noise(text: str) -> str:
    """Remove timestamps, "X joined the call" system messages, and trailing
    signature blocks. Runs line by line so it works on transcripts, chat
    exports, and emails alike.
    """
    cleaned_lines: list[str] = []
    in_signature = False

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            in_signature = False
            cleaned_lines.append("")
            continue

        if in_signature:
            continue

        if SIGNATURE_STARTERS.match(line):
            in_signature = True
            continue

        if SYSTEM_MESSAGE_PATTERN.match(line) or CALL_LIFECYCLE_PATTERN.match(line):
            continue

        for pattern in TIMESTAMP_PATTERNS:
            line = pattern.sub("", line).strip()

        if line:
            cleaned_lines.append(line)

    # Collapse runs of blank lines left behind by stripped-out noise.
    result_lines: list[str] = []
    previous_blank = False
    for line in cleaned_lines:
        blank = line == ""
        if blank and previous_blank:
            continue
        result_lines.append(line)
        previous_blank = blank

    return "\n".join(result_lines).strip()


def chunk_text(text: str, max_chars: int = 4000) -> list[str]:
    """Split text on paragraph / speaker-turn boundaries (blank lines) and
    greedily pack paragraphs into chunks up to ``max_chars``. Never splits a
    paragraph mid-sentence, even if that means a single chunk runs over the
    limit.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        paragraph_len = len(paragraph)
        if current and current_len + paragraph_len + 2 > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += paragraph_len + 2

    if current:
        chunks.append("\n\n".join(current))

    return chunks
