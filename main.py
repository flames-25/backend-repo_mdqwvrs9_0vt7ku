import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Gig, Proposal

app = FastAPI(title="GIGS Marketplace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility: convert Mongo documents to JSONable dicts

def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    # Convert datetime to isoformat if present
    for k, v in list(doc.items()):
        if hasattr(v, "isoformat"):
            doc[k] = v.isoformat()
    return doc


@app.get("/")
def read_root():
    return {"message": "GIGS Marketplace API is running"}


@app.get("/test")
def test_database():
    """Check DB connection and list collections"""
    resp = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "collections": []
    }
    try:
        if db is not None:
            resp["database"] = "✅ Connected"
            try:
                resp["collections"] = db.list_collection_names()
                resp["database"] = "✅ Connected & Working"
            except Exception as e:
                resp["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            resp["database"] = "❌ db is None"
    except Exception as e:
        resp["database"] = f"❌ Error: {str(e)[:80]}"
    return resp


# 1) Users

@app.post("/api/users", response_model=dict)
async def create_user(user: User):
    # Simple role validation handled by schema regex
    user_id = create_document("user", user)
    return {"id": user_id}


@app.get("/api/users", response_model=List[dict])
async def list_users(role: Optional[str] = None):
    filt = {"role": role} if role else {}
    docs = get_documents("user", filt, limit=100)
    return [serialize_doc(d) for d in docs]


# 2) Gigs

@app.post("/api/gigs", response_model=dict)
async def create_gig(gig: Gig):
    # Ensure creator exists
    creator = db["user"].find_one({"_id": ObjectId(gig.creator_id)}) if ObjectId.is_valid(gig.creator_id) else None
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    gig.creator_name = creator.get("name")
    gig_id = create_document("gig", gig)
    return {"id": gig_id}


@app.get("/api/gigs", response_model=List[dict])
async def list_gigs(category: Optional[str] = None, q: Optional[str] = None):
    filt = {}
    if category:
        filt["category"] = category
    if q:
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"creator_name": {"$regex": q, "$options": "i"}},
        ]
    docs = get_documents("gig", filt, limit=100)
    return [serialize_doc(d) for d in docs]


# 3) Proposals

@app.post("/api/proposals", response_model=dict)
async def create_proposal(p: Proposal):
    # Validate gig and client
    gig = db["gig"].find_one({"_id": ObjectId(p.gig_id)}) if ObjectId.is_valid(p.gig_id) else None
    if not gig:
        raise HTTPException(status_code=404, detail="Gig not found")
    client = db["user"].find_one({"_id": ObjectId(p.client_id)}) if ObjectId.is_valid(p.client_id) else None
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    prop_id = create_document("proposal", p)
    return {"id": prop_id}


@app.get("/api/proposals", response_model=List[dict])
async def list_proposals(gig_id: Optional[str] = None, client_id: Optional[str] = None):
    filt = {}
    if gig_id and ObjectId.is_valid(gig_id):
        filt["gig_id"] = gig_id
    if client_id and ObjectId.is_valid(client_id):
        filt["client_id"] = client_id
    docs = get_documents("proposal", filt, limit=100)
    return [serialize_doc(d) for d in docs]


# Health endpoint for frontend to ping
@app.get("/api/health")
async def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
