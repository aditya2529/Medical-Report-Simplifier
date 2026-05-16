import os
import re
import time
import base64
import random
import logging
import groq
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Groq vision model (Llama 4 Scout supports images)
_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
# Groq text model — 8B is fast for English
_TEXT_MODEL   = "llama-3.1-8b-instant"
# Larger model for non-English (Devanagari, etc.) where 8B is too weak
_MULTILINGUAL_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Audit #23 — bounded retries on rate-limit, capped at ~7s wall time across
# three attempts so a queued Reddit user never blocks longer than the LLM call.
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0   # seconds — 1s, 2s, 4s exponential
_REQUEST_TIMEOUT = 30  # seconds — caps single-call wait so slow 3G doesn't hang the UI


class LLMBusyError(RuntimeError):
    """Raised when Groq returns 429s for the full retry budget.

    app.py catches this explicitly and shows the localised "busy" message
    instead of the generic "something went wrong" — so the user knows to
    wait 30s and retry, not re-upload.
    """


def _client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Get a free key at console.groq.com")
    return Groq(api_key=api_key, timeout=_REQUEST_TIMEOUT)


def _retry_after_seconds(err: groq.RateLimitError) -> float | None:
    """Best-effort parse of a retry-after hint from a Groq 429.

    The SDK puts the response headers / body inside the exception's message
    or .response attribute. We accept a few formats and return None if we
    can't extract a sensible value — caller falls back to exponential backoff.
    """
    # Try the structured response first
    resp = getattr(err, "response", None)
    if resp is not None:
        headers = getattr(resp, "headers", None) or {}
        ra = headers.get("retry-after") or headers.get("Retry-After")
        if ra:
            try:
                return max(0.0, float(ra))
            except (TypeError, ValueError):
                pass
    # Fall back to scraping the error message
    msg = str(err)
    m = re.search(r"(?:retry[-_ ]after|try again in)\s*[: ]?\s*(\d+(?:\.\d+)?)", msg, re.IGNORECASE)
    if m:
        try:
            return max(0.0, float(m.group(1)))
        except ValueError:
            pass
    return None


def call_llm(
    prompt: str,
    image_bytes: bytes = None,
    mime_type: str = None,
    json_mode: bool = False,
    multilingual: bool = False,
) -> str:
    client = _client()

    if image_bytes and mime_type:
        # Vision call — encode image as base64
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64}"
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        model = _VISION_MODEL
    else:
        # Text-only call — use multilingual model for non-English
        messages = [{"role": "user", "content": prompt}]
        model = _MULTILINGUAL_MODEL if multilingual else _TEXT_MODEL

    kwargs = dict(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=4096,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    # Audit #23 — bounded retry on 429s with exponential backoff. Honors
    # retry-after when Groq sends one, otherwise 1s → 2s → 4s with jitter.
    # All retries within the per-call _REQUEST_TIMEOUT envelope.
    last_rate_limit: groq.RateLimitError | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except groq.RateLimitError as e:
            last_rate_limit = e
            if attempt == _MAX_RETRIES - 1:
                break
            hinted = _retry_after_seconds(e)
            delay = hinted if hinted is not None else _BACKOFF_BASE * (2 ** attempt)
            delay = min(delay, 8.0)  # hard cap — never block a worker > 8s
            delay += random.uniform(0, 0.25)  # jitter — avoid thundering herd
            logger.warning(
                "llm_client: rate-limited (attempt %d/%d), sleeping %.2fs",
                attempt + 1, _MAX_RETRIES, delay,
            )
            time.sleep(delay)
        except Exception:
            # Audit #9 — never let raw Groq SDK errors (which can echo API key
            # / URL) surface to the UI. Log full detail server-side, surface a
            # generic message.
            logger.exception("llm_client: Groq call failed")
            raise RuntimeError("Our AI service is temporarily unavailable. Please try again in a moment.")

    # All retries exhausted on 429s
    logger.warning("llm_client: rate-limit retries exhausted (%s)", last_rate_limit)
    raise LLMBusyError("Our AI service is busy right now. Please try again in 30 seconds.")
