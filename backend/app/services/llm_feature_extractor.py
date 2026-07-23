import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("kerala_home_planner.services.llm_feature_extractor")

SYSTEM_PROMPT = """You are a real estate feature extractor. Analyze the following site description and extract the features.
Return ONLY a valid JSON object. Do not include any markdown format (like ```json), other text, or explanations.

Allowed values for each feature:
- vehicle_access: "good", "poor", "none" (if not mentioned, omit the key or return null)
- terrain_type: "flat", "hilly" (if not mentioned, omit the key or return null)
- road_quality: "good", "average", "poor" (if not mentioned, omit the key or return null)
- scenic_view: true, false (if not mentioned, omit the key or return null)
- distance_from_city: "low", "medium", "high" (if not mentioned, omit the key or return null)
- water_availability: "good", "poor" (if not mentioned, omit the key or return null)
- flood_risk: "yes", "no" (if not mentioned, omit the key or return null)
- location_advantage: "positive", "neutral", "negative" (if not mentioned, omit the key or return null)

Site description:
"{site_description}"

Example Output:
{{
  "vehicle_access": "none",
  "terrain_type": "hilly",
  "scenic_view": true,
  "location_advantage": "positive"
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
