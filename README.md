# SIGGRAPH 2025 Summary

This repository contains a simple scraper for the SIGGRAPH 2025 conference schedule.
The script `scrape_siggraph2025.py` downloads the schedule from the
official website and extracts information about individual **Technical Papers**
by parsing the daily schedule snippets. The parser walks through each
technical paper session and collects the presentations within it.
Sessions such as "Papers Fast Forward", "SIGGRAPH 2025 Technical Papers Town Hall",
and "Technical Papers Closing Session" are excluded from the results.

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

```bash
python scrape_siggraph2025.py
```

The scraped papers will be saved to `data/papers.json` in JSON format. Each entry
includes the paper's title, authors, session and paper IDs, schedule information,
and a link to its dedicated presentation page on the SIGGRAPH site. The
representative images for each paper are downloaded to `data/images/` and the
JSON file stores both the original image URL and the saved image filename.

## Building the HTML summary

After scraping the data, install the Node.js dependencies and generate the web page:

```bash
npm install
npm run build
```

The generated HTML (`dist/index.html`) references the scraped images under `data/images/` and lists the technical papers grouped by session.

## Building slide deck

You can also generate a slide-style HTML file. The deck begins with a title slide (including the schedule source), followed by numbered session title pages and individual paper slides. Install the dependencies as above and run:

```bash
npm run build:slides
```

This produces `dist/slides.html` and `dist/slides.css`.
To automatically save a PDF version of the slides, run:

```bash
npm run build:slides-pdf
```

The script outputs `dist/slides.pdf` using Puppeteer with a page size of `1280x720`.
