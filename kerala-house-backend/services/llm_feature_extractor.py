import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("kerala_home_planner.services.llm_feature_extractor")

try:
    from app.services.text_normalizer import normalize_text, get_llm_config
except ImportError:
    from services.text_normalizer import normalize_text, get_llm_config

# ---------------------------------------------------------------------------
# LLM Prompt for Feature Extraction
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an AI feature extractor for construction site descriptions and building material quality in Kerala.
Analyze the provided clean site description and extract the Construction and Site features.

Return ONLY a valid JSON object. Do not include markdown, code fences, or any explanation.
All values should be normalized strings or booleans, or null if not mentioned.

JSON Schema:
{{
  "construction_features": {{
    "material_quality": "basic" | "standard" | "premium" | "luxury" | null,
    "flooring_quality": "basic" | "standard" | "premium" | "luxury" | null,
    "wood_work_quality": "none" | "minimal" | "standard" | "premium" | null,
    "kitchen_specification": "basic" | "modular" | "premium_modular" | null,
    "bathroom_quality": "basic" | "standard" | "premium" | null,
    "electrical_work": "standard" | "premium" | null,
    "construction_grade": "standard" | "premium" | "luxury" | null,
    "premium_features": ["solar", "pool", "automation", "landscaping"] (array of strings, empty if none)
  }},
  "site_features": {{
    "terrain": "flat" | "hilly" | "sloped" | null,
    "road_accessibility": "good" | "average" | "poor" | null,
    "vehicle_access": "good" | "poor" | "none" | null,
    "location_advantage": "positive" | "neutral" | "negative" | null,
    "scenic_view": true | false | null,
    "flood_risk": "high" | "low" | "none" | null
  }}
}}

Guidelines for semantic understanding:
- "far from main road", "remote location", "no proper transportation" -> vehicle_access: "poor", road_accessibility: "poor".
- "near flood area", "low lying", "waterlogged" -> flood_risk: "high".
- "hilly area", "sloped ground", "mountains" -> terrain: "hilly".
- "granite flooring", "marble flooring" -> flooring_quality: "luxury" (marble/granite is luxury).
- "premium tiles" -> flooring_quality: "premium".
- "luxury kitchen", "premium modular" -> kitchen_specification: "premium_modular".
- "modular kitchen" -> kitchen_specification: "modular".
- "high quality wood work", "teak wood" -> wood_work_quality: "premium".
- "premium fittings", "automated" -> electrical_work: "premium".
- "premium construction", "luxury grade" -> construction_grade: "luxury" or "premium".

