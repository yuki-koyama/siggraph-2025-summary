# Repository instructions

## Purpose and boundaries

This repository scrapes SIGGRAPH program data and builds independent paper-summary artifacts. It is not tied to the `siggraph.xyz` study group. Do not introduce wording such as “study-group scope”, “out of scope”, or “reference only” into generated summaries.

Generated files live under `dist/` and are ignored by Git. For SIGGRAPH 2026, the generated `dist/siggraph-2026/` directory is copied into the `siggraph-xyz` repository at `s2026/summary/`.

## Source-of-truth rules

- Do not classify `papers_*` as Conference Papers. That prefix covers both Journal and Conference track papers scheduled at SIGGRAPH 2026.
- `paperstog_*` records are `Invited from TOG` presentations.
- Separate Journal and Conference tracks using ACM/Crossref publication metadata, matched by normalized title and ordered author list.
- Determine deferral by comparing the 327 official accepted `papers_*` IDs/publications with the 309 `papers_*` records present in the SIGGRAPH 2026 schedule.
- Never change expected counts merely to make a failing scrape pass. Investigate upstream schedule, accepted-ID PDF, and ACM/Crossref changes first.

SIGGRAPH 2026 currently has five mutually exclusive tags:

- `conference`: 183
- `journal`: 126
- `invited-tog`: 36
- `conference-deferred`: 12
- `journal-deferred`: 6

The 345 presented papers and 18 deferred papers form a complete 363-paper catalog. The deferral program was new for SIGGRAPH 2026, so there is no incoming-deferred category for this edition.

## Implementation

- `scrape_siggraph2026.py` collects official schedule records, descriptions, affiliations, and images, then delegates classification to `siggraph2026_classification.py`.
- `siggraph2026_classification.py` fetches ACM/Crossref metadata and the official accepted-ID PDF, assigns exactly one tag to every scheduled paper, appends deferred publications, and validates all counts.
- `scripts/paper-data.js` keeps deferred publications outside the 57 actual conference sessions while exposing both sets to the HTML and slide templates.
- Deferred publications may lack schedule-only assets such as a representative image or session abstract; use their DOI as the source link.

## Commands

Use a Python environment containing `requirements.txt` dependencies and install Node dependencies before building.

```bash
python scrape_siggraph2026.py
npm run build:2026
npm run build:slides:2026
npm run build:slides-pdf:2026
```

Run regression builds after shared template or style changes:

```bash
npm run build
npm run build:asia
npm run build:slides
npm run build:slides:asia
```

## Required verification

- `papers.json`: 363 records, 363 unique IDs, 363 unique titles, no missing tag labels.
- Presented subset: 345 records in 57 sessions, with 345 descriptions and representative images.
- Deferred subset: 18 records, split 12 Conference and 6 Journal.
- HTML: 363 paper cards and exactly one tag per card.
- Slides: 422 pages and 363 paper tags; check that no slide overflows its 1280x720 canvas.
- Render and visually inspect at least the title page, one normal paper, the deferred-section title, and the first and last deferred paper.
- Run `git diff --check` and syntax checks for modified Python and JavaScript files.

Unless the user explicitly authorizes it, do not commit or push.

