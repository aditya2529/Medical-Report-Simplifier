# ClarityMed — Medical Report Simplifier
### Product Spec v1.0 · May 2026

---

## 1. Problem Statement

Medical reports in India are written in clinical language that patients cannot understand. A routine CBC returns 18+ parameters with reference ranges in scientific notation; a lipid panel uses abbreviations like LDL-C, VLDL, and apoB; a discharge summary contains ICD-10 diagnosis codes that mean nothing to a layperson. The result: patients ignore reports until their next appointment, panic unnecessarily about borderline values, or spend ₹500–1,500 on a repeat consultation just to be told "it's fine."

India-specific aggravators compound the problem. Reports from SRL, Dr. Lal PathLabs, Metropolis, and Apollo each use different layouts but the same opaque jargon. Most patients have 10th or 12th standard English literacy — not medical literacy. Reports travel by WhatsApp photo and are read by family members who are equally unequipped to interpret them. Follow-up appointments are expensive and weeks away.

The cost of not solving this: ~250 million lab reports are issued annually in India. Conservative estimates suggest fewer than 15% of patients fully understand their results. The rest are either over-anxious or dangerously under-informed.

---

## 2. Goals

1. Any person with a smartphone can understand their medical report within 2 minutes, without a medical background.
2. 40% of users share their simplified summary within the same session (WhatsApp share).
3. Report interpretation accuracy validated against medical professional review at ≥95% on a test set of 50 reports before launch.
4. End-to-end processing (upload → explanation displayed) completes in under 15 seconds at the p95.
5. Support the 8 most common Indian lab report types covering ~80% of diagnostic output.

---

## 3. Non-Goals

1. **Not a diagnostic tool.** ClarityMed will never state "you have diabetes" or "you need surgery." It explains what values mean — it does not diagnose, prescribe, or recommend treatment. This boundary is legal and non-negotiable.
2. **No EHR or hospital integration in v1.** Connecting to Apollo, Fortis, or Practo APIs is a Phase 3 initiative. Out of scope.
3. **No longitudinal report tracking in v1.** Comparing today's report against last month's requires user accounts and persistent storage. Out of scope for MVP.
4. **No prescription or medication analysis.** Interpreting drug dosages, interactions, or pharmacy labels is a regulated domain and a separate product.
5. **No real-time doctor consultation.** ClarityMed explains; it does not advise. Telemedicine is out of scope.

---

## 4. User Personas

### Priya — The Caregiver (Primary)
**Profile:** 45-year-old homemaker, Pune. Her husband has Type 2 diabetes and receives a lab report every 3 months.
**Pain:** She reads English but HbA1c, eGFR, and "borderline dyslipidemia" mean nothing. She photographs the report, sends it on WhatsApp to her son in Bangalore, who spends 2 hours Googling each value. They still aren't confident about what's serious.
**Job to be done:** Understand the report before the next doctor visit so she can ask the right questions.

### Rahul — The Health-Conscious Professional (Secondary)
**Profile:** 28-year-old software engineer, Bangalore. Annual full-body checkups, health-conscious.
**Pain:** Gets his report online, cross-references values across 4 different health websites, finds conflicting information about what "slightly elevated TSH" means, wastes 30 minutes and ends up more confused.
**Job to be done:** One authoritative, plain-language explanation he can trust.

### Sunita — The Community Health Worker (Tertiary)
**Profile:** 35-year-old ASHA worker, rural Maharashtra.
**Pain:** Receives printed lab reports for patients who don't speak English. Needs to triage and communicate findings without medical training.
**Job to be done:** Quickly understand the key take-aways from a report to communicate them to the patient in Marathi.

---

## 5. User Stories

### Patient / Caregiver

- As a patient, I want to upload my lab report as a PDF or photo so that I can get an explanation without retyping everything.
- As a patient, I want each test value explained in plain English so that I understand what my body is telling me.
- As a patient, I want each value colour-coded as Normal / Monitor / See Doctor so that I can see at a glance which results need attention.
- As a patient, I want a shareable summary I can send on WhatsApp so that my family stays informed without needing to read the full technical report.
- As a patient who prefers Hindi, I want the explanation in Hindi so that I don't have to rely on English to understand my health.
- As a caregiver managing elderly parents' health, I want to photograph a printed report and get an explanation so that I can discuss it intelligently with the doctor.

