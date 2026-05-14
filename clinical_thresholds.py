"""Hard-coded clinical danger thresholds.

Audit finding #2 + #30. The status engine must not rely solely on the lab's
printed reference range. Many labs print generous house ranges that would
silently normalise diabetic glucose or severely-low haemoglobin. Any value
that crosses one of these clinical floors forces status="see_doctor"
regardless of what the lab printed.

Conservative numbers — chosen so the table only fires on values where any
clinician would say "this person should see a doctor today, not in three
weeks." Borderline values still flow through the normal % deviation logic.

Keys are lower-case substrings matched against the parameter name.
"""

CLINICAL_DANGER = {
    # Diabetes / glucose
    "hba1c":                  {"high": 6.5},                # >=6.5% = diabetes (ADA)
    "fasting glucose":        {"high": 126},                # >=126 mg/dL = diabetes (ADA)
    "fasting blood sugar":    {"high": 126},                # alias

    # Lipids
    "ldl":                    {"high": 190},                # severe hypercholesterolaemia
    "triglyceride":           {"high": 500},                # pancreatitis risk

    # Thyroid
    "tsh":                    {"high": 10.0, "low": 0.1},   # overt hypo / hyperthyroidism

    # Electrolytes
    "potassium":              {"high": 6.0, "low": 3.0},    # hyper/hypokalaemia — arrhythmia risk
    "sodium":                 {"high": 155, "low": 125},    # hyper/hyponatraemia

    # Kidney
    "creatinine":             {"high": 2.0},                # significant renal dysfunction

    # Haematology
    "haemoglobin":            {"low": 8.0},                 # severe anaemia
    "hemoglobin":             {"low": 8.0},                 # US spelling alias
    "platelet":               {"low": 50000},               # severe thrombocytopenia — bleeding risk
}


def clinical_danger_status(name: str, value) -> str | None:
    """Return 'see_doctor' if value crosses a hardcoded clinical floor.

    Returns None if no clinical override applies. Caller falls back to its
    normal range/flag logic. Matches case-insensitively on substring so
    'Glycated Haemoglobin (HbA1c)' triggers the 'hba1c' rule.

    Numeric coercion is tolerant: '7.8%', '7,800', ' 13.2 ' all parse.
    Non-numeric values return None — the caller's text-value path applies.
    """
    if name is None or value is None:
        return None
    try:
        v = float(str(value).replace("%", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None

    name_lc = name.lower()
    for key, bounds in CLINICAL_DANGER.items():
        if key not in name_lc:
            continue
        high = bounds.get("high")
        low = bounds.get("low")
        if high is not None and v >= high:
            return "see_doctor"
        if low is not None and v <= low:
            return "see_doctor"
    return None
