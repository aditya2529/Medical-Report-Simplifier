import streamlit as st
from extractor import extract_parameters, annotate_status
from explainer import explain_parameters

st.set_page_config(
    page_title="ClarityMed — Understand Your Lab Report",
    page_icon="🩺",
    layout="centered",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .status-normal  { background:#d4edda; color:#155724; padding:4px 10px; border-radius:12px; font-weight:600; font-size:0.85rem; }
  .status-monitor { background:#fff3cd; color:#856404; padding:4px 10px; border-radius:12px; font-weight:600; font-size:0.85rem; }
  .status-see_doctor { background:#f8d7da; color:#721c24; padding:4px 10px; border-radius:12px; font-weight:600; font-size:0.85rem; }
  .param-card { border:1px solid #e0e0e0; border-radius:10px; padding:16px; margin-bottom:12px; }
  .param-name { font-size:1.05rem; font-weight:700; margin-bottom:4px; }
  .param-value { font-size:0.95rem; color:#444; margin-bottom:8px; }
  .explanation { font-size:0.92rem; color:#333; line-height:1.55; }
  .low-conf-badge { background:#e2e3e5; color:#383d41; padding:3px 8px; border-radius:8px; font-size:0.8rem; }
  .disclaimer-box { background:#fff8e1; border-left:4px solid #ffc107; padding:14px 16px; border-radius:6px; font-size:0.85rem; color:#555; margin-top:32px; }
  .urgent-banner { background:#f8d7da; border:1px solid #f5c6cb; border-radius:8px; padding:14px 16px; color:#721c24; font-weight:600; margin-bottom:20px; }
</style>
""", unsafe_allow_html=True)

STATUS_LABEL = {
    "normal": "Normal",
    "monitor": "Monitor",
    "see_doctor": "See Doctor",
}

PHOTO_TIPS = [
    "📄 Lay the report flat on a table — no folds or curves",
    "💡 Use good lighting — avoid shadows across the page",
    "📐 Keep the full page in frame — don't cut off the edges",
    "🔍 Hold steady — blurry photos can't be read accurately",
]

DISCLAIMER = (
    "**ClarityMed** explains what lab values mean in plain language. "
    "It is not a medical diagnosis and is not a substitute for professional medical advice. "
    "Always consult a qualified doctor before making any health decision."
)


def _status_badge(status: str) -> str:
    label = STATUS_LABEL.get(status, status)
    css = f"status-{status}"
    return f'<span class="{css}">{label}</span>'


def _build_whatsapp_text(report_type: str, params: list[dict]) -> str:
    urgent = [p for p in params if p.get("status") == "see_doctor"]
    monitor = [p for p in params if p.get("status") == "monitor"]
    normal = [p for p in params if p.get("status") == "normal"]

    lines = [f"🩺 *ClarityMed — {report_type} Summary*", ""]
    if urgent:
        lines.append("🔴 *Needs Attention:*")
        for p in urgent:
            lines.append(f"  • {p['name']}: {p['value']} {p.get('unit','')} — {p.get('your_result','').split('.')[0]}.")
        lines.append("")
    if monitor:
        lines.append("🟡 *Worth Monitoring:*")
        for p in monitor:
            lines.append(f"  • {p['name']}: {p['value']} {p.get('unit','')}")
        lines.append("")
    if normal:
        lines.append(f"🟢 *Normal ({len(normal)} values)*")
        lines.append("")
    lines.append("_This summary is for information only. Always consult your doctor._")
    return "\n".join(lines)


def render_param_card(p: dict):
    status = p.get("status", "normal")
    badge = _status_badge(status)
    unit = p.get("unit", "")
    val_display = f"{p['value']} {unit}".strip()

    ref_low = p.get("ref_low")
    ref_high = p.get("ref_high")
    ref_str = ""
    if ref_low is not None and ref_high is not None:
        ref_str = f"<span style='color:#888;font-size:0.82rem;'>(Ref: {ref_low}–{ref_high} {unit})</span>"

    low_conf = p.get("low_confidence", False)
    conf_badge = '<span class="low-conf-badge">⚠ Verify against original</span>' if low_conf else ""

    what = p.get("what_it_is", "")
    your = p.get("your_result", "")

    st.markdown(f"""
<div class="param-card">
  <div class="param-name">{p['name']} &nbsp; {badge} &nbsp; {conf_badge}</div>
  <div class="param-value">{val_display} &nbsp; {ref_str}</div>
  <div class="explanation"><b>What it measures:</b> {what}</div>
  <div class="explanation" style="margin-top:6px;">{your}</div>
</div>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
for key in ("params", "report_type", "error", "processing"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🩺 ClarityMed")
st.caption("Understand your lab report in plain language — in under 15 seconds.")

# ── Upload section ─────────────────────────────────────────────────────────────
with st.expander("📸 Tips for uploading a photo of a printed report", expanded=False):
    for tip in PHOTO_TIPS:
        st.markdown(f"- {tip}")

uploaded = st.file_uploader(
    "Upload your lab report (PDF, JPG, PNG, HEIC — up to 10 MB)",
    type=["pdf", "jpg", "jpeg", "png", "heic"],
    label_visibility="visible",
)

col1, col2 = st.columns([2, 1])
with col1:
    age = st.number_input("Your age (optional — improves accuracy)", min_value=1, max_value=120, value=None, step=1)
with col2:
    gender = st.selectbox("Gender (optional)", ["Not specified", "Male", "Female", "Other"])
    if gender == "Not specified":
        gender = None

analyze_btn = st.button("Analyse Report", type="primary", disabled=uploaded is None)

# ── Manual entry fallback ──────────────────────────────────────────────────────
with st.expander("✏️ Or enter values manually (for handwritten or unclear reports)", expanded=False):
    st.caption("Add one row per test. Press + to add more.")

    if "manual_rows" not in st.session_state:
        st.session_state.manual_rows = [{"name": "", "value": "", "unit": "", "ref_low": "", "ref_high": ""}]

    manual_changed = False
    rows_to_keep = []
    for i, row in enumerate(st.session_state.manual_rows):
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1.5, 1.5, 1.5, 0.8])
        name = c1.text_input("Test name", value=row["name"], key=f"mn_{i}", label_visibility="collapsed" if i > 0 else "visible", placeholder="e.g. HbA1c")
        val  = c2.text_input("Value", value=row["value"], key=f"mv_{i}", label_visibility="collapsed" if i > 0 else "visible", placeholder="e.g. 7.8")
        unit = c3.text_input("Unit", value=row["unit"], key=f"mu_{i}", label_visibility="collapsed" if i > 0 else "visible", placeholder="e.g. %")
        rl   = c4.text_input("Ref low", value=row["ref_low"], key=f"rl_{i}", label_visibility="collapsed" if i > 0 else "visible", placeholder="e.g. 4.0")
        rh   = c5.text_input("Ref high", value=row["ref_high"], key=f"rh_{i}", label_visibility="collapsed" if i > 0 else "visible", placeholder="e.g. 6.0")
        keep = True
        if i > 0 and c6.button("✕", key=f"del_{i}"):
            keep = False
        if keep:
            rows_to_keep.append({"name": name, "value": val, "unit": unit, "ref_low": rl, "ref_high": rh})

    st.session_state.manual_rows = rows_to_keep

    if st.button("+ Add another test"):
        st.session_state.manual_rows.append({"name": "", "value": "", "unit": "", "ref_low": "", "ref_high": ""})
        st.rerun()

    manual_btn = st.button("Analyse Manual Entry", type="secondary")

    if manual_btn:
        manual_params = []
        for row in st.session_state.manual_rows:
            if not row["name"] or not row["value"]:
                continue
            try:
                rl = float(row["ref_low"]) if row["ref_low"] else None
                rh = float(row["ref_high"]) if row["ref_high"] else None
            except ValueError:
                rl = rh = None
            manual_params.append({
                "name": row["name"],
                "value": row["value"],
                "unit": row["unit"],
                "ref_low": rl,
                "ref_high": rh,
                "flag": "",
            })
        if not manual_params:
            st.warning("Please enter at least one test name and value.")
        else:
            with st.spinner("Generating explanations…"):
                try:
                    annotated = annotate_status(manual_params)
                    explained = explain_parameters(annotated, age=age, gender=gender)
                    st.session_state.params = explained
                    st.session_state.report_type = "Manual Entry"
                    st.session_state.error = None
                except Exception as e:
                    st.session_state.error = str(e)

# ── Analyse uploaded file ──────────────────────────────────────────────────────
if analyze_btn and uploaded:
    st.session_state.params = None
    st.session_state.error = None
    file_bytes = uploaded.read()
    suffix = uploaded.name.rsplit(".", 1)[-1].lower()
    mime_map = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "heic": "image/heic"}
    mime = mime_map.get(suffix, "image/jpeg")

    with st.spinner("Reading your report… this takes about 10–15 seconds."):
        try:
            params, report_type = extract_parameters(file_bytes, mime)
            annotated = annotate_status(params)
            explained = explain_parameters(annotated, age=age, gender=gender)
            st.session_state.params = explained
            st.session_state.report_type = report_type
        except Exception as e:
            st.session_state.error = str(e)

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.error:
    st.error(st.session_state.error)
    st.info("You can try again with a clearer image, or use **manual entry** above.")

if st.session_state.params:
    params = st.session_state.params
    report_type = st.session_state.report_type or "Lab Report"

    # Report type confirmation banner
    st.success(f"✅ Detected: **{report_type}** · {len(params)} parameters found")

    # Urgent banner if many see_doctor flags
    see_doc_count = sum(1 for p in params if p.get("status") == "see_doctor")
    if see_doc_count >= 5:
        st.markdown(
            '<div class="urgent-banner">⚠️ Several values need attention — please consult your doctor before making any health decisions.</div>',
            unsafe_allow_html=True,
        )

    # Low confidence warning
    low_conf_count = sum(1 for p in params if p.get("low_confidence"))
    if low_conf_count > len(params) * 0.3:
        st.warning(f"⚠️ {low_conf_count} values could not be read clearly. Please verify these against your original report.")

    # Sort: see_doctor → monitor → normal
    sort_order = {"see_doctor": 0, "monitor": 1, "normal": 2}
    sorted_params = sorted(params, key=lambda p: sort_order.get(p.get("status", "normal"), 2))

    # WhatsApp share
    wa_text = _build_whatsapp_text(report_type, sorted_params)
    wa_url = "https://wa.me/?text=" + wa_text.replace(" ", "%20").replace("\n", "%0A")

    col_share, col_copy = st.columns(2)
    col_share.link_button("📲 Share via WhatsApp", wa_url, use_container_width=True)
    col_copy.text_area("Copy summary", value=wa_text, height=80, label_visibility="collapsed", key="copy_area")

    st.divider()

    for p in sorted_params:
        render_param_card(p)

    # Disclaimer (non-dismissable)
    st.markdown(f'<div class="disclaimer-box">ℹ️ {DISCLAIMER}</div>', unsafe_allow_html=True)
