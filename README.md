# Talent Copilot - Backend (Django 6.1 + DRF 3.18, Python 3.13)

## Quick start
```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill DJANGO_SECRET_KEY with your own generated value
set -a; source .env; set +a
python manage.py migrate
python manage.py createsuperuser   # local dev only
python manage.py runserver
python manage.py test
```
Health check: `GET /api/v1/health/`

## Who owns which app (Phase 1)
| App | URL prefix | Owner | Module |
|---|---|---|---|
| `apps/accounts` | `/api/v1/auth/` | Srikanth | JWT auth & user management |
| `apps/screening` | `/api/v1/screening/` | Veeran | JD input, results, session history |
| `apps/matching` | `/api/v1/matching/` | Vinay | Matching engine & knowledge base |
| `apps/vectorsearch` | `/api/v1/vectorsearch/` | Abhyuday | Milvus vector search |
| `apps/resumes` | `/api/v1/resumes/` | Manoj | Resume file serving for the viewer |
| `apps/interview` | `/api/v1/interview/` | Phase 2 | Questions, chatbot, feedback |
| `apps/common` | `/api/v1/health/` | Shared | Error handler, shared utilities |

Stay inside your own app. If you need something from another app, agree the interface (function or endpoint) with its owner in the PR.

## Conventions (every PR)
- Pattern: model -> serializer -> view -> permission -> url -> test. Copy `ping` in your app to start.
- Every endpoint is authenticated by default. Opt out only with an explicit `AllowAny` and a comment saying why.
- Authorize by object (e.g. "can this user see *this* resume"), not just "is logged in".
- Validate all input in serializers (allowlist type/shape/range). No raw SQL string building; use the ORM.
- No secrets, real resumes or candidate data in code, tests or fixtures. Use synthetic data.
- No new dependency without approval (see below).
- Branches: `feature/<app>-<short-name>`; PR needs one reviewer from the owning team and one learner reviewer.

## Dependencies
Approved/in manifest: Django, djangorestframework. **Pending approval (not installed):**
`djangorestframework-simplejwt` (Srikanth, JWT), a PostgreSQL driver `psycopg` (database; dev uses SQLite for now),
`celery` + `redis`, `pymongo`, `boto3`, `pymilvus`. Raise these via the approval process before use.

## Known gaps (tracked)
- Auth is session-only until the JWT module lands; Simple JWT approval and security-team confirmation on app-managed passwords are open.
- Login rate limiting, refresh token in http-only cookie: part of the accounts module.
- Database is SQLite locally; PostgreSQL settings come with the driver approval.