### Healthcare Worker

- As a community health worker, I want to quickly get a plain-language summary of a patient's report so that I can communicate findings to patients in their language.
- As a healthcare worker with limited time, I want the most concerning values highlighted at the top so that I can triage without reading everything.

### Edge Cases

- As a patient whose scan is low quality (photographed at an angle in dim light), I want the app to tell me clearly which values it couldn't read confidently so that I can re-upload or enter them manually.
- As a patient with a multi-page discharge summary, I want the entire document processed — not just the first page — so that I don't miss anything important.

---

## 6. Feature Requirements

### P0 — MVP (Must ship)

| # | Requirement | Acceptance Criteria |
|---|-------------|---------------------|
| P0-1 | Upload PDF or image (JPG, PNG, HEIC) | Files up to 10MB accepted; drag-and-drop and browse both work on mobile and desktop |
| P0-2 | AI extraction of all test parameters | Given a standard Indian lab report (SRL/Dr. Lal/Metropolis format), the app correctly extracts ≥90% of parameters by name, value, unit, and reference range |
| P0-3 | Plain-language explanation per parameter | Each parameter shows: what it measures (1 sentence), what the patient's value means in context (2 sentences max), status badge |
| P0-4 | Colour-coded status: Normal / Monitor / See Doctor | Status determined by comparison to reference range: within range = Normal, 0–20% outside = Monitor, >20% outside or flagged H/L by lab = See Doctor |
| P0-5 | Summary card with shareable plain-text | "Share via WhatsApp" button generates pre-formatted text summary including top concerns + overall status. Copy-to-clipboard also available |
| P0-6 | Medical disclaimer on every output | Fixed non-dismissable footer: "This explanation is for information only and is not medical advice. Always consult your doctor before making health decisions." |
| P0-7 | Mobile-responsive layout | App renders correctly on a 375px viewport (iPhone SE baseline); all text legible without zoom |
| P0-8 | Handles multi-page PDFs | All pages processed; parameters from any page included in output |

### P1 — Sprint 2 (High priority, fast-follow)

| # | Requirement | Notes |
|---|-------------|-------|
| P1-1 | Hindi language toggle | One-click switch; entire explanation re-generated in Hindi; validate quality with native speaker before shipping |
| P1-2 | Age + gender input for contextualised ranges | Reference ranges differ for men/women and by age bracket (e.g., haemoglobin, creatinine). Input at start of session. |
| P1-3 | Download simplified report as PDF | Clean printable summary; useful for bringing to doctor appointment |
| P1-4 | Report type auto-detection display | Show detected report type (e.g., "Complete Blood Count" or "Thyroid Function Test") at the top of results so user can confirm the right thing was processed |

**Added to v1 scope (previously P1):**
| # | Requirement | Notes |
|---|-------------|-------|
| P0-9 | Manual value entry fallback | If extraction fails or confidence is low, show a form for user to enter values manually. Too critical for real-world low-quality scans to defer to Sprint 2. |
| P0-10 | Photo guidance on mobile | Before upload, show 4 tips: flat surface, good lighting, no shadows, full page in frame. Reduces bad-scan failure rate significantly. |
| P0-11 | Extraction failure flow | If Gemini returns empty or malformed JSON after 1 retry: show friendly error ("We couldn't read this report clearly"), offer manual entry or re-upload option. Never show a blank result silently. |
| P0-12 | Report type confirmation | After extraction, show a one-line banner ("Detected: Complete Blood Count — does this look right?") before displaying full results. Builds trust, catches wrong-report uploads. |

### P2 — Future / Phase 2

