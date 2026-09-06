# SIGGRAPH 2025 / 2026 / SIGGRAPH Asia 2025 Summary

This repository contains a scraper and static builders for:
- SIGGRAPH 2025 (`siggraph-2025`)
- SIGGRAPH 2026 (`siggraph-2026`)
- SIGGRAPH Asia 2025 (`siggraph-asia-2025`)

The scripts `scrape_siggraph2025.py`, `scrape_siggraph2026.py`, and `scrape_siggraph_asia2025.py` download the official schedule and extract
individual **Technical Papers** by parsing daily schedule snippets. The parser
collects papers for each technical paper session and excludes non-paper sessions
such as "Papers Fast Forward", "Technical Papers Town Hall", and
"Technical Papers Closing Session".

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

```bash
# SIGGRAPH 2025
python scrape_siggraph2025.py

# SIGGRAPH 2026
python scrape_siggraph2026.py

# SIGGRAPH Asia 2025
python scrape_siggraph_asia2025.py
```

The scraped papers are saved to `dist/<event>/papers.json` in JSON format. Each entry
includes the paper's title, authors, session and paper IDs, schedule information,
and a link to its dedicated presentation page on the SIGGRAPH site. The
representative images for each paper are downloaded to `dist/<event>/images/` and the
JSON file stores both the original image URL and the saved image filename.

For SIGGRAPH 2026, the scraper also reconciles the official schedule, the official
conditionally accepted paper-ID list, and ACM/Crossref publication metadata. Every
paper receives exactly one of these tags:

- `Conference Papers`
- `Journal Papers`
- `Invited from TOG`
- `Conference Papers (Deferred Paper Presentation)`
- `Journal Papers (Deferred Paper Presentation)`

The first three tags comprise the 345 papers presented at SIGGRAPH 2026. The 18
deferred papers are shown in a separate section, for a complete publication catalog
of 363 papers. The scraper checks all category counts and stops with an error if the
sources no longer reconcile.

This summary is an independent SIGGRAPH paper catalog. It is not specific to any
study group, so generated pages and slides should describe publication and
presentation status only.

### SIGGRAPH 2026 data reconciliation

The five tags are mutually exclusive. Current verified counts are:

| Tag | Count | Presented at SIGGRAPH 2026 |
| --- | ---: | :---: |
| `Conference Papers` | 183 | Yes |
| `Journal Papers` | 126 | Yes |
| `Invited from TOG` | 36 | Yes |
| `Conference Papers (Deferred Paper Presentation)` | 12 | No |
| `Journal Papers (Deferred Paper Presentation)` | 6 | No |

The totals reconcile as follows:

- Accepted by SIGGRAPH 2026: 327 = 132 Journal + 195 Conference
- Deferred to SIGGRAPH Asia 2026: 18 = 6 Journal + 12 Conference
- Accepted papers presented at SIGGRAPH 2026: 309 = 126 Journal + 183 Conference
- All papers presented at SIGGRAPH 2026: 345 = 309 accepted + 36 invited from TOG
- Complete summary catalog: 363 = 345 presented + 18 deferred

The classification code checks three independent sources:

1. The [SIGGRAPH 2026 conference schedule](https://s2026.conference-schedule.org/)
   supplies the 345 actual presentations, their sessions, abstracts, and images.
2. The [official conditionally accepted paper-ID list](https://s2026.siggraph.org/wp-content/uploads/2026/03/SIGGRAPH-2026-TECHNICAL-PAPERS-CONDITIONALLY-ACCEPTED-PAPERS.pdf)
   contains 327 `papers_*` IDs. Comparing it with the schedule leaves 18 deferred IDs.
3. ACM publication metadata obtained through Crossref separates the 132 Journal
   Papers in TOG 45(4) from the 195 Conference Papers. Titles and ordered author
   lists are used to reconcile publication records with schedule records.

The deferral program was [new for SIGGRAPH 2026](https://s2026.siggraph.org/program/technical-papers/),
so SIGGRAPH 2026 has no incoming deferred presentations from an earlier conference.
The 18 deferred SIGGRAPH 2026 papers remain published with SIGGRAPH 2026 but will be
presented at SIGGRAPH Asia 2026 under the [Deferred Paper Presentation Policy](https://www.siggraph.org/siggraph-events/conferences/deferred-paper-presentation/).

## Building the HTML summary

After scraping the data, install the Node.js dependencies and generate the web page:

```bash
npm install

# SIGGRAPH 2025
npm run build

# SIGGRAPH 2026
npm run build:2026

# SIGGRAPH Asia 2025
npm run build:asia

# Both events
npm run build:all
```

Generated HTML files:
- `dist/siggraph-2025/index.html`
- `dist/siggraph-2026/index.html`
- `dist/siggraph-asia-2025/index.html`

## Building slide deck

You can also generate a slide-style HTML file. The deck begins with a title slide that centers the deck title on the page, lists the total session and paper counts beneath it in bold text, and shows the source link in a small footer. Numbered session title pages and individual paper slides follow. Install the dependencies as above and run:

```bash
# SIGGRAPH 2025
npm run build:slides

# SIGGRAPH 2026
npm run build:slides:2026

# SIGGRAPH Asia 2025
npm run build:slides:asia

# Both events
npm run build:slides:all
```

This produces `dist/<event>/slides.html` and `dist/<event>/slides.css`.
To automatically save a PDF version of the slides, run:

```bash
# SIGGRAPH 2025
npm run build:slides-pdf

# SIGGRAPH 2026
npm run build:slides-pdf:2026

# SIGGRAPH Asia 2025
npm run build:slides-pdf:asia
```

The script outputs `dist/<event>/slides.pdf` using Puppeteer with a page size of `1280x720`.

For SIGGRAPH 2026, the PDF currently contains 422 pages: one title page, 57 session
title pages, 345 presented-paper pages, one deferred-section title page, and 18
deferred-paper pages.
