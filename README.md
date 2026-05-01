# LeadMySaaS

A Django + React app that automates B2B cold email lead generation. Describe your SaaS and target audience — AI generates targeted search queries, finds matching LinkedIn profiles via Google, extracts emails using multi-strategy hunting, and scores each lead for relevance.

## Features

- Create campaigns with your SaaS description and target audience
- AI generates targeted LinkedIn search queries optimized for email visibility
- Finds real LinkedIn profiles via Serper.dev (Google search API)
- Multi-strategy email extraction: snippet parsing → Serper search → LinkedIn page scrape → domain guessing
- AI batch-scores all leads in one call (0–100) with strict ICP rubric
- Profiles with visible emails are prioritized and score-boosted
- Lead status management (New → Contacted → Qualified → Rejected)
- Export leads to Excel (.xlsx) with one click
- Modern React + Tailwind dark UI
- Rate-limited AI calls with OpenRouter free models + Groq fallback

## Tech Stack

**Backend**
- Django 4.2+
- Serper.dev (Google Search API — 2500 free queries)
- OpenRouter free models (Llama 3.3 70B, Gemma, etc.)
- Groq API fallback (Llama 3.3 70B — 14,400 free req/day)
- openpyxl for Excel export
- SQLite (default, swap for Postgres in production)

**Frontend**
- React 18 + Vite
- Tailwind CSS v4
- Lucide icons

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/leadmysaas.git
cd leadmysaas
```

### 2. Create and activate a virtual environment

```bash
python -m venv env
# Windows
env\Scripts\activate
# macOS/Linux
source env/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure environment variables

Copy `.env.example` to `.env` and fill in your keys:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
GROQ_API_KEY=your_groq_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

| Key | Where to get it | Free tier |
|-----|----------------|-----------|
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) | Free models available |
| `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) | 14,400 req/day |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) | 2,500 free searches |

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Build the frontend

```bash
cd frontend
npm run build
cd ..
```

### 8. Start the server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Development (hot reload)

Run both servers simultaneously:

```bash
# Terminal 1 — Django API
python manage.py runserver

# Terminal 2 — React dev server (proxies /api to Django)
cd frontend
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173)

## Usage

1. Click **+ New Campaign**
2. Fill in your SaaS description and target audience (be specific — e.g. *"CTOs at B2B SaaS startups with 10–100 employees"*)
3. Click **Run AI Scrape** — the pipeline will:
   - Generate 5 targeted search queries optimized for email-visible profiles
   - Find up to 50 real LinkedIn profiles via Serper
   - Batch-score all profiles in one AI call
   - Hunt emails for all good fits (score ≥ 60)
4. Leads appear ranked by AI score — email-visible profiles float to the top
5. Click **Export Excel** to download the full lead list as `.xlsx`
6. Update lead status as you work through outreach

## How Email Hunting Works

For each good-fit profile the scraper tries 3 strategies in order:

1. **Serper search** — searches `"Name" "Company" email` and `"Name" "Company" contact "@"` to find publicly indexed emails
2. **LinkedIn page scrape** — fetches the public profile page and extracts any visible email
3. **Domain guessing** — finds the company domain via Serper, then tries common formats: `first@domain.com`, `first.last@domain.com`, `flast@domain.com`

## Project Structure

```
leadmysaas/
├── leads/
│   ├── models.py           # Campaign + Lead models
│   ├── scraper.py          # AI + Serper search + email hunting pipeline
│   ├── views.py            # REST API views + Excel export
│   ├── urls.py             # URL routes
│   └── templates/leads/    # SPA shell template
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   └── CampaignDetail.jsx
│   │   └── components/
│   │       └── NewCampaignModal.jsx
│   └── vite.config.js
├── leadmysaas/
│   ├── settings.py
│   └── urls.py
├── requirements.txt
├── .env.example
└── manage.py
```

## Notes

- LinkedIn blocks direct scraping — this app uses Google search (`site:linkedin.com/in/`) via Serper as a proxy
- Email discovery rate depends on how publicly visible the person's email is — typically 20–40% of leads will have a confirmed email
- AI rate limiting is built in (8 calls/min max) with automatic fallback across providers
- Re-running a scrape on an existing campaign updates emails and scores on existing leads rather than creating duplicates

## License

MIT
