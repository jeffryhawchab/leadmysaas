import os
import re
import sys
import time
import threading
import requests
from dotenv import load_dotenv

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def log(msg):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode(), flush=True)


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SERPER_URL = "https://google.serper.dev/search"

FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-3-27b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "qwen/qwen3-coder:free",
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "gemma2-9b-it",
]

SCORE_THRESHOLD = 60
MAX_AI_CALLS_PER_MIN = 8
MAX_QUERIES = 5
MAX_PROFILES_PER_QUERY = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# -- Rate limiter --------------------------------------------------------------

class RateLimiter:
    def __init__(self, max_calls: int, period: float = 60.0):
        self.max_calls = max_calls
        self.period = period
        self.calls: list[float] = []
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.time()
            self.calls = [t for t in self.calls if now - t < self.period]
            if len(self.calls) >= self.max_calls:
                sleep_for = self.period - (now - self.calls[0])
                log(f"[rate-limiter] quota reached, waiting {sleep_for:.1f}s...")
                time.sleep(max(sleep_for, 0))
                self.calls = [t for t in self.calls if time.time() - t < self.period]
            self.calls.append(time.time())


_limiter = RateLimiter(MAX_AI_CALLS_PER_MIN)


# -- AI ------------------------------------------------------------------------

def _call(url, api_key, model, prompt):
    try:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        if resp.status_code == 429:
            log(f"[rate-limited] {model}")
            return None
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log(f"[error] {model}: {e}")
        return None


def ai(prompt: str) -> str:
    _limiter.wait()
    if OPENROUTER_API_KEY:
        for model in FREE_MODELS:
            result = _call(OPENROUTER_URL, OPENROUTER_API_KEY, model, prompt)
            if result:
                return result
            time.sleep(0.5)
    if GROQ_API_KEY:
        for model in GROQ_MODELS:
            result = _call(GROQ_URL, GROQ_API_KEY, model, prompt)
            if result:
                return result
            time.sleep(0.5)
    raise Exception("All AI providers are rate-limited. Try again shortly.")


# -- Search --------------------------------------------------------------------

def serper_search(query: str, num: int = MAX_PROFILES_PER_QUERY) -> list[dict]:
    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("organic", [])
    except Exception as e:
        log(f"[serper error] {e}")
        return []


def clean_query(q: str) -> str:
    """Strip quotes, punctuation and extra whitespace from AI-generated queries."""
    q = re.sub(r'["\u201c\u201d\u2018\u2019]', '', q)  # remove all quote types
    q = re.sub(r'[^\w\s]', ' ', q)                      # remove punctuation
    q = re.sub(r'\s+', ' ', q).strip()                   # collapse whitespace
    return q


def search_linkedin_profiles(query: str) -> list[dict]:
    query = clean_query(query)
    results = []
    seen_urls = set()

    # Primary search: profiles with email signals in the query
    for search_q in [
        f"site:linkedin.com/in/ {query}",
        f"site:linkedin.com/in/ {query} email",
        f"site:linkedin.com/in/ {query} gmail",
    ]:
        items = serper_search(search_q, num=MAX_PROFILES_PER_QUERY)
        for item in items:
            url = item.get("link", "")
            if "linkedin.com/in/" not in url:
                continue
            clean_url = url.split("?")[0].rstrip("/")
            if clean_url in seen_urls:
                continue
            seen_urls.add(clean_url)
            snippet = item.get("snippet", "")
            has_email = bool(extract_email(snippet))
            results.append({
                "url": clean_url,
                "title": item.get("title", ""),
                "snippet": snippet,
                "has_email": has_email,
            })

    # Sort: profiles with visible email first
    results.sort(key=lambda x: x["has_email"], reverse=True)
    return results


# -- Email hunting -------------------------------------------------------------

def find_email(name: str, company: str, linkedin_url: str) -> str:
    username = linkedin_url.rstrip("/").split("/")[-1]

    # Strategy 1: search for their email via Serper
    search_queries = []
    if name and company:
        search_queries.append(f'"{name}" "{company}" email')
        search_queries.append(f'"{name}" "{company}" contact "@"')
    search_queries.append(f'"{username}" linkedin email contact')

    for q in search_queries:
        items = serper_search(q, num=5)
        for item in items:
            text = item.get("snippet", "") + " " + item.get("title", "")
            email = extract_email(text)
            if email and not any(x in email for x in ["linkedin.com", "example.com", "google.com"]):
                log(f"[email] found via search: {email}")
                return email
        time.sleep(0.5)

    # Strategy 2: scrape LinkedIn page directly
    try:
        resp = requests.get(linkedin_url, headers=HEADERS, timeout=10)
        email = extract_email(resp.text)
        if email and "linkedin.com" not in email:
            log(f"[email] found on profile page: {email}")
            return email
    except Exception:
        pass

    # Strategy 3: guess common email formats from company domain
    if name and company:
        domain = guess_domain(company)
        if domain:
            parts = name.lower().split()
            if len(parts) >= 2:
                first, last = parts[0], parts[-1]
                for fmt in [f"{first}@{domain}", f"{first}.{last}@{domain}",
                             f"{first[0]}{last}@{domain}", f"{first}{last[0]}@{domain}"]:
                    if verify_email_format(fmt):
                        log(f"[email] guessed: {fmt}")
                        return fmt

    return ""


def guess_domain(company: str) -> str:
    try:
        items = serper_search(f"{company} official website", num=3)
        for item in items:
            url = item.get("link", "")
            m = re.search(r'https?://(?:www\.)?([a-zA-Z0-9\-]+\.[a-zA-Z]{2,})', url)
            if m:
                domain = m.group(1)
                if not any(x in domain for x in ["linkedin", "facebook", "twitter", "wikipedia", "google", "youtube"]):
                    return domain
    except Exception:
        pass
    return ""


