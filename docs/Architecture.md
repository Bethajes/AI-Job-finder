# JobFinder Architecture

## 1. Overview

JobFinder uses a **modular monolith architecture** for V1.

The system consists of:

* React Native + Expo mobile application
* Next.js employer dashboard
* Next.js admin dashboard
* FastAPI backend
* PostgreSQL database
* Cloudinary storage
* Firebase notifications
* Future AI services

The architecture is intentionally simple enough for rapid V1 development while leaving room for future expansion.

---

# 2. High-Level Architecture

```text
                         Users
                           │
             ┌─────────────┴─────────────┐
             │                           │
       Mobile Application          Web Applications
       React Native + Expo         Next.js
             │                    /           \
             │              Employer          Admin
             │              Dashboard       Dashboard
             │                    \           /
             └────────────────────┬──────────┘
                                  │
                            HTTPS / REST
                                  │
                         ┌────────▼────────┐
                         │                 │
                         │  FastAPI API    │
                         │                 │
                         │ Modular Monolith│
                         │                 │
                         └────────┬────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
             PostgreSQL      Cloudinary        Firebase
              Database         Storage       Notifications
                                  │
                                  ▼
                             Future AI
```

---

# 3. Why a Modular Monolith?

V1 uses a modular monolith instead of microservices.

Reasons:

* Faster development
* Easier local development
* Easier debugging
* Simpler deployment
* Lower infrastructure complexity
* Easier database transactions
* Clear path toward future service extraction

The system should still maintain strong internal boundaries between modules.

---

# 4. Client Applications

## 4.1 Mobile

Location:

```text
mobile-app/
```

Technology:

```text
React Native
Expo
TypeScript
NativeWind
React Navigation
TanStack Query
Zustand
React Hook Form
Zod
```

The mobile application is organized by feature.

```text
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

---

## 4.2 Employer Dashboard

Location:

```text
employer-dashboard/
```

Technology:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

The employer dashboard communicates with the same FastAPI backend as the mobile application.

---

## 4.3 Admin Dashboard

Location:

```text
admin-dashboard/
```

Technology:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

The admin application provides administrative functionality while authorization is enforced by the backend.

---

# 5. Backend

Location:

```text
backend/
```

Technology:

```text
FastAPI
SQLAlchemy
Alembic
Pydantic
JWT Authentication
```

Backend structure:

```text
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

---

# 6. Request Flow

A typical API request follows:

```text
Client
  ↓
HTTP Request
  ↓
FastAPI Route
  ↓
Authentication / Authorization
  ↓
Service
  ↓
Repository
  ↓
PostgreSQL
  ↓
Repository
  ↓
Service
  ↓
Response Schema
  ↓
HTTP Response
  ↓
Client
```

Routes should remain thin.

Business logic belongs primarily in services.

Database access belongs primarily in repositories.

---

# 7. Core Backend Layers

## API Routes

Responsible for:

* HTTP methods
* Request handling
* Response handling
* Dependency injection

---

## Dependencies

Responsible for reusable request dependencies such as authentication and shared request context.

---

## Middleware

Responsible for cross-cutting HTTP behavior.

---

## Core

Contains infrastructure-level functionality:

```text
config.py
security.py
database.py
```

---

## Models

Represent database entities.

Initial entities:

```text
User
Profile
Company
Job
Application
SavedJob
```

---

## Schemas

Define API request and response structures using Pydantic.

---

## Services

Contain business logic.

Potential services include:

```text
auth_service
user_service
job_service
company_service
application_service
```

---

## Repositories

Contain database access logic.

Potential repositories include:

```text
user_repository
job_repository
company_repository
application_repository
```

---

# 8. Database

Primary database:

**PostgreSQL**

Initial conceptual model:

```text
User
 │
 ├──────────── Profile
 │
 ├──────────── Application
 │
 └──────────── SavedJob
                    │
                    ▼
                   Job
                    │
                    ▼
                 Company
```

Relationships:

