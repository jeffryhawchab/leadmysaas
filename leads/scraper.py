import os
import re
import time
import requests
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.0-flash"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def generate_search_queries(saas_description: str, target_audience: str) -> list[str]:
    """Use Gemini Flash to generate LinkedIn search queries."""
    prompt = f"""
You are a B2B lead generation expert.

SaaS product: {saas_description}
Target audience: {target_audience}

Generate 5 Google search queries to find LinkedIn profiles of ideal customers.
Each query should use: site:linkedin.com/in/ + job title + industry keywords.
Return ONLY the queries, one per line, no numbering or extra text.
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    queries = [q.strip() for q in response.text.strip().split("\n") if q.strip()]
    return queries[:5]


def score_lead(name: str, title: str, company: str, saas_description: str, target_audience: str) -> int:
    """Use Gemini Flash to score how relevant a lead is (0-100)."""
    prompt = f"""
Rate this lead's relevance from 0 to 100 for the following SaaS product.

SaaS: {saas_description}
Target audience: {target_audience}

Lead:
- Name: {name}
- Title: {title}
- Company: {company}

Return ONLY a number between 0 and 100. Nothing else.
"""
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        score = int(re.search(r'\d+', response.text).group())
        return min(max(score, 0), 100)
    except Exception:
        return 50


def scrape_linkedin_profiles(query: str, max_results: int = 5) -> list[dict]:
    """Search Google for LinkedIn profiles and scrape basic info."""
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={max_results}"
    leads = []

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for result in soup.select("div.g")[:max_results]:
            link_tag = result.select_one("a[href]")
            title_tag = result.select_one("h3")
            snippet_tag = result.select_one("div.VwiC3b, span.aCOpRe")

            if not link_tag or not title_tag:
                continue

            href = link_tag["href"]
            if "linkedin.com/in/" not in href:
                continue

            # Clean LinkedIn URL
            linkedin_url = re.search(r'https://[^\s&"]+linkedin\.com/in/[^\s&"]+', href)
            if not linkedin_url:
                continue

            snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""
            full_text = title_tag.get_text(" ", strip=True) + " " + snippet

            # Parse name, title, company from Google snippet
            name, title, company = parse_profile_text(full_text)
            email = extract_email(snippet)

            leads.append({
                "name": name,
                "linkedin_url": linkedin_url.group(),
                "email": email,
                "title": title,
                "company": company,
            })
            time.sleep(0.5)

    except Exception as e:
        print(f"Scraping error: {e}")

    return leads


def parse_profile_text(text: str) -> tuple[str, str, str]:
    """Extract name, title, company from LinkedIn Google snippet."""
    name, title, company = "", "", ""

    # LinkedIn snippets often: "Name - Title at Company | LinkedIn"
    match = re.match(r'^([^|–\-]+?)[\s–\-]+([^|]+?)(?:\s+at\s+([^|]+))?(?:\s*\|.*)?$', text)
    if match:
        name = match.group(1).strip()
        title = match.group(2).strip() if match.group(2) else ""
        company = match.group(3).strip() if match.group(3) else ""

    return name, title, company


def extract_email(text: str) -> str:
    """Extract email from text if present."""
    match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    return match.group() if match else ""


def run_campaign_scrape(campaign) -> list[dict]:
    """Full pipeline: generate queries → scrape → score leads."""
    queries = generate_search_queries(campaign.saas_description, campaign.target_audience)
    campaign.ai_search_queries = "\n".join(queries)
    campaign.save()

    all_leads = []
    for query in queries:
        profiles = scrape_linkedin_profiles(query)
        for profile in profiles:
            profile["ai_score"] = score_lead(
                profile["name"], profile["title"], profile["company"],
                campaign.saas_description, campaign.target_audience
            )
            all_leads.append(profile)
        time.sleep(2)  # be polite between queries

    return all_leads
