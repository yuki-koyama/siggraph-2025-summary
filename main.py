from scrape_siggraph2025 import scrape_technical_papers, save_as_json
import os


def main() -> None:
    papers = scrape_technical_papers()
    output_path = os.path.join("data", "papers.json")
    save_as_json(papers, output_path)
    print(f"Saved {len(papers)} papers to {output_path}")


if __name__ == "__main__":
    main()
