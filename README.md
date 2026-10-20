# Hotel Management System

A full-stack hotel system with a **REST API**, a **staff panel** and a **public booking website**.
Guests can browse rooms and book online; staff manage rooms, guests, bookings, payments and reports.
All prices are in **PKR**.

Built as an internship learning project with Python, FastAPI and PostgreSQL.

## Features

**Public website (`/`)**
- Browse room types with photos, amenities and live availability for chosen dates
- Customer accounts: register, sign in, forgot and reset password
- Online booking (adults, children, special requests, optional ID and address) with a booking code
- My bookings: view and cancel; find a booking with code and email

**Staff panel (`/app/`)**
- Dashboard: occupancy ring, arrivals and departures today, 7-day revenue
- Rooms, room types (with photo upload), guests (search and edit), staff users
- Bookings: create, check-in, check-out, cancel, search by year, month or day
- Payments per booking with balance due
- Change password, forgot password

**Backend rules**
- Double-booking protection: a code check plus a PostgreSQL exclusion constraint
- The server calculates every price; the total is saved with the booking
- Booking status flow, capacity check, and an ID required before check-in
- Payments are never edited or deleted
- Roles: admin, receptionist, manager

## Tech stack

| Area | Tools |
|---|---|
| Backend | Python 3.13, FastAPI, Uvicorn |
| Database | PostgreSQL, SQLAlchemy 2, Alembic |
| Validation and settings | Pydantic v2, pydantic-settings, email-validator |
| Security | JWT (python-jose), bcrypt |
| Frontend | Plain HTML, CSS and JavaScript (no build step) |
| Tests | pytest, httpx |
| Deployment | Docker, Docker Compose |

## Roles

| Action | Admin | Receptionist | Manager |
|---|---|---|---|
| Manage staff, room types, rooms | Yes | No | No |
| View rooms, guests, bookings, payments | Yes | Yes | Yes |
| Create and edit guests | Yes | Yes | No |
| Delete guests | Yes | No | No |
| Create bookings, check-in, check-out, cancel | Yes | Yes | No |
| Take payments | Yes | Yes | No |
| Arrivals, departures, occupancy | Yes | Yes | Yes |
| Revenue report | Yes | No | Yes |
| Change own password | Yes | Yes | Yes |

Website customers use a separate account type and can only book and manage their own bookings.

## Project structure

```
app/
  main.py            app setup, CORS, static mounts (/app, /uploads, /)
  core/              settings, security (JWT, bcrypt), password reset, mail, uploads
  db/                engine and session
  models/            SQLAlchemy tables
  schemas/           Pydantic request and response models
  crud/              database queries
  services/          business rules (bookings, billing, reports)
  api/               dependencies (login, roles) and v1 endpoints
alembic/             database migrations
frontend/            staff panel
website/             public booking website
scripts/             create_admin, reset_password, seed
tests/               pytest tests
```

Endpoints handle HTTP, `crud/` talks to the database, and `services/` holds the business rules.

## Database

Tables: `users` (staff), `guests` (people who stay), `customers` (website accounts), `room_types`, `rooms`, `bookings`, `payments`.

Constraints worth knowing: unique room numbers, emails and ID documents, `check_out > check_in`, `payment amount > 0`, and a PostgreSQL **exclusion constraint** that stops two active bookings of one room from overlapping.

## Run locally (Windows PowerShell)

1. Create a PostgreSQL database named `hotel_db`.
2. Create the environment and install packages:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your values. Make a secret key with:
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
4. Create the tables and the first admin:
   ```
   alembic upgrade head
   python -m scripts.create_admin
   ```
5. Optional sample room types and rooms:
   ```
   python -m scripts.seed
   ```
6. Start the server:
   ```
   uvicorn app.main:app --reload
   ```

| Address | What it is |
|---|---|
| http://localhost:8000/ | Public booking website |
| http://localhost:8000/app/ | Staff panel |
| http://localhost:8000/docs | API documentation (development only) |

## Run with Docker

