import streamlit as st
from extractor import extract_parameters, annotate_status
from explainer import explain_parameters
from pdf_generator import generate_pdf

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClarityMed — Understand Your Lab Report",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* App container */
  .main .block-container { padding-top: 1.5rem; max-width: 820px; }

  /* Hero */
  .hero-card {
    background: linear-gradient(135deg, #2163a8 0%, #4a90e2 100%);
    color: white;
    padding: 24px 26px;
    border-radius: 14px;
    margin-bottom: 18px;
    box-shadow: 0 4px 14px rgba(33, 99, 168, 0.15);
  }
  .hero-card h1 {
    color: white !important;
    margin: 0 0 6px 0 !important;
    font-size: 1.85rem !important;
  }
  .hero-card p { margin: 0; font-size: 0.98rem; opacity: 0.95; }

  /* Status badges */
  .status-normal      { background:#d4edda; color:#155724; padding:4px 12px; border-radius:14px; font-weight:600; font-size:0.78rem; letter-spacing:.3px; }
  .status-monitor     { background:#fff3cd; color:#856404; padding:4px 12px; border-radius:14px; font-weight:600; font-size:0.78rem; letter-spacing:.3px; }
  .status-see_doctor  { background:#f8d7da; color:#721c24; padding:4px 12px; border-radius:14px; font-weight:600; font-size:0.78rem; letter-spacing:.3px; }

  /* Parameter card */
  .param-card {
    border: 1px solid #e6e8eb;
    border-left: 4px solid #ddd;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 14px;
    background: rgba(255,255,255,0.02);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .param-card:hover { transform: translateY(-1px); box-shadow: 0 3px 10px rgba(0,0,0,0.06); }
  .param-card.see_doctor { border-left-color: #dc3545; }
  .param-card.monitor    { border-left-color: #ffc107; }
  .param-card.normal     { border-left-color: #28a745; }

  .param-name { font-size:1.08rem; font-weight:700; margin-bottom:5px; }
  .param-value { font-size:0.95rem; color:#666; margin-bottom:10px; }
  .ref-range { color:#999; font-size:0.82rem; margin-left:6px; }
  .what-label { font-weight:600; color:#444; font-size:0.88rem; }
  .explanation { font-size:0.93rem; color:#333; line-height:1.6; margin-top:4px; }
  .your-result { font-size:0.93rem; line-height:1.6; margin-top:8px; }
  .low-conf-badge { background:#e2e3e5; color:#383d41; padding:3px 9px; border-radius:8px; font-size:0.74rem; }

  /* Banners */
  .urgent-banner {
    background: linear-gradient(135deg, #f8d7da 0%, #f5b3b8 100%);
    border:1px solid #f1aeb5; border-radius:10px;
    padding:14px 16px; color:#721c24; font-weight:600; margin-bottom:18px;
  }
  .detection-banner {
    background:#e7f3ff; border:1px solid #b3d7ff; border-radius:10px;
    padding:11px 16px; color:#004085; margin-bottom:14px; font-size:0.95rem;
  }

  /* Disclaimer */
  .disclaimer-box {
    background:#fff8e1; border-left:4px solid #ffc107;
    padding:13px 16px; border-radius:6px;
    font-size:0.82rem; color:#555; margin-top:32px;
  }

  /* Summary chips */
  .summary-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px; }
  .chip {
    padding:6px 14px; border-radius:18px; font-size:0.85rem; font-weight:600;
    display:inline-flex; align-items:center; gap:6px;
  }
  .chip-normal { background:#d4edda; color:#155724; }
  .chip-monitor { background:#fff3cd; color:#856404; }
  .chip-see_doctor { background:#f8d7da; color:#721c24; }

  /* Buttons */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2163a8 0%, #4a90e2 100%);
    border: none;
    font-weight: 600;
  }

  /* Mobile */
  @media (max-width: 600px) {
    .hero-card h1 { font-size: 1.4rem !important; }
    .param-name { font-size: 1rem; }
    .param-card { padding: 14px 14px; }
  }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
STATUS_LABEL = {
    "normal":     "Normal",
    "monitor":    "Monitor",
    "see_doctor": "See Doctor",
}

PHOTO_TIPS = [
    "📄 Lay the report flat — no folds or curves",
    "💡 Use good lighting — avoid shadows",
    "📐 Keep the full page in frame",
    "🔍 Hold steady — blur ruins extraction",
]

DISCLAIMER = (
    "**ClarityMed** explains what lab values mean in plain language. "
    "It is not a medical diagnosis and is not a substitute for professional medical advice. "
    "Always consult a qualified doctor before making any health decision."
)

LANG_CODES = {"English": "english", "हिन्दी (Hindi)": "hindi"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _status_badge(status: str) -> str:
    label = STATUS_LABEL.get(status, status)
    return f'<span class="status-{status}">{label}</span>'


def _build_whatsapp_text(report_type: str, params: list[dict]) -> str:
    urgent  = [p for p in params if p.get("status") == "see_doctor"]
    monitor = [p for p in params if p.get("status") == "monitor"]
    normal  = [p for p in params if p.get("status") == "normal"]

    lines = [f"🩺 *ClarityMed — {report_type} Summary*", ""]
    if urgent:
        lines.append("🔴 *Needs Attention:*")
        for p in urgent:
            lines.append(f"  • {p['name']}: {p['value']} {p.get('unit','')}")
        lines.append("")
    if monitor:
        lines.append("🟡 *Worth Monitoring:*")
        for p in monitor:
            lines.append(f"  • {p['name']}: {p['value']} {p.get('unit','')}")
        lines.append("")
    if normal:
        lines.append(f"🟢 *Normal: {len(normal)} values*")
        lines.append("")
    lines.append("_For information only. Always consult your doctor._")
    return "\n".join(lines)


def render_param_card(p: dict):
    status = p.get("status", "normal")
    badge  = _status_badge(status)
    unit   = p.get("unit", "")
    val_display = f"{p['value']} {unit}".strip()

    ref_low, ref_high = p.get("ref_low"), p.get("ref_high")
    ref_str = ""
    if ref_low is not None and ref_high is not None:
        ref_str = f'<span class="ref-range">Reference: {ref_low}–{ref_high} {unit}</span>'

    low_conf = p.get("low_confidence", False)
    conf_badge = '<span class="low-conf-badge">⚠ Verify</span>' if low_conf else ""

    what = p.get("what_it_is", "")
    your = p.get("your_result", "")

    st.markdown(f"""
<div class="param-card {status}">
  <div class="param-name">{p['name']} &nbsp; {badge} &nbsp; {conf_badge}</div>
  <div class="param-value"><b>{val_display}</b> {ref_str}</div>
  <div><span class="what-label">What it measures:</span></div>
  <div class="explanation">{what}</div>
  <div class="your-result">{your}</div>
</div>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
for key in ("params", "report_type", "error"):
    if key not in st.session_state:
        st.session_state[key] = None
if "manual_rows" not in st.session_state:
    st.session_state.manual_rows = [{"name": "", "value": "", "unit": "", "ref_low": "", "ref_high": ""}]

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-card">
  <h1>🩺 ClarityMed</h1>
  <p>Understand your lab report in plain language — in under 15 seconds.</p>
</div>
""", unsafe_allow_html=True)

# ── Settings row ──────────────────────────────────────────────────────────────
col_lang, col_age, col_gender = st.columns([1, 1, 1])
with col_lang:
    lang_choice = st.selectbox("Language", list(LANG_CODES.keys()), index=0)
with col_age:
    age = st.number_input("Age (optional)", min_value=1, max_value=120, value=None, step=1)
with col_gender:
    gender = st.selectbox("Gender (optional)", ["Not specified", "Male", "Female", "Other"])
    if gender == "Not specified":
        gender = None

language = LANG_CODES[lang_choice]

# ── Upload section ────────────────────────────────────────────────────────────
with st.expander("📸 Tips for uploading a photo of a printed report", expanded=False):
    for tip in PHOTO_TIPS:
        st.markdown(f"- {tip}")

uploaded = st.file_uploader(
    "Upload your lab report (PDF, JPG, PNG, HEIC — up to 10 MB)",
    type=["pdf", "jpg", "jpeg", "png", "heic"],
)

analyze_btn = st.button("🔍 Analyse Report", type="primary", disabled=uploaded is None, use_container_width=True)

# ── Manual entry fallback ─────────────────────────────────────────────────────
with st.expander("✏️ Or enter values manually (for handwritten or unclear reports)", expanded=False):
    st.caption("Add one row per test. Press + to add more.")

    rows_to_keep = []
    for i, row in enumerate(st.session_state.manual_rows):
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1.5, 1.5, 1.5, 0.6])
        name = c1.text_input("Test name", value=row["name"], key=f"mn_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder="e.g. HbA1c")
        val  = c2.text_input("Value", value=row["value"], key=f"mv_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder="e.g. 7.8")
        unit = c3.text_input("Unit", value=row["unit"], key=f"mu_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder="e.g. %")
        rl   = c4.text_input("Ref low", value=row["ref_low"], key=f"rl_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder="4.0")
        rh   = c5.text_input("Ref high", value=row["ref_high"], key=f"rh_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder="6.0")
        keep = True
        if i > 0 and c6.button("✕", key=f"del_{i}"):
            keep = False
        if keep:
            rows_to_keep.append({"name": name, "value": val, "unit": unit, "ref_low": rl, "ref_high": rh})

    st.session_state.manual_rows = rows_to_keep

    col_add, col_analyse = st.columns([1, 2])
    if col_add.button("+ Add row"):
        st.session_state.manual_rows.append({"name": "", "value": "", "unit": "", "ref_low": "", "ref_high": ""})
        st.rerun()

    if col_analyse.button("Analyse Manual Entry", use_container_width=True):
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
                    explained = explain_parameters(annotated, age=age, gender=gender, language=language)
                    st.session_state.params = explained
                    st.session_state.report_type = "Manual Entry"
                    st.session_state.error = None
                except Exception as e:
                    st.session_state.error = str(e)

# ── Analyse uploaded file ─────────────────────────────────────────────────────
if analyze_btn and uploaded:
    st.session_state.params = None
    st.session_state.error = None
    file_bytes = uploaded.read()
    suffix = uploaded.name.rsplit(".", 1)[-1].lower()
    mime_map = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "heic": "image/heic"}
    mime = mime_map.get(suffix, "image/jpeg")

    progress = st.progress(0, text="📖 Reading your report…")
    try:
        progress.progress(20, text="🔍 Extracting test parameters…")
        params, report_type = extract_parameters(file_bytes, mime)
        progress.progress(55, text="📊 Analysing values against reference ranges…")
        annotated = annotate_status(params)
        progress.progress(75, text="✍️ Generating plain-language explanations…")
        explained = explain_parameters(annotated, age=age, gender=gender, language=language)
        progress.progress(100, text="✅ Done!")
        st.session_state.params = explained
        st.session_state.report_type = report_type
        progress.empty()
    except Exception as e:
        progress.empty()
        st.session_state.error = str(e)

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.error:
    st.error(f"❌ {st.session_state.error}")
    st.info("💡 Try a clearer image, or use **manual entry** above.")

if st.session_state.params:
    params = st.session_state.params
    report_type = st.session_state.report_type or "Lab Report"

    # Detection banner
    st.markdown(
        f'<div class="detection-banner">✅ Detected: <b>{report_type}</b> · {len(params)} parameters found</div>',
        unsafe_allow_html=True,
    )

    # Counts
    counts = {"normal": 0, "monitor": 0, "see_doctor": 0}
    for p in params:
        counts[p.get("status", "normal")] = counts.get(p.get("status", "normal"), 0) + 1

    # Summary chips
    chips_html = '<div class="summary-row">'
    if counts["see_doctor"]:
        chips_html += f'<span class="chip chip-see_doctor">🔴 {counts["see_doctor"]} See Doctor</span>'
    if counts["monitor"]:
        chips_html += f'<span class="chip chip-monitor">🟡 {counts["monitor"]} Monitor</span>'
    if counts["normal"]:
        chips_html += f'<span class="chip chip-normal">🟢 {counts["normal"]} Normal</span>'
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

    # Urgent banner
    if counts["see_doctor"] >= 5:
        st.markdown(
            '<div class="urgent-banner">⚠️ Several values need attention — please consult your doctor before making any health decisions.</div>',
            unsafe_allow_html=True,
        )

    # Low-confidence warning
    low_conf_count = sum(1 for p in params if p.get("low_confidence"))
    if low_conf_count > len(params) * 0.3:
        st.warning(f"⚠️ {low_conf_count} values could not be read clearly. Please verify against your original report.")

    # Sort: see_doctor → monitor → normal
    sort_order = {"see_doctor": 0, "monitor": 1, "normal": 2}
    sorted_params = sorted(params, key=lambda p: sort_order.get(p.get("status", "normal"), 2))

    # Action buttons row
    wa_text = _build_whatsapp_text(report_type, sorted_params)
    wa_url = "https://wa.me/?text=" + wa_text.replace(" ", "%20").replace("\n", "%0A")
    pdf_bytes = generate_pdf(report_type, sorted_params)

    col_share, col_pdf = st.columns(2)
    col_share.link_button("📲 Share on WhatsApp", wa_url, use_container_width=True)
    col_pdf.download_button(
        "📄 Download PDF",
        data=pdf_bytes,
        file_name=f"ClarityMed_{report_type.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    with st.expander("📋 Copy summary text"):
        st.text_area("Summary", value=wa_text, height=180, label_visibility="collapsed", key="copy_area")

    st.divider()

    for p in sorted_params:
        render_param_card(p)

    # Disclaimer
    st.markdown(f'<div class="disclaimer-box">ℹ️ {DISCLAIMER}</div>', unsafe_allow_html=True)
