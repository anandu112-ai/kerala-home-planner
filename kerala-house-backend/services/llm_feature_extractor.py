"""
services/llm_feature_extractor.py
-----------------------------------
Extracts site condition features from free-text user input.

Strategy:
  1. LLM (Gemini or OpenAI) — best accuracy, handles natural language,
     spelling mistakes, and context. Used when API key is configured.
  2. Keyword/regex fallback — zero cost, works offline, no API key needed.
     Handles common phrases and mild typos via loose regex patterns.

Environment variables (set ONE):
  GEMINI_API_KEY   — Google Gemini (recommended, free tier available)
  OPENAI_API_KEY   — OpenAI GPT

Optional:
  LLM_API_KEY      — generic key (provider auto-detected by prefix)
  LLM_PROVIDER     — "gemini" | "openai"
"""

import os
import re
import json
import logging
import urllib.request

logger = logging.getLogger("kerala_house_backend.llm_feature_extractor")


# ---------------------------------------------------------------------------
# LLM Prompt
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """You are a construction site condition extractor for Kerala house construction projects.
Analyze the site description and extract features that affect CONSTRUCTION COST.
Return ONLY a valid JSON object. Do not include markdown, code fences, or any explanation.

Feature extraction guidelines:
- vehicle_access: How easily can construction vehicles (trucks, mixers, cranes) reach the site?
  "good"  = vehicles can reach directly
  "poor"  = vehicles can reach with difficulty (narrow road, partial access)
  "none"  = no vehicle access at all, everything must be carried manually

- terrain_type: What is the ground/slope condition?
  "flat"  = level ground, easy to build
  "hilly" = sloped, hilly, mountainous, valley area, uneven terrain

- road_quality: What is the condition of the road to the site?
  "good"    = paved, wide road
  "average" = narrow or partially paved
  "poor"    = dirt track, damaged road, kutcha road

- scenic_view: Does the site have a scenic/valley/mountain/river view?
  true  = yes (valley view, river view, mountain view, beautiful scenery)
  false = no

- distance_from_city: How far is the site from the nearest town or city?
  "low"    = within town / city limits, close to main road
  "medium" = 5-20 km from town
  "high"   = remote, far from city, isolated, deep village

- water_availability: Is water available at or near the site during construction?
  "good" = well, river, municipal supply nearby
  "poor" = no water source, needs tanker

- flood_risk: Is the site in a flood-prone, low-lying, or waterlogged area?
  "yes" = flood-prone, waterlogged, near river that floods, low-lying
  "no"  = not flood-prone

- location_advantage: Overall location quality (omit if unclear)
  "positive" / "neutral" / "negative"

Omit any key that is NOT mentioned or cannot be inferred.

Site description:
"{site_description}"

Example - "House is in hilly area with beautiful valley view. No vehicle access and road is 1 km away. Far from city.":
{{
  "vehicle_access": "none",
  "terrain_type": "hilly",
  "road_quality": "poor",
  "scenic_view": true,
  "distance_from_city": "high"
}}"""


# ---------------------------------------------------------------------------
# Keyword / regex fallback rules
# ---------------------------------------------------------------------------
# Each entry: (feature_key, feature_value, list_of_patterns)
# Matched case-insensitively. First match per feature_key wins.

