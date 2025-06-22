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
includes the paper's title, authors, schedule information, and a link to its
dedicated presentation page on the SIGGRAPH site.
