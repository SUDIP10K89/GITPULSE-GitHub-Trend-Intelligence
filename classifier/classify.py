import os
import random
import re
import time
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError, InternalServerError, APIStatusError

load_dotenv()

client_ai = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY")
    )

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
collection = db["trending_repos"]

MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "10"))
BASE_BACKOFF_SECONDS = float(os.getenv("AI_BASE_BACKOFF_SECONDS", "1.5"))
MAX_BACKOFF_SECONDS = float(os.getenv("AI_MAX_BACKOFF_SECONDS", "30"))
MAX_RETRY_WAIT_SECONDS = float(os.getenv("AI_MAX_RETRY_WAIT_SECONDS", "120"))

repos = collection.find({"category": {"$exists": False}})

def classify_repo(name, description):
    prompt = f"""
    Classify this GitHub repository into one category:
    AI, Developer Tools, Infrastructure, Web, Mobile, Other.

    Repo Name: {name}
    Description: {description}

    Respond with only the category name.
    """

    response = create_with_retry(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    category = response.choices[0].message.content.strip()
    return category


def is_rate_limited(err):
    if isinstance(err, RateLimitError):
        return True
    status_code = getattr(err, "status_code", None)
    return status_code == 429


def extract_retry_after_seconds(err):
   
    response = getattr(err, "response", None)
    if response is not None:
        headers = getattr(response, "headers", None)
        if headers:
            retry_after = headers.get("retry-after") or headers.get("Retry-After")
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass

    message = getattr(err, "message", None) or str(err)
    match = re.search(r"retry in ([0-9.]+)s", message, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    match = re.search(r"'retryDelay':\s*'([0-9.]+)s'", message, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def create_with_retry(model, messages):
    attempt = 0
    while True:
        try:
            return client_ai.chat.completions.create(
                model=model,
                messages=messages
            )
        except (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError, APIStatusError) as err:
            attempt += 1
            if attempt > MAX_RETRIES:
                raise

            if not is_rate_limited(err) and isinstance(err, APIStatusError) and getattr(err, "status_code", 500) < 500:
                raise

            retry_after = extract_retry_after_seconds(err)
            if retry_after is not None:
                
                sleep_for = min(MAX_RETRY_WAIT_SECONDS, retry_after)
            else:
                backoff = min(MAX_BACKOFF_SECONDS, BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)))
                jitter = random.uniform(0, backoff * 0.2)
                sleep_for = min(MAX_RETRY_WAIT_SECONDS, backoff + jitter)
            print(f"AI request failed (attempt {attempt}/{MAX_RETRIES}). Retrying in {sleep_for:.1f}s...")
            time.sleep(sleep_for)


for repo in repos:
    category = classify_repo(repo["name"], repo["description"])
    
    collection.update_one(
        {"_id": repo["_id"]},
        {"$set": {"category": category}}
    )

    print(f"{repo['name']} -> {category}")

print("Classification complete")
