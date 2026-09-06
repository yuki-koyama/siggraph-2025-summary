"""Classify SIGGRAPH 2026 papers by publication and presentation status."""

from collections import Counter
from io import BytesIO
import re
from typing import Dict, List, Optional, Sequence, Set, Tuple

from bs4 import BeautifulSoup
from pypdf import PdfReader


CONFERENCE_PROCEEDINGS_TITLE = (
    "Proceedings of the Special Interest Group on Computer Graphics and "
    "Interactive Techniques Conference Conference Papers"
)
ACCEPTED_PAPERS_URL = (
    "https://s2026.siggraph.org/wp-content/uploads/2026/03/"
    "SIGGRAPH-2026-TECHNICAL-PAPERS-CONDITIONALLY-ACCEPTED-PAPERS.pdf"
)
CROSSREF_WORKS_URL = "https://api.crossref.org/works"

TAG_LABELS = {
    "conference": "Conference Papers",
    "journal": "Journal Papers",
    "invited-tog": "Invited from TOG",
    "conference-deferred": "Conference Papers (Deferred Paper Presentation)",
    "journal-deferred": "Journal Papers (Deferred Paper Presentation)",
}

EXPECTED_COUNTS = {
    "conference": 183,
    "journal": 126,
    "invited-tog": 36,
    "conference-deferred": 12,
    "journal-deferred": 6,
}


def _clean_markup(value: str) -> str:
    return " ".join(BeautifulSoup(value or "", "html.parser").get_text(" ").split())


def _normalize(value: str) -> str:
    return "".join(ch for ch in _clean_markup(value).casefold() if ch.isalnum())


def _crossref_authors(publication: Dict) -> List[str]:
    return [
        " ".join(
            part
            for part in (author.get("given", ""), author.get("family", ""))
            if part
        )
        for author in publication.get("author", [])
    ]


def _author_signature(names: Sequence[str]) -> Tuple[str, ...]:
    return tuple(_normalize(name) for name in names)


