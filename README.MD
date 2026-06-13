# StreamDB API

REST API for a streaming platform (Netflix-style), built as a portfolio project to demonstrate relational database design, authentication, and business logic implementation with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.

> ⚠️ This project is under active development. New modules (content catalog, watch history, ratings) are being added incrementally.

---

## Overview

StreamDB models the core domain of a video streaming service: users, subscription plans, and active subscriptions, with JWT-based authentication and role-based access control (admin vs. regular users).

The goal of this project is to showcase:

- Relational schema design with proper constraints and relationships
- Authentication and authorization with JWT
- Business logic enforced at the API layer (e.g., subscription expiration, plan validation)
- Clean separation of concerns (models, schemas, auth, routes)
- Database migrations with Alembic

---

## Tech Stack

| Layer       | Technology                            |
|-------------|-----------------------------------------|
| Language    | Python 3.13                            |
| Framework   | FastAPI                                  |
| ORM         | SQLAlchemy 2.x                          |
| Database    | PostgreSQL 17                           |
| Migrations  | Alembic                                  |
| Auth        | JWT (python-jose) + bcrypt (passlib)     |
| Validation  | Pydantic                                 |

---

## Project Structure

```
streamdb/
├── alembic.ini
├── config.py              # Environment configuration (pydantic-settings)
├── database.py            # SQLAlchemy engine, session, connection check
├── main.py                 # FastAPI app and route definitions
├── migrations/             # Alembic migration scripts
├── src/
│   ├── auth/
│   │   └── auth.py         # Password hashing, JWT creation/validation
│   └── models/
│       ├── content.py      # SQLAlchemy ORM models
│       └── schemas.py      # Pydantic request/response schemas
├── requirements.txt
└── .env.example
```

---

## Database Design

The schema covers users, subscription plans, and active subscriptions, with the following key relationships:

- A **user** can have multiple **subscriptions** over time, but only one active at a time.
- A **subscription** references a **subscription plan**, which defines pricing, quality, and screen limits.
- **Admin users** can manage subscription plans; regular users can only manage their own subscriptions.

### Core entities

**Users**
- Authentication credentials (hashed passwords)
- Role flag (`is_admin`) for access control

**Subscription Plans**
- Name, price, quality tier, max simultaneous screens
- Can be activated/deactivated by admins

**Subscriptions**
- Linked to a user and a plan
- Tracks `starts_at`, `ends_at`, and `status` (`active`, `cancelled`, `expired`)
- Automatically expires when `ends_at` is reached

---

## Authentication & Authorization

Authentication is handled via **JWT bearer tokens**:

1. Users register with `email`, `password`, and `full_name`
2. Passwords are hashed with **bcrypt** before storage
3. On login, a JWT access token is issued
4. Protected endpoints require an `Authorization: Bearer <token>` header
5. An `is_admin` flag restricts certain endpoints (e.g., creating subscription plans) to administrators

---

## API Endpoints

### Authentication

| Method | Endpoint     | Description                 | Auth required |
|--------|--------------|------------------------------|----------------|
| POST   | `/register`  | Register a new user           | No |
| POST   | `/login`     | Authenticate and get a JWT    | No |
| GET    | `/me`        | Get current user info         | Yes |
| PUT    | `/user`      | Update current user's name    | Yes |
| DELETE | `/user`      | Delete current user account   | Yes |

### Subscription Plans (admin-managed)

| Method | Endpoint                   | Description                | Auth required |
|--------|----------------------------|------------------------------|----------------|
| GET    | `/subscription-plans`      | List all active plans         | No |
| GET    | `/subscription-plans/{id}` | Get a specific plan           | No |
| POST   | `/subscription-plans`      | Create a new plan              | Admin |
| PUT    | `/subscription-plans/{id}` | Update an existing plan        | Admin |
| DELETE | `/subscription-plans/{id}` | Delete a plan                  | Admin |

### Subscriptions

| Method | Endpoint                     | Description                              | Auth required |
|--------|------------------------------|---------------------------------------------|----------------|
| POST   | `/subscriptions`             | Subscribe the current user to a plan          | Yes |
| GET    | `/subscriptions`             | List the current user's subscriptions         | Yes |
| GET    | `/subscriptions/active`      | Get the current user's active subscription    | Yes |
| PUT    | `/subscriptions/{id}/cancel` | Cancel a subscription                          | Yes |

---

## Business Logic Highlights

- **Subscription expiration**: when checking for an active subscription, the API automatically marks it as `expired` if the current date is past `ends_at`.
- **Plan availability**: users cannot subscribe to a plan that has been deactivated by an admin.
- **Role-based access**: subscription plan management is restricted to users with `is_admin = true`.

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 17

### 1. Clone the repository

```bash
git clone https://github.com/BryanCCortes/streamdb.git
cd streamdb
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate    # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=streamdb
DB_USER=postgres
DB_PASSWORD=your_password

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the API

```bash
python -m uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with interactive documentation at `http://127.0.0.1:8000/docs`.

---

## Roadmap

- [ ] Content catalog (movies & series) with genre filtering
- [ ] Episode management for series
- [ ] Premium content access control based on active subscription
- [ ] Watch history tracking
- [ ] Reporting views (most watched, top rated)

---

## Author

**Bryan Cedeño Cortés**
Software Developer | Backend Development with Python, FastAPI & PostgreSQL

[GitHub](https://github.com/BryanCCortes)