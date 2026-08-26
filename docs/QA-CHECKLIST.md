# Ethiopian Job Platform — Week 12 QA & Final Testing Checklist

End-to-end verification across web (employer/admin), mobile, and API.
Run against a staging deployment before go-live; record the date and
result of each item.

## 1. Authentication

- [ ] Register employer via web dashboard (`/register`)
- [ ] Login as job seeker on mobile
- [ ] Login as admin on web → redirected to `/admin`
- [ ] Job seeker login attempt on web is rejected with clear message
- [ ] Invalid credentials show validation error (no stack traces)
- [ ] Access token refresh works after expiry (no forced logout)
- [ ] Logout clears tokens and redirects to `/login`

## 2. Employer flows (web)

- [ ] Create company profile (`/profile`)
- [ ] Post a new job (`/jobs/new`) with requirements, salary, deadline
- [ ] Edit and publish a draft job
- [ ] Close a published job
- [ ] View applicants for a job (`/applicants`), change status
  (viewed → shortlisted → interviewed → offered → hired / rejected)
- [ ] Resume file uploads render/download correctly

## 3. Job seeker flows (mobile)

- [ ] Browse/search jobs with keyword + filters (location, type, category)
- [ ] Pagination / infinite scroll returns more results
- [ ] Save a job, view saved list
- [ ] Apply with resume upload + cover letter
- [ ] Application status reflects employer updates
- [ ] Push notification received when application status changes
      (if FCM configured)

## 4. Admin console (web `/admin`)

- [ ] Non-admin users are redirected away from `/admin`
      (server-side `requireAdmin`)
- [ ] **Overview**: stats cards show plausible totals; user-growth and
      job-trend charts render; stats auto-refresh every 60 s
- [ ] **Users**: search by email/name, filters by role/status/verification,
      sorting works; view details dialog shows role-specific data;
      block/unblock toggles immediately; change role updates row;
      manual email verify marks verified; soft delete deactivates
- [ ] **Companies**: pending companies listed; approve with optional note;
      reject requires reason; owner receives outcome email;
      suspend deactivates company
- [ ] **Jobs moderation**: filter by status/flagged/hidden/search;
      approve publishes; reject with required reason closes job;
      flag/unflag/hide/unhide reflect instantly; detail dialog shows
      application stats and prior admin notes
- [ ] **Reports**: activity metrics (DAU/WAU/MAU, applications) populate;
      top jobs table and industry chart render; range switcher works
- [ ] **Audit logs**: every admin action from this session appears with
      admin email, action badge, resource ID, IP, timestamp; detail dialog
      shows before→after diff; action/resource/date filters work

## 5. Error handling & resilience

- [ ] Global error boundary renders "Something went wrong" with Try again
      (simulate by stopping API and loading any page)
- [ ] `not-found.tsx` renders for unknown routes
- [ ] Network failures surface toast errors, never blank screens
- [ ] Form validation errors display inline (zod + react-hook-form)
- [ ] Rate limiting returns HTTP 429 with Retry-After in production mode
- [ ] API returns clean JSON errors (no internal details leaked)
- [ ] Empty states show guidance (no jobs, no applicants, no audit entries)

## 6. Performance checks

- [ ] Admin stats served from Redis cache on repeat requests
      (TTL 300 s; check `admin:stats:*` keys in redis-cli)
- [ ] Job search p95 < 500 ms with seeded dataset (≥ 1k jobs)
- [ ] Dashboard lists paginate server-side (page size ≤ 100)
- [ ] Lighthouse ≥ 80 performance on `/dashboard` and `/admin`

## 7. Security spot-checks

- [ ] `/api/v1/admin/*` returns 403 for authenticated non-admins
- [ ] Expired JWT returns 401 and client refreshes or redirects to login
- [ ] Passwords are bcrypt-hashed in DB; no tokens in localStorage logs
- [ ] CORS only allows configured origins
