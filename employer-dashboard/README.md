# Employer Dashboard — Ethiopian Job Platform (Week 11)

Employer web dashboard built with **Next.js 16 (App Router) + TypeScript + Tailwind CSS v4 + shadcn/ui + React Query + React Hook Form/Zod**.

## Features

- **Auth** — employer login & registration (`/login`, `/register`), JWT stored in localStorage + cookie, automatic token refresh on 401, route protection via `src/middleware.ts`.
- **Dashboard overview** (`/dashboard`) — stats cards (total/published/draft jobs, new applicants), recent applicants & recent postings.
- **Jobs CRUD** (`/jobs`) — status-filterable list, publish/close/soft-delete actions, create (`/jobs/new`, saved as draft) and edit (`/jobs/[id]/edit`) forms with Zod validation.
- **Applicants pipeline** (`/applicants`) — filter by status/job, paginated table, applicant detail dialog (cover letter + resume), optimistic status updates through the full hiring pipeline.
- **Company profile** (`/profile`) — view/update company info with completeness score.
- **Settings** (`/settings`) — account details and sign out.

## Getting started

```bash
npm install
cp .env.example .env.local   # adjust API URL if needed
npm run dev                  # http://localhost:3000
```

The backend must be running on `http://localhost:8000` (see `../backend`). CORS already allows `localhost:3000`.

## Environment

| Variable | Default | Description |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | FastAPI base URL |

## Backend endpoints used

| Purpose | Endpoint |
| --- | --- |
| Register / login / refresh / me | `POST /api/v1/auth/register`, `/auth/login`, `/auth/refresh`, `GET /auth/me` |
| Company profile | `GET/PUT /api/v1/profiles/me/companies[/{id}]` |
| List company jobs (per status) | `GET /api/v1/jobs?company_id=&status=` (owners may query drafts/closed/expired) |
| Create / edit / soft-delete job | `POST /api/v1/jobs`, `PUT /jobs/{id}`, `DELETE /jobs/{id}` |
| Publish / close job | `PATCH /jobs/{id}/publish`, `/close` |
| Company applications | `GET /api/v1/applications/company` |
| Update application status | `PATCH /applications/{id}/status` |

Note: the public jobs listing filters by exactly one status at a time, so the
"all statuses" views merge one request per status client-side (see
`src/hooks/useJobs.ts`).

## Scripts

```bash
npm run dev     # dev server
npm run build   # production build
npm start       # serve production build
npm run lint    # eslint
npx tsc --noEmit  # typecheck
```
