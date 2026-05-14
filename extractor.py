import json
import fitz  # PyMuPDF
from llm_client import call_llm

EXTRACTION_PROMPT = """You are a medical data extraction engine. Extract ALL test parameters from this lab report image or PDF.

For each parameter return a JSON object with exactly these fields:
- "name": test name as printed (e.g., "Haemoglobin", "HbA1c", "TSH")
- "value": the patient's result as a string (e.g., "13.2", "Positive", "7.8%")
- "unit": unit of measurement as printed (e.g., "g/dL", "%", "mIU/L") — empty string if none
- "ref_low": lower bound of reference range as a number — null if not applicable or not numeric
- "ref_high": upper bound of reference range as a number — null if not applicable or not numeric
- "flag": lab's own flag as printed ("H", "L", "HIGH", "LOW", "*", or empty string if none)
- "report_type": (only on the FIRST parameter) the type of report detected (e.g., "Complete Blood Count", "Lipid Profile", "Thyroid Function Test")

Return ONLY a valid JSON array. No markdown, no explanation, no commentary.
If a value cannot be read clearly, include the parameter with value set to "UNCLEAR".

Example output:
[
  {"name": "Haemoglobin", "value": "11.2", "unit": "g/dL", "ref_low": 12.0, "ref_high": 16.0, "flag": "L", "report_type": "Complete Blood Count"},
  {"name": "WBC Count", "value": "7800", "unit": "cells/μL", "ref_low": 4000, "ref_high": 11000, "flag": ""}
]"""


def _pdf_to_images(pdf_bytes: bytes) -> list[tuple[bytes, str]]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        images.append((pix.tobytes("png"), "image/png"))
    return images


def _parse_json(raw: str):
    """Robustly extract JSON array or object from LLM output.

    Handles: markdown code fences, surrounding prose, leading/trailing junk.
    """
    raw = raw.strip()
    # Strip markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Find first '[' or '{' and matching close bracket
    for open_ch, close_ch in [("[", "]"), ("{", "}")]:
        start = raw.find(open_ch)
        if start == -1:
            continue
        # Find matching close bracket (handles nested)
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == open_ch:
                depth += 1
            elif raw[i] == close_ch:
                depth -= 1
                if depth == 0:
                    candidate = raw[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break  # try other bracket type
    # If all else fails, re-raise the original error
    return json.loads(raw)


def extract_parameters(file_bytes: bytes, mime_type: str) -> tuple[list[dict], str]:
    """
    Returns (parameters, report_type).
    parameters: list of dicts with name/value/unit/ref_low/ref_high/flag
    report_type: detected report type string
    Raises ValueError if extraction fails after retry.
    """
    if mime_type == "application/pdf":
        page_images = _pdf_to_images(file_bytes)
    else:
        page_images = [(file_bytes, mime_type)]

    all_params = []
    report_type = "Lab Report"

    for img_bytes, img_mime in page_images:
        last_error = None
        for attempt in range(2):
            try:
                raw = call_llm(EXTRACTION_PROMPT, image_bytes=img_bytes, mime_type=img_mime, json_mode=False)
                params = _parse_json(raw)
                if not isinstance(params, list) or len(params) == 0:
                    raise ValueError("Empty parameter list returned by Gemini.")
                break
            except Exception as e:
                last_error = e
                if attempt == 1:
                    raise ValueError(f"Extraction failed: {last_error}")
        for p in params:
            if "report_type" in p and p["report_type"]:
                report_type = p.pop("report_type")
            else:
                p.pop("report_type", None)
            all_params.append(p)

    return all_params, report_type


def compute_status(param: dict) -> str:
    """Returns 'normal', 'monitor', or 'see_doctor'.

    Rule: % deviation is measured relative to the violated bound, not range span.
    - Within range          → normal
    - 0-20% above/below bound → monitor (unless lab flagged H/L → see_doctor)
    - >20% above/below bound → see_doctor
    """
    flag = (param.get("flag") or "").upper()
    flagged = flag in ("H", "L", "HIGH", "LOW", "*")

    try:
        val = float(str(param.get("value", "")).replace("%", "").replace(",", "").strip())
        low = param.get("ref_low")
        high = param.get("ref_high")

        if low is None or high is None:
            # No numeric range — fall back to lab flag
            if flagged:
                return "see_doctor"
            return "normal"

        low, high = float(low), float(high)
        if low <= val <= high:
            return "normal"

        # Calculate % deviation relative to the violated bound
        if val > high:
            deviation_pct = (val - high) / abs(high) if high != 0 else 1.0
        else:  # val < low
            deviation_pct = (low - val) / abs(low) if low != 0 else 1.0

        if deviation_pct > 0.20:
            return "see_doctor"
        # Mildly outside range
        return "see_doctor" if flagged else "monitor"
    except (ValueError, TypeError):
        # Non-numeric value
        sval = str(param.get("value", "")).upper()
        if sval in ("POSITIVE", "REACTIVE"):
            return "see_doctor"
        if flagged:
            return "see_doctor"
        return "monitor"


def annotate_status(params: list[dict]) -> list[dict]:
    for p in params:
        p["status"] = compute_status(p)
        p["low_confidence"] = str(p.get("value", "")) == "UNCLEAR"
    return params
