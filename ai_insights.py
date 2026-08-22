"""
Generates a plain-English insight + recommendation for a detected usage
anomaly, using Groq's free-tier API (OpenAI-compatible chat completions).

No API key? The app still works - get_insight() falls back to a
template-based insight so you can develop and demo offline.

Get a free key at https://console.groq.com (no credit card required).
Set it as an environment variable: GROQ_API_KEY
"""

import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
GROQ_MODEL = "openai/gpt-oss-20b"  # current Groq production model as of Aug 2026 (fast + cheap)


def _get_working_model(api_key: str) -> str:
    """Returns GROQ_MODEL if likely valid, otherwise asks Groq for any
    currently active model so a future deprecation doesn't break the demo."""
    try:
        resp = requests.get(
            GROQ_MODELS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=8,
        )
        resp.raise_for_status()
        available_ids = {m["id"] for m in resp.json().get("data", [])}
        if GROQ_MODEL in available_ids:
            return GROQ_MODEL
        # Prefer any gpt-oss or llama chat model over audio/guard/tts models
        for candidate in available_ids:
            if "gpt-oss" in candidate or "llama" in candidate.lower():
                if "guard" not in candidate and "whisper" not in candidate:
                    return candidate
        return GROQ_MODEL  # fall through, let the actual call surface the error
    except Exception:
        return GROQ_MODEL


def _fallback_insight(building: str, usage: float, baseline: float, timestamp: str) -> str:
    pct = round(((usage - baseline) / baseline) * 100, 1) if baseline else 0
    return (
        f"{building} used {usage:.1f} kWh at {timestamp}, "
        f"{pct}% above its typical baseline of {baseline:.1f} kWh. "
        f"This pattern is consistent with equipment (e.g. HVAC or lighting) "
        f"left running outside normal occupancy hours. Recommended action: "
        f"check building schedules/automation for that time window."
    )


def get_insight(building: str, usage: float, baseline: float, timestamp: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return _fallback_insight(building, usage, baseline, timestamp)

    prompt = (
        f"A campus building called '{building}' recorded an energy usage "
        f"anomaly of {usage:.1f} kWh at {timestamp}, compared to its normal "
        f"baseline of {baseline:.1f} kWh. In 2 short sentences, explain the "
        f"likely cause and one concrete, actionable recommendation for "
        f"campus facilities staff. Be specific and practical."
    )

    try:
        model_to_use = _get_working_model(api_key)
        response = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model_to_use,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.4,
            },
            timeout=15,
        )
        if response.status_code == 404:
            return (
                _fallback_insight(building, usage, baseline, timestamp)
                + f"\n\n(AI model '{model_to_use}' not found on Groq — check "
                "https://console.groq.com/docs/models for current model IDs "
                "and update GROQ_MODEL in ai_insights.py)"
            )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # noqa: BLE001 - want graceful fallback for any API issue
        return _fallback_insight(building, usage, baseline, timestamp) + f"\n\n(AI API unavailable: {exc})"