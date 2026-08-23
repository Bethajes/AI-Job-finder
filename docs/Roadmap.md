# JobFinder Roadmap

## V1 — Phases

```text
Foundation (complete)
    ↓
Authentication (next)
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

## Phase Status

### Foundation — complete

- Repository scaffolded
- Backend application starts (FastAPI)
- `/api/v1/health` works
- PostgreSQL connectivity verified
- Alembic configured
- Authentication/security utilities implemented (password hashing, JWT)
- Docker configuration in place
- Test suite passing

### Authentication — planned (next)

- Email/password registration
- Password hashing
- Login
- JWT access token
- Refresh token
- Current-user endpoint
- Role-based authorization (JOB_SEEKER, EMPLOYER, ADMIN)

## Out of V1 scope

- Google Sign-In
- AI-powered matching
- Messaging
- Subscriptions/payments
