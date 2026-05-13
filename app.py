import streamlit as st
from extractor import extract_parameters, annotate_status
from explainer import explain_parameters
from pdf_generator import generate_pdf
from translations import t, T

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
  .main .block-container { padding-top: 1.5rem; max-width: 820px; }

  .hero-card {
    background: linear-gradient(135deg, #2163a8 0%, #4a90e2 100%);
    color: white; padding: 24px 26px; border-radius: 14px;
    margin-bottom: 18px; box-shadow: 0 4px 14px rgba(33, 99, 168, 0.15);
  }
  .hero-card h1 { color: white !important; margin: 0 0 6px 0 !important; font-size: 1.85rem !important; }
  .hero-card p  { margin: 0; font-size: 0.98rem; opacity: 0.95; }

  .status-normal      { background:#d4edda; color:#155724; padding:4px 12px; border-radius:14px; font-weight:600; font-size:0.78rem; letter-spacing:.3px; }
  .status-monitor     { background:#fff3cd; color:#856404; padding:4px 12px; border-radius:14px; font-weight:600; font-size:0.78rem; letter-spacing:.3px; }
  .status-see_doctor  { background:#f8d7da; color:#721c24; padding:4px 12px; border-radius:14px; font-weight:600; font-size:0.78rem; letter-spacing:.3px; }

  .param-card {
    border: 1px solid #e6e8eb; border-left: 4px solid #ddd;
    border-radius: 10px; padding: 16px 18px; margin-bottom: 14px;
    background: rgba(255,255,255,0.02);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .param-card:hover { transform: translateY(-1px); box-shadow: 0 3px 10px rgba(0,0,0,0.06); }
  .param-card.see_doctor { border-left-color: #dc3545; }
  .param-card.monitor    { border-left-color: #ffc107; }
  .param-card.normal     { border-left-color: #28a745; }

  .param-name  { font-size:1.08rem; font-weight:700; margin-bottom:5px; }
  .param-value { font-size:0.95rem; color:#666; margin-bottom:10px; }
  .ref-range   { color:#999; font-size:0.82rem; margin-left:6px; }
  .what-label  { font-weight:600; color:#444; font-size:0.88rem; }
  .explanation { font-size:0.93rem; color:#333; line-height:1.6; margin-top:4px; }
  .your-result { font-size:0.93rem; line-height:1.6; margin-top:8px; }
  .low-conf-badge { background:#e2e3e5; color:#383d41; padding:3px 9px; border-radius:8px; font-size:0.74rem; }

  .urgent-banner {
    background: linear-gradient(135deg, #f8d7da 0%, #f5b3b8 100%);
    border:1px solid #f1aeb5; border-radius:10px;
    padding:14px 16px; color:#721c24; font-weight:600; margin-bottom:18px;
  }
  .detection-banner {
    background:#e7f3ff; border:1px solid #b3d7ff; border-radius:10px;
    padding:11px 16px; color:#004085; margin-bottom:14px; font-size:0.95rem;
  }
  .disclaimer-box {
    background:#fff8e1; border-left:4px solid #ffc107;
    padding:13px 16px; border-radius:6px;
    font-size:0.82rem; color:#555; margin-top:32px;
  }

  .summary-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px; }
  .chip { padding:6px 14px; border-radius:18px; font-size:0.85rem; font-weight:600; display:inline-flex; align-items:center; gap:6px; }
  .chip-normal     { background:#d4edda; color:#155724; }
  .chip-monitor    { background:#fff3cd; color:#856404; }
  .chip-see_doctor { background:#f8d7da; color:#721c24; }

  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2163a8 0%, #4a90e2 100%);
    border: none; font-weight: 600;
  }

  @media (max-width: 600px) {
    .hero-card h1 { font-size: 1.4rem !important; }
    .param-name  { font-size: 1rem; }
    .param-card  { padding: 14px 14px; }
  }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
LANG_CODES = {"English": "english", "हिन्दी (Hindi)": "hindi"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _status_badge(status: str, lang: str) -> str:
    label_map = {
        "normal":     t(lang, "normal"),
        "monitor":    t(lang, "monitor"),
        "see_doctor": t(lang, "see_doctor"),
    }
    label = label_map.get(status, status)
    return f'<span class="status-{status}">{label}</span>'


def _build_whatsapp_text(report_type: str, params: list[dict], lang: str) -> str:
    urgent  = [p for p in params if p.get("status") == "see_doctor"]
    monitor = [p for p in params if p.get("status") == "monitor"]
    normal  = [p for p in params if p.get("status") == "normal"]

    lines = [f"🩺 *ClarityMed — {report_type} {t(lang, 'wa_summary')}*", ""]
    if urgent:
        lines.append(t(lang, "wa_attention"))
        for p in urgent:
            lines.append(f"  • {p['name']}: {p['value']} {p.get('unit','')}")
        lines.append("")
    if monitor:
        lines.append(t(lang, "wa_monitor"))
        for p in monitor:
            lines.append(f"  • {p['name']}: {p['value']} {p.get('unit','')}")
        lines.append("")
    if normal:
        lines.append(t(lang, "wa_normal").format(n=len(normal)))
        lines.append("")
    lines.append(t(lang, "wa_disclaimer"))
    return "\n".join(lines)


def render_param_card(p: dict, lang: str):
    status = p.get("status", "normal")
    badge  = _status_badge(status, lang)
    unit   = p.get("unit", "")
    val_display = f"{p['value']} {unit}".strip()

    ref_low, ref_high = p.get("ref_low"), p.get("ref_high")
    ref_str = ""
    if ref_low is not None and ref_high is not None:
        ref_str = f'<span class="ref-range">{t(lang, "reference")}: {ref_low}–{ref_high} {unit}</span>'

    conf_badge = ""
    if p.get("low_confidence"):
        conf_badge = f'<span class="low-conf-badge">{t(lang, "verify_badge")}</span>'

    what = p.get("what_it_is", "")
    your = p.get("your_result", "")

    st.markdown(f"""
<div class="param-card {status}">
  <div class="param-name">{p['name']} &nbsp; {badge} &nbsp; {conf_badge}</div>
  <div class="param-value"><b>{val_display}</b> {ref_str}</div>
  <div><span class="what-label">{t(lang, "what_it_measures")}</span></div>
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

# ── Language picker (always visible up top) ───────────────────────────────────
# Render this BEFORE other UI so language switch reflows everything below
lang_label_col, _ = st.columns([1, 2])
with lang_label_col:
    lang_choice = st.selectbox(" ", list(LANG_CODES.keys()), index=0, label_visibility="collapsed")
language = LANG_CODES[lang_choice]
L = lambda key: t(language, key)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-card">
  <h1>{L("app_title")}</h1>
  <p>{L("app_tagline")}</p>
</div>
""", unsafe_allow_html=True)

# ── Settings row ──────────────────────────────────────────────────────────────
col_age, col_gender = st.columns([1, 1])
with col_age:
    age = st.number_input(L("age"), min_value=1, max_value=120, value=None, step=1)
with col_gender:
    gender_opts = T[language]["gender_options"]
    gender_pick = st.selectbox(L("gender"), gender_opts)
    if gender_pick == gender_opts[0]:
        gender = None
    else:
        # Always send English internally to the LLM
        en_opts = T["english"]["gender_options"]
        idx = gender_opts.index(gender_pick)
        gender = en_opts[idx] if idx > 0 else None

# ── Upload section ────────────────────────────────────────────────────────────
with st.expander(L("photo_tips_title"), expanded=False):
    for tip in L("photo_tips"):
        st.markdown(f"- {tip}")

uploaded = st.file_uploader(L("uploader_label"), type=["pdf", "jpg", "jpeg", "png", "heic"])

analyze_btn = st.button(L("analyse_btn"), type="primary", disabled=uploaded is None, use_container_width=True)

# ── Manual entry fallback ─────────────────────────────────────────────────────
with st.expander(L("manual_title"), expanded=False):
    st.caption(L("manual_caption"))

    rows_to_keep = []
    for i, row in enumerate(st.session_state.manual_rows):
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1.5, 1.5, 1.5, 0.6])
        name = c1.text_input(L("col_test"),  value=row["name"], key=f"mn_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder=L("ph_test_name"))
        val  = c2.text_input(L("col_value"), value=row["value"], key=f"mv_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder=L("ph_value"))
        unit = c3.text_input(L("col_unit"),  value=row["unit"], key=f"mu_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder=L("ph_unit"))
        rl   = c4.text_input(L("col_ref_low"),  value=row["ref_low"],  key=f"rl_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder=L("ph_ref_low"))
        rh   = c5.text_input(L("col_ref_high"), value=row["ref_high"], key=f"rh_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder=L("ph_ref_high"))
        keep = True
        if i > 0 and c6.button("✕", key=f"del_{i}"):
            keep = False
        if keep:
            rows_to_keep.append({"name": name, "value": val, "unit": unit, "ref_low": rl, "ref_high": rh})

    st.session_state.manual_rows = rows_to_keep

    col_add, col_analyse = st.columns([1, 2])
    if col_add.button(L("add_row")):
        st.session_state.manual_rows.append({"name": "", "value": "", "unit": "", "ref_low": "", "ref_high": ""})
        st.rerun()

    if col_analyse.button(L("analyse_manual"), use_container_width=True):
        manual_params = []
        for row in st.session_state.manual_rows:
            if not row["name"] or not row["value"]:
                continue
            try:
                rl = float(row["ref_low"])  if row["ref_low"]  else None
                rh = float(row["ref_high"]) if row["ref_high"] else None
            except ValueError:
                rl = rh = None
            manual_params.append({
                "name": row["name"], "value": row["value"], "unit": row["unit"],
                "ref_low": rl, "ref_high": rh, "flag": "",
            })
        if not manual_params:
            st.warning(L("manual_warn"))
        else:
            with st.spinner(L("p_explaining")):
                try:
                    annotated = annotate_status(manual_params)
                    explained = explain_parameters(annotated, age=age, gender=gender, language=language)
                    st.session_state.params = explained
                    st.session_state.report_type = L("manual_report_type")
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

    progress = st.progress(0, text=L("p_reading"))
    try:
        progress.progress(20, text=L("p_extracting"))
        params, report_type = extract_parameters(file_bytes, mime)
        progress.progress(55, text=L("p_analysing"))
        annotated = annotate_status(params)
        progress.progress(75, text=L("p_explaining"))
        explained = explain_parameters(annotated, age=age, gender=gender, language=language)
        progress.progress(100, text=L("p_done"))
        st.session_state.params = explained
        st.session_state.report_type = report_type
        progress.empty()
    except Exception as e:
        progress.empty()
        st.session_state.error = str(e)

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.error:
    st.error(f"{L('err_prefix')} {st.session_state.error}")
    st.info(L("err_hint"))

if st.session_state.params:
    params = st.session_state.params
    report_type = st.session_state.report_type or "Lab Report"

    st.markdown(
        f'<div class="detection-banner">✅ {L("detected")}: <b>{report_type}</b> · {len(params)} {L("params_found")}</div>',
        unsafe_allow_html=True,
    )

    counts = {"normal": 0, "monitor": 0, "see_doctor": 0}
    for p in params:
        counts[p.get("status", "normal")] = counts.get(p.get("status", "normal"), 0) + 1

    chips_html = '<div class="summary-row">'
    if counts["see_doctor"]:
        chips_html += f'<span class="chip chip-see_doctor">🔴 {counts["see_doctor"]} {L("see_doctor")}</span>'
    if counts["monitor"]:
        chips_html += f'<span class="chip chip-monitor">🟡 {counts["monitor"]} {L("monitor")}</span>'
    if counts["normal"]:
        chips_html += f'<span class="chip chip-normal">🟢 {counts["normal"]} {L("normal")}</span>'
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

    if counts["see_doctor"] >= 5:
        st.markdown(f'<div class="urgent-banner">{L("urgent_banner")}</div>', unsafe_allow_html=True)

    low_conf_count = sum(1 for p in params if p.get("low_confidence"))
    if low_conf_count > len(params) * 0.3:
        st.warning(f"⚠️ {low_conf_count} {L('low_conf_warn')}")

    sort_order = {"see_doctor": 0, "monitor": 1, "normal": 2}
    sorted_params = sorted(params, key=lambda p: sort_order.get(p.get("status", "normal"), 2))

    wa_text = _build_whatsapp_text(report_type, sorted_params, language)
    wa_url = "https://wa.me/?text=" + wa_text.replace(" ", "%20").replace("\n", "%0A")
    pdf_bytes = generate_pdf(report_type, sorted_params)

    col_share, col_pdf = st.columns(2)
    col_share.link_button(L("share_whatsapp"), wa_url, use_container_width=True)
    col_pdf.download_button(
        L("download_pdf"),
        data=pdf_bytes,
        file_name=f"ClarityMed_{report_type.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    with st.expander(L("copy_summary")):
        st.text_area("Summary", value=wa_text, height=180, label_visibility="collapsed", key="copy_area")

    st.divider()

    for p in sorted_params:
        render_param_card(p, language)

    st.markdown(f'<div class="disclaimer-box">ℹ️ {L("disclaimer")}</div>', unsafe_allow_html=True)
