"""
llm_feature_extractor.py
Optimised version — single LLM call handles both text normalisation AND feature
extraction, cutting latency roughly in half compared to the previous two-call design.
Falls back instantly to a rich regex extractor when no LLM key is set.
"""
import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("kerala_home_planner.services.llm_feature_extractor")

try:
    from app.services.text_normalizer import clean_text_local, get_llm_config
except ImportError:
    from services.text_normalizer import clean_text_local, get_llm_config

# ---------------------------------------------------------------------------
# COMBINED prompt — normalise + extract in one shot
# ---------------------------------------------------------------------------
COMBINED_PROMPT = """You are an AI assistant for Kerala property construction analysis.
Given the raw user-typed site description (which may contain typos), do TWO things:
1. Return a corrected/normalised version of the text (fix typos, keep meaning identical).
2. Extract construction and site features as a structured JSON.

Return ONLY this JSON (no markdown, no code fences, no explanation):
{{
  "corrected_text": "<normalised description here>",
  "construction_features": {{
    "material_quality": "basic"|"standard"|"premium"|"luxury"|null,
    "flooring_quality": "basic"|"standard"|"premium"|"luxury"|null,
    "wood_work_quality": "none"|"minimal"|"standard"|"premium"|null,
    "kitchen_specification": "basic"|"modular"|"premium_modular"|null,
    "bathroom_quality": "basic"|"standard"|"premium"|null,
    "electrical_work": "standard"|"premium"|null,
    "construction_grade": "standard"|"premium"|"luxury"|null,
    "premium_features": []
  }},
  "site_features": {{
    "terrain": "flat"|"hilly"|"sloped"|null,
    "road_accessibility": "good"|"average"|"poor"|null,
    "vehicle_access": "good"|"poor"|"none"|null,
    "location_advantage": "positive"|"neutral"|"negative"|null,
    "scenic_view": true|false|null,
    "flood_risk": "high"|"low"|"none"|null
  }}
}}

Guidelines:
- "far from road", "no vehicle access", "head-load" → vehicle_access:"none", road_accessibility:"poor"
- "near flood", "low lying", "waterlogged" → flood_risk:"high"
- "hilly", "sloped", "mountain" → terrain:"hilly"
- "marble"/"granite" flooring → flooring_quality:"luxury"
- "premium tiles"/"vitrified" → flooring_quality:"premium"
- "luxury kitchen"/"premium modular" → kitchen_specification:"premium_modular"
- "modular kitchen" → kitchen_specification:"modular"
- "teak wood"/"high quality wood" → wood_work_quality:"premium"
- "automation"/"smart switches" → electrical_work:"premium"
- premium_features: include "solar","pool","automation","landscaping" only if mentioned

Raw input: "{site_description}"
"""

# ---------------------------------------------------------------------------
# Rich Keyword Fallback — fully offline, no API needed
# ---------------------------------------------------------------------------
def _keyword_extract(text: str) -> dict:
    """Advanced regex-based fallback when LLM is unavailable or times out."""
    t = text.lower()

    c_features = {
        "material_quality": None,
        "flooring_quality": None,
        "wood_work_quality": None,
        "kitchen_specification": None,
        "bathroom_quality": None,
        "electrical_work": None,
        "construction_grade": None,
        "premium_features": []
    }
    s_features = {
        "terrain": None,
        "road_accessibility": None,
        "vehicle_access": None,
        "location_advantage": None,
        "scenic_view": False,
        "flood_risk": None
    }

    # ── Site Terrain ──
    if re.search(r"\b(hill|hilly|mountain|slope|sloped|sloping|elevation|steep|gradient|uneven|valley)\b", t):
        s_features["terrain"] = "hilly"
    elif re.search(r"\b(flat|level|plain)\b", t):
        s_features["terrain"] = "flat"

    # ── Vehicle Access & Road Quality ──
    if re.search(r"(no.{0,10}(vehicle|car|truck|lorry|access|road))|(\bhead.?load\b)|(\bmanual carry\b)|\binaccessible\b", t):
        s_features["vehicle_access"] = "none"
        s_features["road_accessibility"] = "poor"
    elif re.search(r"(poor|bad|difficult|narrow|restricted|far from).{0,15}(vehicle|access|road|highway|transport)", t) or re.search(r"\b(narrow|single.?lane).{0,10}(road|lane)\b", t):
        s_features["vehicle_access"] = "poor"
        s_features["road_accessibility"] = "poor"
    elif re.search(r"\b(good|easy|direct|wide).{0,10}(access|road|highway)\b", t):
        s_features["vehicle_access"] = "good"
        s_features["road_accessibility"] = "good"

    # ── Location Advantage ──
    if re.search(r"\b(remote|isolated|deep village|interior|far from town|far from city)\b", t):
        s_features["location_advantage"] = "negative"
    elif re.search(r"\b(highway proximity|near city|near town|close to city|close to town|prime location)\b", t):
        s_features["location_advantage"] = "positive"

    # ── Scenic View ──
    if re.search(r"\b(view|scenic|scenery|panoramic|valley view|river view|mountain view|good view|beautiful view)\b", t):
        s_features["scenic_view"] = True

    # ── Flood Risk ──
    if re.search(r"\b(flood|flooded|flooding|waterlog|waterlogg|low.?lying|low lying|river side|near river)\b", t):
        s_features["flood_risk"] = "high"

    # ── Material Quality & Construction Grade ──
    if re.search(r"\b(luxury|ultra-premium|elite)\b", t):
        c_features["material_quality"] = "luxury"
        c_features["construction_grade"] = "luxury"
    elif re.search(r"\b(premium|high quality|superior)\b", t):
        c_features["material_quality"] = "premium"
        c_features["construction_grade"] = "premium"
    elif re.search(r"\b(basic|cheap|economy|budget)\b", t):
        c_features["material_quality"] = "basic"

    # ── Flooring Quality ──
    if re.search(r"\b(marble|granite)\b", t):
        c_features["flooring_quality"] = "luxury"
    elif re.search(r"\b(premium tile|vitrified|tiles|tiling)\b", t):
        c_features["flooring_quality"] = "premium"
    elif re.search(r"\b(ceramic|cement flooring|basic flooring)\b", t):
        c_features["flooring_quality"] = "basic"

    # ── Woodwork ──
    if re.search(r"\b(teak|mahogany|high quality wood|premium wood|wood work)\b", t):
        c_features["wood_work_quality"] = "premium"
    elif re.search(r"\b(standard woodwork|semi-furnished)\b", t):
        c_features["wood_work_quality"] = "standard"

    # ── Kitchen Specification ──
    if re.search(r"\b(luxury kitchen|premium modular kitchen|high-end modular kitchen)\b", t):
        c_features["kitchen_specification"] = "premium_modular"
    elif re.search(r"\b(modular kitchen|kitchn|kitchen)\b", t):
        c_features["kitchen_specification"] = "modular"

    # ── Bathroom Quality ──
    if re.search(r"\b(luxury bath|premium sanitary|concealed plumbing)\b", t):
        c_features["bathroom_quality"] = "premium"
    elif re.search(r"\b(basic bath|simple plumbing)\b", t):
        c_features["bathroom_quality"] = "basic"

    # ── Electrical Work ──
    if re.search(r"\b(automation|smart switches|3-phase|three phase)\b", t):
        c_features["electrical_work"] = "premium"

    # ── Premium Addons ──
    p_addons = []
    if "solar" in t:                            p_addons.append("solar")
    if "pool" in t or "swimming" in t:          p_addons.append("pool")
    if "automation" in t or "smart home" in t:  p_addons.append("automation")
    if "landscaping" in t or "garden" in t:     p_addons.append("landscaping")
    c_features["premium_features"] = p_addons

    return {"construction_features": c_features, "site_features": s_features}


