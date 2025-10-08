from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from typing import List
from .config import settings
from .database import connect_to_mongo, close_mongo_connection
from .models import (
    Contact,
    ContactCreate,
    ContactUpdate,
    FilterParams,
    Token,
    LoginRequest,
    User,
    SuggestionCreate
)
from . import crud
from .auth import authenticate_user, create_access_token, get_current_user

app = FastAPI(
    title="Telbook API",
    description="Telephone directory API with MongoDB backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await close_mongo_connection()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Telbook API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Auth endpoints
@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Authenticate and get access token."""
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user


# Public contact endpoints
@app.get("/api/contacts", response_model=dict)
async def list_contacts(
    search: str = None,
    tag: str = None,
    language: str = None,
    is_ert: bool = None,
    is_ifa: bool = None,
    is_third_party: bool = None,
    exclude_third_party: bool = None,
    sort_by: str = "name",
    page: int = 1,
    limit: int = 20
):
    """List all contacts with filtering and pagination."""
    skip = (page - 1) * limit

    contacts, total = await crud.get_contacts(
        search=search,
        tag=tag,
        language=language,
        is_ert=is_ert,
        is_ifa=is_ifa,
        is_third_party=is_third_party,
        exclude_third_party=exclude_third_party,
        sort_by=sort_by,
        skip=skip,
        limit=limit
    )

    total_pages = (total + limit - 1) // limit

    return {
        "contacts": contacts,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }


@app.get("/api/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str):
    """Get a single contact by ID."""
    contact = await crud.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.get("/api/tags")
async def get_tags():
    """Get all unique tags."""
    tags = await crud.get_all_tags()
    return {"tags": tags}


@app.get("/api/languages")
async def get_languages():
    """Get all unique languages (excluding English)."""
    languages = await crud.get_all_languages()
    return {"languages": languages}


# Public contact creation endpoint
@app.post("/api/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact_public(contact: ContactCreate):
    """Create a new contact (public endpoint)."""
    try:
        return await crud.create_contact(contact)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Public contact update endpoint
@app.put("/api/contacts/{contact_id}", response_model=Contact)
async def update_contact_public(contact_id: str, contact_update: ContactUpdate):
    """Update a contact (public endpoint)."""
    try:
        contact = await crud.update_contact(contact_id, contact_update)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Suggestion endpoints (public - sends emails via EmailJS on frontend)
@app.post("/api/suggestions", status_code=status.HTTP_201_CREATED)
async def create_suggestion(suggestion: SuggestionCreate):
    """
    Receive a suggestion for new contact or edit.
    Note: Email is sent from frontend via EmailJS.
    This endpoint just validates the data.
    """
    return {"message": "Suggestion received", "type": suggestion.type}


# Admin-only endpoints
@app.post("/api/admin/contacts", response_model=Contact, dependencies=[Depends(get_current_user)])
async def create_contact(contact: ContactCreate):
    """Create a new contact (admin only)."""
    try:
        return await crud.create_contact(contact)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/admin/contacts/{contact_id}", response_model=Contact, dependencies=[Depends(get_current_user)])
async def update_contact(contact_id: str, contact_update: ContactUpdate):
    """Update a contact (admin only)."""
    try:
        contact = await crud.update_contact(contact_id, contact_update)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/admin/contacts/{contact_id}", dependencies=[Depends(get_current_user)])
async def delete_contact(contact_id: str):
    """Delete a contact (admin only)."""
    success = await crud.delete_contact(contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}


@app.patch("/api/admin/contacts/{contact_id}/ert", response_model=Contact, dependencies=[Depends(get_current_user)])
async def toggle_ert(contact_id: str, is_ert: bool):
    """Toggle Emergency Response Team status (admin only)."""
    contact = await crud.update_contact(contact_id, ContactUpdate(is_ert=is_ert))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.patch("/api/admin/contacts/{contact_id}/ifa", response_model=Contact, dependencies=[Depends(get_current_user)])
async def toggle_ifa(contact_id: str, is_ifa: bool):
    """Toggle IFA status (admin only)."""
    contact = await crud.update_contact(contact_id, ContactUpdate(is_ifa=is_ifa))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.patch("/api/admin/contacts/{contact_id}/expose", response_model=Contact, dependencies=[Depends(get_current_user)])
async def toggle_expose(contact_id: str, expose: bool):
    """Toggle contact expose status (admin only)."""
    contact = await crud.update_contact(contact_id, ContactUpdate(expose=expose))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.patch("/api/admin/contacts/{contact_id}/third-party", response_model=Contact, dependencies=[Depends(get_current_user)])
async def toggle_third_party(contact_id: str, is_third_party: bool):
    """Toggle third party status (admin only)."""
    contact = await crud.update_contact(contact_id, ContactUpdate(is_third_party=is_third_party))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact
