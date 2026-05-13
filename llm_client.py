import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_PRIMARY_MODEL  = "gemini-1.5-flash"
_FALLBACK_MODEL = "gemini-1.5-flash-8b"


def _client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Get a free key at aistudio.google.com")
    return genai.Client(api_key=api_key)


def call_llm(
    prompt: str,
    image_bytes: bytes = None,
    mime_type: str = None,
    json_mode: bool = False,
) -> str:
    client = _client()

    config = types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=4096,
        response_mime_type="application/json" if json_mode else "text/plain",
    )

    parts = []
    if image_bytes and mime_type:
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
    parts.append(prompt)

    for model_name in [_PRIMARY_MODEL, _FALLBACK_MODEL]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=parts,
                config=config,
            )
            return response.text
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "quota", "rate", "RESOURCE_EXHAUSTED")):
                if model_name == _PRIMARY_MODEL:
                    continue  # try fallback
            raise

    raise RuntimeError("Both Gemini models are rate-limited. Please wait a moment and try again.")
