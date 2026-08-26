# JobFinder

A modern job-finding platform built for the Ethiopian market.

**Status:** V1 — Weeks 1–12 complete (API, mobile, employer dashboard, admin dashboard, production deployment)

- **Backend:** FastAPI modular monolith — see [`backend/README.md`](backend/README.md)
- **Mobile:** React Native + Expo (`mobile-app/`, `ethiopian-jobs-mobile/`)
- **Employer Dashboard:** Next.js (`employer-dashboard/`)
- **Admin Dashboard:** served by the Next.js app at `/admin` (role-gated)
- **Docs:** [`docs/`](docs/)
- **Deployment:** [`DEPLOYMENT.md`](DEPLOYMENT.md) · QA checklist: [`docs/QA-CHECKLIST.md`](docs/QA-CHECKLIST.md)

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
