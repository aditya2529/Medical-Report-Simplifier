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
- "what_it_is": one plain sentence explaining what this test measures (no jargon)
- "your_result": two sentences explaining what the patient's specific value means
- "status": copy the status field exactly from the input — do NOT change it

Rules:
- Never say "you have [disease]", never name a diagnosis
- Never suggest any medication or treatment
- Be calm and factual
- Return ONLY a valid JSON array. No markdown, no code blocks, no commentary.

Parameters:
{params_json}"""


def _clean_output(text: str) -> str:
    lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            idx = lower.find(phrase)
            text = text[:idx] + "[see your doctor]" + text[idx + len(phrase):]
            lower = text.lower()
    return text


def _parse_json(raw: str) -> list[dict]:
    raw = raw.strip()
    # Strip markdown code fences
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("["):
                raw = part
                break
    # Find the JSON array
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start:end + 1]
    return json.loads(raw)


LANGUAGE_INSTRUCTIONS = {
    "english": "Write all explanations in clear, simple English.",
    "hindi": (
        "CRITICAL: Write what_it_is and your_result values in HINDI using DEVANAGARI SCRIPT ONLY (देवनागरी लिपि). "
        "DO NOT use Roman/English letters for Hindi. "
        "WRONG (do not do this): 'yeh test aapke shareer mein cholesterol ke matalab karta hai'\n"
        "CORRECT (do this): 'यह टेस्ट आपके शरीर में कोलेस्ट्रॉल की मात्रा को मापता है।'\n"
        "Every Hindi word must be written in Devanagari script (अ, आ, क, ख, ग...). "
        "JSON field names (name, what_it_is, your_result, status) stay in English. "
        "The 'name' value also stays in English (parameter name from the report). "
        "Only what_it_is and your_result text content should be in Devanagari Hindi."
    ),
}


def _explain_batch(batch: list[dict], age_gender_line: str, language: str = "english") -> list[dict]:
    context = f"{age_gender_line}\n" if age_gender_line else ""
    lang_instr = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["english"])
    prompt = (
        f"{context}"
        f"You are a friendly health educator. For each parameter below, return a JSON array.\n"
        f"Each item must have exactly these fields:\n"
        f"- name: same as input (keep in English)\n"
        f"- what_it_is: 1 plain sentence explaining what this test measures (no jargon)\n"
        f"- your_result: 2 sentences explaining what this patient's value means\n"
        f"- status: copy from input unchanged (keep in English: normal/monitor/see_doctor)\n"
        f"{lang_instr}\n"
        f"Rules: never diagnose, never suggest medication, be calm.\n"
        f"Return ONLY the JSON array. No markdown, no code blocks, no extra text.\n\n"
        f"Parameters:\n{json.dumps(batch, ensure_ascii=False)}"
    )
    use_multilingual = language != "english"
    for attempt in range(2):
        try:
            raw = call_llm(prompt, multilingual=use_multilingual)
            result = _parse_json(raw)
            if isinstance(result, list) and len(result) > 0:
                return result
        except Exception as e:
            if attempt == 1:
                raise RuntimeError(f"Explanation failed: {e}")
    return []


def explain_parameters(params: list[dict], age: int = None, gender: str = None, language: str = "english") -> list[dict]:
    if age and gender:
        age_gender_line = f"Patient: {age} year old {gender}."
    elif age:
        age_gender_line = f"Patient: {age} years old."
    else:
        age_gender_line = ""

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
        return params

    # Process in batches of 8 to avoid token limits
    BATCH_SIZE = 8
    explanations = []
    for i in range(0, len(slim), BATCH_SIZE):
        batch = slim[i:i + BATCH_SIZE]
        explanations.extend(_explain_batch(batch, age_gender_line, language=language))

    # Build lookup and merge
    lookup = {e["name"]: e for e in explanations}
    result = []
    for p in params:
        exp = lookup.get(p["name"], {})
        merged = {**p}
        merged["what_it_is"] = _clean_output(exp.get("what_it_is", "No explanation available."))
        merged["your_result"] = _clean_output(exp.get("your_result", ""))
        result.append(merged)

    return result
