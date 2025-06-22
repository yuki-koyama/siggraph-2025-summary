import json
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
import time

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

# Reuse a session for all HTTP requests
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "siggraph-scraper"})
REQUEST_TIMEOUT = 10


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch a page and return its BeautifulSoup object."""
    resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    # Snippet pages are served without an explicit charset and default to
    # ISO-8859-1 in ``requests``. Force UTF-8 so characters like en-dashes do
    # not get decoded as "\xc2" (displayed as "\xc2").
    resp.encoding = "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def fetch_paper_details(url: str) -> Tuple[str, str]:
    """Fetch a paper presentation page and return its description and image URL."""
    try:
        soup = fetch_page(url)
    except requests.RequestException:
        return "", ""

    img_el = soup.find("img", class_="representative-img")
    img_url = urljoin(BASE_URL, img_el.get("src", "")) if img_el else ""

    abstract_el = soup.find("span", class_="abstract")
    description = abstract_el.get_text(strip=True) if abstract_el else ""

    return description, img_url


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
    detail_urls: List[str] = []
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
        detail_urls.append(url)

    # Fetch each paper's details concurrently
    with ThreadPoolExecutor(max_workers=8) as ex:
        details = list(ex.map(fetch_paper_details, detail_urls))

    for paper, (description, image_url) in zip(papers, details):
        paper["description"] = description
        paper["image_url"] = image_url

    return papers


def parse_technical_papers(base_soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Parse the main schedule page and all snippet pages."""
    papers: List[Dict[str, str]] = []
    for link in parse_snippet_links(base_soup):
        try:
            resp = SESSION.get(link, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            # Snippet responses omit the charset and default to ISO-8859-1; fix
            # it so we do not get stray characters in titles.
            resp.encoding = "utf-8"
        except requests.HTTPError:
            # Skip snippets that fail to load
            continue
        papers.extend(parse_snippet(resp.text))
        time.sleep(0.1)
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
