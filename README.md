# Medelite Facility Assessment Report Generator

A lightweight web application that automates the generation of facility assessment reports for Medelite directors. Enter a CMS Certification Number (CCN) to instantly pull public nursing home data, combine it with manual operational inputs, and download a polished PDF or Word report.

## Live Application
🔗 **https://medelite-assessment.onrender.com**

> Note: Hosted on Render free tier. First load may take 30-60 seconds if the server has been idle.

## GitHub Repository
🔗 **https://github.com/Praniti03/medelite-assessment**

---

## What It Does

1. User enters a 6-digit CCN into the search box
2. App fetches live data from the CMS Provider Data Catalog API
3. User fills in manual operational fields (EMR, census, patient type, Medelite history)
4. User clicks Download PDF or Download Word to get a polished, print-ready report
5. Report includes the INFINITE logo, all star ratings, 12 hospitalization metrics, and a clickable Medicare source link

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend | Python 3 + FastAPI | Matches job requirement for Python-based PDF automation |
| PDF Generation | ReportLab | Server-side pixel-level PDF control |
| Word Export | python-docx | Generates editable .docx matching PDF layout |
| HTTP Client | httpx | Async non-blocking CMS API calls |
| Frontend | Vanilla HTML + Tailwind CSS (CDN) | Lightweight, no build step required |
| Deployment | Render.com | Free Python hosting with GitHub auto-deploy |

---

## How to Run Locally

**Step 1 — Clone the repo**
```bash
git clone https://github.com/Praniti03/medelite-assessment.git
cd medelite-assessment
```

**Step 2 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3 — Start the server**
```bash
uvicorn main:app --reload
```

**Step 4 — Open in browser**
```
http://127.0.0.1:8000
```

**Test with CCN:** `686123` (Kendall Lakes Healthcare and Rehab Center, Miami FL)

---

## CMS API Endpoints

| Dataset | Resource ID | Data Fetched |
|---------|------------|--------------|
| NH_ProviderInfo | `4pq5-n9py` | Name, address, beds, star ratings |
| NH_QualityMsr_Claims | `ijh5-nb2v` | 12 hospitalization and ED metrics |
| NH_StateUSAverages | `fnz5-sq3n` | State and national averages |

### Claims Measure Code Mapping

| Measure Code | Report Label |
|-------------|-------------|
| 521 | Short Term Hospitalization |
| 522 | STR ED Visit |
| 551 | LT Hospitalization |
| 552 | ED Visit (LT) |

---

## Facility Name Override Logic

The display name is resolved using a single conditional expression in `cms_client.py`:

```python
display_name = manual.get("name_override", "").strip() or raw_api_name
```

If the user types a custom name in the override field, that value takes precedence in both the on-screen preview and all exported files. If the field is left blank, the official CMS `provider_name` is used after applying `.title()` case formatting. The INFINITE branding header is hardcoded separately and is never affected by this logic.

---

## Bonus Features Implemented

- ✅ All 12 Hospitalization/ED Metrics mapped (STR and LT)
- ✅ Word Document (.docx) export with clickable Medicare hyperlink
- ✅ Advanced error handling for invalid CCNs, API timeouts, and missing data
- ✅ Custom high-fidelity design with INFINITE logo, star ratings, and alternating table rows

---

## Assumptions & Engineering Decisions

**1. CMS Data Currency**
The CMS Provider Data Catalog is updated quarterly. Star ratings and hospitalization metrics reflect the most current CMS data and may differ from the reference PDF (Kendall Lakes), which was generated at an earlier data snapshot. This is expected behavior, not a data mapping error.

**2. City Field Name Discrepancy**
The CMS API returns the city field as `citytown` (no underscore), not `city_town` as documented in the NH Data Dictionary. This was discovered by inspecting the raw API response directly and corrected programmatically.

**3. Claims Metrics Resource ID**
The NH_QualityMsr_Claims dataset resource ID referenced in older CMS documentation returned a 404 error. The correct active resource ID (`ijh5-nb2v`) was identified by navigating the CMS Provider Data Catalog directly and inspecting the dataset URL.

**4. State/National Averages Fallback**
State and national averages are fetched from the NH_StateUSAverages endpoint. Where the endpoint returns no matching data for a specific measure code, values fall back to the last published CMS averages hardcoded as constants in `cms_client.py`.

**5. INFINITE Branding**
The INFINITE logo and FACILITY ASSESSMENT SNAPSHOT header are hardcoded in both PDF and Word exports and are never overwritten by facility name data from the API or manual override per the critical branding guardrail in the brief.

---

## Biggest Technical Hurdle

**Outdated Claims Metrics Resource ID**

The NH_QualityMsr_Claims dataset resource ID referenced in older documentation returned a 404 error when queried.

**Debugging Process:**
1. Identified the 404 from the raw API response in the browser
2. Navigated to data.cms.gov/provider-data and searched for the dataset manually
3. Found the active resource ID by inspecting the dataset URL on the Provider Data Catalog
4. Updated the constant in `cms_client.py` and re-tested with CCN `686123`

---

## Project Structure

```
medelite-assessment/
│
├── main.py              # FastAPI server — all routes
├── cms_client.py        # CMS API calls and data mapping
├── pdf_generator.py     # ReportLab PDF builder
├── docx_generator.py    # python-docx Word export
├── requirements.txt     # Python dependencies
│
└── static/
    ├── index.html       # Frontend UI
    └── logo.png         # INFINITE logo
```

---

## Requirements

```
fastapi
uvicorn[standard]
httpx
reportlab
python-docx
python-multipart
```
