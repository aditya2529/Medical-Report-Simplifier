# 🩺 ClarityMed — Medical Report Simplifier

> Upload a lab report → get plain-language explanations in English or Hindi → share on WhatsApp.

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)]()

## 🎯 What it does

Medical lab reports in India use clinical language that most patients can't understand. **ClarityMed** turns them into plain English or Hindi:

- 📤 Upload your **PDF / JPG / PNG** lab report
- 🔍 AI extracts every test parameter (CBC, Lipid, Thyroid, LFT, KFT, etc.)
- 🎨 Each value is color-coded: **🟢 Normal · 🟡 Monitor · 🔴 See Doctor**
- ✍️ Get a 2-line explanation of what each value means for *you*
- 🇮🇳 One-tap Hindi toggle (proper Devanagari, not transliteration)
- 📲 Share summary via WhatsApp, or download as PDF
- ✏️ Manual entry fallback for unclear scans

## ⚙️ Tech stack

| Layer | Tech | Why |
|---|---|---|
| UI | Streamlit | Fast build, mobile-friendly |
| Vision | Groq + Llama 4 Scout 17B | Free tier, reads images/PDFs |
| Text | Groq + Llama 3.1 8B | Fast, free |
| Hindi | Groq + Llama 4 Scout 17B | Better Devanagari than 8B |
| PDF parsing | PyMuPDF | Multi-page support |
| PDF export | fpdf2 + Noto Sans (Devanagari) | Proper Hindi rendering |

**Total cost: ₹0/month** (free tiers for everything).

## 🚀 Run locally

```bash
git clone https://github.com/aditya2529/Medical-Report-Simplifier.git
cd Medical-Report-Simplifier
pip install -r requirements.txt
```

Create a `.env` file:
```env
GROQ_API_KEY=your_groq_key_from_console.groq.com
```

Then:
```bash
streamlit run app.py
```

## 📦 Sample reports

The repo includes 5 sample lab reports to test with:
- `sample_CBC_report.pdf` — Complete Blood Count
- `sample_Lipid_report.pdf` — Lipid Profile
- `sample_Thyroid_report.pdf` — Thyroid Function Test
- `sample_LFT_report.pdf` — Liver Function Test
- `sample_KFT_report.pdf` — Kidney Function Test

## 🛡️ Privacy & disclaimer

- **No data stored.** Reports are processed in-memory and discarded.
- **No signup, no tracking.**
- This is **not medical advice.** ClarityMed explains values in plain language. Always consult a qualified doctor before any health decision.

## 🤝 Contributing

PRs welcome! Areas that need help:
- More Indian regional languages (Tamil, Marathi, Bengali, Telugu)
- Better extraction for handwritten reports
- Support for X-ray / ultrasound reports
- Test cases for edge-case lab formats
