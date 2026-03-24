# GitPulse

A GitHub trending repository monitoring and analysis system that scrapes trending repositories, classifies them by category, calculates growth metrics, and sends daily email digests.

## Features

- **Trending Repository Scraping**: Automatically scrapes GitHub trending repositories daily
- **AI-Powered Classification**: Classifies repositories into categories (AI, Developer Tools, Infrastructure, Web, Mobile, Other) using OpenAI
- **Growth Analytics**: Calculates daily star growth by comparing with previous day's data
- **Email Digest**: Sends daily email summaries with top accelerating repositories
- **MongoDB Integration**: Stores all data for historical analysis and trend tracking

## Architecture

```
RepoRadar/
├── scraper/           # GitHub trending scraper
├── classifier/        # AI-powered repository classification
├── analytics/         # Growth calculation and analytics
├── email/             # Email generation and sending
├── .env               # Environment variables
├── .gitignore         # Git ignore rules
├── README.md          # This file
└── run_pipeline.py    # Main pipeline orchestrator
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd RepoRadar
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

Create a `.env` file with the following variables:

```env
MONGO_URI=mongodb+srv://your-connection-string
DB_NAME=repodradar

OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=arcee-ai/trinity-mini:free
OPENAI_API_KEY=your-api-key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

## Usage

Run the complete pipeline:
```bash
python run_pipeline.py
```

This will:
1. Scrape trending repositories from GitHub
2. Classify each repository by category
3. Calculate daily growth metrics
4. Send an email digest with top accelerating repositories

## Pipeline Components

### 1. Scraper (`scraper/scrape_trending.py`)
- Scrapes GitHub trending repositories
- Extracts name, URL, description, language, stars, and forks
- Stores data in MongoDB with timestamp

### 2. Classifier (`classifier/classify.py`)
- Uses OpenAI to classify repositories into categories
- Categories: AI, Developer Tools, Infrastructure, Web, Mobile, Other
- Updates MongoDB with classification results

### 3. Analytics (`analytics/growth.py`)
- Calculates daily star growth by comparing with previous day
- Updates MongoDB with `stars_growth` field
- Identifies accelerating repositories

### 4. Email (`email/send_email.py`)
- Generates daily email digest
- Includes top 10 accelerating repositories with detailed information
- Sends email via SMTP

## Data Model

Each repository document in MongoDB contains:
- `name`: Repository name
- `url`: GitHub URL
- `description`: Repository description
- `language`: Primary programming language
- `stars`: Current star count
- `forks`: Current fork count
- `category`: AI-classified category
- `stars_growth`: Daily star growth
- `scraped_at`: Timestamp of data collection

## Dependencies

- `pymongo`: MongoDB Python driver
- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing for scraping
- `python-dotenv`: Environment variable management
- `openai`: OpenAI API client
- `smtplib`: Email sending functionality


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Troubleshooting

### Common Issues

- **MongoDB Connection**: Ensure your MongoDB URI is correct and the database is accessible
- **OpenAI API**: Verify your API key and model are valid
- **Email Sending**: Check SMTP credentials and enable less secure apps if needed
- **Dependencies**: Run `pip install -r requirements.txt` to ensure all packages are installed