| # | Requirement | Notes |
|---|-------------|-------|
| P2-1 | User accounts + report history | Requires auth (Supabase); enables longitudinal view |
| P2-2 | Side-by-side trend comparison | "Your HbA1c has improved from 7.8% to 7.2% since last quarter" |
| P2-3 | Shareable doctor link | Unique URL that renders the simplified report for the doctor |
| P2-4 | Regional languages | Marathi, Tamil, Telugu, Bengali — in priority order by user base |
| P2-5 | API for diagnostic lab integration | Labs embed ClarityMed as a value-add: "Understand your report" button on their portal |
| P2-6 | WhatsApp bot | Patient receives report PDF on WhatsApp → forwards to ClarityMed bot → gets explanation inline |

---

## 7. Supported Report Types (MVP Scope)

| Priority | Report Type | Common Tests | Prevalence |
|----------|-------------|--------------|------------|
| 1 | Complete Blood Count (CBC) | Hb, WBC, platelets, RBC indices | Very high |
| 2 | Blood Sugar / Diabetes Panel | FBS, PPBS, HbA1c, insulin | Very high |
| 3 | Lipid Profile | Total cholesterol, LDL, HDL, VLDL, TG | High |
| 4 | Thyroid Function Test (TFT) | TSH, T3, T4, FT3, FT4 | High |
| 5 | Liver Function Test (LFT) | SGOT, SGPT, bilirubin, albumin, ALP | High |
| 6 | Kidney Function Test (KFT/RFT) | Creatinine, BUN, eGFR, uric acid | High |
| 7 | Urine Routine & Microscopy | Protein, glucose, ketones, cells | Medium |
| 8 | Vitamin Panel | B12, D3, iron, ferritin | Medium |

---

## 8. AI Architecture

### Model Choice
**Primary:** Gemini 1.5 Flash (multimodal — processes PDFs and images natively; 1M tokens/day free on Google AI Studio key)

