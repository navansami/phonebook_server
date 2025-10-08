from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    extension: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    designation: Optional[str] = Field(None, max_length=200)
    mobile: Optional[str] = Field(None, max_length=50)
    landline: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=500)
    languages: List[str] = Field(default_factory=list)
    comments: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    expose: bool = Field(default=True)  # Whether contact is publicly visible
    is_ert: bool = Field(default=False)  # Emergency Response Team member
    is_third_party: bool = Field(default=False)  # Third party company contact
    is_ifa: bool = Field(default=False)  # IFA (Intercontinental Festival Arena) contact
    profile_picture: Optional[str] = None  # Base64 encoded image or URL


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    extension: Optional[str] = Field(None, max_length=20)
    is_ifa: Optional[bool] = None
    company: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    designation: Optional[str] = Field(None, max_length=200)
    mobile: Optional[str] = Field(None, max_length=50)
    landline: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=500)
    languages: Optional[List[str]] = None
    comments: Optional[str] = None
    tags: Optional[List[str]] = None
    expose: Optional[bool] = None
    is_ert: Optional[bool] = None
    is_third_party: Optional[bool] = None
    profile_picture: Optional[str] = None


class ContactInDB(ContactBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "0001",
                "name": "John Doe",
                "extension": "3301",
                "company": "Fairmont The Palm",
                "department": "Executive Office",
                "designation": "General Manager",
                "mobile": "0501234567",
                "landline": "044573388",
                "email": "john.doe@fairmont.com",
                "languages": ["English", "French"],
                "tags": ["Executive Office", "Higher Management"],
                "is_ert": True,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }


class Contact(ContactBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SuggestionCreate(BaseModel):
    type: str = Field(..., pattern="^(new|edit)$")  # "new" or "edit"
    contact_id: Optional[str] = None  # For edit suggestions
    name: str
    extension: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    mobile: Optional[str] = None
    landline: Optional[str] = None
    email: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = None
    languages: Optional[str] = None  # Comma-separated for EmailJS compatibility
    comments: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated for EmailJS compatibility


class FilterParams(BaseModel):
    search: Optional[str] = None
    tag: Optional[str] = None
    language: Optional[str] = None
    is_ert: Optional[bool] = None
    is_third_party: Optional[bool] = None
    exclude_third_party: Optional[bool] = None
    sort_by: Optional[str] = Field(default="name", pattern="^(name|department|extension)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
