from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient
import os

load_dotenv()

app = FastAPI(title="RepoRadar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "RepoRadar API is running"

mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("DB_NAME")]
subscribers_collection = db["subscribers"]
subscribers_collection.create_index("email", unique=True)

class SubscribeRequest(BaseModel):
    email: EmailStr

class UnsubscribeRequest(BaseModel):
    email: EmailStr

@app.post("/api/subscribe")
async def subscribe(request: SubscribeRequest):
    email = request.email.lower().strip()
    
    existing = subscribers_collection.find_one({"email": email, "active": True})
    if existing:
        return {
            "success": True,
            "message": "Already subscribed",
            "already_subscribed": True
        }
    
    subscribers_collection.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "active": True,
                "subscribed_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return {
        "success": True,
        "message": "Successfully subscribed",
        "already_subscribed": False
    }

@app.post("/api/unsubscribe")
async def unsubscribe(request: UnsubscribeRequest):
    email = request.email.lower().strip()
    
    result = subscribers_collection.update_one(
        {"email": email, "active": True},
        {"$set": {"active": False, "unsubscribed_at": datetime.utcnow()}}
    )
    
    was_subscribed = result.modified_count > 0
    
    return {
        "success": True,
        "message": "Successfully unsubscribed" if was_subscribed else "Email was not subscribed",
        "was_subscribed": was_subscribed
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