Set `DB_PASSWORD` in `.env` (letters and numbers only), then:

```
docker compose up --build
docker compose exec api python -m scripts.create_admin
docker compose exec api python -m scripts.seed
```

`docker compose down` stops the containers and keeps the data. `docker compose down -v` also deletes the database.

## Environment variables

| Name | Meaning |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Long random text that signs tokens (at least 32 characters in production) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Login lifetime, default 60 |
| `ENVIRONMENT` | `development` or `production` (production turns off `/docs`) |
| `CORS_ORIGINS` | Comma-separated websites allowed to call the API from a browser |
| `PUBLIC_BASE_URL` | Address used inside password reset links |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Email settings. If `SMTP_HOST` is empty, reset links are printed in the server log instead of being emailed |
| `DB_PASSWORD` | Database password for Docker Compose only |

Never commit `.env`.

## Tests

```
pytest -v
```

More than 50 tests cover login and roles, rooms, bookings (overlap, price, status flow), payments, reports, password change and reset, and booking details. They run on a separate `hotel_test_db`, created automatically, and a safety check stops them from ever touching the real database.

## Main business rules

- Two stays overlap when `existing.check_in < new.check_out` and `existing.check_out > new.check_in`. The check-out day is free for the next guest. Only `reserved` and `checked_in` bookings block a room.
- `total_amount` = nights x room type price, saved with the booking so later price changes do not change old bookings. Money uses `Numeric`, never `float`.
- Booking status: `reserved` to `checked_in` to `checked_out`, or `reserved` to `cancelled`.
- Adults plus children cannot exceed the room capacity. A guest needs an ID type and number before check-in.
- A payment cannot be more than the balance due, and cancelled bookings cannot take payments.
- Rooms and guests that have bookings cannot be deleted. Rooms are set to maintenance instead.
- An admin cannot deactivate their own account or remove their own admin role.

## Security

- Passwords are hashed with bcrypt. Login errors are the same for a wrong email and a wrong password.
- JWT login with an expiry. Roles are read from the database on every request.
- Password reset links last 30 minutes and work only once.
- Uploaded room photos are checked by file content (JPG, PNG, WebP), limited to 3 MB, and saved with random names.
- User text is escaped before it is shown in the pages.

## API overview

All endpoints are under `/api/v1`.

| Area | Endpoints |
|---|---|
| Auth (staff) | `POST /auth/login`, `GET /auth/me`, `POST /auth/forgot`, `/auth/reset`, `/auth/change-password` |
| Users | `GET/POST /users`, `GET/PATCH /users/{id}` |
| Room types | `GET/POST /room-types`, `GET/PATCH/DELETE /room-types/{id}`, `POST /room-types/{id}/image` |
| Rooms | `GET/POST /rooms`, `GET /rooms/available`, `GET/PATCH/DELETE /rooms/{id}` |
| Guests | `GET/POST /guests` (search with `?q=`), `GET/PATCH/DELETE /guests/{id}` |
| Bookings | `GET/POST /bookings` (filters `status`, `year`, `month`, `day`), `GET /bookings/{id}`, `POST /bookings/{id}/check-in`, `/check-out`, `/cancel`, `GET /bookings/{id}/balance` |
| Payments | `GET/POST /payments`, `GET /payments/{id}` |
| Reports | `GET /reports/arrivals`, `/departures`, `/occupancy`, `/revenue` |
| Public (website) | `POST /public/auth/register`, `/login`, `/forgot`, `/reset`, `GET /public/auth/me`, `GET /public/room-types`, `POST /public/bookings`, `GET /public/my-bookings`, `POST /public/my-bookings/{code}/cancel`, `GET /public/bookings/{code}?email=` |

## Known limits

- Email needs SMTP settings; without them reset links appear in the server log.
- No rate limiting on login and forgot password yet.
- No online card payment: guests pay at the hotel.
- Reports have no charts and there is no printable invoice yet.
- Uploaded photos live in the `uploads/` folder; with Docker they need a volume to survive a rebuild.

## Author

Maaz Saeed