```text
User 1 ─── 1 Profile

User 1 ─── N Application

User 1 ─── N SavedJob

Company 1 ─── N Job

Job 1 ─── N Application

Job 1 ─── N SavedJob
```

The detailed schema belongs in:

```text
docs/database/DATABASE.md
```

---

# 9. Authentication

V1 authentication is planned around:

* Email/password
* JWT authentication
* Secure password hashing
* Email verification
* Password reset

Google Sign-In is a future option rather than a V1 requirement.

---

# 10. Authorization

The system has three primary roles:

```text
JOB_SEEKER
EMPLOYER
ADMIN
```

Authorization must be enforced by the backend.

Frontend restrictions are not sufficient security.

---

# 11. API Style

The project uses REST.

API version:

```text
/api/v1/
```

Example endpoint structure:

```text
/api/v1/auth/...
/api/v1/users/...
/api/v1/companies/...
/api/v1/jobs/...
/api/v1/applications/...
```

The detailed API contract belongs in:

```text
docs/api/API.md
```

---

# 12. File Storage

Uploaded files should be stored externally rather than directly on the API server.

Planned storage:

```text
Cloudinary
```

Potential future alternatives:

```text
Cloudflare R2
Amazon S3
```

Examples of stored files:

* Profile images
* Company logos
* Other application assets

---

# 13. Notifications

The planned notification infrastructure is:

```text
Firebase Cloud Messaging
```

Notification functionality can be introduced as the product requirements evolve.

---

# 14. Future AI

AI is intentionally outside the core V1 architecture.

Future AI functionality may include:

* Job matching
* Resume processing
* Career assistance

The architecture reserves a path for future AI services without requiring AI infrastructure in the initial system.

---

# 15. Deployment

Planned deployment:

```text
Mobile
   ↓
Expo EAS

Web
   ↓
Vercel

API
   ↓
Railway or Render

Database
   ↓
PostgreSQL
```

Docker and GitHub Actions are part of the planned DevOps foundation.

---

# 16. Repository Structure

The repository is structured as:

```text
ethiopian-job-platform/

├── backend/
├── mobile-app/
├── employer-dashboard/
├── admin-dashboard/
├── docs/
├── CONTRIBUTING.md
└── .gitignore
```

> Note: The documentation originally described an `apps/` monorepo layout with
> shared `packages/`. The actual repository uses top-level directories and has
> no shared package workspace yet. Introduce one only when sharing code between
> applications actually requires it.

---

# 17. Architecture Evolution

The intended evolution is:

```text
V1

Clients
   ↓
FastAPI Modular Monolith
   ↓
PostgreSQL
```

Later:

```text
Clients
   ↓
FastAPI
   ↓
PostgreSQL
   ↓
Additional services
```

Only introduce microservices or additional infrastructure when actual product requirements justify them.

---

# 18. Architecture Principles

The architecture follows these principles:

### Simple

Avoid unnecessary infrastructure.

### Modular

Keep functionality separated by responsibility.

### Maintainable

Make code understandable to future contributors.

### Scalable

Avoid decisions that make future growth unnecessarily difficult.

### Incremental

Introduce complexity only when the product requires it.

---

# 19. Current Architectural Decision

The current V1 decisions are:

| Area              | Decision            |
| ----------------- | ------------------- |
| Mobile            | React Native + Expo |
| Web               | Next.js             |
| Backend           | FastAPI             |
| API               | REST                |
| Architecture      | Modular Monolith    |
| Database          | PostgreSQL          |
| ORM               | SQLAlchemy          |
| Migrations        | Alembic             |
| Validation        | Pydantic            |
| Authentication    | JWT                 |
| Storage           | Cloudinary          |
| Notifications     | Firebase            |
| Containerization  | Docker              |
| CI/CD             | GitHub Actions      |
| Web Deployment    | Vercel              |
| Mobile Deployment | Expo EAS            |
| API Deployment    | Railway or Render   |

These decisions should be treated as the current foundation and revisited only when a concrete requirement justifies a change.
