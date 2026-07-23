import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("kerala_home_planner.services.llm_feature_extractor")

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
  "medium" = 5–20 km from town
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

Example — "House is in hilly area with beautiful valley view. No vehicle access and road is 1 km away. Far from city.":
{{
  "vehicle_access": "none",
  "terrain_type": "hilly",
  "road_quality": "poor",
  "scenic_view": true,
  "distance_from_city": "high"
}}"""

def get_llm_config():
    """
    Resolves API key and provider from environment variables.
    Supports LLM_API_KEY, LLM_PROVIDER, OPENAI_API_KEY, and GEMINI_API_KEY.
    """
    api_key = os.getenv("LLM_API_KEY")
    provider = os.getenv("LLM_PROVIDER")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    # Auto-detect provider if not explicitly set
    if not provider:
        if api_key:
            if api_key.startswith("sk-"):
                provider = "openai"
            else:
                provider = "gemini"
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

def extract_features(site_description: str) -> dict:
    """
    Extracts features from the site description text using an LLM.
    Returns a dictionary of features if successful, or an empty dictionary if not available.
    """
    if not site_description or not site_description.strip():
        return {}

    api_key, provider = get_llm_config()
    if not api_key:
        logger.warning("LLM API key not configured. Skipping feature extraction.")
        return {}

    prompt = SYSTEM_PROMPT.format(site_description=site_description)

    try:
        if provider == "openai":
            return _call_openai(prompt, api_key)
        else:
            return _call_gemini(prompt, api_key)
    except Exception as e:
        logger.error(f"Error calling LLM API ({provider}): {e}", exc_info=True)
        return {}

def _call_openai(prompt: str, api_key: str) -> dict:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        res_body = json.loads(response.read().decode("utf-8"))
        content = res_body["choices"][0]["message"]["content"]
        return _clean_and_parse_json(content)

def _call_gemini(prompt: str, api_key: str) -> dict:
    # Use gemini-2.5-flash for feature extraction
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        res_body = json.loads(response.read().decode("utf-8"))
        content = res_body["candidates"][0]["content"]["parts"][0]["text"]
        return _clean_and_parse_json(content)

def _clean_and_parse_json(text: str) -> dict:
    text = text.strip()
    # Remove markdown code blocks if the LLM still wrapped it
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    
    try:
        parsed = json.loads(text)
        # Normalize and filter out invalid/null keys
        normalized = {}
        for key in [
            "vehicle_access", "terrain_type", "road_quality", 
            "scenic_view", "distance_from_city", "water_availability", 
            "flood_risk", "location_advantage"
        ]:
            if key in parsed and parsed[key] is not None:
                val = parsed[key]
                if key == "scenic_view":
                    normalized[key] = bool(val)
                else:
                    normalized[key] = str(val).lower().strip()
        return normalized
    except Exception as e:
        logger.error(f"Failed to parse JSON output from LLM: {text}. Error: {e}")
        return {}
