import os
from datetime import datetime, timedelta

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
collection = db["trending_repos"]

today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)
today_str = today.isoformat()
yesterday_str = yesterday.isoformat()


yesterday_docs = collection.find(
    {"scraped_date": yesterday_str},
    {"name": 1, "stars_growth": 1}
)
yesterday_growth_by_name = {
    doc.get("name"): doc.get("stars_growth") for doc in yesterday_docs
}

today_repos = collection.find(
    {"scraped_date": today_str},
    {"stars_growth": 1, "name": 1}
)

updated = 0
for repo in today_repos:
    name = repo.get("name")
    growth_today = repo.get("stars_growth")
    growth_yesterday = yesterday_growth_by_name.get(name)

    if growth_today is None or growth_yesterday in (None, 0):
        growth_multiple = None
    else:
        growth_multiple = round(growth_today / growth_yesterday, 2)

    collection.update_one(
        {"_id": repo["_id"]},
        {"$set": {"growth_multiple": growth_multiple}}
    )
    updated += 1

print(f"Growth multiple calculation complete. Updated {updated} repos.")
