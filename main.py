from scrape_siggraph2025 import scrape_technical_papers, save_as_json


def main() -> None:
    papers = scrape_technical_papers()
    save_as_json(papers, "papers.json")
    print(f"Saved {len(papers)} papers to papers.json")


if __name__ == "__main__":
    main()
