import json
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from typing import List, Dict

# Session titles to exclude even though they are labeled as Technical Papers
EXCLUDE_TITLES = {
    "Papers Fast Forward",
    "SIGGRAPH 2025 Technical Papers Town Hall",
    "Technical Papers Closing Session",
}


def normalize_title(title: str) -> str:
    """Return a normalized title with collapsed whitespace."""
    return " ".join(title.replace("\u00a0", " ").split())


BASE_URL = "https://s2025.conference-schedule.org/"


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch a page and return its BeautifulSoup object."""
    resp = requests.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_snippet_links(soup: BeautifulSoup) -> List[str]:
    """Extract snippet URLs containing daily schedule tables."""
    links = []
    for div in soup.find_all("div", class_="post-load", attrs={"source": True}):
        src = div.get("source")
        if src:
            links.append(urljoin(BASE_URL, src))
    return links


def _has_presentation_type(row: BeautifulSoup, keyword: str) -> bool:
    ptype = row.find("span", class_="presentation-type")
    return bool(ptype and keyword in ptype.get_text())


def parse_snippet(html: str) -> List[Dict[str, str]]:
    """Parse a schedule snippet and return individual technical papers."""
    soup = BeautifulSoup(html, "html.parser")

    # Collect technical paper session information first
    sessions: Dict[str, Dict[str, str]] = {}
    for row in soup.find_all("tr", class_="agenda-item"):
        if row.get("ssid") != "none":
            continue
        if not _has_presentation_type(row, "Technical Paper"):
            continue
        title_el = row.find("span", class_="presentation-title")
        title = normalize_title(title_el.get_text(strip=True)) if title_el else ""
        if title in EXCLUDE_TITLES:
            continue
        location_el = row.find("span", class_="presentation-location")
        sessions[row.get("psid", "")] = {
            "session_title": title,
            "location": location_el.get_text(strip=True) if location_el else "",
        }

    papers: List[Dict[str, str]] = []
    for row in soup.find_all("tr", class_="agenda-item"):
        psid = row.get("psid")
        ssid = row.get("ssid")
        if not psid or ssid == "none" or psid not in sessions:
            continue

        title_link = row.find("a", attrs={"data-link-type": lambda x: x and ".presentation" in x})
        if not title_link:
            continue
        title = normalize_title(title_link.get_text(strip=True))
        url = urljoin(BASE_URL, title_link.get("href", ""))

        author_links = row.find_all("a", attrs={"data-link-type": lambda x: x and ".person" in x})
        authors = [normalize_title(a.get_text(strip=True)) for a in author_links]

        papers.append({
            "title": title,
            "url": url,
            "authors": authors,
            "session": sessions[psid]["session_title"],
            "location": sessions[psid]["location"],
            "start": row.get("s_utc", ""),
            "end": row.get("e_utc", ""),
        })
    return papers


def parse_technical_papers(base_soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Parse the main schedule page and all snippet pages."""
    papers: List[Dict[str, str]] = []
    for link in parse_snippet_links(base_soup):
        try:
            resp = requests.get(link)
            resp.raise_for_status()
        except requests.HTTPError:
            # Skip snippets that fail to load
            continue
        papers.extend(parse_snippet(resp.text))
    return papers


def scrape_technical_papers() -> List[Dict[str, str]]:
    """Scrape the schedule site for technical papers."""
    soup = fetch_page(BASE_URL)
    papers = parse_technical_papers(soup)
    return papers


def save_as_json(data: List[Dict[str, str]], path: str) -> None:
    """Save scraped data as JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    papers = scrape_technical_papers()
    save_as_json(papers, "papers.json")
    print(f"Saved {len(papers)} papers to papers.json")
