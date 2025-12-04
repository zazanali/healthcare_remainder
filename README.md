<div align="center">

# Healthcare Reminders & Alerts System (v2)

Timely reminders for medication, appointments, and follow‑ups — secure, reliable, and production‑ready.

</div>

## Features

- FastAPI API with JWT bearer auth and role‑based access (admin/user)
- APScheduler for reliable scheduling with startup/shutdown lifecycle
- Email (SMTP) and SMS (Twilio) delivery with retry (tenacity)
- Prometheus metrics endpoint (`/metrics`) for observability
- UUID user identifiers and request‑scoped JSON logging
- SQLite for local development, PostgreSQL for production

## Project Structure

```
app/
  main.py            # App entry point, routes and middleware
  config.py          # Settings via pydantic‑settings (.env)
  routes/
    auth.py          # Authentication & JWT issuance (demo users)
    reminders.py     # Reminder CRUD, webhook, RBAC guards
  services/
    db.py            # SQLAlchemy models & queries
    scheduler.py     # APScheduler jobs & lifecycle
    delivery.py      # Email/SMS delivery helpers
  utils/
    security.py      # JWT decode, RBAC, webhook HMAC
    time.py          # ISO8601 + UTC helpers
    logging.py       # JSON logging + request id
  schemas/
    reminder.py      # Pydantic request/response models

alembic/             # Alembic migrations (versions directory)
Dockerfile           # Container image for the API
docker-compose.yml   # API + Postgres services for local/dev
requirements.txt     # Python dependencies
.env                 # Environment variables (example values provided)
```

## Quick Start

### 1) Configure environment

Create and edit `.env` in the repo root (example keys below):

```
# Security (change in production)
JWT_SECRET=dev-secret-key-change-in-production
JWT_ALG=HS256
WEBHOOK_SECRET=dev-webhook-secret-change-in-production

# SMTP (for real email delivery)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-specific-password

# Twilio (for real SMS delivery)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM=your-twilio-number

# Database
DATABASE_URL=sqlite:///reminders.db   # dev
# For Postgres:
# DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/reminders_db

LOG_LEVEL=INFO
```

### 2) Run with Docker Compose (recommended)

```
docker compose up --build
```

This starts the API on `http://localhost:8000` and a local PostgreSQL on `localhost:5432`.

### 3) Or run locally (no Docker)

```
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Authentication

- Obtain a JWT via `POST /auth/token` using demo users defined in `routes/auth.py`.
- Use the token in `Authorization: Bearer <token>` header for all protected endpoints.

Example (curl):

```
curl -sX POST http://localhost:8000/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"zazan","password":"1234"}'
```

## API Overview

- `GET /` — Welcome message
- `GET /metrics` — Prometheus metrics

Authentication
- `POST /auth/token` — Issue JWT

Reminders (JWT required)
- `POST /reminders` — Create reminder for current user
- `GET /users/{uid}/reminders` — List reminders (self unless admin)
- `GET /reminders/{rem_id}` — Get reminder by id
- `PUT /reminders/{rem_id}` — Update reminder (title/message/etc.)
- `POST /reminders/{rem_id}/cancel` — Cancel reminder
- `POST /webhooks/trigger_reminder` — Trigger via webhook (HMAC header required)

### Request Model (Create)

```
{
  "title": "Doctor Appointment",
  "message": "Follow‑up tomorrow at 10 AM.",
  "delivery_time": "2025-09-26T10:00:00Z",
  "method": "email",                # or "sms"
  "timezone": "UTC",
  "reminder_metadata": {"to": "patient@example.com"}
}
```

Note: In the current demo implementation, the delivery address is derived from the user context. For production, provide explicit destination via `reminder_metadata.to` (email or phone) and adjust delivery accordingly.

## Scheduling & Delivery

- APScheduler starts on app lifespan, schedules per‑reminder jobs.
- A fallback job checks due reminders every minute to ensure delivery.
- Delivery uses SMTP (email) and Twilio (SMS) with retries. If SMTP/Twilio are not configured, messages are logged as fake deliveries.

## Database & Migrations

- SQLite is used by default for development; PostgreSQL recommended in production.
- Alembic is included for migrations. Generate an initial migration before using Postgres:

```
alembic init alembic                        # if not initialized
alembic revision --autogenerate -m "init"   # create versions/*
alembic upgrade head                        # apply schema
```

Tip: When using migrations, prefer removing `Base.metadata.create_all(...)` from runtime and relying on Alembic for schema management.

## Configuration

Key environment variables:

- `JWT_SECRET`, `JWT_ALG` — JWT signing
- `WEBHOOK_SECRET` — HMAC secret for webhook requests
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` — Email delivery
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM` — SMS delivery
- `DATABASE_URL` — Database connection string
- `LOG_LEVEL` — Logging level (e.g., INFO, DEBUG)

## Observability

- Metrics available at `GET /metrics` (Prometheus format).
- Logs emitted in JSON with `request_id`. Include `X-Request-ID` header to propagate tracing.

## Security Notes

- Demo users are for development only. Replace with a real user store, hashed passwords, and role management for production.
- Change secrets for production and store via environment/secret manager.
- Webhook endpoint requires HMAC signature (send a hex digest in header like `X-Signature`); ensure sender uses the same `WEBHOOK_SECRET`.

## Development Tips

- Use `uvicorn --reload` during local development.
- Consider adding unit tests for auth, scheduling, delivery, and CRUD.
- For Postgres, index `user_id`, `status`, `delivery_time`, `created_at` for performance.

## Contributing

Issues and PRs are welcome. Please open an issue for feature requests or bugs.

## License

Everyone can use it.
