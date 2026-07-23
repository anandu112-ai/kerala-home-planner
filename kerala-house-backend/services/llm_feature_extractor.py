"""
services/llm_feature_extractor.py
----------------------------------
Sends the user's site_description to an LLM (Gemini or OpenAI) and parses
the returned JSON into a structured feature dict.

Environment variables (set one pair):
  GEMINI_API_KEY   — Google Gemini (recommended, free tier available)
  OPENAI_API_KEY   — OpenAI GPT

Optional overrides:
  LLM_API_KEY      — generic key (auto-detect provider by prefix)
  LLM_PROVIDER     — "gemini" | "openai"  (force a specific provider)

If no key is configured the function returns {} and the price adjustment
engine applies zero adjustment (graceful fallback — no crash).
"""

import os
import json
import logging
import urllib.request

logger = logging.getLogger("kerala_house_backend.llm_feature_extractor")

# ── Prompt ─────────────────────────────────────────────────────────────────
_PROMPT_TEMPLATE = """You are a real estate site condition extractor for Kerala properties.
Analyze the site description below and return ONLY a valid JSON object.
Do NOT wrap it in markdown code fences or add any explanation.

Allowed keys and values:
  vehicle_access   : "good" | "poor" | "none"
  terrain_type     : "flat" | "hilly"
  road_quality     : "good" | "average" | "poor"
  scenic_view      : true | false
  distance_from_city: "low" | "medium" | "high"
  water_availability: "good" | "poor"
  flood_risk       : "yes" | "no"
  location_advantage: "positive" | "neutral" | "negative"

Omit any key that is not clearly mentioned.

Site description:
"{site_description}"

Example output:
{{
  "vehicle_access": "none",
  "terrain_type": "hilly",
  "scenic_view": true,
  "road_quality": "poor"
}}"""

_VALID_KEYS = [
    "vehicle_access",
    "terrain_type",
    "road_quality",
    "scenic_view",
    "distance_from_city",
    "water_availability",
    "flood_risk",
    "location_advantage",
]


# ── Provider resolution ─────────────────────────────────────────────────────
def _resolve_provider() -> tuple[str | None, str | None]:
    """Return (api_key, provider) from environment variables."""
    key     = os.getenv("LLM_API_KEY")
    provider = (os.getenv("LLM_PROVIDER") or "").lower() or None

    openai_key  = os.getenv("OPENAI_API_KEY")
    gemini_key  = os.getenv("GEMINI_API_KEY")

    if not provider:
        if key:
            provider = "openai" if key.startswith("sk-") else "gemini"
        elif openai_key:
            key, provider = openai_key, "openai"
        elif gemini_key:
            key, provider = gemini_key, "gemini"
    else:
        if not key:
            key = openai_key if provider == "openai" else gemini_key

    return key, provider


# ── Public API ──────────────────────────────────────────────────────────────
def extract_features(site_description: str) -> dict:
    """
    Extract site condition features from free-text description.
    Returns an empty dict on any failure (graceful degradation).
    """
    if not (site_description or "").strip():
        return {}

    api_key, provider = _resolve_provider()
    if not api_key:
        logger.warning("No LLM API key configured — skipping site analysis.")
        return {}

    prompt = _PROMPT_TEMPLATE.format(site_description=site_description)

    try:
        raw = (
            _call_openai(prompt, api_key)
            if provider == "openai"
            else _call_gemini(prompt, api_key)
        )
        return _parse_and_normalize(raw)
    except Exception as exc:
        logger.error("LLM call failed (%s): %s", provider, exc, exc_info=True)
        return {}


# ── Provider implementations ────────────────────────────────────────────────
def _call_openai(prompt: str, api_key: str) -> str:
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"]


def _call_gemini(prompt: str, api_key: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read())
    return body["candidates"][0]["content"]["parts"][0]["text"]


# ── JSON normalisation ──────────────────────────────────────────────────────
def _parse_and_normalize(text: str) -> dict:
    text = text.strip()
    # Strip accidental markdown fences
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Cannot parse LLM JSON: %s | raw: %.200s", exc, text)
        return {}

    normalized: dict = {}
    for key in _VALID_KEYS:
        val = parsed.get(key)
        if val is None:
            continue
        normalized[key] = bool(val) if key == "scenic_view" else str(val).lower().strip()

    return normalized
