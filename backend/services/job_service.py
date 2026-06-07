import requests
from backend.config import settings


def fetch_usajobs(keyword: str, location: str = "remote", results_per_page: int = 5) -> list:
    """Search USAJobs API and return list of job result items."""
    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": "job-search-agent@app.com",
        "Authorization-Key": settings.USAJOBS_API_KEY,
    }

    url = "https://data.usajobs.gov/api/search"
    params = {
        "Keyword": keyword,
        "LocationName": location,
        "ResultsPerPage": results_per_page,
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("SearchResult", {}).get("SearchResultItems", [])
    return []


def parse_job_item(item: dict) -> dict:
    """Parse a raw USAJobs item into a clean dict for the frontend."""
    descriptor = item.get("MatchedObjectDescriptor", {})
    locations = descriptor.get("PositionLocation", [])
    location_str = locations[0].get("LocationName", "Unknown") if locations else "Unknown"

    # Get the job URL
    position_uri = descriptor.get("PositionURI", "")
    apply_uri = descriptor.get("ApplyURI", [""])[0] if descriptor.get("ApplyURI") else position_uri

    # Get job summary
    user_area = descriptor.get("UserArea", {})
    details = user_area.get("Details", {})
    job_summary = details.get("JobSummary", "No summary available.")

    return {
        "position_title": descriptor.get("PositionTitle", "Unknown"),
        "organization_name": descriptor.get("OrganizationName", "Unknown"),
        "location": location_str,
        "job_summary": job_summary,
        "url": apply_uri or position_uri,
        "raw_data": descriptor,
    }
