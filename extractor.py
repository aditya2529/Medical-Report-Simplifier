import json
import fitz  # PyMuPDF
from llm_client import call_llm
from clinical_thresholds import clinical_danger_status

EXTRACTION_PROMPT = """You are a medical data extraction engine. Extract ALL test parameters from this lab report image or PDF.

For each parameter return a JSON object with exactly these fields:
- "name": test name as printed (e.g., "Haemoglobin", "HbA1c", "TSH")
- "value": the patient's result as a string (e.g., "13.2", "Positive", "7.8%")
- "unit": unit of measurement as printed (e.g., "g/dL", "%", "mIU/L") — empty string if none
- "ref_low": lower bound of reference range as a number — null if no lower bound exists
- "ref_high": upper bound of reference range as a number — null if no upper bound exists
- "flag": lab's own flag as printed ("H", "L", "HIGH", "LOW", "*", or empty string if none)
- "report_type": (only on the FIRST parameter) the type of report detected (e.g., "Complete Blood Count", "Lipid Profile", "Thyroid Function Test")

Reference-range parsing rules — MUST follow exactly:
- "0.4 - 4.0" or "0.4-4.0"   -> ref_low=0.4,  ref_high=4.0
- "<200" or "Less than 200"  -> ref_low=null, ref_high=200       (only an upper bound)
- ">40"  or "More than 40"   -> ref_low=40,   ref_high=null      (only a lower bound)
- "<=7"  or "Up to 7"        -> ref_low=null, ref_high=7
- ">=12" or "At least 12"    -> ref_low=12,   ref_high=null
- "Negative" / "Nil" / blank -> ref_low=null, ref_high=null
NEVER copy one bound into both fields. If only one side of the range exists, the other field MUST be null.

Return ONLY a valid JSON array. No markdown, no explanation, no commentary.
If a value cannot be read clearly, include the parameter with value set to "UNCLEAR".

Example output:
[
  {"name": "Haemoglobin", "value": "11.2", "unit": "g/dL", "ref_low": 12.0, "ref_high": 16.0, "flag": "L", "report_type": "Complete Blood Count"},
  {"name": "HDL Cholesterol", "value": "38", "unit": "mg/dL", "ref_low": 40, "ref_high": null, "flag": "L"},
  {"name": "LDL Cholesterol", "value": "168", "unit": "mg/dL", "ref_low": null, "ref_high": 100, "flag": "H"}
]"""


MAX_PDF_PAGES = 5    # Audit #8 — cap pages to bound memory + LLM cost
PDF_RENDER_DPI = 110  # Audit #8 — was 150; 110 keeps OCR usable at ~half memory


def _pdf_to_images(pdf_bytes: bytes) -> list[tuple[bytes, str]]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for i, page in enumerate(doc):
        if i >= MAX_PDF_PAGES:
            break
        pix = page.get_pixmap(dpi=PDF_RENDER_DPI)
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

    Rule order:
    1. Hardcoded clinical danger table (audit #2 + #30) — fires first; any
       value crossing a clinical floor returns see_doctor regardless of the
       lab's printed range.
    2. Lab flag (H/L/*) or printed range comparison.

    Range handling (audit #1) supports one-sided ranges:
    - both bounds present  -> in-range vs out-of-range with % deviation
    - only ref_high (e.g. <200) -> compare against high only
    - only ref_low  (e.g. >40)  -> compare against low only
    - neither bound        -> fall back to the lab flag
    """
    name = param.get("name", "")
    raw_value = param.get("value", "")

    clinical = clinical_danger_status(name, raw_value)
    if clinical:
        return clinical

    flag = (param.get("flag") or "").upper()
    flagged = flag in ("H", "L", "HIGH", "LOW", "*")

    try:
        val = float(str(raw_value).replace("%", "").replace(",", "").strip())
        low = param.get("ref_low")
        high = param.get("ref_high")
        low = float(low) if low is not None else None
        high = float(high) if high is not None else None

        # No numeric range at all — fall back to lab flag
        if low is None and high is None:
            return "see_doctor" if flagged else "normal"

        # Within whichever bounds exist
        within_low  = low  is None or val >= low
        within_high = high is None or val <= high
        if within_low and within_high:
            return "normal"

        # Out of range — figure deviation against the violated bound
        if high is not None and val > high:
            deviation_pct = (val - high) / abs(high) if high != 0 else 1.0
        else:  # val < low
            deviation_pct = (low - val) / abs(low) if low and low != 0 else 1.0

        if deviation_pct > 0.20:
            return "see_doctor"
        # Mildly outside range
        return "see_doctor" if flagged else "monitor"
    except (ValueError, TypeError):
        # Non-numeric value
        sval = str(raw_value).upper()
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
