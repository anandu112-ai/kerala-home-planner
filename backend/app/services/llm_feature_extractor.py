import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("kerala_home_planner.services.llm_feature_extractor")

# ---------------------------------------------------------------------------
# LLM Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a construction site condition extractor for Kerala house construction projects.
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

Omit any key that is NOT mentioned or cannot be inferred. Return null for uncertain values.

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
# Keyword fallback — works with NO API key
# ---------------------------------------------------------------------------
# Each entry: (feature_key, feature_value, list_of_keyword_patterns)
# Patterns are matched case-insensitively against the full description text.
# Earlier entries take priority within the same feature_key.

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


def _keyword_extract(text: str) -> dict:
    """
    Pure keyword/regex-based feature extractor.
    Fast, zero API cost, handles typos reasonably well via loose patterns.
    Used when no LLM API key is configured OR as a fallback when LLM fails.
    """
    t = text.lower()
    features: dict = {}

    for feat_key, feat_val, patterns in _KEYWORD_RULES:
        # Skip if we already set a value for this feature (first match wins)
        if feat_key in features:
            continue
        for pattern in patterns:
            if re.search(pattern, t):
                features[feat_key] = feat_val
                logger.debug("Keyword match: %s = %s  (pattern: %s)", feat_key, feat_val, pattern)
                break

    return features


# ---------------------------------------------------------------------------
# LLM config resolution
# ---------------------------------------------------------------------------

def get_llm_config():
    api_key = os.getenv("LLM_API_KEY")
    provider = os.getenv("LLM_PROVIDER")

    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not provider:
        if api_key:
            provider = "openai" if api_key.startswith("sk-") else "gemini"
        elif openai_key:
            provider = "openai"
            api_key = openai_key
        elif gemini_key:
            provider = "gemini"
            api_key = gemini_key
    else:
        provider = provider.lower()
        if not api_key:
            if provider == "openai":
                api_key = openai_key
            elif provider == "gemini":
                api_key = gemini_key

    return api_key, provider


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_features(site_description: str) -> dict:
    """
    Extract site condition features from free-text description.

    Strategy:
      1. Try LLM (Gemini or OpenAI) if an API key is configured.
         LLM handles natural language, spelling mistakes, and context best.
      2. If no API key OR the LLM call fails, fall back to the built-in
         keyword/regex detector — works offline, zero cost, handles
         common phrases and mild typos via loose regex patterns.

    Returns a dict of features, or {} if nothing is detected.
    """
    if not site_description or not site_description.strip():
        return {}

    api_key, provider = get_llm_config()

    # ── Try LLM first ───────────────────────────────────────────────────────
    if api_key:
        prompt = SYSTEM_PROMPT.format(site_description=site_description)
        try:
            if provider == "openai":
                result = _call_openai(prompt, api_key)
            else:
                result = _call_gemini(prompt, api_key)

            if result:
                logger.info("LLM extracted %d features via %s", len(result), provider)
                return result
            else:
                logger.warning("LLM returned empty result — falling back to keyword detector")
        except Exception as e:
            logger.error("LLM call failed (%s): %s — falling back to keyword detector", provider, e)
    else:
        logger.info("No LLM API key configured — using built-in keyword detector")

    # ── Keyword fallback ────────────────────────────────────────────────────
    result = _keyword_extract(site_description)
    logger.info("Keyword detector extracted %d features", len(result))
    return result


# ---------------------------------------------------------------------------
# LLM provider implementations
# ---------------------------------------------------------------------------

def _call_openai(prompt: str, api_key: str) -> dict:
    url = "https://api.openai.com/v1/chat/completions"
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read())
    return _clean_and_parse_json(body["choices"][0]["message"]["content"])


def _call_gemini(prompt: str, api_key: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read())
    return _clean_and_parse_json(body["candidates"][0]["content"]["parts"][0]["text"])


def _clean_and_parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
        normalized = {}
        for key in [
            "vehicle_access", "terrain_type", "road_quality",
            "scenic_view", "distance_from_city", "water_availability",
            "flood_risk", "location_advantage",
        ]:
            if key in parsed and parsed[key] is not None:
                val = parsed[key]
                normalized[key] = bool(val) if key == "scenic_view" else str(val).lower().strip()
        return normalized
    except Exception as e:
        logger.error("Failed to parse LLM JSON: %s | raw: %.200s", e, text)
        return {}
