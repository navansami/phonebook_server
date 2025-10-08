# Telbook API - Backend

FastAPI backend for the Telbook telephone directory application.

## Features

- 🚀 Fast async API with FastAPI
- 🔐 JWT authentication for admin routes
- 📊 MongoDB database with Motor (async driver)
- 🔍 Advanced filtering, search, and pagination
- 🏥 Emergency Response Team (ERT) management
- 📱 RESTful API design

## Setup

### 1. Install Python Dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

**Important:** Change the `ADMIN_PASSWORD` and `SECRET_KEY` in production!

### 3. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Public Endpoints

- `GET /api/contacts` - List all contacts (with filters)
- `GET /api/contacts/{id}` - Get single contact
- `GET /api/tags` - Get all unique tags
- `GET /api/languages` - Get all unique languages
- `POST /api/suggestions` - Submit contact suggestion

### Auth Endpoints

- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user

### Admin Endpoints (Requires Authentication)

- `POST /api/admin/contacts` - Create contact
- `PUT /api/admin/contacts/{id}` - Update contact
- `DELETE /api/admin/contacts/{id}` - Delete contact
- `PATCH /api/admin/contacts/{id}/ert` - Toggle ERT status

## Query Parameters

### List Contacts

- `search` - Search across name, department, tags, designation
- `tag` - Filter by tag
- `language` - Filter by language
- `is_ert` - Filter Emergency Response Team members
- `sort_by` - Sort by: `name`, `department`, `extension`
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20, max: 100)

## Authentication

Admin endpoints require a Bearer token:

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token
curl -X POST http://localhost:8000/api/admin/contacts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", ...}'
```

## Database Schema

```json
{
  "_id": "0001",
  "name": "John Doe",
  "extension": "3301",
  "company": "Fairmont The Palm",
  "department": "Executive Office",
  "designation": "General Manager",
  "mobile": "0501234567",
  "landline": "044573388",
  "email": "john.doe@example.com",
  "website": "https://linkedin.com/in/johndoe",
  "languages": ["English", "French"],
  "comments": "Additional notes",
  "tags": ["Executive Office", "Management"],
  "expose": "all",
  "is_ert": true,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

## Production Deployment

1. Set `ENVIRONMENT=production` in `.env`
2. Generate secure `SECRET_KEY`: `openssl rand -hex 32`
3. Use strong `ADMIN_PASSWORD`
4. Update `CORS_ORIGINS` to your frontend URL
5. Use a production WSGI server (uvicorn with multiple workers)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
