# JobFinder

A modern job-finding platform built for the Ethiopian market.

**Status:** V1 — Foundation (complete), Authentication (next)

- **Backend:** FastAPI modular monolith — see [`backend/README.md`](backend/README.md)
- **Mobile:** React Native + Expo (`mobile-app/`)
- **Employer Dashboard:** Next.js (`employer-dashboard/`)
- **Admin Dashboard:** Next.js (`admin-dashboard/`)
- **Docs:** [`docs/`](docs/)

## Quick Start (backend)

```bash
cd backend
cp .env.example .env   # then fill in real values
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
