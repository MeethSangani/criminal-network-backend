# AI-Powered Criminal Network Analysis System Backend

Production-quality, modular backend built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.x**, **Pydantic v2**, **NetworkX**, and **pytest** for law-enforcement & intelligence network analytics.

---

## High-Level Architecture

```
Structured CSV / Unstructured JSON
             │
             ▼
        PostgreSQL
             │
             ▼
          FastAPI
             │
   ┌─────────┴────────────────────────┐
   │                                  │
   ▼                                  ▼
Database Services             Analytics Services
   │                                  │
   │                   ┌──────────────┼──────────────┐
   │                   │              │              │
   │                   ▼              ▼              ▼
   │               Graph          Community       Anomaly
   │               Analysis       Detection       Detection
   │                   │
   └───────────────────┤
                       │
                       ▼
                 Evidence Layer
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        AI Assistant        Simulation
             │
             ▼
       React Frontend
```

---

## Quick Start Guide

### 1. Environment Setup
```powershell
# Navigate to backend folder
cd Backend

# Activate Virtual Environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install Dependencies
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and update your database credentials:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/criminal_network
DEBUG=true
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 3. Running the Server
```powershell
uvicorn app.main:app --reload --port 8000
```
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

### 4. Running Automated Tests
```powershell
pytest
```

---

## Core API Endpoints (Phase 1 Implemented)

- **GET `/api/v1/health`**: System and PostgreSQL database connectivity check.
- **GET `/api/v1/persons`**: Paginated listing of persons.
- **GET `/api/v1/persons/{person_id}`**: Detailed profile of a person entity (e.g. `P017`).
