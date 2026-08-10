# JobFinder

> A modern job-finding platform built for the Ethiopian market.

**Status:** V1 — Foundation

JobFinder is being developed as a platform that connects job seekers with employers through a mobile application and web-based dashboards.

The V1 architecture is intentionally simple and scalable: a React Native mobile application and Next.js web applications communicate with a FastAPI modular monolith through a REST API, with PostgreSQL as the primary database.

---

## Project Goal

The first version focuses on establishing a strong technical foundation and delivering the core recruitment workflow.

The core development flow is:

```text
Foundation
    ↓
Authentication
    ↓
Database
    ↓
Employer APIs
    ↓
Job APIs
    ↓
Application APIs
    ↓
Mobile UI
    ↓
Testing
    ↓
Deployment
```

The objective is to avoid unnecessary complexity while creating an architecture that can evolve as the product grows.

---

## Architecture

```text
                    Users
                       │
        ┌──────────────┴──────────────┐
        │                             │
   Mobile App                  Employer Dashboard
 React Native + Expo              Next.js
        │                             │
        └──────────────┬──────────────┘
                       │
                 REST API (HTTPS)
                       │
                FastAPI Backend
                       │
        ┌──────────────┼──────────────┐
        │              │              │
 PostgreSQL      Cloudinary      Firebase
 Database          Storage      Notifications
                       │
                   Future AI
```

The backend follows a **modular monolith** architecture rather than microservices.

---

## Applications

### Mobile

`mobile-app/`

Technology:

* React Native
* Expo
* TypeScript
* NativeWind
* React Navigation
* TanStack Query
* Zustand
* React Hook Form
* Zod

---

### Employer Dashboard

`employer-dashboard/`

Technology:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

---

### Admin Dashboard

`admin-dashboard/`

Technology:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

---

### API

`backend/`

Technology:

* FastAPI
* SQLAlchemy
* Alembic
* Pydantic
* JWT Authentication

---

## Database

The primary database is:

**PostgreSQL**

The initial schema is intentionally focused on:

```text
Users
Profiles
Companies
Jobs
Applications
SavedJobs
```

AI, messaging, and subscription-related tables are intentionally excluded from the initial schema.

---

## Storage

The application uses external storage for uploaded files.

Primary planned storage:

* Cloudinary

Potential future storage options:

* Cloudflare R2
* Amazon S3

---

## Notifications

The planned notification technology is:

* Firebase Cloud Messaging

---

## Development & Deployment

Development and DevOps technologies:

* Git
* GitHub
* Docker
* GitHub Actions

Planned deployment:

* Web: Vercel
* Mobile: Expo EAS
* API: Railway or Render

---

## Repository Structure

```text
ethiopian-job-platform/
│
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   └── ...
│
├── mobile-app/
├── employer-dashboard/
├── admin-dashboard/
│
├── docs/
│   ├── Architecture.md
│   ├── API.md
│   ├── Database.md
│   ├── PRD.md
│   └── Roadmap.md
│
├── README.md
├── CONTRIBUTING.md
└── .gitignore
```

> Note: The documentation originally described an `apps/` monorepo layout.
> The actual repository uses top-level `backend/`, `mobile-app/`,
> `employer-dashboard/`, and `admin-dashboard/` directories. Shared packages
> (`packages/`) do not exist yet and are a future option.

---

## Backend Structure

```text
backend/

app/

├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   ├── dependencies.py
│   │   └── router.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── database.py
│   └── exceptions.py
│
├── models/
├── schemas/
├── services/
├── repositories/
├── tests/
└── main.py
```

### Responsibilities

| Layer        | Responsibility                    |
| ------------ | --------------------------------- |
| Routes       | HTTP/API endpoints                |
| Dependencies | Shared request dependencies       |
| Middleware   | Cross-cutting HTTP behavior       |
| Core         | Configuration, security, database |
| Models       | Database models                   |
| Schemas      | API request/response schemas      |
| Services     | Business logic                    |
| Repositories | Database access                   |
| Tests        | Automated tests                   |

---

## Mobile Structure

```text
mobile-app/

src/

├── assets/
├── components/
│   ├── auth/
│   ├── common/
│   ├── jobs/
│   └── profile/
├── navigation/
├── screens/
│   ├── auth/
│   ├── jobs/
│   ├── profile/
│   └── applications/
├── api/
├── hooks/
├── store/
├── utils/
├── constants/
├── types/
└── App.tsx
```

The mobile application is organized primarily by feature so that functionality can evolve independently.

> Note: The mobile app is currently scaffolding only — no application code has
> been implemented yet.

---

## Git Workflow

The main branches are:

```text
main
develop
```

Feature branches use:

```text
feature/auth
feature/jobs
feature/profile
feature/company
feature/application
```

A feature should be developed in its own branch and merged into `develop`.

---

## Documentation

Project documentation lives inside `docs/`.

```text
docs/
├── Architecture.md
├── API.md
├── Database.md
├── PRD.md
└── Roadmap.md
```

See:

* [Architecture](docs/Architecture.md)
* [Database](docs/Database.md)
* [API](docs/API.md)
* [Roadmap](docs/Roadmap.md)

---

## Current Status

The project is currently in:

**Foundation**

The foundation audit is complete. The backend application starts, the health
endpoint works, database connectivity and Alembic are verified, and the
authentication/security utilities are in place.

Current priorities:

1. ~~Finalize architecture~~
2. ~~Create repository~~
3. ~~Scaffold applications~~
4. ~~Configure backend~~
5. ~~Configure database~~
6. Implement authentication (email/password + JWT)
7. Establish development workflow

---

## Architecture Decisions

Three important decisions have been established for V1:

### Authentication

Email/password first.

Google Sign-In can be added later.

### API

REST API.

### Backend

Modular monolith.

These choices prioritize a fast path to a stable V1 while maintaining a clear path for future expansion.

---

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before making changes.

---

## License

License information will be added when the project's licensing decision is finalized.
