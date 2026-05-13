"""Generates sample lab report PDFs for testing different report types."""
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


class SampleReport(FPDF):
    def __init__(self, lab_name="SRL Diagnostics"):
        super().__init__()
        self.lab_name = lab_name

    def header(self):
        self.set_fill_color(0, 102, 153)
        self.rect(0, 0, 210, 28, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(10, 6)
        self.cell(0, 8, self.lab_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.set_x(10)
        self.cell(0, 5, "12, MG Road, Bangalore - 560001  |  Tel: 1800-102-0990",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.set_y(32)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "SAMPLE REPORT - For testing purposes only.", align="C")


def make_report(filename, title, patient_info, rows, remarks, lab_name="SRL Diagnostics"):
    pdf = SampleReport(lab_name)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Patient info box
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(10, 34, 190, 28, "F")
    for i, (label, value) in enumerate(patient_info):
        col, row = i % 2, i // 2
        pdf.set_xy(12 + col * 95, 36 + row * 8)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(35, 6, label + ":", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(55, 6, value, new_x=XPos.RIGHT, new_y=YPos.TOP)

    pdf.set_y(66)
    pdf.ln(2)

    # Title
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(0, 102, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, f"  {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(220, 235, 245)
    for col, w in [("Test Parameter", 75), ("Result", 35), ("Unit", 25), ("Reference Range", 45), ("Flag", 10)]:
        pdf.cell(w, 7, col, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for i, (name, val, unit, ref, flag, ab) in enumerate(rows):
        pdf.set_fill_color(250, 250, 250) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(180, 0, 0) if ab else pdf.set_text_color(0, 0, 0)
        pdf.cell(75, 6.5, "  " + name, border=1, fill=True)
        pdf.set_font("Helvetica", "B" if ab else "", 9)
        pdf.cell(35, 6.5, val, border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(25, 6.5, unit, border=1, fill=True, align="C")
        pdf.cell(45, 6.5, ref, border=1, fill=True, align="C")
        if flag:
            pdf.set_text_color(180, 0, 0)
            pdf.set_font("Helvetica", "B", 9)
        pdf.cell(10, 6.5, flag, border=1, fill=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        pdf.ln()

    if remarks:
        pdf.ln(4)
        pdf.set_fill_color(255, 243, 205)
        pdf.rect(10, pdf.get_y(), 190, 18, "F")
        pdf.set_x(12)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, "Lab Remarks:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(12)
        pdf.multi_cell(186, 5, remarks)

    out = os.path.join(OUTPUT_DIR, filename)
    pdf.output(out)
    print(f"Generated: {filename}")


# ── 1. LIPID PROFILE ──────────────────────────────────────────────────────────
make_report(
    "sample_Lipid_report.pdf",
    "LIPID PROFILE",
    [("Patient Name", "Anjali Verma"), ("Age / Gender", "42 Years / Female"),
     ("Sample ID", "SRL-2026-088112"), ("Ref. Doctor", "Dr. Rajesh Singh"),
     ("Collected", "06-May-2026, 08:00"), ("Reported", "06-May-2026, 14:30")],
    [
        ("Total Cholesterol",    "248",  "mg/dL", "< 200",       "H",  True),
        ("LDL Cholesterol",      "168",  "mg/dL", "< 100",       "H",  True),
        ("HDL Cholesterol",      "38",   "mg/dL", "> 40",        "L",  True),
        ("Triglycerides",        "215",  "mg/dL", "< 150",       "H",  True),
        ("VLDL Cholesterol",     "43",   "mg/dL", "< 30",        "H",  True),
        ("Non-HDL Cholesterol",  "210",  "mg/dL", "< 130",       "H",  True),
        ("Cholesterol/HDL Ratio","6.5",  "",      "< 4.5",       "H",  True),
    ],
    "Elevated lipid levels indicate increased cardiovascular risk. Lifestyle modification and clinical correlation advised."
)

# ── 2. THYROID FUNCTION TEST ──────────────────────────────────────────────────
make_report(
    "sample_Thyroid_report.pdf",
    "THYROID FUNCTION TEST (TFT)",
    [("Patient Name", "Sunita Iyer"), ("Age / Gender", "38 Years / Female"),
     ("Sample ID", "SRL-2026-088203"), ("Ref. Doctor", "Dr. Meera Kapoor"),
     ("Collected", "06-May-2026, 07:45"), ("Reported", "06-May-2026, 13:00")],
    [
        ("TSH",          "8.42",  "mIU/L",  "0.4 - 4.0",    "H", True),
        ("Free T3 (FT3)","2.8",   "pg/mL",  "2.0 - 4.4",    "",  False),
        ("Free T4 (FT4)","0.78",  "ng/dL",  "0.8 - 1.8",    "L", True),
        ("Total T3",     "98",    "ng/dL",  "80 - 200",     "",  False),
        ("Total T4",     "5.2",   "ug/dL",  "5.0 - 12.0",   "",  False),
        ("Anti-TPO",     "145",   "IU/mL",  "< 35",         "H", True),
    ],
    "Elevated TSH with low Free T4 suggests primary hypothyroidism. Elevated Anti-TPO suggests autoimmune thyroiditis. Clinical correlation advised."
)

# ── 3. LIVER FUNCTION TEST ────────────────────────────────────────────────────
make_report(
    "sample_LFT_report.pdf",
    "LIVER FUNCTION TEST (LFT)",
    [("Patient Name", "Vikram Joshi"), ("Age / Gender", "51 Years / Male"),
     ("Sample ID", "SRL-2026-088311"), ("Ref. Doctor", "Dr. Arun Patel"),
     ("Collected", "06-May-2026, 09:15"), ("Reported", "06-May-2026, 15:00")],
    [
        ("Total Bilirubin",       "1.8",  "mg/dL", "0.2 - 1.2",   "H", True),
        ("Direct Bilirubin",      "0.6",  "mg/dL", "0.0 - 0.3",   "H", True),
        ("Indirect Bilirubin",    "1.2",  "mg/dL", "0.2 - 0.9",   "H", True),
        ("SGOT (AST)",            "78",   "U/L",   "0 - 40",      "H", True),
        ("SGPT (ALT)",            "102",  "U/L",   "0 - 41",      "H", True),
        ("ALP",                   "115",  "U/L",   "40 - 129",    "",  False),
        ("Total Protein",         "7.2",  "g/dL",  "6.4 - 8.3",   "",  False),
        ("Albumin",               "3.9",  "g/dL",  "3.5 - 5.0",   "",  False),
        ("Globulin",              "3.3",  "g/dL",  "2.0 - 3.5",   "",  False),
        ("A/G Ratio",             "1.2",  "",      "1.0 - 2.1",   "",  False),
    ],
    "Elevated liver enzymes and bilirubin suggest hepatocellular injury. Recommend evaluation for hepatitis, alcohol use, and medications. Clinical correlation advised."
)

# ── 4. KIDNEY FUNCTION TEST ───────────────────────────────────────────────────
make_report(
    "sample_KFT_report.pdf",
    "KIDNEY FUNCTION TEST (KFT/RFT)",
    [("Patient Name", "Ramesh Kumar"), ("Age / Gender", "62 Years / Male"),
     ("Sample ID", "SRL-2026-088459"), ("Ref. Doctor", "Dr. Anita Reddy"),
     ("Collected", "06-May-2026, 08:30"), ("Reported", "06-May-2026, 14:00")],
    [
        ("Serum Creatinine",  "1.6",  "mg/dL",     "0.7 - 1.3",    "H", True),
        ("Blood Urea",        "52",   "mg/dL",     "15 - 40",      "H", True),
        ("BUN",               "24",   "mg/dL",     "7 - 20",       "H", True),
        ("eGFR",              "48",   "mL/min/1.73", "> 90",       "L", True),
        ("Uric Acid",         "7.8",  "mg/dL",     "3.4 - 7.0",    "H", True),
        ("Sodium",            "138",  "mEq/L",     "136 - 145",    "",  False),
        ("Potassium",         "5.4",  "mEq/L",     "3.5 - 5.1",    "H", True),
        ("Chloride",          "104",  "mEq/L",     "98 - 107",     "",  False),
        ("Calcium",           "9.2",  "mg/dL",     "8.6 - 10.3",   "",  False),
        ("Phosphorus",        "4.8",  "mg/dL",     "2.5 - 4.5",    "H", True),
    ],
    "Elevated creatinine and urea with reduced eGFR (48) suggest Stage 3 chronic kidney disease. Hyperkalemia noted. Nephrology consult advised."
)

print("\nAll sample reports generated in:", OUTPUT_DIR)
