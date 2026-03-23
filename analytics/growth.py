import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
collection = db["trending_repos"]

today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)

# get todays repo
today_repos = collection.find({
    "scraped_at": {
        "$gte": datetime(today.year, today.month, today.day),
        "$lt": datetime(today.year, today.month, today.day) + timedelta(days=1)
    }
})

for repo in today_repos:
    name = repo["name"]
    stars_today = repo["stars"]

    # find yesterday record for same repo
    yesterday_repo = collection.find_one({
        "name": name,
        "scraped_at": {
            "$gte": datetime(yesterday.year, yesterday.month, yesterday.day),
            "$lt": datetime(yesterday.year, yesterday.month, yesterday.day) + timedelta(days=1)
        }
    })

    if yesterday_repo:
        stars_yesterday = yesterday_repo["stars"]
        growth = stars_today - stars_yesterday
    else:
        growth = 0

    # Update today document
    collection.update_one(
        {"_id": repo["_id"]},
        {"$set": {"stars_growth": growth}}
    )

    print(f"{name} growth: {growth}")

print("Growth calculation complete")