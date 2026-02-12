# SIGGRAPH 2025 / SIGGRAPH Asia 2025 Summary

This repository contains a scraper and static builders for:
- SIGGRAPH 2025 (`siggraph-2025`)
- SIGGRAPH Asia 2025 (`siggraph-asia-2025`)

The scripts `scrape_siggraph2025.py` and `scrape_siggraph_asia2025.py` download the official schedule and extract
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

# SIGGRAPH Asia 2025
python scrape_siggraph_asia2025.py
```

The scraped papers are saved to `dist/<event>/papers.json` in JSON format. Each entry
includes the paper's title, authors, session and paper IDs, schedule information,
and a link to its dedicated presentation page on the SIGGRAPH site. The
representative images for each paper are downloaded to `dist/<event>/images/` and the
JSON file stores both the original image URL and the saved image filename.

## Building the HTML summary

After scraping the data, install the Node.js dependencies and generate the web page:

```bash
npm install

# SIGGRAPH 2025
npm run build

# SIGGRAPH Asia 2025
npm run build:asia

# Both events
npm run build:all
```

Generated HTML files:
- `dist/siggraph-2025/index.html`
- `dist/siggraph-asia-2025/index.html`

## Building slide deck

You can also generate a slide-style HTML file. The deck begins with a title slide that centers the deck title on the page, lists the total session and paper counts beneath it in bold text, and shows the source link in a small footer. Numbered session title pages and individual paper slides follow. Install the dependencies as above and run:

```bash
# SIGGRAPH 2025
npm run build:slides

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

# SIGGRAPH Asia 2025
npm run build:slides-pdf:asia
```

The script outputs `dist/<event>/slides.pdf` using Puppeteer with a page size of `1280x720`.
