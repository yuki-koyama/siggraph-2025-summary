import json
import os
import random
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time

# Session title keywords to exclude even though they are labeled as Technical Papers
EXCLUDE_TITLE_KEYWORDS = (
    "Papers Fast Forward",
    "Technical Papers Town Hall",
    "Technical Papers Closing Session",
    "Technical Papers Interactive Discussion",
)

AD_HOC_PAPER_FIXES = {
    "Implicit Bonded Discrete Element Method with Manifold Optimization": {
        "authors": [
            "Jia-Ming Lu",
            "Geng-Chen Cao",
            "Chenfeng Li",
            "Shi-Min Hu",
        ],
        "affiliations": [
            ["Tsinghua University"],
            ["Tsinghua University"],
            ["Swansea University Bay Campus"],
            ["Tsinghua University"],
        ],
    },
    "Reliable Iterative Dynamics: A Versatile Method for Fast and Robust Simulation": {
        "authors": [
            "Jia-Ming Lu",
            "Shi-Min Hu",
        ],
        "affiliations": [
            ["Tsinghua University"],
            ["Tsinghua University"],
        ],
    },
}


def normalize_title(title: str) -> str:
    """Return a normalized title with collapsed whitespace."""
    return " ".join(title.replace("\u00a0", " ").split())


# Reuse a session for all HTTP requests
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "siggraph-scraper"})
REQUEST_TIMEOUT = 10
BASE_URL = "https://sa2025.conference-schedule.org/"
FAST_FORWARD_PRESENTER_CLASS = "technical-papers-fast-forward-presenter"
RETRY_ATTEMPTS = 4
RETRY_SLEEP_MIN_SECONDS = 1.0
RETRY_SLEEP_MAX_SECONDS = 4.0


def _is_fast_forward_presenter_descendant(tag) -> bool:
    """Return True when a tag is nested under fast-forward presenter markup."""
    return bool(tag.find_parent(class_=FAST_FORWARD_PRESENTER_CLASS))


