import os
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Groq vision model (Llama 4 Scout supports images)
_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
# Groq text model — 8B is fast for English
_TEXT_MODEL   = "llama-3.1-8b-instant"
# Larger model for non-English (Devanagari, etc.) where 8B is too weak
_MULTILINGUAL_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def _client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Get a free key at console.groq.com")
    return Groq(api_key=api_key)


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

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content
