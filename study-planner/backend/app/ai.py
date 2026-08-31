"""
AI layer: wraps the Anthropic Claude API for two jobs:
  1. Turning a raw schedule into a friendly natural-language summary + tips.
  2. Powering the study-strategy chat assistant.

If ANTHROPIC_API_KEY is not set, both functions fall back to solid
rule-based responses so the app still works end-to-end in a demo
without a key.
"""
import os
import json
import httpx

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def _call_claude(system: str, user_message: str, max_tokens: int = 500) -> str | None:
    if not ANTHROPIC_API_KEY:
        return None
    try:
        resp = httpx.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user_message}],
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return "\n".join(parts).strip() or None
    except Exception:
        return None


def summarize_plan(subjects: list[dict], sessions: list[dict], warnings: list[str]) -> str:
    """Produce a natural-language explanation of the generated plan."""
    system = (
        "You are a concise, encouraging study coach. Given a JSON study plan, "
        "write a short (4-6 sentence) summary explaining the prioritization logic "
        "in plain language, and give 1-2 concrete study tips. No headers, no markdown."
    )
    payload = json.dumps({"subjects": subjects, "sessions": sessions[:40], "warnings": warnings})
    ai_text = _call_claude(system, f"Plan data:\n{payload}")
    if ai_text:
        return ai_text
    return _fallback_summary(subjects, sessions, warnings)


def _fallback_summary(subjects: list[dict], sessions: list[dict], warnings: list[str]) -> str:
    if not subjects:
        return "Add some subjects to generate a plan."
    hardest = max(subjects, key=lambda s: s["difficulty"] * s["priority"])
    soonest = min(subjects, key=lambda s: s["exam_date"])
    total_hours = sum(s["hours"] for s in sessions)
    lines = [
        f"Your plan allocates {total_hours:.1f} hours across {len(subjects)} subject(s), "
        f"weighting time by how close each exam is, how hard the subject is, and how you "
        f"prioritized it.",
        f"'{hardest['name']}' gets extra attention given its difficulty/priority, and "
        f"'{soonest['name']}' is scheduled early since its exam ({soonest['exam_date']}) "
        f"is coming up soonest.",
        "Tip: study the hardest material earlier in the day when focus is highest, and "
        "review recently-covered material for 5-10 minutes before starting something new "
        "(spaced repetition beats cramming).",
    ]
    if warnings:
        lines.append("Heads up: " + " ".join(warnings))
    return " ".join(lines)


def chat_reply(user_message: str, context: dict) -> str:
    system = (
        "You are a friendly, practical study coach embedded in a study planner app. "
        "The student may ask about their schedule, request changes, or ask for study "
        "techniques (active recall, spaced repetition, Pomodoro, etc). Keep replies to "
        "2-5 sentences, plain text, no markdown headers."
    )
    payload = json.dumps(context)
    ai_text = _call_claude(system, f"Context:\n{payload}\n\nStudent message: {user_message}")
    if ai_text:
        return ai_text
    return _fallback_chat(user_message)


def _fallback_chat(user_message: str) -> str:
    msg = user_message.lower()
    if "behind" in msg or "missed" in msg or "fall" in msg:
        return (
            "No worries — falling behind happens. Regenerate your plan and the scheduler "
            "will automatically redistribute your remaining hours across the days left "
            "before each exam, weighting urgency higher. Try to protect at least one "
            "session for your most urgent subject tomorrow."
        )
    if "pomodoro" in msg:
        return (
            "The Pomodoro technique: study in focused 25-minute blocks, then take a 5-minute "
            "break. After 4 blocks, take a longer 15-30 minute break. It works well for "
            "sessions of 1+ hours since it keeps focus fresh."
        )
    if "recall" in msg or "memoriz" in msg or "remember" in msg:
        return (
            "Active recall beats re-reading: close the book and try to write down or say "
            "everything you remember about a topic, then check what you missed. Pair it "
            "with spaced repetition — revisit the same topic after 1 day, then 3 days, "
            "then a week."
        )
    return (
        "I can help you adjust your schedule, explain the plan, or suggest study "
        "techniques like active recall, spaced repetition, or the Pomodoro method. "
        "What would be most useful right now?"
    )
