from fpdf import FPDF
from datetime import date

class SampleReport(FPDF):
    def header(self):
        self.set_fill_color(0, 102, 153)
        self.rect(0, 0, 210, 28, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(10, 6)
        self.cell(0, 8, "SRL Diagnostics", ln=True)
        self.set_font("Helvetica", "", 9)
        self.set_x(10)
        self.cell(0, 5, "12, MG Road, Bangalore - 560001 | Tel: 1800-102-0990 | www.srlworld.com", ln=True)
        self.set_text_color(0, 0, 0)
        self.set_y(32)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "This report is generated for testing purposes only. Not a real medical report.", align="C")


pdf = SampleReport()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# ── Patient Info ──────────────────────────────────────────────────────────────
pdf.set_font("Helvetica", "B", 10)
pdf.set_fill_color(240, 248, 255)
pdf.rect(10, 34, 190, 28, 'F')
pdf.set_xy(12, 36)

info = [
    ("Patient Name", "Rahul Mehta"),        ("Age / Gender", "34 Years / Male"),
    ("Sample ID",    "SRL-2026-084521"),    ("Ref. Doctor",   "Dr. Priya Sharma"),
    ("Collected",    "06-May-2026, 07:30"), ("Reported",      "06-May-2026, 11:45"),
]
pdf.set_font("Helvetica", "", 9)
for i, (label, value) in enumerate(info):
    col = i % 2
    row = i // 2
    x = 12 + col * 95
    y = 36 + row * 8
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(35, 6, label + ":", ln=False)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(55, 6, value, ln=False)

pdf.set_y(66)
pdf.ln(2)

# ── Report Title ──────────────────────────────────────────────────────────────
pdf.set_font("Helvetica", "B", 12)
pdf.set_fill_color(0, 102, 153)
pdf.set_text_color(255, 255, 255)
pdf.cell(190, 8, "  COMPLETE BLOOD COUNT (CBC) WITH DIFFERENTIAL", ln=True, fill=True)
pdf.set_text_color(0, 0, 0)
pdf.ln(2)

# ── Table Header ──────────────────────────────────────────────────────────────
pdf.set_font("Helvetica", "B", 9)
pdf.set_fill_color(220, 235, 245)
pdf.cell(75, 7, "Test Parameter", border=1, fill=True)
pdf.cell(35, 7, "Result", border=1, fill=True, align="C")
pdf.cell(25, 7, "Unit", border=1, fill=True, align="C")
pdf.cell(45, 7, "Reference Range", border=1, fill=True, align="C")
pdf.cell(10, 7, "Flag", border=1, fill=True, align="C")
pdf.ln()

# ── CBC Parameters ────────────────────────────────────────────────────────────
# (name, value, unit, ref_range, flag, abnormal)
rows = [
    ("Haemoglobin (Hb)",          "10.8",   "g/dL",       "13.0 – 17.0",   "L",  True),
    ("RBC Count",                  "3.9",    "mill/μL",    "4.5 – 5.9",     "L",  True),
    ("Haematocrit (PCV)",          "34.2",   "%",          "40.0 – 50.0",   "L",  True),
    ("MCV",                        "87.7",   "fL",         "83.0 – 101.0",  "",   False),
    ("MCH",                        "27.7",   "pg",         "27.0 – 32.0",   "",   False),
    ("MCHC",                       "31.6",   "g/dL",       "31.5 – 34.5",   "",   False),
    ("RDW-CV",                     "15.8",   "%",          "11.6 – 14.0",   "H",  True),
    ("WBC Count",                  "11,400", "cells/μL",   "4,000 – 11,000","H",  True),
    ("Neutrophils",                "72.4",   "%",          "40.0 – 70.0",   "H",  True),
    ("Lymphocytes",                "19.2",   "%",          "20.0 – 45.0",   "L",  True),
    ("Monocytes",                  "6.8",    "%",          "2.0 – 10.0",    "",   False),
    ("Eosinophils",                "1.2",    "%",          "1.0 – 6.0",     "",   False),
    ("Basophils",                  "0.4",    "%",          "0.0 – 2.0",     "",   False),
    ("Platelet Count",             "1,42,000","cells/μL",  "1,50,000–4,10,000","L",True),
    ("MPV",                        "9.8",    "fL",         "7.5 – 12.5",    "",   False),
]

pdf.set_font("Helvetica", "", 9)
for i, (name, val, unit, ref, flag, abnormal) in enumerate(rows):
    fill = i % 2 == 0
    if fill:
        pdf.set_fill_color(250, 250, 250)
    else:
        pdf.set_fill_color(255, 255, 255)

    if abnormal:
        pdf.set_text_color(180, 0, 0)
    else:
        pdf.set_text_color(0, 0, 0)

    pdf.cell(75, 6.5, "  " + name, border=1, fill=True)
    pdf.set_font("Helvetica", "B" if abnormal else "", 9)
    pdf.cell(35, 6.5, val, border=1, fill=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(25, 6.5, unit, border=1, fill=True, align="C")
    pdf.cell(45, 6.5, ref, border=1, fill=True, align="C")
    if flag in ("H", "L"):
        pdf.set_text_color(180, 0, 0)
        pdf.set_font("Helvetica", "B", 9)
    pdf.cell(10, 6.5, flag, border=1, fill=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.ln()

pdf.ln(4)

# ── Interpretation note ───────────────────────────────────────────────────────
pdf.set_font("Helvetica", "B", 9)
pdf.set_fill_color(255, 243, 205)
pdf.rect(10, pdf.get_y(), 190, 16, 'F')
pdf.set_x(12)
pdf.cell(0, 5, "Lab Remarks:", ln=True)
pdf.set_font("Helvetica", "", 9)
pdf.set_x(12)
pdf.multi_cell(186, 5,
    "Haemoglobin and RBC count are below normal limits suggestive of mild anaemia. "
    "Elevated WBC count with neutrophilia may indicate an ongoing infection or inflammation. "
    "Platelet count is mildly low. Clinical correlation is advised."
)

pdf.ln(3)
pdf.set_font("Helvetica", "I", 8)
pdf.set_text_color(100, 100, 100)
pdf.set_x(10)
pdf.cell(0, 5, "H = High   |   L = Low   |   Values outside reference range are highlighted in red", ln=True)

out = r"D:\Projects\Medical Report Simplifier\sample_CBC_report.pdf"
pdf.output(out)
print(f"Sample report saved: {out}")
