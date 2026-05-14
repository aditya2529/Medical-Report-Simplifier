"""Generates a downloadable simplified PDF of the analysed report.

Supports both English (Latin) and Hindi (Devanagari) via bundled Noto Sans fonts.
"""
import io
import os
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime


FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

STATUS_COLORS = {
    "normal":     (212, 237, 218),   # green
    "monitor":    (255, 243, 205),   # amber
    "see_doctor": (248, 215, 218),   # red
}

# Localised UI strings inside the PDF
PDF_STRINGS = {
    "english": {
        "tagline":      "Your lab report, simplified",
        "generated":    "Generated on",
        "summary":      "Summary",
        "normal":       "Normal",
        "monitor":      "Monitor",
        "see_doctor":   "See Doctor",
        "see_doctor_b": "SEE DOCTOR",
        "monitor_b":    "MONITOR",
        "normal_b":     "NORMAL",
        "result":       "Result",
        "reference":    "Reference",
        "what":         "What it measures:",
        "footer1":      "ClarityMed explains lab values in plain language. It is not a medical diagnosis.",
        "footer2":      "Always consult a qualified doctor before making any health decision.",
    },
    "hindi": {
        "tagline":      "आपकी लैब रिपोर्ट, सरल भाषा में",
        "generated":    "तैयार किया गया",
        "summary":      "सारांश",
        "normal":       "सामान्य",
        "monitor":      "निगरानी करें",
        "see_doctor":   "डॉक्टर से मिलें",
        "see_doctor_b": "डॉक्टर से मिलें",
        "monitor_b":    "निगरानी करें",
        "normal_b":     "सामान्य",
        "result":       "मान",
        "reference":    "संदर्भ सीमा",
        "what":         "यह क्या मापता है:",
        "footer1":      "यह उपकरण लैब के मानों को सरल भाषा में समझाता है। यह कोई चिकित्सकीय निदान नहीं है।",
        "footer2":      "स्वास्थ्य संबंधी कोई भी निर्णय लेने से पहले हमेशा योग्य डॉक्टर से सलाह लें।",
    },
}

# Detect Devanagari characters
_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
# Split text into contiguous runs of Devanagari vs non-Devanagari
_SPLIT_RE = re.compile(r"([ऀ-ॿ]+)")


def _has_devanagari(text: str) -> bool:
    return bool(text) and bool(_DEVANAGARI_RE.search(text))


def _segments(text: str) -> list[tuple[str, bool]]:
    """Split text into (chunk, is_devanagari) segments so we can switch fonts."""
    if not text:
        return []
    parts = _SPLIT_RE.split(text)
    return [(p, bool(_DEVANAGARI_RE.search(p))) for p in parts if p]


