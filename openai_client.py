


"""
openai_client.py — FocusGuardian AI
AI screenshot analysis using Google Gemini Vision.
Includes retry logic, confidence thresholds, caching, and graceful fallback.
"""

import os
import json
import time
import hashlib
import threading
from datetime import datetime
from pathlib import Path

# ── Gemini setup ───────────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    from PIL import Image
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    print("[openai_client] google-generativeai or Pillow not installed.")

# ── Configuration ──────────────────────────────────────────────────────────────
_API_KEY = "AIzaSyAPdGUryn35l3VqXhCWJLVyaeuigf3ia2k"
_MODEL     = "gemini-2.5-flash"
_MAX_RETRY = 3
_RETRY_DELAY = 2          # seconds between retries
_CONF_THRESHOLD = 0.55    # below this → treat as FOCUSED (benefit of the doubt)

# Recent-result cache (avoid re-analyzing identical screenshots)
_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()
_CACHE_MAX  = 50

if _GEMINI_AVAILABLE:
    genai.configure(api_key=_API_KEY)
    _model = genai.GenerativeModel(_MODEL)

# ── Prompt template ────────────────────────────────────────────────────────────
_PROMPT_TEMPLATE = """
You are a strict but fair workplace focus monitor.

The user said they are working on: {user_spec}

Look at this screenshot carefully and decide if the user is FOCUSED or DISTRACTED.

FOCUSED means: the visible content directly relates to their stated task.
  Examples: code editor for a coding task, docs for writing, browser on relevant research.

DISTRACTED means: visible content is clearly unrelated to their task.
  Examples: YouTube, Netflix, social media (Instagram / Twitter / TikTok), online shopping,
  gaming, messaging apps, news feeds unrelated to the task.

Borderline cases (email, Slack, notifications) → lean FOCUSED unless obvious distraction.

Respond ONLY with valid JSON, no markdown fences:
{{
  "status":     "FOCUSED" or "DISTRACTED",
  "reason":     "one sentence describing what is on screen",
  "confidence": 0.0 to 1.0,
  "category":   one of [coding, writing, research, design, social_media, video, messaging, shopping, gaming, news, other],
  "advice":     "one short actionable tip if distracted, else empty string"
}}
"""

# ── Public API ─────────────────────────────────────────────────────────────────
def analyze_screenshot(image_path: str, user_spec: str) -> dict:
    """
    Analyze a screenshot and return a classification dict:
    {status, reason, confidence, category, advice}
    Retries up to _MAX_RETRY times on transient errors.
    Falls back gracefully if Gemini is unavailable.
    """
    if not _GEMINI_AVAILABLE:
        return _fallback("Gemini SDK not installed.")

    if not os.path.exists(image_path):
        return _fallback(f"Screenshot not found: {image_path}")

    # ── Cache check ────────────────────────────────────────────────────────────
    cache_key = _file_hash(image_path)
    with _cache_lock:
        if cache_key in _cache:
            cached = _cache[cache_key].copy()
            cached["from_cache"] = True
            return cached

    # ── Retry loop ─────────────────────────────────────────────────────────────
    last_error = ""
    for attempt in range(1, _MAX_RETRY + 1):
        try:
            result = _call_gemini(image_path, user_spec)

            # Confidence gate
            if result["confidence"] < _CONF_THRESHOLD:
                result["status"] = "FOCUSED"
                result["reason"] += f" (low confidence {result['confidence']:.2f} → defaulting FOCUSED)"

            # Store in cache
            with _cache_lock:
                if len(_cache) >= _CACHE_MAX:
                    oldest = next(iter(_cache))
                    del _cache[oldest]
                _cache[cache_key] = result.copy()

            return result

        except Exception as exc:
            last_error = str(exc)
            print(f"[openai_client] Attempt {attempt}/{_MAX_RETRY} failed: {exc}")
            if attempt < _MAX_RETRY:
                time.sleep(_RETRY_DELAY * attempt)

    return _fallback(f"All retries failed. Last error: {last_error}")


def analyze_batch(image_paths: list[str], user_spec: str) -> list[dict]:
    """Analyze multiple screenshots and return majority-vote result."""
    results = [analyze_screenshot(p, user_spec) for p in image_paths]
    distracted = sum(1 for r in results if r["status"] == "DISTRACTED")
    # Majority wins
    if distracted > len(results) / 2:
        # Return the highest-confidence distracted result
        dist_results = [r for r in results if r["status"] == "DISTRACTED"]
        return sorted(dist_results, key=lambda r: r["confidence"], reverse=True)[0]
    else:
        focused_results = [r for r in results if r["status"] == "FOCUSED"]
        if focused_results:
            return sorted(focused_results, key=lambda r: r["confidence"], reverse=True)[0]
        return results[0]


# ── Internal helpers ───────────────────────────────────────────────────────────
def _call_gemini(image_path: str, user_spec: str) -> dict:
    image  = Image.open(image_path)
    prompt = _PROMPT_TEMPLATE.format(user_spec=user_spec)
    response = _model.generate_content([prompt, image])
    text     = response.text.strip()

    # Strip markdown fences if model adds them
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    # Extract JSON object
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON in response: {text[:200]}")

    parsed = json.loads(text[start:end])

    return {
        "status":     str(parsed.get("status",     "FOCUSED")).upper().strip(),
        "reason":     str(parsed.get("reason",     "Screen analysis complete.")),
        "confidence": float(parsed.get("confidence", 0.8)),
        "category":   str(parsed.get("category",   "other")).lower().strip(),
        "advice":     str(parsed.get("advice",     "")),
    }


def _fallback(reason: str = "AI unavailable") -> dict:
    return {
        "status":     "FOCUSED",
        "reason":     reason,
        "confidence": 0.5,
        "category":   "other",
        "advice":     "Continue working.",
        "from_cache": False,
    }


def _file_hash(path: str) -> str:
    """MD5 of file content for cache keying."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    except Exception:
        return path
    return h.hexdigest()


# ── Self-test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python openai_client.py <image_path> <user_spec>")
        sys.exit(1)
    res = analyze_screenshot(sys.argv[1], sys.argv[2])
    print(json.dumps(res, indent=2))
