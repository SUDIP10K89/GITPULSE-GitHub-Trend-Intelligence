import os
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client_ai = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY")
    )

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
collection = db["trending_repos"]


repos = collection.find({"category": {"$exists": False}})

def classify_repo(name, description):
    prompt = f"""
    Classify this GitHub repository into one category:
    AI, Developer Tools, Infrastructure, Web, Mobile, Other.

    Repo Name: {name}
    Description: {description}

    Respond with only the category name.
    """

    response = client_ai.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    category = response.choices[0].message.content.strip()
    return category


for repo in repos:
    category = classify_repo(repo["name"], repo["description"])
    
    collection.update_one(
        {"_id": repo["_id"]},
        {"$set": {"category": category}}
    )

    print(f"{repo['name']} -> {category}")

print("Classification complete")