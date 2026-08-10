# JobFinder API

Base URL:

```text
/api/v1
```

All endpoints are prefixed with `/api/v1`.

Interactive documentation is available at:

```text
/docs
```

OpenAPI schema:

```text
/api/v1/openapi.json
```

---

## Health

### GET /api/v1/health

Basic liveness check.

Response:

```json
{
  "status": "ok"
}
```

---

## Planned Endpoints (not yet implemented)

The following endpoint groups are planned for V1. They are listed here so the
API surface is documented in advance, but they are **not implemented yet**.

```text
/api/v1/auth/...
/api/v1/users/...
/api/v1/companies/...
/api/v1/jobs/...
/api/v1/applications/...
```

The first group to be implemented is **authentication**:

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
POST   /api/v1/auth/logout
```
