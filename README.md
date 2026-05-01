# LeadMySaaS

A Django app that automates B2B lead generation by scraping LinkedIn profiles using AI-powered targeting. Describe your SaaS and target audience — Gemini Flash generates search queries, finds matching LinkedIn profiles, extracts emails, and scores each lead for relevance.

## Features

- Create campaigns with your SaaS description and target audience
- Gemini Flash generates LinkedIn search queries tailored to your ICP
- Scrapes LinkedIn profiles via Google search (no LinkedIn account needed)
- AI relevance scoring (0–100) for each lead
- Lead status management (New → Contacted → Qualified → Rejected)

## Tech Stack

- Django 4.2+
- Gemini 2.0 Flash (free tier via `google-genai`)
- BeautifulSoup4 + Requests for scraping
- SQLite (default, swap for Postgres in production)
- Bootstrap 5 (UI)

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get a free Gemini API key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Usage

1. Click **+ New Campaign**
2. Fill in your SaaS description and target audience (be specific — e.g. *"CTOs at B2B SaaS startups with 10–100 employees"*)
3. Click **Run AI Scrape** on the campaign page
4. Leads appear ranked by AI relevance score
5. Update lead status as you work through outreach

## Project Structure

```
leadmysaas/
├── leads/
│   ├── models.py          # Campaign + Lead models
│   ├── scraper.py         # Gemini AI + Google/LinkedIn scraping pipeline
│   ├── views.py           # All views
│   ├── forms.py           # Campaign form
│   ├── urls.py            # URL routes
│   └── templates/leads/   # HTML templates
├── leadmysaas/
│   ├── settings.py
│   └── urls.py
├── requirements.txt
├── .env                   # Not committed — add your API key here
└── manage.py
```

## Notes

- LinkedIn blocks direct scraping, so this app uses Google search (`site:linkedin.com/in/`) as a proxy
- Emails visible in Google snippets are extracted automatically; for higher email yield consider integrating [Hunter.io](https://hunter.io) or [Apollo.io](https://apollo.io)
- Gemini Flash free tier has generous limits (15 RPM, 1M tokens/day) — sufficient for testing and small campaigns

## License

MIT