Input text:
"{site_description}"
"""

# ---------------------------------------------------------------------------
# Rich Keyword Fallback — Offline / API Error Fallback
# ---------------------------------------------------------------------------
def _keyword_extract(text: str) -> dict:
    """
    Advanced regex-based fallback extractor when LLM API keys are missing or calls fail.
    Ensures correct structure mapping and handles typos.
    """
    t = text.lower()
    
    # Initialize defaults
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

    # ── Location Advantage / Distance ──
    if re.search(r"\b(remote|isolated|deep village|interior|far from town|far from city)\b", t):
        s_features["location_advantage"] = "negative"
    elif re.search(r"\b(highway proximity|near city|near town|close to city|close to town|prime location)\b", t):
        s_features["location_advantage"] = "positive"

    # ── Scenic View ──
    if re.search(r"\b(view|scenic|scenery|panoramic|valley view|river view|mountain view|good view|beautiful view)\b", t):
        s_features["scenic_view"] = True

    # ── Flood Risk ──
    if re.search(r"\b(flood|flooded|flooding|waterlog|waterlogging|low.?lying|low lying|river side|near river)\b", t):
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
    if re.search(r"\b(luxury kitchn|luxury kitchen|premium modular kitchen|high-end modular kitchen)\b", t):
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

    # ── Premium features / Addons list ──
    p_addons = []
    if "solar" in t:
        p_addons.append("solar")
    if "pool" in t or "swimming" in t:
        p_addons.append("pool")
    if "automation" in t or "smart home" in t:
        p_addons.append("automation")
    if "landscaping" in t or "garden" in t:
        p_addons.append("landscaping")
    c_features["premium_features"] = p_addons

    return {
        "construction_features": c_features,
        "site_features": s_features
    }

# ---------------------------------------------------------------------------
# Public Feature Extraction Endpoint
# ---------------------------------------------------------------------------
def extract_features(site_description: str) -> dict:
    """
    Extract construction and site features from site description text.
    1. Call Text Normalizer to resolve typos and normalize text.
    2. Try LLM (Gemini or OpenAI) with corrected text.
    3. Fall back to Regex-based extraction if LLM fails or keys are missing.
    """
    if not site_description or not site_description.strip():
        return {
            "corrected_text": "",
            "detected_features": {},
            "construction_features": {},
            "site_features": {}
        }

    # Step 1: Normalize text (handles spell check and formatting)
    corrected_text = normalize_text(site_description)
    if not corrected_text:
        corrected_text = site_description

    api_key, provider = get_llm_config()

    # Step 2: Try LLM extraction
    if api_key:
        prompt = SYSTEM_PROMPT.format(site_description=corrected_text)
        try:
            model = os.getenv("LLM_MODEL")
            if provider == "openai":
                if not model:
                    model = "gpt-4o-mini"
                result = _call_openai(prompt, api_key, model)
            else:
                if not model:
                    model = "gemini-2.5-flash"
                result = _call_gemini(prompt, api_key, model)

            if result and ("construction_features" in result or "site_features" in result):
                logger.info("LLM successfully extracted features using provider: %s", provider)
                
                # Format to flat detected_features for user format
                detected_features = {}
                # Merge construction features
                c_feats = result.get("construction_features") or {}
                for k, v in c_feats.items():
                    if v is not None:
                        # map keys logically
                        key_map = {
                            "material_quality": "construction_quality",
                            "flooring_quality": "flooring"
                        }
                        mapped_key = key_map.get(k, k)
                        detected_features[mapped_key] = v

                # Merge site features
                s_feats = result.get("site_features") or {}
                for k, v in s_feats.items():
                    if v is not None:
                        detected_features[k] = v

                return {
                    "corrected_text": corrected_text,
                    "detected_features": detected_features,
                    "construction_features": c_feats,
                    "site_features": s_feats
                }
            else:
                logger.warning("LLM returned empty or malformed feature response — falling back to keyword extractor")
        except Exception as e:
            logger.error("LLM extraction failed (%s): %s — falling back to keyword extractor", provider, e)
    else:
        logger.info("No LLM key configured for feature extraction — using keyword extractor fallback")

    # Step 3: Fall back to Regex keyword extraction
    raw_feats = _keyword_extract(corrected_text)
    
    # Flatten detected_features for the user format
    detected_features = {}
    for k, v in raw_feats["construction_features"].items():
        if v is not None:
            key_map = {"material_quality": "construction_quality", "flooring_quality": "flooring"}
            detected_features[key_map.get(k, k)] = v
    for k, v in raw_feats["site_features"].items():
        if v is not None:
            detected_features[k] = v

    return {
        "corrected_text": corrected_text,
        "detected_features": detected_features,
        "construction_features": raw_feats["construction_features"],
        "site_features": raw_feats["site_features"]
    }

# ---------------------------------------------------------------------------
# LLM Providers for Feature Extraction
# ---------------------------------------------------------------------------
def _call_openai(prompt: str, api_key: str, model: str) -> dict:
    url = "https://api.openai.com/v1/chat/completions"
    data = {
        "model": model,
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
    raw_content = body["choices"][0]["message"]["content"]
    return _clean_and_parse_json(raw_content)

def _call_gemini(prompt: str, api_key: str, model: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
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
    raw_content = body["candidates"][0]["content"]["parts"][0]["text"]
    return _clean_and_parse_json(raw_content)

def _clean_and_parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except Exception as e:
        logger.error("Failed to parse LLM JSON response: %s | text: %s", e, text)
        return {}
