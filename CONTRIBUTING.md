# Contributing to JobFinder

Thank you for contributing to JobFinder.

This document defines the development workflow and architectural expectations for the project.

---

# 1. Before You Start

Read these documents first:

```text
README.md
docs/Architecture.md
docs/Database.md
docs/API.md
docs/PRD.md
```

---

# 2. Project Structure

The repository is structured as:

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   └── main.py
├── alembic/
├── tests/

mobile-app/
admin-dashboard/
employer-dashboard/

docs/
├── Architecture.md
├── API.md
├── Database.md
├── PRD.md
└── Roadmap.md
```

Do not create new top-level directories without discussing the architectural reason.

---

# 3. Branching

The primary branches are:

```text
main
develop
```

Create feature branches from `develop`.

Examples:

```text
feature/auth
feature/jobs
feature/profile
feature/company
feature/application
```

Bug fixes:

```text
fix/login
fix/job-filter
fix/application-status
```

---

# 4. Development Workflow

Use the following workflow:

```text
Create branch
     ↓
Implement feature
     ↓
Test locally
     ↓
Update documentation
     ↓
Commit changes
     ↓
Open Pull Request
     ↓
Review
     ↓
Merge into develop
```

Do not directly push feature work into `main`.

---

# 5. Commit Messages

Use clear commit messages.

Recommended format:

```text
type: description
```

Examples:

```text
feat: add authentication endpoint
feat: add job search screen
fix: resolve login validation error
refactor: separate job service from repository
docs: update architecture documentation
test: add application API tests
```

Avoid messages such as:

```text
update
changes
test
final
new
```

---

# 6. Backend Rules

The backend uses:

* FastAPI
* SQLAlchemy
* Alembic
* Pydantic
* JWT Authentication
* PostgreSQL

Keep responsibilities separated.

```text
Route
  ↓
Service
  ↓
Repository
  ↓
Database
```

### Routes

Routes should handle HTTP concerns.

### Services

Services should contain business logic.

### Repositories

Repositories should handle database access.

### Models

Models represent database structures.

### Schemas

Schemas define API input and output.

Do not place large amounts of business logic inside route handlers.

---

# 7. Mobile Rules

The mobile application uses:

* React Native
* Expo
* TypeScript
* NativeWind
* React Navigation
* TanStack Query
* Zustand
* React Hook Form
* Zod

Organize code primarily by feature.

```text
features/
├── auth/
├── jobs/
├── profile/
├── applications/
└── ...
```

Use TanStack Query for server/API state.

Use Zustand for appropriate local/global application state.

Use React Hook Form + Zod for forms and validation.

---

# 8. Validation

Validation should happen on both sides.

### Frontend

Used primarily for user experience.

### Backend

Used for security and correctness.

Never assume frontend validation is sufficient.

---

# 9. Database Changes

Database changes must use migrations.

The project uses:

**Alembic**

Do not manually modify production database structures.

Whenever a model change requires a database change:

1. Modify the model.
2. Generate/create a migration.
3. Review the migration.
4. Test it.
5. Commit the migration.

---

# 10. API Versioning

API routes should use:

```text
/api/v1/
```

Examples:

```text
/api/v1/auth/login
/api/v1/users/me
/api/v1/jobs
/api/v1/applications
```

Avoid introducing breaking changes into existing V1 endpoints without discussion.

---

# 11. Security

Never commit:

```text
.env
API keys
Passwords
JWT secrets
Database credentials
Private keys
```

Use environment variables.

Commit only:

```text
.env.example
```

Example:

```text
DATABASE_URL=
JWT_SECRET=
```

Never place real credentials in source code.

---

# 12. Pull Requests

Every significant feature should be submitted through a Pull Request.

A PR should explain:

```text
What changed?
Why was it needed?
How was it tested?
Are there breaking changes?
```

Example:

```markdown
## What changed

Added the job creation API.

## Why

Employers need to publish jobs.

## Testing

- Tested authentication
- Tested employer authorization
- Tested job creation
- Tested validation

## Breaking changes

None
```

---

# 13. Testing

Test new functionality before submitting a PR.

Backend testing should include, where appropriate:

* Unit tests
* API tests
* Authentication tests
* Authorization tests
* Database tests

Mobile testing should include appropriate:

* Component tests
* Screen tests
* User-flow tests

---

# 14. Feature Completion

A feature is not considered complete simply because it works locally.

A feature should have:

* Implementation
* Validation
* Authentication where required
* Authorization where required
* Error handling
* Database migration where required
* Tests where appropriate
* Loading states where appropriate
* Error states where appropriate
* Updated documentation

---

# 15. Adding Dependencies

Do not add a library just because it looks useful.

Before adding a dependency, consider:

* Is it actually necessary?
* Does an existing dependency already solve the problem?
* Is it maintained?
* Does it introduce unnecessary complexity?

Keep the dependency footprint under control.

---

# 16. Architecture Changes

Do not change major architecture decisions casually.

Examples:

* Changing REST to GraphQL
* Introducing microservices
* Adding another database
* Replacing PostgreSQL
* Changing authentication architecture

These changes should be discussed before implementation.

---

# 17. V1 Scope

Keep V1 focused.

The initial database should focus on:

```text
Users
Profiles
Companies
Jobs
Applications
SavedJobs
```

Do not introduce AI, messaging, subscriptions, or other future systems unless the feature has been explicitly approved for the current development phase.

---

# 18. Development Philosophy

The project prioritizes:

```text
Simplicity
    +
Maintainability
    +
Correctness
    +
Scalability
```

Do not optimize for maximum technical complexity.

Build the simplest system that correctly solves the current problem.

---

# 19. Questions and Decisions

When proposing a significant technical change, document:

```text
Problem
Possible solutions
Chosen solution
Reason
Trade-offs
```

This keeps architectural decisions understandable to future contributors.

---

# 20. Final Rule

Build for today's validated requirements while leaving room for tomorrow.

Do not build tomorrow's entire system before today's product works.
