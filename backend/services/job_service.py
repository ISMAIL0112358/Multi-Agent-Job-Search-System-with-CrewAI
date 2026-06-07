import requests
from bs4 import BeautifulSoup
from backend.config import settings


def fetch_linkedin_jobs(keyword: str, location: str = "remote", results_per_page: int = 5) -> list:
    """Search LinkedIn guest job postings and return list of parsed job items."""
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {
        "keywords": keyword,
        "location": location,
        "start": 0
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("li")
        
        results = []
        for card in job_cards[:results_per_page]:
            # Extract title
            title_el = card.find("h3", class_="base-search-card__title")
            title = title_el.text.strip() if title_el else "Unknown Position"
            
            # Extract company
            company_el = card.find("h4", class_="base-search-card__subtitle")
            company = company_el.text.strip() if company_el else "Unknown Company"
            
            # Extract location
            location_el = card.find("span", class_="job-search-card__location")
            location_str = location_el.text.strip() if location_el else "Remote"
            
            # Extract link
            link_el = card.find("a", class_="base-card__full-link")
            link = link_el["href"] if link_el else ""
            if link:
                link = link.split("?")[0]
            
            # Fetch job summary / description
            job_summary = "No description available."
            if link:
                try:
                    detail_res = requests.get(link, headers=headers, timeout=5)
                    if detail_res.status_code == 200:
                        detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                        desc_container = (
                            detail_soup.find("div", class_="show-more-less-html__markup") or
                            detail_soup.find("section", class_="description") or
                            detail_soup.find("div", class_="description__text") or
                            detail_soup.find("div", class_="job-description")
                        )
                        if desc_container:
                            job_summary = desc_container.get_text(separator="\n").strip()
                except Exception:
                    pass
            
            results.append({
                "position_title": title,
                "organization_name": company,
                "location": location_str,
                "job_summary": job_summary,
                "url": link,
                "raw_data": {
                    "title": title,
                    "company": company,
                    "location": location_str,
                    "url": link,
                }
            })
        return results
    except Exception:
        return []


def parse_job_item(item: dict) -> dict:
    """Passthrough helper for compatibility with router."""
    return item
