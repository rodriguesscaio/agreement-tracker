# Agreement Tracker — Video Script

**Length:** ~3.5 min — one solid single-purpose project with two connected technical beats (deterministic preprocessing measured with real data, and handling unreliable LLM output), plus a live demo moment. Enough real material to earn the time without padding.
**Audience:** mixed (developers + non-technical / recruiters)

## Hook (0:00–0:10)
[screen: Agreement Tracker dashboard open in the browser, the 4 open agreement cards visible]
> Somewhere in a Slack thread right now, someone said "I'll have this done by Friday." Nobody remembers if they did it. This tool fixes that.

## Context (0:10–0:35)
[screen: README.md, scrolled to the "Problem it solves" section]
> Teams talk in Slack, Teams, or email. People say "I'll take this" or "I'll send it by Friday." But that promise gets buried in the chat. Nobody tracks it. So I built Agreement Tracker. You paste in a chat, or upload a file. It reads the text, finds who promised what, and saves it. Then you see it on a simple dashboard, open or resolved.

## Technical walkthrough (0:35–2:50)
[screen: app/services/preprocessing.py, the strip_noise function visible]
> Here's the part I actually want to talk about. Before any text goes to the AI model, it passes through plain Python code first. This code removes noise. Things like timestamps, or messages like "X joined the call." No AI involved. Just simple pattern matching, called regex.

[screen: docs/screenshots/langfuse-raw-uncleaned.png and langfuse-cleaned-preprocessed.png, side by side or flipping between them]
> I wanted a real answer, not a guess. So I ran the same chat twice. Once with the raw text, and once with the cleaned text. I measured it with a tool called Langfuse. It tracks every call to the model, and shows exactly how many tokens you used. Tokens are the units the model charges you for. The raw version used five hundred twenty tokens. The cleaned version used four hundred fifty five. That's real, and it's free. No extra model call. Just Python code, running first.

[screen: app/services/extraction.py, the per-item validation try/except block visible]
> There's a second lesson here too. The model returns a list of agreements as JSON — a structured way to write data as text. Early on, one item in that list was missing a field. My code tried to validate the whole list at once, and it crashed. One bad item broke everything. So I changed it. Now each item gets checked on its own. If one is bad, I skip it, and keep the rest. Small fix. But you only learn this kind of thing when something actually breaks.

## Why it matters (2:50–3:15)
[screen: terminal running `pytest`, or back to the dashboard]
> This is what AI engineering actually looks like, day to day. It's not just calling a model and hoping. It's knowing when plain code is the better tool. And it's building guardrails around a model. Because the model won't always give you exactly what you expect. That mix — solid backend thinking, plus AI on top — is exactly where I want to grow.

## Close (3:15–3:30)
[screen: GitHub repo page, agreement-tracker]
> The full project is open source, link is in the description. If you've ever lost a promise in a group chat, go take a look.

---
**Vocabulary check:**
- **LLM** — the AI model that reads the text and extracts the agreements
- **regex** — a pattern-matching technique for finding and removing text, no AI involved
- **tokens** — the units an LLM API charges you for; roughly, chunks of text
- **JSON** — a structured, text-based way to represent data
- **Langfuse** — a tool that tracks and measures LLM calls (tokens, cost, latency)
- **guardrails** — checks and rules that catch a model's mistakes before they cause bigger problems
