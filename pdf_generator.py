"""Generates a downloadable simplified PDF of the analysed report."""
import io
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime


STATUS_COLORS = {
    "normal":     (212, 237, 218),   # green
    "monitor":    (255, 243, 205),   # amber
    "see_doctor": (248, 215, 218),   # red
}

STATUS_LABELS = {
    "normal":     "NORMAL",
    "monitor":    "MONITOR",
    "see_doctor": "SEE DOCTOR",
}


class ReportPDF(FPDF):
    def header(self):
        self.set_fill_color(33, 99, 168)
        self.rect(0, 0, 210, 22, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(10, 5)
        self.cell(0, 7, "ClarityMed", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.set_x(10)
        self.cell(0, 5, "Your lab report, simplified", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.set_y(26)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(
            0, 5,
            "ClarityMed explains lab values in plain language. It is not a medical diagnosis.",
            align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.cell(0, 5, "Always consult a qualified doctor before making any health decision.", align="C")


def _safe(text: str) -> str:
    """Strip characters not supported by Helvetica's latin-1 encoding."""
    if not text:
        return ""
    return text.encode("latin-1", "replace").decode("latin-1")


def generate_pdf(report_type: str, params: list[dict]) -> bytes:
    pdf = ReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Title block
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _safe(report_type), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Summary counts
    counts = {"normal": 0, "monitor": 0, "see_doctor": 0}
    for p in params:
        counts[p.get("status", "normal")] = counts.get(p.get("status", "normal"), 0) + 1

    pdf.set_font("Helvetica", "B", 10)
    summary = f"Summary:  {counts['normal']} Normal   |   {counts['monitor']} Monitor   |   {counts['see_doctor']} See Doctor"
    pdf.cell(0, 6, _safe(summary), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Sort: see_doctor → monitor → normal
    sort_order = {"see_doctor": 0, "monitor": 1, "normal": 2}
    sorted_params = sorted(params, key=lambda p: sort_order.get(p.get("status", "normal"), 2))

    for p in sorted_params:
        status = p.get("status", "normal")
        r, g, b = STATUS_COLORS[status]

        y_start = pdf.get_y()
        # Calculate height needed
        pdf.set_font("Helvetica", "B", 11)
        name_h = 6
        pdf.set_font("Helvetica", "", 9)
        what = _safe(p.get("what_it_is", ""))
        your = _safe(p.get("your_result", ""))
        # Approximate height
        block_h = name_h + 6 + 6 + (len(what) // 80 + 1) * 5 + (len(your) // 80 + 1) * 5 + 4

        if pdf.get_y() + block_h > 270:
            pdf.add_page()

        # Background
        y_start = pdf.get_y()
        pdf.set_fill_color(r, g, b)
        pdf.rect(10, y_start, 190, block_h, "F")
        pdf.set_x(13)
        pdf.set_y(y_start + 2)

        # Name + badge
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(120, 6, _safe(p["name"]), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(60, 6, _safe(STATUS_LABELS[status]), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

        # Value
        pdf.set_x(13)
        pdf.set_font("Helvetica", "", 9)
        unit = p.get("unit", "")
        val_line = f"Result: {p['value']} {unit}"
        if p.get("ref_low") is not None and p.get("ref_high") is not None:
            val_line += f"   (Reference: {p['ref_low']} - {p['ref_high']} {unit})"
        pdf.cell(0, 5, _safe(val_line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # What it is
        pdf.set_x(13)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(28, 5, "What it measures:", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(159, 5, _safe(what))

        # Your result
        pdf.set_x(13)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(184, 5, _safe(your))

        pdf.ln(3)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
