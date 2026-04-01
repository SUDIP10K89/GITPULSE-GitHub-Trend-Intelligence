# GitPulse

GitPulse is a GitHub trending repository monitoring and analysis system. It scrapes trending repositories, classifies them by category, tracks "stars today" growth, and sends daily email digests. A small FastAPI service powers subscriptions, and a GitPulse-branded UI provides a simple signup experience.

## Features

- Trending Repository Scraping: Automatically scrapes GitHub Trending daily
- AI-Powered Classification: Categorizes repos into AI, Developer Tools, Infrastructure, Web, Mobile, Other
- Growth Signals: Tracks GitHub Trending "stars today" and growth multiples
- Email Digest: Sends daily email summaries (optionally category-filtered)
- Subscriber API: Subscribe/unsubscribe endpoint with category preferences
- GitPulse UI: Static landing page with subscribe/unsubscribe form
- MongoDB Integration: Stores trending data and subscriber preferences

## Architecture

```
GitPulse/
|-- api/                 # FastAPI subscriber API
|-- analytics/           # Growth multiple calculations
|-- classifier/          # AI-powered repository classification
|-- email/               # Email generation and sending
|-- scraper/             # GitHub Trending scraper
|-- ui/                  # GitPulse landing page (static)
|-- .env                 # Environment variables (local)
|-- .env.example         # Environment template
|-- README.md            # This file
|-- requirements.txt     # Python dependencies
|-- run_pipeline.py      # Main pipeline orchestrator
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd GitPulse
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

Create a `.env` file with the following variables (see `.env.example` for the full template):

```env
MONGO_URI=mongodb+srv://<DB_USER>:<DB_PASSWORD>@<CLUSTER_URL>/?appName=<APP_NAME>
DB_NAME=<DB_NAME>

OPENAI_BASE_URL=<OPENAI_BASE_URL>
OPENAI_MODEL=<OPENAI_MODEL>
OPENAI_API_KEY=<OPENAI_API_KEY>
AI_MAX_RETRIES=6
AI_BASE_BACKOFF_SECONDS=1.5
AI_MAX_BACKOFF_SECONDS=30
AI_MAX_RETRY_WAIT_SECONDS=120

SMTP_HOST=<SMTP_HOST>
SMTP_PORT=<SMTP_PORT>
SMTP_USER=<SMTP_EMAIL>
SMTP_PASS=<SMTP_PASSWORD>
```

## Usage

Run the complete pipeline:
```bash
python run_pipeline.py
```

This runs:
1. Scrape trending repositories from GitHub
2. Classify each repository by category
3. Calculate growth multiples vs yesterday
4. Send an email digest with top accelerating repositories

Run the API locally:
```bash
python api/main.py
```

Run with autoreload:
```bash
uvicorn api.main:app --reload
```

Open the UI:
- Open `ui/index.html` in a browser, or serve `ui/` with any static server.
- Update `API_BASE` in `ui/script.js` to point to your API if running locally.

## GitHub Actions Automation

This repo includes a workflow that runs the pipeline on a schedule and can be triggered manually.

### Setup Secrets
Create these repository secrets in GitHub (`Settings` -> `Secrets and variables` -> `Actions`):

- MONGO_URI
- DB_NAME
- OPENAI_API_KEY
- OPENAI_BASE_URL
- OPENAI_MODEL
- SMTP_HOST
- SMTP_PORT
- SMTP_USER
- SMTP_PASS

### Schedule
The workflow is scheduled daily at 02:00 UTC. Update the cron expression in
`.github/workflows/repodradar-pipeline.yml` if you want a different time.

## Pipeline Components

### 1. Scraper (`scraper/scrape_trending.py`)
- Scrapes GitHub Trending repositories
- Extracts name, URL, description, language, stars, forks, and "stars today"
- Writes to MongoDB collection `trending_repos_test` with `scraped_date` + `scraped_at`

### 2. Classifier (`classifier/classify.py`)
- Uses OpenAI to classify repositories into categories
- Categories: AI, Developer Tools, Infrastructure, Web, Mobile, Other
- Reads from `trending_repos` and updates MongoDB with classification results

### 3. Analytics (`analytics/growth.py`)
- Calculates how many times a repo grew vs yesterday
- Reads from `trending_repos` and updates MongoDB with `growth_multiple`

### 4. Email (`email/send_email.py`)
- Generates daily email digest
- Includes top 10 accelerating repositories with detailed information
- Sends email via SMTP to active subscribers (optionally category-filtered)

## API

### POST /api/subscribe
- Body: `{ "email": "you@example.com", "categories": ["AI", "Web"] }`
- If `categories` is empty or omitted, the subscription defaults to all categories.

### POST /api/unsubscribe
- Body: `{ "email": "you@example.com" }`

Allowed categories: AI, Developer Tools, Infrastructure, Web, Mobile, Other.

## Data Model

### Trending Repos
Each repository document includes:
- `name`: Repository name
- `url`: GitHub URL
- `description`: Repository description
- `language`: Primary programming language
- `stars`: Current star count
- `forks`: Current fork count
- `category`: AI-classified category
- `stars_growth`: Stars today from GitHub Trending
- `growth_multiple`: Stars today divided by yesterday's stars today (rounded)
- `scraped_date`: Date string (YYYY-MM-DD)
- `scraped_at`: Timestamp of data collection

### Subscribers
Each subscriber document includes:
- `email`: Subscriber email
- `active`: Boolean flag
- `categories`: Optional list of categories to filter the digest
- `subscribed_at`: UTC timestamp
- `unsubscribed_at`: UTC timestamp (when deactivated)

## Dependencies

- `pymongo`: MongoDB Python driver
- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing for scraping
- `python-dotenv`: Environment variable management
- `openai`: OpenAI API client
- `fastapi`: API framework
- `uvicorn`: ASGI server
- `email-validator`: Email validation for API
- `smtplib`: Email sending functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Troubleshooting

### Common Issues

- MongoDB Connection: Ensure your MongoDB URI is correct and the database is accessible
- OpenAI API: Verify your API key and model are valid
- Email Sending: Check SMTP credentials and enable app passwords if needed
- Dependencies: Run `pip install -r requirements.txt` to ensure all packages are installed
