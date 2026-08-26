# Ethiopian Job Platform — Deployment Guide

Production deployment for the Week 12 release: FastAPI backend, Next.js
employer/admin dashboard, and Expo mobile app.

## Architecture Overview

| Component          | Location                  | Hosting                |
| ------------------ | ------------------------- | ---------------------- |
| Backend API        | `backend/` (FastAPI)      | Docker on a VPS/VM     |
| PostgreSQL 14      | docker-compose service    | Same VM (managed volume)|
| Redis 6            | docker-compose service    | Same VM                |
| Employer/Admin web | `employer-dashboard/`     | Vercel                 |
| Mobile app         | `ethiopian-jobs-mobile/`  | Google Play / App Store|

## Prerequisites

- Docker & Docker Compose v2
- Node.js 18+ (for Vercel CLI / local builds)
- PostgreSQL 14+ (containerized here; managed RDS also works)
- Redis 6+
- A domain with DNS control (e.g. `api.yourdomain.com`, dashboard on Vercel)

## 1. Backend Deployment (Docker)

### 1.1 Prepare environment

```bash
cp .env.production.example .env.production
# Edit .env.production – generate secrets with:
openssl rand -hex 32   # once for SECRET_KEY, once for JWT_SECRET_KEY
```

### 1.2 Build & start

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

This starts:

- **db** – postgres:14 with a named volume (`postgres_data`)
- **redis** – redis:6 with AOF persistence (admin stats cache)
- **api** – FastAPI behind uvicorn; runs `alembic upgrade head` on every boot,
  so database migrations are applied automatically

Verify the rollout:

```bash
curl http://localhost:8000/api/v1/health       # → {"status": "ok"}
docker compose -f docker-compose.prod.yml logs -f api
```

### 1.3 Create the first admin user

```bash
docker compose -f docker-compose.prod.yml exec api python -c "
import asyncio
from app.core.database import async_session
from app.services.auth_service import AuthService

async def main():
    async with async_session() as s:
        user, _ = await AuthService(s).register(
            email='admin@yourdomain.com',
            first_name='Platform', last_name='Admin',
            password='<strong-password>', role='admin',
        )
        print('created admin', user.id)

asyncio.run(main())
"
# Then add the email to SUPER_ADMIN_EMAILS in .env.production and restart api.
```

### 1.4 Reverse proxy & TLS

Terminate TLS in front of the API (Caddy example):

```
api.yourdomain.com {
    reverse_proxy localhost:8000
    header Strict-Transport-Security "max-age=31536000; includeSubDomains"
    header X-Content-Type-Options "nosniff"
    header X-Frame-Options "DENY"
    header Content-Security-Policy "default-src 'none'; frame-ancestors 'none'"
}
```

Nginx + certbot works equally well; always redirect HTTP→HTTPS.

## 2. Web Dashboard Deployment (Vercel)

The Next.js app in `employer-dashboard/` serves both the employer dashboard
and the admin console (`/admin`, gated server-side by `requireAdmin`).

1. Push the repository to GitHub.
2. In Vercel: **Add New Project → Import** the repo.
3. Set **Root Directory** to `employer-dashboard`.
4. Configure environment variables:

   | Variable              | Value                              |
   | --------------------- | ---------------------------------- |
   | `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com/api/v1` |

5. Deploy the production branch. Every push to it auto-deploys.
6. Add the deployed URL to `CORS_ORIGINS` on the backend and restart the API.

> Note: admin access requires a user with role `admin`; the login screen
> routes admins straight to `/admin`.

## 3. Mobile App Deployment

1. Update the API endpoint in the Expo config
   (`ethiopian-jobs-mobile/`) to point at `https://api.yourdomain.com/api/v1`.
2. Build native binaries with [EAS](https://docs.expo.dev/build/introduction/):

   ```bash
   eas build --platform android
   eas build --platform ios
   ```

3. Submit to stores:

   ```bash
   eas submit --platform android
   eas submit --platform ios
   ```

## 4. Monitoring Setup

- **Error tracking** – create a Sentry project, paste its DSN into
  `SENTRY_DSN` in `.env.production`, and restart the API. Unhandled
  exceptions are already logged server-side with stack traces suppressed
  from responses.
- **Centralized logging** – the API container uses json-file rotation
  (10 MB × 3). Ship with:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f api | your-log-collector
  ```
- **Uptime monitoring** – point an external checker (UptimeRobot,
  Better Stack, etc.) at `https://api.yourdomain.com/api/v1/health`
  every 60s; alert when non-200 or slower than 2s.

## 5. Backups

Nightly logical backup of Postgres (add to cron on the host):

```bash
0 2 * * * docker compose -f /srv/jobplatform/docker-compose.prod.yml \
  --env-file /srv/jobplatform/.env.production exec -T db \
  pg_dump -U jobplatform jobplatform | gzip > /backups/db-$(date +\%F).sql.gz
```

Retain ≥ 14 days and test restores quarterly:

```bash
gunzip -c db-2026-01-01.sql.gz | \
  docker compose ... exec -T db psql -U jobplatform jobplatform
```

Redis holds only cache data – no backup required.

## 6. Security Notes

- All traffic over HTTPS; HSTS enabled at the proxy.
- Rate limiting is automatically enforced in production on `/auth/*` and
  every `/admin/*` endpoint (100 req / 60 s / IP by default; tune via
  `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_PERIOD`).
- Admin endpoints are double-gated: JWT role check (`require_admin`) plus
  super-admin allow-list for privileged operations.
- Every admin mutation writes an audit log row atomically with the change.
- Secrets live only in `.env.production` (never committed) and Vercel env vars.
- Static assets are served through Vercel's CDN.

## 7. Launch Checklist

### Pre-launch

- [x] All environment variables configured (`.env.production`, Vercel)
- [x] Database migrations applied (automatic via `alembic upgrade head`)
- [ ] SSL certificates installed and HTTP→HTTPS redirect verified
- [x] Security headers configured (CSP, HSTS) at reverse proxy
- [x] Rate limiting implemented on auth + admin endpoints
- [x] Backup strategy documented (§5) and first restore tested
- [x] Monitoring & alerting set up (uptime check + Sentry)
- [x] Error tracking integrated (Sentry DSN)
- [ ] Load testing performed (see QA-CHECKLIST.md)
- [x] Documentation complete (this guide + docs/QA-CHECKLIST.md)

### Post-launch monitoring

- [ ] Check `docker compose logs api` daily for errors during week one
- [ ] Monitor server resources (`docker stats`, CPU/memory alerts)
- [ ] Track key metrics from the Admin Dashboard (registrations, applications)
- [ ] Alert on 5xx rate > 1% and health-check failures
- [ ] Collect user feedback (in-app channel + store reviews)
