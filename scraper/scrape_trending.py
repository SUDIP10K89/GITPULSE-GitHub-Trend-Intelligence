import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
collection = db["trending_repos"]
collection.create_index([("name", 1), ("scraped_date", 1)], unique=True)

URL = "https://github.com/trending"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(URL, headers=headers)

if response.status_code != 200:
    print("Failed to fetch Github Trending")
    exit()

soup = BeautifulSoup(response.text, "html.parser")
repos = soup.find_all("article", class_="Box-row")

inserted = 0
today = datetime.utcnow().date().isoformat()

for repo in repos:
    name_tag = repo.h2.a
    name = name_tag.text.strip().replace("\n", "").replace(" ", "")
    url = "https://github.com" + name_tag['href']

    description_tag = repo.p
    description = description_tag.text.strip() if description_tag else ""

    language_tag = repo.find("span", itemprop="programmingLanguage")
    language = language_tag.text.strip() if language_tag else ""

    stars_tag = repo.find("a", href=lambda h: h and "/stargazers" in h)
    stars = int(stars_tag.text.strip().replace(",", "")) if stars_tag else 0

    forks_tag = repo.find("a", href=lambda h: h and "/forks" in h)
    forks = int(forks_tag.text.strip().replace(",", "")) if forks_tag else 0

    repo_data = {
        "name": name,
        "url": url,
        "description": description,
        "language": language,
        "stars": stars,
        "forks": forks,
        "scraped_date": today,
        "scraped_at": datetime.utcnow()
    }

    result = collection.update_one(
        {"name": name, "scraped_date": today},
        {"$setOnInsert": repo_data},
        upsert=True
    )
    if result.upserted_id is not None:
        inserted += 1
    else:
        print(f"Skipped duplicate for today: {name}")

print(f"Inserted {inserted} repos into MongoDB")