class ReportPDF(FPDF):
    def __init__(self, language: str = "english"):
        super().__init__()
        self.language = language
        self.S = PDF_STRINGS.get(language, PDF_STRINGS["english"])

        # Register Latin font (Noto Sans — supports Unicode fallback gracefully)
        self.add_font("Noto", "",  os.path.join(FONTS_DIR, "NotoSans-Regular.ttf"))
        self.add_font("Noto", "B", os.path.join(FONTS_DIR, "NotoSans-Bold.ttf"))
        # Register Devanagari font
        self.add_font("NotoDev", "",  os.path.join(FONTS_DIR, "NotoSansDevanagari-Regular.ttf"))
        self.add_font("NotoDev", "B", os.path.join(FONTS_DIR, "NotoSansDevanagari-Bold.ttf"))

    def _set_font(self, devanagari: bool, style: str = "", size: int = 10):
        family = "NotoDev" if devanagari else "Noto"
        self.set_font(family, style, size)

    def header(self):
        self.set_fill_color(33, 99, 168)
        self.rect(0, 0, 210, 22, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Noto", "B", 16)
        self.set_xy(10, 5)
        self.cell(0, 7, "ClarityMed", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_x(10)
        self.write_mixed(self.S["tagline"], 5, style="", size=9)
        self.ln()
        self.set_text_color(0, 0, 0)
        self.set_y(26)

    def footer(self):
        self.set_y(-15)
        self.set_text_color(120, 120, 120)
        # Center-aligned footers — use a full-width cell with the right font
        for line in (self.S["footer1"], self.S["footer2"]):
            self._set_font(_has_devanagari(line), "", 8)
            self.cell(0, 5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def write_mixed(self, text: str, h: float = 5, style: str = "", size: int = 10):
        """Write text inline, switching font per script segment (no new line)."""
        for chunk, is_dev in _segments(text):
            self._set_font(is_dev, style, size)
            self.write(h, chunk)

    def multi_mixed(self, text: str, w: float, h: float = 5, style: str = "", size: int = 10):
        """Multi-line write with per-segment font switching.

        Approach: render the whole string with the dominant font; if the string
        is mixed we still need a single multi_cell call for proper wrapping.
        We pick the font based on what fraction of the text is Devanagari.
        """
        if not text:
            return
        # If the string is purely one script, easy case
        has_dev = _has_devanagari(text)
        has_latin = bool(re.search(r"[A-Za-z]", text))
        if not (has_dev and has_latin):
            self._set_font(has_dev, style, size)
            self.multi_cell(w, h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            return

        # Mixed script — write inline by segments with manual line breaks
        x0 = self.get_x()
        for chunk, is_dev in _segments(text):
            self._set_font(is_dev, style, size)
            # Word-wrap inside this chunk
            words = re.findall(r"\S+\s*", chunk)
            if not words:
                continue
            for word in words:
                word_w = self.get_string_width(word)
                # Wrap if past right margin
                if self.get_x() + word_w > x0 + w:
                    self.ln(h)
                    self.set_x(x0)
                self.write(h, word)
        self.ln(h)


def generate_pdf(report_type: str, params: list[dict], language: str = "english") -> bytes:
    pdf = ReportPDF(language=language)
    S = pdf.S
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=22)

    # Title block (report name) — may be mixed script
    pdf.set_x(10)
    pdf.write_mixed(report_type, h=8, style="B", size=13)
    pdf.ln(10)

    pdf.set_text_color(110, 110, 110)
    # Use numeric date format to avoid Latin month names in Hindi PDF
    date_str = datetime.now().strftime("%d/%m/%Y, %H:%M")
    timestamp = f"{S['generated']} {date_str}"
    pdf.set_x(10)
    pdf.write_mixed(timestamp, h=5, size=9)
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # Summary counts
    counts = {"normal": 0, "monitor": 0, "see_doctor": 0}
    for p in params:
        s = p.get("status", "normal")
        counts[s] = counts.get(s, 0) + 1

    summary = (
        f"{S['summary']}:  {counts['normal']} {S['normal']}   |   "
        f"{counts['monitor']} {S['monitor']}   |   "
        f"{counts['see_doctor']} {S['see_doctor']}"
    )
    pdf.set_x(10)
    pdf.write_mixed(summary, h=6, style="B", size=10)
    pdf.ln(8)

    sort_order = {"see_doctor": 0, "monitor": 1, "normal": 2}
    sorted_params = sorted(params, key=lambda p: sort_order.get(p.get("status", "normal"), 2))

    status_label = {
        "normal":     S["normal_b"],
        "monitor":    S["monitor_b"],
        "see_doctor": S["see_doctor_b"],
    }

    for p in sorted_params:
        status = p.get("status", "normal")
        r, g, b = STATUS_COLORS[status]

        what = p.get("what_it_is", "")
        your = p.get("your_result", "")
        char_per_line = 60
        what_lines = max(1, len(what) // char_per_line + 1)
        your_lines = max(1, len(your) // char_per_line + 1)
        block_h = 8 + 7 + (what_lines * 5) + (your_lines * 5) + 8

        if pdf.get_y() + block_h > 268:
            pdf.add_page()

        y_start = pdf.get_y()
        pdf.set_fill_color(r, g, b)
        pdf.rect(10, y_start, 190, block_h, "F")
        pdf.set_xy(13, y_start + 2)

        # Name (left). Parameter name is always English from the report.
        name_text = p["name"]
        pdf._set_font(False, "B", 11)  # Latin font for parameter name
        pdf.cell(120, 6, name_text, new_x=XPos.RIGHT, new_y=YPos.TOP)
        # Status badge (right) — may be Hindi
        pdf.set_text_color(80, 80, 80)
        badge = status_label[status]
        pdf._set_font(_has_devanagari(badge), "B", 8)
        pdf.cell(60, 6, badge, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

        # Result line (mixed: Hindi label + Latin numbers/units)
        pdf.set_x(13)
        unit = p.get("unit", "")
        ref_low, ref_high = p.get("ref_low"), p.get("ref_high")
        val_line = f"{S['result']}: {p['value']} {unit}"
        if ref_low is not None and ref_high is not None:
            val_line += f"   ({S['reference']}: {ref_low} - {ref_high} {unit})"
        pdf.write_mixed(val_line, h=5, size=9)
        pdf.ln(5)

        # "What it measures:" label
        pdf.set_x(13)
        pdf.write_mixed(S["what"], h=5, style="B", size=9)
        pdf.ln(5)

        # What it measures content (multi-line, possibly mixed script)
        pdf.set_x(13)
        pdf.multi_mixed(what, w=184, h=5, size=9)

        # Your result content
        pdf.set_x(13)
        pdf.multi_mixed(your, w=184, h=5, size=9)

        pdf.ln(2)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
