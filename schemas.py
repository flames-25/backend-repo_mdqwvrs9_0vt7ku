"""
Database Schemas for GIGS Marketplace

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase class name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection: "user"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field(..., pattern="^(creator|client)$", description="Role in marketplace: 'creator' or 'client'")
    bio: Optional[str] = Field(None, description="Short bio")
    skills: Optional[List[str]] = Field(default_factory=list, description="List of skills for creators")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    is_active: bool = Field(True, description="Whether user is active")

class Gig(BaseModel):
    """
    Gigs offered by creators
    Collection: "gig"
    """
    title: str = Field(..., description="Gig title")
    description: str = Field(..., description="Gig description")
    category: str = Field(..., description="Category")
    price: float = Field(..., ge=0, description="Base price in USD")
    creator_id: str = Field(..., description="Creator user _id as string")
    creator_name: Optional[str] = Field(None, description="Denormalized creator name for fast listing")

class Proposal(BaseModel):
    """
    Proposals sent by clients to gigs
    Collection: "proposal"
    """
    gig_id: str = Field(..., description="Target gig _id as string")
    client_id: str = Field(..., description="Client user _id as string")
    message: str = Field(..., description="Message to the creator")
    offered_price: Optional[float] = Field(None, ge=0, description="Client offered price")
    status: str = Field("pending", pattern="^(pending|accepted|rejected)$", description="Proposal status")