def _get_with_retry(url: str) -> requests.Response:
    """GET with randomized backoff retries for transient failures."""
    last_exc = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt == RETRY_ATTEMPTS - 1:
                break
            time.sleep(random.uniform(RETRY_SLEEP_MIN_SECONDS, RETRY_SLEEP_MAX_SECONDS))
    raise last_exc


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch a page and return its BeautifulSoup object."""
    resp = _get_with_retry(url)
    # Snippet pages are served without an explicit charset and default to
    # ISO-8859-1 in ``requests``. Force UTF-8 so characters like en-dashes do
    # not get decoded as "\xc2" (displayed as "\xc2").
    resp.encoding = "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def fetch_paper_details(url: str) -> Tuple[str, str, List[List[str]]]:
    """Fetch a paper presentation page and return its description, image URL, and
    author affiliations."""
    soup = fetch_page(url)

    img_el = soup.find("img", class_="representative-img")
    img_url = urljoin(BASE_URL, img_el.get("src", "")) if img_el else ""

    abstract_el = soup.find("span", class_="abstract")
    description = abstract_el.get_text(strip=True) if abstract_el else ""

    affiliations: List[List[str]] = []
    for presenter in soup.find_all("div", class_="presenter-details"):
        if _is_fast_forward_presenter_descendant(presenter):
            continue
        inst_links = presenter.find_all(
            "a", attrs={"data-link-type": "presentation.person.institution"}
        )
        insts = [a.get_text(strip=True) for a in inst_links]
        affiliations.append(insts)

    return description, img_url, affiliations


def _download_image(paper: Dict[str, str], dest_dir: str) -> str:
    """Download a representative image and return the filename."""
    url = paper.get("image_url")
    paper_id = paper.get("paper_id")
    if not url or not paper_id:
        return ""

    ext = os.path.splitext(urlparse(url).path)[1]
    if not ext:
        ext = ".jpg"
    filename = f"{paper_id}{ext}"
    path = os.path.join(dest_dir, filename)

    resp = _get_with_retry(url)
    with open(path, "wb") as f:
        f.write(resp.content)
    return filename


def download_images(papers: List[Dict[str, str]], dest_dir: str) -> None:
    """Download representative images for all papers."""
    os.makedirs(dest_dir, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        filenames = list(
            tqdm(
                ex.map(lambda p: _download_image(p, dest_dir), papers),
                total=len(papers),
                desc="Downloading images",
            )
        )
    for paper, fname in zip(papers, filenames):
        paper["image_file"] = fname


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


def apply_ad_hoc_paper_fixes(papers: List[Dict[str, str]]) -> None:
    """Apply event-specific manual corrections for known bad source metadata."""
    for paper in papers:
        fix = AD_HOC_PAPER_FIXES.get(paper.get("title", ""))
        if not fix:
            continue
        paper["authors"] = fix["authors"]
        paper["affiliations"] = fix["affiliations"]


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
        if any(keyword in title for keyword in EXCLUDE_TITLE_KEYWORDS):
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

        title_link = row.find(
            "a", attrs={"data-link-type": lambda x: x and ".presentation" in x}
        )
        if not title_link:
            continue
        title = normalize_title(title_link.get_text(strip=True))
        url = urljoin(BASE_URL, title_link.get("href", ""))

        # Exclude interactive discussions and miscellaneous schedule items
        if "Interactive Discussion" in title:
            continue
        qs = parse_qs(urlparse(url).query)
        paper_id_val = qs.get("id", [""])[0]
        if paper_id_val.startswith("misc_"):
            continue

        author_links = row.find_all(
            "a", attrs={"data-link-type": lambda x: x and ".person" in x}
        )
        authors = [
            normalize_title(a.get_text(strip=True))
            for a in author_links
            if not _is_fast_forward_presenter_descendant(a)
        ]

        papers.append(
            {
                "paper_id": ssid,
                "session_id": psid,
                "title": title,
                "url": url,
                "authors": authors,
                "session": sessions[psid]["session_title"],
                "location": sessions[psid]["location"],
                "start": row.get("s_utc", ""),
                "end": row.get("e_utc", ""),
            }
        )
        detail_urls.append(url)

    # Fetch each paper's details concurrently with a progress bar
    with ThreadPoolExecutor(max_workers=8) as ex:
        details = list(
            tqdm(
                ex.map(fetch_paper_details, detail_urls),
                total=len(detail_urls),
                desc="Fetching paper details",
            )
        )

    for paper, (description, image_url, affiliations) in zip(papers, details):
        paper["description"] = description
        paper["image_url"] = image_url
        if affiliations:
            paper["affiliations"] = affiliations

    return papers


def parse_technical_papers(base_soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Parse the main schedule page and all snippet pages."""
    papers: List[Dict[str, str]] = []
    links = parse_snippet_links(base_soup)
    for link in tqdm(links, desc="Fetching schedule snippets"):
        resp = _get_with_retry(link)
        # Snippet responses omit the charset and default to ISO-8859-1; fix
        # it so we do not get stray characters in titles.
        resp.encoding = "utf-8"
        papers.extend(parse_snippet(resp.text))
        time.sleep(0.1)

    # Deduplicate papers by paper_id because each schedule snippet lists
    # every presentation multiple times (e.g., different time zones).
    unique: Dict[str, Dict[str, str]] = {}
    for paper in papers:
        pid = paper.get("paper_id")
        if pid and pid not in unique:
            unique[pid] = paper

    return list(unique.values())


def scrape_technical_papers(images_dir: str) -> List[Dict[str, str]]:
    """Scrape the schedule site for technical papers."""
    soup = fetch_page(BASE_URL)
    papers = parse_technical_papers(soup)
    apply_ad_hoc_paper_fixes(papers)
    download_images(papers, images_dir)
    return papers


def save_as_json(data: List[Dict[str, str]], path: str) -> None:
    """Save scraped data as JSON."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    event_dir = os.path.join("dist", "siggraph-asia-2025")
    images_dir = os.path.join(event_dir, "images")
    papers = scrape_technical_papers(images_dir)
    output_path = os.path.join(event_dir, "papers.json")
    save_as_json(papers, output_path)
    print(f"Saved {len(papers)} papers to {output_path}")