def _fetch_crossref(session, params: Dict[str, str]) -> List[Dict]:
    response = session.get(CROSSREF_WORKS_URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()["message"]["items"]


def _fetch_publications(session) -> Tuple[List[Dict], List[Dict]]:
    common_select = (
        "DOI,title,author,page,container-title,type,abstract,link,volume,issue"
    )
    conference_results = _fetch_crossref(
        session,
        {
            "query.container-title": CONFERENCE_PROCEEDINGS_TITLE,
            "filter": "prefix:10.1145,from-pub-date:2026-07-01,until-pub-date:2026-07-31",
            "rows": "1000",
            "select": common_select,
        },
    )
    conference = [
        item
        for item in conference_results
        if item.get("container-title", [""])[0] == CONFERENCE_PROCEEDINGS_TITLE
    ]

    journal_results = _fetch_crossref(
        session,
        {
            "filter": "issn:1557-7368,from-pub-date:2026-07-01,until-pub-date:2026-07-31",
            "rows": "1000",
            "select": common_select,
        },
    )
    journal = [
        item
        for item in journal_results
        if item.get("volume") == "45"
        and item.get("issue") == "4"
        and item.get("type") == "journal-article"
        and "editorial" not in _normalize(item.get("title", [""])[0])
    ]
    return conference, journal


def _find_schedule_match(
    publication: Dict, schedule_papers: Sequence[Dict], used_ids: Set[str]
) -> Optional[Dict]:
    candidates = [p for p in schedule_papers if p["paper_id"] not in used_ids]
    publication_title = _normalize(publication.get("title", [""])[0])
    title_matches = [p for p in candidates if _normalize(p["title"]) == publication_title]
    if len(title_matches) == 1:
        return title_matches[0]
    if len(title_matches) > 1:
        raise ValueError(f"Ambiguous title match: {publication.get('title', [''])[0]}")

    publication_authors = _author_signature(_crossref_authors(publication))
    author_matches = [
        p
        for p in candidates
        if publication_authors and _author_signature(p.get("authors", [])) == publication_authors
    ]
    if len(author_matches) == 1:
        return author_matches[0]
    if len(author_matches) > 1:
        raise ValueError(f"Ambiguous author match: {publication.get('title', [''])[0]}")
    return None


def _tag_presented_papers(
    schedule_papers: Sequence[Dict], publications: Sequence[Dict], tag: str, used_ids: Set[str]
) -> List[Dict]:
    deferred = []
    for publication in publications:
        paper = _find_schedule_match(publication, schedule_papers, used_ids)
        if paper is None:
            deferred.append(publication)
            continue
        paper["paper_type"] = tag
        paper["paper_type_label"] = TAG_LABELS[tag]
        paper["is_deferred"] = False
        paper["publication_url"] = f"https://doi.org/{publication['DOI']}"
        used_ids.add(paper["paper_id"])
    return deferred


def _deferred_paper(publication: Dict, tag: str) -> Dict:
    authors = _crossref_authors(publication)
    affiliations = [
        [affiliation["name"] for affiliation in author.get("affiliation", [])]
        for author in publication.get("author", [])
    ]
    doi = publication["DOI"]
    return {
        "paper_id": "doi_" + re.sub(r"[^a-zA-Z0-9]+", "_", doi),
        "session_id": "",
        "title": _clean_markup(publication.get("title", [""])[0]),
        "url": f"https://doi.org/{doi}",
        "authors": authors,
        "affiliations": affiliations,
        "session": "Deferred Paper Presentations",
        "location": "",
        "start": "",
        "end": "",
        "description": _clean_markup(publication.get("abstract", "")),
        "image_url": "",
        "image_file": "",
        "paper_type": tag,
        "paper_type_label": TAG_LABELS[tag],
        "is_deferred": True,
        "publication_url": f"https://doi.org/{doi}",
    }


def _accepted_paper_ids(session) -> Set[str]:
    response = session.get(ACCEPTED_PAPERS_URL, timeout=60)
    response.raise_for_status()
    text = "\n".join(
        page.extract_text() or "" for page in PdfReader(BytesIO(response.content)).pages
    )
    return set(re.findall(r"papers_\d+", text))


def classify_siggraph2026_papers(papers: List[Dict], session) -> List[Dict]:
    """Add one of five tags and append deferred publications as a reference appendix."""
    schedule_papers = [p for p in papers if p["paper_id"].startswith("papers_")]
    invited_papers = [p for p in papers if p["paper_id"].startswith("paperstog_")]
    conference_publications, journal_publications = _fetch_publications(session)

    if len(conference_publications) != 195 or len(journal_publications) != 132:
        raise ValueError(
            "Unexpected publication counts: "
            f"Conference={len(conference_publications)}, Journal={len(journal_publications)}"
        )

    used_ids: Set[str] = set()
    deferred_journal = _tag_presented_papers(
        schedule_papers, journal_publications, "journal", used_ids
    )
    deferred_conference = _tag_presented_papers(
        schedule_papers, conference_publications, "conference", used_ids
    )

    for paper in invited_papers:
        paper["paper_type"] = "invited-tog"
        paper["paper_type_label"] = TAG_LABELS["invited-tog"]
        paper["is_deferred"] = False

    unclassified = [p["paper_id"] for p in schedule_papers if "paper_type" not in p]
    if unclassified:
        raise ValueError(f"Unclassified scheduled papers: {unclassified}")

    deferred = [
        *(_deferred_paper(p, "conference-deferred") for p in deferred_conference),
        *(_deferred_paper(p, "journal-deferred") for p in deferred_journal),
    ]
    result = papers + sorted(deferred, key=lambda p: (p["paper_type"], p["title"]))

    accepted_ids = _accepted_paper_ids(session)
    scheduled_ids = {p["paper_id"] for p in schedule_papers}
    if len(accepted_ids) != 327:
        raise ValueError(f"Expected 327 accepted paper IDs, found {len(accepted_ids)}")
    if not scheduled_ids <= accepted_ids:
        raise ValueError("The schedule contains paper IDs absent from the accepted-paper list")
    if len(accepted_ids - scheduled_ids) != 18:
        raise ValueError(
            f"Expected 18 deferred paper IDs, found {len(accepted_ids - scheduled_ids)}"
        )

    counts = Counter(p["paper_type"] for p in result)
    if counts != Counter(EXPECTED_COUNTS):
        raise ValueError(f"Unexpected classification counts: {dict(counts)}")
    return result
