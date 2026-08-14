import asyncio
import httpx
from bs4 import BeautifulSoup
from backend.config import settings


async def _fetch_job_description(client: httpx.AsyncClient, link: str, headers: dict) -> str:
    """Fetch and parse detailed job description asynchronously."""
    if not link:
        return "No description available."
    try:
        detail_res = await client.get(link, headers=headers, timeout=5)
        if detail_res.status_code == 200:
            detail_soup = BeautifulSoup(detail_res.text, "html.parser")
            desc_container = (
                detail_soup.find("div", class_="show-more-less-html__markup") or
                detail_soup.find("section", class_="description") or
                detail_soup.find("div", class_="description__text") or
                detail_soup.find("div", class_="job-description")
            )
            if desc_container:
                return desc_container.get_text(separator="\n").strip()
    except Exception:
        pass
    return "No description available."


async def fetch_linkedin_jobs(keyword: str, location: str = "remote", results_per_page: int = 5) -> list:
    """Search LinkedIn guest job postings and return list of parsed job items asynchronously."""
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
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("li")

            cards_to_process = job_cards[:results_per_page]
            card_data = []

            for card in cards_to_process:
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

                card_data.append({
                    "title": title,
                    "company": company,
                    "location_str": location_str,
                    "link": link
                })

            # Fetch job descriptions concurrently in non-blocking tasks
            desc_tasks = [_fetch_job_description(client, item["link"], headers) for item in card_data]
            descriptions = await asyncio.gather(*desc_tasks, return_exceptions=True)

            results = []
            for item, desc in zip(card_data, descriptions):
                job_summary = desc if isinstance(desc, str) else "No description available."
                results.append({
                    "position_title": item["title"],
                    "organization_name": item["company"],
                    "location": item["location_str"],
                    "job_summary": job_summary,
                    "url": item["link"],
                    "raw_data": {
                        "title": item["title"],
                        "company": item["company"],
                        "location": item["location_str"],
                        "url": item["link"],
                    }
                })
            return results
    except Exception:
        return []


def parse_job_item(item: dict) -> dict:
    """Passthrough helper for compatibility with router."""
    return item