**Why Gemini over Groq/Claude for this:**
- Native PDF vision: send the PDF bytes directly, no pre-processing pipeline needed
- 1M free tokens/day gives ~5,000 report analyses free daily — sufficient for MVP validation
- Handles low-quality photos (Gemini's vision is state-of-the-art for documents)

**Fallback:** Gemini 1.5 Flash-8B (also free on Google AI Studio) — lighter model, same free tier, used when primary model is rate-limited. No paid API required.

### Prompt Strategy
Two-stage approach:

**Stage 1 — Extraction prompt** (structured output, JSON mode on)
```
You are a medical data extraction engine. Extract ALL test parameters from this lab report.
For each parameter return: name, value (numeric), unit, reference_range_low, reference_range_high, flag (H/L/normal as printed).
Return ONLY valid JSON. No commentary. If a value is not numeric (e.g., "Positive"), set value to the text as-is.
```

**Stage 2 — Explanation prompt** (one call for all parameters)
```
You are a friendly health educator explaining lab results to a patient with no medical background.
Patient: [age] year old [gender].
For each parameter below, write:
1. "what_it_is": One plain sentence explaining what this test measures (avoid jargon)
2. "your_result": Two sentences explaining what the patient's value means for them personally
3. "status": exactly one of: "normal", "monitor", or "see_doctor"
   - normal = within reference range
   - monitor = 0-20% outside range OR borderline
   - see_doctor = >20% outside range OR flagged H/L
Do not diagnose. Do not prescribe. Do not suggest medications.
```

### Safety Rails
**Forbidden phrase filter (exact strings blocked in post-processing):**
- "you have [any disease name]" / "you are diabetic" / "you have cancer"
- "take [any medication]" / "you should take" / "prescribe"
- "you need surgery" / "you need a [procedure]"
- "this is serious" / "this is dangerous" (too alarmist without context)

**Threshold-based escalation:**
- If `see_doctor` count ≥ 5: show persistent banner — *"Multiple values need attention. Please consult your doctor before making any health decisions."*
- If any single value is >50% outside reference range: force `see_doctor` regardless of lab flag

**Extraction confidence handling:**
- If Gemini returns a value with no unit and no reference range, mark it as `low_confidence` and display with a warning icon: "We couldn't read this value clearly — please verify against your original report."
- If total `low_confidence` parameters > 30% of all parameters: show top-level warning before results — "Some values may not have been read correctly. Please verify against your original report."
- Retry malformed JSON once before falling back to graceful error

**Legal disclaimer (fixed, non-dismissable):**
> *"ClarityMed explains what lab values mean in plain language. It is not a medical diagnosis and is not a substitute for professional medical advice. Always consult a qualified doctor before making any health decision."*

- All outputs include raw extracted value alongside AI explanation so user can verify accuracy

---

## 9. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Framework | Streamlit | 2-day build; same stack as EduCraft; easy mobile deployment |
| AI Vision + NLP | Gemini 1.5 Flash | Native PDF/image processing; 1M tokens/day free |
| AI Fallback | Gemini 1.5 Flash-8B | Lighter model, same free Google AI Studio key, zero cost |
| PDF processing | PyMuPDF (fitz) | Extract text from born-digital PDFs before sending to Gemini |
| Deployment | Streamlit Community Cloud | Free, always-on for public apps; no infrastructure cost |
| Analytics | Streamlit session counter (v1) | In-session upload/completion tracking; add PostHog when budget allows |
| Storage | None (stateless, v1) | No data retained; each session is ephemeral |

---

## 10. MVP Build Plan

### Day 1 — Core pipeline
- Streamlit app skeleton: upload widget, session state management
- Gemini 1.5 Flash integration with PDF/image input
- Stage 1 extraction prompt + JSON parsing with retry logic
- Raw extracted values displayed (proof of concept)

### Day 2 — Explanation + UI
- Stage 2 explanation prompt for all parameters
- Colour-coded results cards (Normal / Monitor / See Doctor)
- Sort order: See Doctor first, then Monitor, then Normal
- Mobile-responsive layout

### Day 3 — Sharing + Polish
- WhatsApp share button (pre-formatted text message)
- Copy-to-clipboard fallback
- Disclaimer footer (non-dismissable)
- Error states: bad file format, unclear scan, Gemini rate limit
- Test against 10 real report PDFs

### Day 4 — QA + Deploy
- Test against 20+ report types (CBC, lipid, thyroid, LFT, KFT, sugar, urine, vitamins)
- Edge case hardening: multi-page PDFs, handwritten values, non-English reports
- Deploy to Streamlit Community Cloud (free; connect GitHub repo → deploy in minutes)
- Verify session counter tracks uploads and completions correctly

---

## 11. Success Metrics

### North Star
**Reports Explained per Day (RED)** — target 100/day by day 30 post-launch

### Leading Indicators (Week 1–4)
| Metric | Target |
|--------|--------|
| Upload → Result completion rate | >80% |
| Time to explanation (p95) | <15 seconds |
| WhatsApp share rate | >30% of completed sessions |
| Extraction accuracy (manual QA, 50-report sample) | ≥90% parameters correct |

### Lagging Indicators (Month 2–3)
| Metric | Target |
|--------|--------|
| Return users (2+ sessions in 30 days) | >20% of users |
| NPS (post-session survey, 1-click) | >45 |
| Viral coefficient from WhatsApp shares | >0.3 (i.e., every 10 shares generates 3 new users) |

---

## 12. Open Questions

| # | Question | Who answers | Blocking? |
|---|----------|------------|-----------|
| OQ-1 | Does explaining lab report values constitute "medical advice" under Indian NMC guidelines? What disclaimer language is legally sufficient? | Legal advisor | **Yes — before launch** · *Working assumption: Use the disclaimer language defined in Section 8 Safety Rails. It mirrors language used by Practo and 1mg health content pages. Revisit if a lawyer flags it.* |
| OQ-2 | What is the acceptable false-positive rate for "See Doctor" flags? False positives cause anxiety; false negatives are dangerous. Need to set threshold. | Medical advisor | **Resolved (working):** >20% outside reference range OR lab-flagged H/L = See Doctor. 0–20% = Monitor. This is a conservative threshold; refine after 50-report QA in Day 4. |
| OQ-3 | Gemini vision accuracy on low-quality WhatsApp-forwarded JPEGs — what % of real-world photos are too degraded to extract reliably? | Engineering (test sprint 1) | No — validate in parallel |
| OQ-4 | Should reference ranges use the lab's printed values or standardised medical ranges? Labs vary. | Medical advisor | No — default to lab's printed range in v1 |
| OQ-5 | Hindi prompt output quality — does Gemini 1.5 Flash produce medically accurate Hindi or does it hallucinate? | QA with native speaker | No — Sprint 2 gate |

---

## 13. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AI misinterprets a value, causing incorrect "See Doctor" flag | Medium | High | Always show raw extracted value alongside explanation; user can verify. Post-launch: human medical review of 50 outputs per week |
| Legal challenge for "practising medicine" | Low | Very High | Tight disclaimer, "information only" framing, no diagnosis language, OQ-1 resolved before launch |
| Low-quality scan breaks extraction (false confidence) | High | Medium | Confidence score per parameter; low-confidence values shown with warning "could not read clearly — please verify" |
| Gemini free tier rate-limited at scale | Medium | Medium | Fall back to Gemini 1.5 Flash-8B (same free key, lighter model); both within 1M token/day free quota. No paid fallback needed at MVP scale (100 reports/day << 5,000 free limit). |
| Medical misinformation at scale if prompt goes wrong | Low | Very High | Output filter for forbidden phrases; prompt locked (no user-controlled system prompt modification) |
| Data privacy concern (health data is sensitive) | Medium | High | Stateless architecture — nothing stored. Clear privacy notice: "Your report is processed and immediately discarded. We never store health data." |

---

## 14. Monetisation Path (Post-MVP)

| Tier | Price | Features | Target |
|------|-------|----------|--------|
| Free | ₹0 | 5 reports/month, English only | Individual patients |
| Personal | ₹99/month | Unlimited reports, Hindi + English, PDF download | Frequent users, caregivers |
| Family | ₹199/month | 5 accounts, report history, trend tracking | Multi-generation families |
| Clinic | ₹999/month | Unlimited, all languages, doctor-share links, API | ASHA workers, small clinics, diagnostic labs |

**Projection (Month 6):** 10,000 MAU × 5% paid conversion × ₹150 ARPU = ₹75,000 MRR (~$900/month). Proof-of-concept for lab API deals.

---

## 15. Competitive Landscape

| Competitor | Approach | Gap ClarityMed fills |
|-----------|----------|----------------------|
| 1mg / Practo health content | Generic article-level explanations | Not personalised to patient's actual values |
| Google "what does HbA1c mean" | Web search returns conflicting sources | Authoritative, context-aware, single output |
| Doctor consultation | Accurate but costs ₹500–1500 and requires appointment | Immediate, free, available at 2am when the report arrives |
| HealthifyMe / Apollo 24/7 | Focused on diet/fitness or telemedicine | Not designed for report interpretation |

**Key differentiator:** ClarityMed is the only tool that takes *your specific values* and explains what *they* mean for *you*, in plain language, in under 15 seconds, for free.

---

## 16. Current Build Status

**Status: Pre-build — spec approved, no code written**

Next step: Set up Streamlit project skeleton and integrate Gemini 1.5 Flash with a PDF upload widget. Estimated time to working MVP: 4 days.

**Pre-requisites before starting:**
- [ ] Google AI Studio API key (Gemini 1.5 Flash) — free at aistudio.google.com, no billing required
- [ ] OQ-1 (disclaimer language) — working disclaimer now defined in Section 8. Validate against a lawyer before public launch, but unblocked for build start.
- [ ] Collect 20 sample lab reports (anonymised) for testing — ask at a local diagnostic center or use publicly available samples
- [ ] GitHub repo created — needed for Streamlit Community Cloud deployment (free)

**Zero-spend stack confirmed:** Google AI Studio (free) + Streamlit Community Cloud (free) = ₹0/month operating cost for MVP.

---

*Spec authored: May 2026 | Next review: After Day 4 deploy*
