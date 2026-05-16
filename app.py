import hashlib
import html
import json
import logging
from urllib.parse import quote

import streamlit as st
from extractor import extract_parameters, annotate_status
from explainer import explain_parameters
from llm_client import LLMBusyError
from pdf_generator import generate_pdf
from translations import t, T

logger = logging.getLogger(__name__)
# Audit #8: enforce 5 MB cap on uploads
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

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

  /* Audit #33 — info-tool strap line, sits right under hero */
  .info-strap {
    background:#eef4fb; border:1px solid #cfe0f3; border-radius:8px;
    padding:9px 14px; color:#1f3e6b; font-size:0.86rem;
    margin-bottom:14px; text-align:center;
  }
  /* Audit #34 — trust pill strip */
  .trust-row { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; margin:6px 0 16px; }
  .trust-pill {
    background:#f5f7fa; border:1px solid #d8dde5; border-radius:14px;
    padding:4px 10px; font-size:0.78rem; color:#3c4a5e;
  }
  /* Audit #1/#11 — discreet author footer */
  .author-footer {
    margin-top:36px; padding-top:14px; border-top:1px solid #eee;
    text-align:center; font-size:0.78rem; color:#7a7a7a;
  }
  .author-footer a { color:#2163a8; text-decoration:none; margin:0 6px; }
  .detection-banner {
    background:#e7f3ff; border:1px solid #b3d7ff; border-radius:10px;
    padding:11px 16px; color:#004085; margin-bottom:14px; font-size:0.95rem;
  }
  .disclaimer-box {
    background:#fff8e1; border-left:4px solid #ffc107;
    padding:13px 16px; border-radius:6px;
    font-size:0.85rem; color:#5a4400; margin-bottom:16px;
    font-weight:500;
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

    /* Audit #13/#16/#17 — manual entry table is unusable on phones.
       Stack any horizontal column row that contains form inputs so each
       field gets full width. Also give all buttons a 48px tap target. */
    [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]),
    [data-testid="stHorizontalBlock"]:has([data-testid="stNumberInput"]) {
      flex-direction: column;
      gap: 8px;
    }
    .stButton > button { min-height: 48px; }
  }

  /* Audit #19 — extra-small phones (320px iPhone SE class). The hero tagline
     was wrapping into 3 lines and pushing the upload zone below the fold. */
  @media (max-width: 380px) {
    .hero-card h1 { font-size: 1.25rem !important; }
    .hero-card p  { font-size: 0.88rem; }
    .hero-card    { padding: 16px 18px; }
  }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
