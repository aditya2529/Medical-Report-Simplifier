# ClarityMed — Privacy Policy

_Last updated: 14 May 2026_

ClarityMed is a free information tool that simplifies lab reports into
plain-language explanations. This document explains what happens to your
data when you use it. Plain language; no legal boilerplate.

## What you give us

When you upload a report (or enter values manually) you may share:

- A PDF or image of your lab report
- Test parameter names, values, units, and reference ranges
- Optional age and gender (entered by you)
- Whatever your lab printed on the page header — which can include your
  name, date of birth, the doctor's name, and the lab's address

You do **not** create an account. You do **not** give us an email or phone
number. We do not see your IP address; that information stops at the
hosting provider (Streamlit Community Cloud) and we have no access to it.

## What we do with it

1. The PDF is read into memory inside your browser session and converted
   to images (PyMuPDF) on the server.
2. The images are sent to **Groq** (a US-based AI inference provider) to
   extract the parameters listed on the report.
3. The extracted parameter list is sent back to Groq for a second pass
   that produces plain-language explanations.
4. The result is rendered to you in the same browser session.

That is the entire data flow. Nothing else.

## Who sees your data

- **You** (in your browser).
- **Groq** processes the file and the extracted text. See Groq's privacy
  notice at https://groq.com/privacy-policy/. Groq states it does not
  use customer data to train its models.
- **Streamlit Community Cloud** hosts the app and routes traffic. The
  app itself does not write your data to its disk.
- **We (the ClarityMed builder)** do not have access to logs, file
  contents, or extracted text. The hosting provider keeps generic
  request logs (timestamp, status code) that we cannot tie back to you.

## What we keep

**Nothing.** No database. No analytics on report content. No log file of
your values. The session ends when you close the tab; all in-memory
state goes with it.

Server-side application logs may record technical errors (e.g. "PDF
parsing failed at page 3"). They never include the report's content.

## Your DPDP Act rights

Under the Digital Personal Data Protection Act, 2023:

- **Right to access**: there is nothing to access — we don't retain
  anything tied to you.
- **Right to erasure**: erasure happens automatically when your session
  ends.
- **Right to grievance redressal**: file a grievance with the Grievance
  Officer named below. We will respond within 30 days.

## Consent

Before you click "Analyse", you tick a checkbox confirming you understand
that the file will leave India for processing by Groq. You can withdraw
this consent at any time by not clicking the button, or by closing the
tab — no further action needed.

## Open source

The full source code is at
https://github.com/aditya2529/Medical-Report-Simplifier. If you want to
verify any claim in this document, read the code.

## Grievance Officer

Aditya Kumar
aditya2529@gmail.com