def verify_email_format(email: str) -> bool:
    return bool(re.match(r'^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$', email))


def extract_email(text: str) -> str:
    m = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    return m.group() if m else ""


# -- Profile parsing -----------------------------------------------------------

def parse_profile(result: dict) -> dict:
    text = result["title"] + " " + result["snippet"]
    name, title, company = "", "", ""
    m = re.match(r'^([^|\-]+?)[\s\-]+([^|]+?)(?:\s+at\s+([^|]+))?(?:\s*\|.*)?$', text.strip())
    if m:
        name = m.group(1).strip()
        title = m.group(2).strip()
        company = m.group(3).strip() if m.group(3) else ""
    # grab email directly from snippet if visible
    email = extract_email(result["snippet"])
    return {
        "name": name,
        "linkedin_url": result["url"],
        "title": title,
        "company": company,
        "email": email,
        "has_email": result.get("has_email", bool(email)),
        "snippet": result["snippet"],
    }


# -- AI tasks ------------------------------------------------------------------

def generate_search_queries(saas_description: str, target_audience: str) -> list[str]:
    prompt = f"""You are a LinkedIn cold email prospecting expert.

SaaS product: {saas_description}
Target audience: {target_audience}

Generate {MAX_QUERIES} short Google search queries (4-8 words) designed to find LinkedIn profiles
that have a visible email address in their bio or snippet.

Rules:
- SHORT keywords only, no quotes, no punctuation, no full sentences
- Always include email-signal words like: email, contact, gmail, @, reach me
- Vary seniority: VP, Director, Head of, Chief, Lead, Manager, Founder, Co-founder
- Vary company stage: startup, scaleup, enterprise, Series A
- Target decision makers who buy this type of SaaS
- Each query must be different

Good examples:
  VP Engineering SaaS startup email contact
  CTO fintech scaleup gmail reach me
  Head of Product B2B email
  Director Engineering enterprise contact me
  Founder SaaS startup email

Return ONLY the {MAX_QUERIES} queries, one per line, no numbering, no quotes, no explanation."""
    text = ai(prompt)
    queries = [clean_query(q) for q in text.strip().split("\n") if q.strip()]
    return [q for q in queries if len(q.split()) >= 2][:MAX_QUERIES]


def batch_score_leads(profiles: list[dict], saas_description: str, target_audience: str) -> list[int]:
    if not profiles:
        return []
    lines = "\n".join(
        f"{i+1}. Name: {p['name']} | Title: {p['title']} | Company: {p['company']} | Bio: {p['snippet'][:120]}"
        for i, p in enumerate(profiles)
    )
    prompt = f"""You are a strict B2B sales qualification expert.

SaaS product: {saas_description}
Ideal customer profile: {target_audience}

Score each lead's fit from 0 to 100:
- 80-100: Perfect fit. Title, seniority, company type all match ICP exactly. Clear decision-maker.
- 60-79: Good fit. Mostly matches ICP, minor gaps in seniority or industry.
- 40-59: Partial fit. Related role but not ideal buyer or wrong company stage.
- 0-39: Poor fit. Wrong title, industry, or seniority.

Leads:
{lines}

Return ONLY a JSON array of integers in the same order, e.g. [92, 45, 78]. Nothing else."""
    try:
        text = ai(prompt)
        numbers = re.findall(r'\d+', text)
        scores = [min(max(int(n), 0), 100) for n in numbers[:len(profiles)]]
        while len(scores) < len(profiles):
            scores.append(50)
        return scores
    except Exception:
        return [50] * len(profiles)


# -- Main pipeline -------------------------------------------------------------

def run_campaign_scrape(campaign) -> list[dict]:
    # Step 1 - generate queries
    queries = generate_search_queries(campaign.saas_description, campaign.target_audience)
    campaign.ai_search_queries = "\n".join(queries)
    campaign.save()
    log(f"[pipeline] {len(queries)} queries generated")

    # Step 2 - find LinkedIn profiles via Serper
    all_results = []
    for query in queries:
        results = search_linkedin_profiles(query)
        log(f"[pipeline] '{query}' -> {len(results)} profiles")
        all_results.extend(results)
        time.sleep(1)

    # Deduplicate by URL
    seen = set()
    profiles = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            profiles.append(parse_profile(r))

    if not profiles:
        log("[pipeline] No profiles found. Check SERPER_API_KEY in .env")
        return []

    log(f"[pipeline] {len(profiles)} unique profiles found")

    # Step 3 - batch score (1 AI call)
    scores = batch_score_leads(profiles, campaign.saas_description, campaign.target_audience)
    for profile, score in zip(profiles, scores):
        # boost score by 10 if email already visible — these are the most actionable
        profile["ai_score"] = min(score + (10 if profile.get("has_email") else 0), 100)

    # Step 4 - email hunting
    # prioritize: profiles with email already visible, then good fits by score
    profiles.sort(key=lambda p: (p.get("has_email", False), p["ai_score"]), reverse=True)
    good_fits = [p for p in profiles if p["ai_score"] >= SCORE_THRESHOLD]
    log(f"[pipeline] {len(good_fits)} good fits - hunting emails...")

    for profile in good_fits:
        if not profile["email"]:
            profile["email"] = find_email(
                profile["name"], profile["company"], profile["linkedin_url"]
            )
            time.sleep(1)

    found_emails = sum(1 for p in profiles if p["email"])
    log(f"[pipeline] done. {len(profiles)} profiles, {found_emails} with emails")

    for p in profiles:
        p.pop("snippet", None)
        p.pop("has_email", None)

    return profiles