# ---------------------------------------------------------------------------
# Single-shot LLM callers (combined normalise + extract)
# ---------------------------------------------------------------------------
def _call_openai_combined(prompt: str, api_key: str, model: str) -> dict:
    url = "https://api.openai.com/v1/chat/completions"
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 512,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        body = json.loads(resp.read())
    raw = body["choices"][0]["message"]["content"]
    return _parse_json(raw)


def _call_gemini_combined(prompt: str, api_key: str, model: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
            "maxOutputTokens": 512,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        body = json.loads(resp.read())
    raw = body["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_json(raw)


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except Exception as e:
        logger.error("Failed to parse LLM JSON: %s | snippet: %.200s", e, text)
        return {}


# ---------------------------------------------------------------------------
# Public API — drop-in replacement for the old extract_features()
# ---------------------------------------------------------------------------
def extract_features(site_description: str) -> dict:
    """
    Normalise the site description and extract construction/site features.

    Speed improvements vs. previous implementation:
    - One LLM call instead of two (normalise + extract merged).
    - Reduced timeout 8 s (was 10–15 s).
    - Faster default models (gemini-2.0-flash / gpt-4o-mini).
    - Immediate fallback to offline regex on any exception.
    """
    if not site_description or not site_description.strip():
        return {
            "corrected_text": "",
            "detected_features": {},
            "construction_features": {},
            "site_features": {}
        }

    api_key, provider = get_llm_config()

    # ── Attempt single combined LLM call ──
    if api_key:
        prompt = COMBINED_PROMPT.format(site_description=site_description.strip())
        try:
            model = os.getenv("LLM_MODEL")
            if provider == "openai":
                model = model or "gpt-4o-mini"
                result = _call_openai_combined(prompt, api_key, model)
            else:
                # gemini-2.0-flash is significantly faster than gemini-2.5-flash
                model = model or "gemini-2.0-flash"
                result = _call_gemini_combined(prompt, api_key, model)

            if result and ("construction_features" in result or "site_features" in result):
                logger.info("Combined LLM call succeeded (provider=%s model=%s)", provider, model)
                corrected_text = result.get("corrected_text", site_description).strip() or site_description
                c_feats = result.get("construction_features") or {}
                s_feats = result.get("site_features") or {}

                # Build flat detected_features map
                detected_features = {}
                key_map = {"material_quality": "construction_quality", "flooring_quality": "flooring"}
                for k, v in c_feats.items():
                    if v is not None:
                        detected_features[key_map.get(k, k)] = v
                for k, v in s_feats.items():
                    if v is not None:
                        detected_features[k] = v

                return {
                    "corrected_text": corrected_text,
                    "detected_features": detected_features,
                    "construction_features": c_feats,
                    "site_features": s_feats,
                }
            else:
                logger.warning("Combined LLM returned empty/malformed JSON — using regex fallback")
        except Exception as e:
            logger.warning("Combined LLM call failed (%s): %s — using regex fallback", provider, e)
    else:
        logger.info("No LLM key — using fast regex extractor")

    # ── Offline regex fallback (instant) ──
    corrected_text = clean_text_local(site_description)
    raw_feats = _keyword_extract(corrected_text)

    detected_features = {}
    key_map = {"material_quality": "construction_quality", "flooring_quality": "flooring"}
    for k, v in raw_feats["construction_features"].items():
        if v is not None:
            detected_features[key_map.get(k, k)] = v
    for k, v in raw_feats["site_features"].items():
        if v is not None:
            detected_features[k] = v

    return {
        "corrected_text": corrected_text,
        "detected_features": detected_features,
        "construction_features": raw_feats["construction_features"],
        "site_features": raw_feats["site_features"],
    }