_KEYWORD_RULES = [
    # ── vehicle_access ──────────────────────────────────────────────────────
    ("vehicle_access", "none", [
        r"no vehicle.{0,10}(access|road|entry|reach)",
        r"vehicle.{0,10}(cannot|can'?t|no).{0,10}(reach|access|enter)",
        r"(cannot|can'?t|no).{0,10}vehicle",
        r"no.{0,6}(road|access).{0,20}(vehicle|truck|lorry|car)",
        r"(foot|head.?load|manual|carry|walking).{0,20}(only|access|material)",
        r"no.{0,6}access\b",
        r"inaccessible",
        r"road.{0,10}(1|one|2|two|half).{0,6}(km|kilo)",
        r"(far|away).{0,10}(road|highway|main road)",
    ]),
    ("vehicle_access", "poor", [
        r"(poor|bad|difficult|narrow|restricted).{0,20}(vehicle|access|road)",
        r"(vehicle|truck|lorry).{0,20}(difficult|hard|problem|issue)",
        r"narrow.{0,10}(road|lane|path)",
        r"(semi|partial).{0,10}access",
    ]),

    # ── terrain_type ────────────────────────────────────────────────────────
    ("terrain_type", "hilly", [
        r"\b(hill|hilly|hills|slope|sloped|sloping|mountain|mountainous)\b",
        r"\b(valley|mala|ghat|uneven|rocky|elevation|steep|gradient)\b",
        r"(on a|on the).{0,10}(hill|slope|mountain)",
    ]),

    # ── road_quality ────────────────────────────────────────────────────────
    ("road_quality", "poor", [
        r"(poor|bad|broken|damaged|no|kutcha|dirt|mud|unpaved|gravel).{0,10}road",
        r"road.{0,10}(poor|bad|broken|damaged|no|kutcha|dirt|mud|unpaved)",
        r"(no|without).{0,6}(tar|tarred|paved|concrete|black.?top).{0,10}road",
        r"road.{0,6}(not|isn.?t).{0,10}(tar|tarred|paved|good)",
        r"\b(track|footpath|path only)\b",
    ]),
    ("road_quality", "average", [
        r"(narrow|single.?lane|small).{0,10}road",
        r"road.{0,10}(narrow|small|single.?lane)",
        r"(average|ok|okay|decent).{0,10}road",
    ]),

    # ── scenic_view ─────────────────────────────────────────────────────────
    ("scenic_view", True, [
        r"(beautiful|scenic|amazing|gorgeous|nice|lovely|great|stunning).{0,20}(view|scenery|scene|landscape)",
        r"(valley|river|mountain|hill|ocean|sea|lake|backwater).{0,10}view",
        r"view.{0,10}(valley|river|mountain|hill|ocean|sea|lake)",
        r"\b(scenic|panoramic|picturesque)\b",
    ]),

    # ── distance_from_city ──────────────────────────────────────────────────
    ("distance_from_city", "high", [
        r"(far|away|remote|isolated|outskirt|deep|interior).{0,20}(city|town|main road|highway|urban)",
        r"(city|town|main road).{0,20}(far|away|remote|isolated)",
        r"\b(remote|isolated|interior|deep village|rural)\b",
        r"(far from|away from).{0,10}(city|town|main)",
        r"\d+\s*(km|kilo).{0,10}(from|away).{0,10}(city|town|road|highway)",
    ]),
    ("distance_from_city", "medium", [
        r"(moderate|some|bit|little).{0,20}(distance|far|away).{0,20}(city|town)",
        r"(5|6|7|8|9|10|11|12|13|14|15).{0,6}(km|kilo).{0,10}(from|away|to).{0,10}(city|town|road)",
    ]),

    # ── water_availability ──────────────────────────────────────────────────
    ("water_availability", "good", [
        r"(good|enough|plenty|abundant|available|near).{0,20}water",
        r"water.{0,20}(good|available|plenty|enough|near)",
        r"(well|borewell|bore.well|river|stream|canal|municipal).{0,10}(water|supply|nearby|available)",
        r"water.{0,10}(supply|source).{0,10}(nearby|available|good)",
    ]),
    ("water_availability", "poor", [
        r"(no|lack|scarce|poor|shortage|problem).{0,20}water",
        r"water.{0,20}(no|lack|scarce|poor|shortage|problem|issue)",
        r"(need|require).{0,10}(water.tanker|tanker|lorry).{0,10}water",
        r"water.{0,10}(tanker|lorry)",
    ]),

    # ── flood_risk ──────────────────────────────────────────────────────────
    ("flood_risk", "yes", [
        r"\b(flood|flooded|flooding|flood.prone|flood.risk)\b",
        r"(water.?log|waterlog|water.?logging)",
        r"(low.?lying|low lying|low level).{0,20}(area|land|plot)",
        r"(near|beside|adjacent|next).{0,10}(river|stream|nadi|canal).{0,30}(flood|water|rain)",
        r"(rain|monsoon).{0,20}(flood|water.?log|inundat)",
    ]),
]

_VALID_KEYS = [
    "vehicle_access", "terrain_type", "road_quality",
    "scenic_view", "distance_from_city", "water_availability",
    "flood_risk", "location_advantage",
]


# ---------------------------------------------------------------------------
# Keyword fallback
# ---------------------------------------------------------------------------

def _keyword_extract(text: str) -> dict:
    """Pure regex-based extractor. No API key needed."""
    t = text.lower()
    features: dict = {}
    for feat_key, feat_val, patterns in _KEYWORD_RULES:
        if feat_key in features:
            continue
        for pattern in patterns:
            if re.search(pattern, t):
                features[feat_key] = feat_val
                logger.debug("Keyword match: %s=%s (pattern: %s)", feat_key, feat_val, pattern)
                break
    return features


# ---------------------------------------------------------------------------
# Provider resolution
# ---------------------------------------------------------------------------

def _resolve_provider() -> tuple[str | None, str | None]:
    key      = os.getenv("LLM_API_KEY")
    provider = (os.getenv("LLM_PROVIDER") or "").lower() or None
    openai_k = os.getenv("OPENAI_API_KEY")
    gemini_k = os.getenv("GEMINI_API_KEY")

    if not provider:
        if key:
            provider = "openai" if key.startswith("sk-") else "gemini"
        elif openai_k:
            key, provider = openai_k, "openai"
        elif gemini_k:
            key, provider = gemini_k, "gemini"
    else:
        if not key:
            key = openai_k if provider == "openai" else gemini_k

    return key, provider


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_features(site_description: str) -> dict:
    """
    Extract site features from free-text.
    Tries LLM first; falls back to keyword detector automatically.
    """
    if not (site_description or "").strip():
        return {}

    api_key, provider = _resolve_provider()

    # ── Try LLM ─────────────────────────────────────────────────────────────
    if api_key:
        prompt = _PROMPT_TEMPLATE.format(site_description=site_description)
        try:
            raw = (
                _call_openai(prompt, api_key)
                if provider == "openai"
                else _call_gemini(prompt, api_key)
            )
            result = _parse_and_normalize(raw)
            if result:
                logger.info("LLM extracted %d features via %s", len(result), provider)
                return result
            logger.warning("LLM returned empty result — falling back to keyword detector")
        except Exception as exc:
            logger.error("LLM call failed (%s): %s — falling back to keyword detector", provider, exc)
    else:
        logger.info("No LLM API key — using built-in keyword detector")

    # ── Keyword fallback ────────────────────────────────────────────────────
    result = _keyword_extract(site_description)
    logger.info("Keyword detector extracted %d features", len(result))
    return result


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

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
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
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
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
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


def _parse_and_normalize(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = [l for l in text.splitlines() if not l.strip().startswith("```")]
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