LANG_CODES = {"English": "english", "हिन्दी (Hindi)": "hindi"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _to_float_or_none(x):
    """Coerce a stored manual-entry value (string from a prior text_input
    run, or already-float from st.number_input) into a float or None. Used
    when migrating session_state schema and when reading user input back."""
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


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


# Audit #22 — cached PDF + WhatsApp-text wrappers. Both are pure functions
# of (report_type, params, language); regenerating them on every language
# toggle / expander click cost ~700 ms (PDF) and several ms (WA text) on
# mobile. st.cache_data needs a hashable key, so we serialise params to a
# canonical JSON string. Cache lives in Streamlit's session-scoped store,
# so different users share nothing.
@st.cache_data(show_spinner=False, max_entries=32)
def _cached_generate_pdf(report_type: str, params_json: str, language: str) -> bytes:
    params = json.loads(params_json)
    return generate_pdf(report_type, params, language=language)


@st.cache_data(show_spinner=False, max_entries=32)
def _cached_build_whatsapp_text(report_type: str, params_json: str, language: str) -> str:
    params = json.loads(params_json)
    return _build_whatsapp_text(report_type, params, language)


def render_param_card(p: dict, lang: str):
    # Audit #7 — every PDF-derived string is escaped before going into HTML.
    # Status, badge HTML, ref-range markup, and 'verify_badge' are produced
    # by us and therefore safe; the user-supplied fields are NOT.
    status = p.get("status", "normal")
    badge  = _status_badge(status, lang)
    unit   = p.get("unit", "")
    name_safe = html.escape(str(p.get("name", "")))
    unit_safe = html.escape(str(unit))
    val_safe  = html.escape(f"{p.get('value', '')} {unit}".strip())

    ref_low, ref_high = p.get("ref_low"), p.get("ref_high")
    ref_str = ""
    if ref_low is not None and ref_high is not None:
        ref_str = (f'<span class="ref-range">{t(lang, "reference")}: '
                   f'{html.escape(str(ref_low))}–{html.escape(str(ref_high))} {unit_safe}</span>')
    elif ref_high is not None:
        ref_str = (f'<span class="ref-range">{t(lang, "reference")}: '
                   f'&lt; {html.escape(str(ref_high))} {unit_safe}</span>')
    elif ref_low is not None:
        ref_str = (f'<span class="ref-range">{t(lang, "reference")}: '
                   f'&gt; {html.escape(str(ref_low))} {unit_safe}</span>')

    conf_badge = ""
    if p.get("low_confidence"):
        conf_badge = f'<span class="low-conf-badge">{t(lang, "verify_badge")}</span>'

    what_safe = html.escape(p.get("what_it_is", ""))
    your_safe = html.escape(p.get("your_result", ""))

    st.markdown(f"""
<div class="param-card {status}">
  <div class="param-name">{name_safe} &nbsp; {badge} &nbsp; {conf_badge}</div>
  <div class="param-value"><b>{val_safe}</b> {ref_str}</div>
  <div><span class="what-label">{t(lang, "what_it_measures")}</span></div>
  <div class="explanation">{what_safe}</div>
  <div class="your-result">{your_safe}</div>
</div>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
for key in ("params", "report_type", "error"):
    if key not in st.session_state:
        st.session_state[key] = None
if "manual_rows" not in st.session_state:
    # Audit #16 — value/ref_low/ref_high are numeric; storing None for empty
    # so st.number_input renders a blank field instead of refusing 0.
    st.session_state.manual_rows = [{"name": "", "value": None, "unit": "", "ref_low": None, "ref_high": None}]

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

# Audit #33 — "information tool, not a medical service" strap line BEFORE upload
st.markdown(f'<div class="info-strap">{L("info_tool_strap")}</div>', unsafe_allow_html=True)

# Audit #34 — trust pill strip in the first viewport
st.markdown(
    '<div class="trust-row">'
    f'<span class="trust-pill">{L("trust_made_in")}</span>'
    f'<span class="trust-pill">{L("trust_no_store")}</span>'
    f'<span class="trust-pill">{L("trust_oss")}</span>'
    f'<span class="trust-pill">{L("trust_free")}</span>'
    '</div>',
    unsafe_allow_html=True,
)

# Audit #1 / #11 — "About" expander right above the uploader
with st.expander(L("about_title"), expanded=False):
    st.markdown(L("about_body"))

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
# Audit #14 — photo tips expanded by default; the single most-preventable failure
# (blurry photo) was hidden behind one extra tap before.
with st.expander(L("photo_tips_title"), expanded=True):
    for tip in L("photo_tips"):
        st.markdown(f"- {tip}")

# Audit #31 — let skeptical first-time visitors try a sample without uploading PII
import os as _os
SAMPLE_FILES = [
    ("CBC",     "sample_CBC_report.pdf"),
    ("Lipid",   "sample_Lipid_report.pdf"),
    ("Thyroid", "sample_Thyroid_report.pdf"),
    ("Liver",   "sample_LFT_report.pdf"),
    ("Kidney",  "sample_KFT_report.pdf"),
]
_existing_samples = [(lab, fn) for lab, fn in SAMPLE_FILES if _os.path.exists(fn)]
if _existing_samples:
    st.caption(L("try_sample"))
    cols = st.columns(len(_existing_samples))
    for col, (label, fname) in zip(cols, _existing_samples):
        with open(fname, "rb") as f:
            col.download_button(label, data=f.read(), file_name=fname,
                                use_container_width=True, key=f"sample_{label}")

uploaded = st.file_uploader(L("uploader_label"), type=["pdf", "jpg", "jpeg", "png", "heic"])

# Audit #10 — DPDP consent gate. Analyse button disabled until checkbox is ticked.
# Same checkbox value gates the manual-entry "Analyse" button below.
consent = st.checkbox(L("consent_label"), value=False, key="consent")

analyze_btn = st.button(
    L("analyse_btn"),
    type="primary",
    disabled=(uploaded is None) or (not consent),
    use_container_width=True,
)

# ── Manual entry fallback ─────────────────────────────────────────────────────
with st.expander(L("manual_title"), expanded=False):
    st.caption(L("manual_caption"))

    rows_to_keep = []
    for i, row in enumerate(st.session_state.manual_rows):
        # Audit #17 — delete column widened 0.6 → 1.0 so the ✕ button has a
        # 48px tap target on mobile (CSS bumps min-height too).
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1.5, 1.5, 1.5, 1.0])
        name = c1.text_input(L("col_test"),  value=row["name"], key=f"mn_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder=L("ph_test_name"))
        # Audit #16 — numeric fields use st.number_input so mobile browsers
        # show the numeric keyboard instead of the full alphanumeric keyboard.
        # No `placeholder=` support on number_input; the label still acts as a hint.
        val  = c2.number_input(L("col_value"), value=_to_float_or_none(row["value"]),
                               step=0.01, format="%g", key=f"mv_{i}",
                               label_visibility="collapsed" if i > 0 else "visible")
        unit = c3.text_input(L("col_unit"),  value=row["unit"], key=f"mu_{i}",
                             label_visibility="collapsed" if i > 0 else "visible",
                             placeholder=L("ph_unit"))
        rl   = c4.number_input(L("col_ref_low"),  value=_to_float_or_none(row["ref_low"]),
                               step=0.01, format="%g", key=f"rl_{i}",
                               label_visibility="collapsed" if i > 0 else "visible")
        rh   = c5.number_input(L("col_ref_high"), value=_to_float_or_none(row["ref_high"]),
                               step=0.01, format="%g", key=f"rh_{i}",
                               label_visibility="collapsed" if i > 0 else "visible")
        keep = True
        if i > 0 and c6.button("✕", key=f"del_{i}"):
            keep = False
        if keep:
            rows_to_keep.append({"name": name, "value": val, "unit": unit, "ref_low": rl, "ref_high": rh})

    st.session_state.manual_rows = rows_to_keep

    col_add, col_analyse = st.columns([1, 2])
    if col_add.button(L("add_row")):
        st.session_state.manual_rows.append({"name": "", "value": None, "unit": "", "ref_low": None, "ref_high": None})
        st.rerun()

    # Audit #10 — manual entry also ships data to Groq, so same consent gate applies.
    if col_analyse.button(L("analyse_manual"), use_container_width=True, disabled=not consent):
        manual_params = []
        for row in st.session_state.manual_rows:
            # Audit #16 — value/ref fields are now floats-or-None from
            # st.number_input. Skip rows missing name or value.
            if not row["name"] or row["value"] in (None, ""):
                continue
            manual_params.append({
                "name": row["name"], "value": row["value"], "unit": row["unit"],
                "ref_low": _to_float_or_none(row["ref_low"]),
                "ref_high": _to_float_or_none(row["ref_high"]),
                "flag": "",
            })
        if not manual_params:
            st.warning(L("manual_warn"))
        else:
            # Audit #20 — same slow-network reassurance as the upload path.
            hint = st.empty()
            hint.caption(f"⏳ {L('slow_hint')}")
            with st.spinner(L("p_explaining")):
                try:
                    annotated = annotate_status(manual_params)
                    explained = explain_parameters(annotated, age=age, gender=gender, language=language)
                    st.session_state.params = explained
                    st.session_state.report_type = L("manual_report_type")
                    st.session_state.error = None
                except LLMBusyError:
                    # Audit #23 — rate-limit-specific message.
                    logger.warning("Manual analysis: LLM busy (rate-limited)")
                    st.session_state.error = L("err_busy")
                except Exception:
                    logger.exception("Manual analysis failed")
                    st.session_state.error = L("err_generic")
                finally:
                    hint.empty()

# ── Analyse uploaded file ─────────────────────────────────────────────────────
if analyze_btn and uploaded:
    file_bytes = uploaded.read()
    # Audit #8 — reject files >5MB at the boundary, before any LLM/image work.
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        st.error(f"{L('err_prefix')} {L('err_too_large')}")
        st.stop()

    # Audit #24 — Streamlit reruns the whole script on every widget change
    # (language toggle, expander click, etc.), and `analyze_btn` stays True
    # for a rerun cycle. Without a gate, the full pipeline re-fired and
    # burned another Groq call on every interaction. Hash the file bytes +
    # language and only re-run when one of them actually changed.
    current_hash = hashlib.md5(file_bytes + language.encode()).hexdigest()
    if st.session_state.get("last_analysis_hash") != current_hash:
        st.session_state.last_analysis_hash = current_hash
        st.session_state.params = None
        st.session_state.error = None
        suffix = uploaded.name.rsplit(".", 1)[-1].lower()
        mime_map = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "heic": "image/heic"}
        mime = mime_map.get(suffix, "image/jpeg")

        # Audit #20 — discrete progress jumps (20%, 55%, 75%) implied an
        # accuracy we didn't have; the bar froze for 8–15s at each tier on
        # slow connections, which looked broken. A spinner + a slow-network
        # reassurance line is honest and works the same on every connection.
        hint = st.empty()
        hint.caption(f"⏳ {L('slow_hint')}")
        with st.spinner(L("p_explaining")):
            try:
                params, report_type = extract_parameters(file_bytes, mime)
                annotated = annotate_status(params)
                explained = explain_parameters(annotated, age=age, gender=gender, language=language)
                st.session_state.params = explained
                st.session_state.report_type = report_type
            except LLMBusyError:
                # Audit #23 — rate-limit-specific message so the user waits, not re-uploads.
                logger.warning("Upload analysis: LLM busy (rate-limited)")
                st.session_state.error = L("err_busy")
                # Clear the hash so a retry actually re-runs the pipeline.
                st.session_state.last_analysis_hash = None
            except Exception:
                # Audit #9 — never surface raw exception strings to the UI. Full
                # traceback is logged server-side for the developer.
                logger.exception("Upload analysis failed")
                st.session_state.error = L("err_generic")
                st.session_state.last_analysis_hash = None
            finally:
                hint.empty()

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.error:
    st.error(f"{L('err_prefix')} {st.session_state.error}")
    st.info(L("err_hint"))

if st.session_state.params:
    params = st.session_state.params
    report_type = st.session_state.report_type or "Lab Report"

    # Audit #3 — disclaimer renders ABOVE the chips/cards, not below.
    st.markdown(f'<div class="disclaimer-box">ℹ️ {L("disclaimer")}</div>', unsafe_allow_html=True)

    # Audit #7 — report_type is OCR'd from the user's PDF, escape before inlining
    st.markdown(
        f'<div class="detection-banner">✅ {L("detected")}: '
        f'<b>{html.escape(str(report_type))}</b> · '
        f'{len(params)} {L("params_found")}</div>',
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

    # Audit #22 — cache PDF + WhatsApp text on the (report_type, params, language)
    # tuple. Language toggle, expander clicks, and other widget reruns now reuse
    # the prior result instead of regenerating (~700 ms / PDF on mobile).
    params_key = json.dumps(sorted_params, sort_keys=True, default=str)
    wa_text = _cached_build_whatsapp_text(report_type, params_key, language)
    # Audit #18 — replace the naive 2-char .replace() with urllib.parse.quote.
    # The old version mangled Devanagari (`आ` became `%E0%A4%86` only by
    # accident if the byte happened to be a space), broke on `&`/`#`/`*`,
    # and produced invalid URLs for emoji. quote() with safe='' is the
    # WhatsApp-documented encoding for share links.
    wa_url = "https://wa.me/?text=" + quote(wa_text, safe='')
    pdf_bytes = _cached_generate_pdf(report_type, params_key, language)

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

# Audit #1/#11 — author footer with real identity, GitHub source, privacy link.
# Renders on EVERY page state (with or without a parsed report).
st.markdown(
    '<div class="author-footer">'
    f'{L("built_by")} <b>Aditya Kumar</b> · '
    f'<a href="https://github.com/aditya2529/Medical-Report-Simplifier" target="_blank">{L("footer_source")}</a> · '
    f'<a href="https://github.com/aditya2529/Medical-Report-Simplifier/blob/main/PRIVACY.md" target="_blank">{L("footer_privacy")}</a> · '
    f'<a href="mailto:aditya2529@gmail.com">aditya2529@gmail.com</a>'
    '</div>',
    unsafe_allow_html=True,
)
