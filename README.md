# Hotel Management System (Backend API)

A REST API for managing a hotel: rooms, guests, bookings, payments and reports.
Built as a learning project with **FastAPI**, **PostgreSQL**, **SQLAlchemy** and **Alembic**.

## Features

- **Login and roles:** JWT login, bcrypt password hashing, three roles (admin, receptionist, manager)
- **Rooms and room types:** full CRUD with filters, pagination and admin-only changes
- **Guests:** CRUD with search by name, phone, ID number or email; no duplicate ID documents
- **Availability search:** find free rooms for a date range
- **Bookings:** automatic price calculation, double-booking protection (code check plus a PostgreSQL exclusion constraint), check-in, check-out and cancel
- **Payments:** many payments per booking, balance due, no editing or deleting of payments
- **Reports:** arrivals, departures, occupancy and revenue
- **Tests:** 52 automated tests with pytest on a separate test database
- **Docker:** one command to run the API and the database

## Roles

| Action | Admin | Receptionist | Manager |
|---|---|---|---|
| Manage users, room types, rooms | Yes | No | No |
| View rooms, guests, bookings, payments | Yes | Yes | Yes |
| Create and edit guests | Yes | Yes | No |
| Delete guests | Yes | No | No |
| Create bookings, check-in, check-out, cancel | Yes | Yes | No |
| Take payments | Yes | Yes | No |
| Arrivals, departures, occupancy reports | Yes | Yes | Yes |
| Revenue report | Yes | No | Yes |

## Tech stack

Python 3.13, FastAPI, Uvicorn, PostgreSQL 16, SQLAlchemy 2, Alembic, Pydantic v2, python-jose (JWT), bcrypt, pytest, Docker.

## Project structure

```
app/
  main.py            FastAPI app, CORS, health checks
  core/              settings (config.py) and security (hashing, JWT)
  db/                engine, session and Base
  models/            SQLAlchemy tables
  schemas/           Pydantic request and response models
  crud/              database queries
  services/          business rules (bookings, billing, reports)
  api/               dependencies (auth, roles) and v1 endpoints
alembic/             database migrations
scripts/             create_admin, reset_password, seed
tests/               pytest tests
```

Each endpoint file handles HTTP, `crud/` talks to the database, and `services/` holds the business rules.

## Run locally (Windows PowerShell)

1. Create a database named `hotel_db` in PostgreSQL.
2. Create the virtual environment and install packages:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your own values. Generate a secret key with:
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
4. Create the tables and the first admin:
   ```
   alembic upgrade head
   python -m scripts.create_admin
   ```
5. (Optional) Add sample room types and rooms:
   ```
   python -m scripts.seed
   ```
6. Start the server and open http://localhost:8000/docs:
   ```
   uvicorn app.main:app --reload
   ```

## Run with Docker

Set `DB_PASSWORD` (letters and numbers only) in `.env`, then:

```
docker compose up --build
docker compose exec api python -m scripts.create_admin
docker compose exec api python -m scripts.seed
```

The API runs at http://localhost:8000. The database data is kept in a Docker volume.
`docker compose down` stops the containers and keeps the data. `docker compose down -v` also deletes the data.

## Run the tests

```
pytest -v
```

Tests run on a separate database called `hotel_test_db`, which is created automatically. A safety check stops the tests if they ever point to another database.

## Environment variables

| Name | Meaning |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Long random text used to sign tokens (at least 32 characters in production) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (default 60) |
| `ENVIRONMENT` | `development` or `production`. In production, the `/docs` pages are turned off |
| `CORS_ORIGINS` | Comma-separated list of website addresses allowed to call the API from a browser |
| `DB_PASSWORD` | Database password used by Docker Compose only |

Never commit the `.env` file.

## Main business rules

- The server calculates `total_amount` (nights x room price) and saves it with the booking, so later price changes do not change old bookings.
- A room cannot have two active bookings on overlapping dates. The check-out day is free for the next guest.
- Booking status moves only in order: reserved, checked in, checked out. Only reserved bookings can be cancelled.
- A payment cannot be more than the balance due, and cancelled bookings cannot take payments.
- Rooms, guests and bookings that have history cannot be deleted. Rooms are set to maintenance instead.
- An admin cannot deactivate their own account or remove their own admin role.

## API overview

All endpoints are under `/api/v1`. Interactive documentation is at `/docs` (development only).

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `GET /auth/me` |
| Users | `GET/POST /users`, `GET/PATCH /users/{id}` |
| Room types | `GET/POST /room-types`, `GET/PATCH/DELETE /room-types/{id}` |
| Rooms | `GET/POST /rooms`, `GET /rooms/available`, `GET/PATCH/DELETE /rooms/{id}` |
| Guests | `GET/POST /guests` (search with `?q=`), `GET/PATCH/DELETE /guests/{id}` |
| Bookings | `GET/POST /bookings`, `GET /bookings/{id}`, `POST /bookings/{id}/check-in`, `/check-out`, `/cancel`, `GET /bookings/{id}/balance` |
| Payments | `GET/POST /payments`, `GET /payments/{id}` |
| Reports | `GET /reports/arrivals`, `/departures`, `/occupancy`, `/revenue` |
