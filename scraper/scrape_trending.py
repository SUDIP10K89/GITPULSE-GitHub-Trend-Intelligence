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

URL = "https://github.com/trending"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(URL, headers=headers)

if response.status_code != 200:
    print("Failed to fetch Github Trending")
    exit()

soup = BeautifulSoup(response.text, "html.parser")
repos = soup.find_all("article", class_="Box-row")

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
        "scraped_at": datetime.utcnow()
    }

    collection.insert_one(repo_data)

print(f"Inserted {len(repos)} repos into MongoDB")