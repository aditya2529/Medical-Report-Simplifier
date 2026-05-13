import json
from llm_client import call_llm

FORBIDDEN_PHRASES = [
    "you have diabetes", "you have cancer", "you are diabetic", "you have hypertension",
    "you have anemia", "you have", "you are", "take ", "you should take", "prescribe",
    "you need surgery", "you need a ", "this is serious", "this is dangerous",
    "you must", "immediately consult", "call emergency",
]

EXPLANATION_PROMPT_TEMPLATE = """You are a friendly health educator explaining lab results to a patient with no medical background.
{age_gender_line}

For each parameter in the JSON array below, return a JSON array with one object per parameter containing:
- "name": same parameter name as input
- "what_it_is": one plain sentence explaining what this test measures (no jargon, no abbreviations)
- "your_result": two sentences explaining what the patient's specific value means for them personally
- "status": exactly one of "normal", "monitor", or "see_doctor" (use the status already computed in input — do NOT change it)

Rules you must follow:
- Never say "you have [disease]", never name a diagnosis
- Never suggest any medication, supplement, or treatment
- Never use the words: prescribe, diagnose, surgery, emergency
- Be calm and factual. For "see_doctor" values, say "worth discussing with your doctor" — not alarming language
- Return ONLY a valid JSON array. No markdown, no commentary.

Parameters:
{params_json}"""


def _clean_output(text: str) -> str:
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text.lower():
            text = text.replace(phrase, "[removed]")
    return text


def _parse_json(raw: str) -> list[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def explain_parameters(params: list[dict], age: int = None, gender: str = None) -> list[dict]:
    """
    Takes annotated params (with status), returns list with what_it_is and your_result added.
    """
    if age and gender:
        age_gender_line = f"Patient: {age} year old {gender}."
    elif age:
        age_gender_line = f"Patient: {age} years old."
    else:
        age_gender_line = ""

    # Only send the fields Gemini needs — strip internal fields
    slim = [
        {
            "name": p["name"],
            "value": p["value"],
            "unit": p.get("unit", ""),
            "ref_low": p.get("ref_low"),
            "ref_high": p.get("ref_high"),
            "status": p.get("status", "normal"),
        }
        for p in params
        if not p.get("low_confidence")
    ]

    if not slim:
        return []

    prompt = EXPLANATION_PROMPT_TEMPLATE.format(
        age_gender_line=age_gender_line,
        params_json=json.dumps(slim, indent=2),
    )

    for attempt in range(2):
        try:
            raw = call_llm(prompt)
            explanations = _parse_json(raw)
            break
        except Exception:
            if attempt == 1:
                raise RuntimeError("Could not generate explanations. Please try again.")

    # Build lookup by name and merge back
    lookup = {e["name"]: e for e in explanations}
    result = []
    for p in params:
        exp = lookup.get(p["name"], {})
        merged = {**p}
        merged["what_it_is"] = _clean_output(exp.get("what_it_is", "No explanation available."))
        merged["your_result"] = _clean_output(exp.get("your_result", ""))
        result.append(merged)

    return result
