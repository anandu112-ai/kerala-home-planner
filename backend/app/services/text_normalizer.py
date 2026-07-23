import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("kerala_home_planner.services.text_normalizer")

# Local correction mapping for common typos (fast, offline fallback)
LOCAL_TYPO_MAP = {
    "vehical": "vehicle",
    "acces": "access",
    "arrea": "area",
    "areaa": "area",
    "kitchn": "kitchen",
    "floring": "flooring",
    "frm": "from",
    "hillyy": "hilly",
    "woodworkk": "woodwork",
    "bathrom": "bathroom",
    "electrikal": "electrical",
    "bthroom": "bathroom",
    "bedrom": "bedroom",
    "constration": "construction",
    "constuction": "construction",
    "floare": "floor",
    "flor": "floor",
    "granit": "granite",
    "marbel": "marble",
    "tilees": "tiles",
}

def clean_text_local(text: str) -> str:
    """Fast local spell correction for common typos."""
    if not text:
        return ""
    words = text.split()
    cleaned = []
    for word in words:
        # Strip trailing punctuation for correction check
        match = re.match(r'^([^\w]*)([\w\'-]+)([^\w]*)$', word)
        if match:
            prefix, core, suffix = match.groups()
            core_lower = core.lower()
            if core_lower in LOCAL_TYPO_MAP:
                core = LOCAL_TYPO_MAP[core_lower]
            word = f"{prefix}{core}{suffix}"
        cleaned.append(word)
    return " ".join(cleaned)

def get_llm_config():
    """Resolve LLM API key and provider from environment variables."""
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

def normalize_text(text: str) -> str:
    """
    Corrects spelling mistakes and normalizes the user text.
    Uses the configured LLM for high-accuracy semantic normalization first.
    Falls back to a local rule-based corrector on failure.
    """
    if not text or not text.strip():
        return ""

    api_key, provider = get_llm_config()

    if not api_key:
        logger.info("No LLM key for text normalization. Using local cleaner.")
        return clean_text_local(text)

    prompt = f"""You are a construction text normalizer. Correct spelling, grammar, and typos.
Keep the meaning identical. Output ONLY the corrected text. No quotes, explanation, or code blocks.

Raw input: "{text}"
Normalized:"""

    try:
        model = os.getenv("LLM_MODEL")
        if provider == "openai":
            if not model:
                model = "gpt-4o-mini"
            corrected = _call_openai_text(prompt, api_key, model)
        else:
            if not model:
                model = "gemini-2.5-flash"
            corrected = _call_gemini_text(prompt, api_key, model)

        if corrected and corrected.strip():
            result = corrected.strip().replace('"', '')
            logger.info("LLM text normalizer: '%s' -> '%s'", text, result)
            return result
    except Exception as e:
        logger.error("LLM text normalization failed: %s. Using local fallback.", e)

    return clean_text_local(text)

def _call_openai_text(prompt: str, api_key: str, model: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"]

def _call_gemini_text(prompt: str, api_key: str, model: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
    return body["candidates"][0]["content"]["parts"][0]["text"]
