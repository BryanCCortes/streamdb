# StreamDB API

REST API for a streaming platform (Netflix-style), built as a portfolio project to demonstrate relational database design, authentication, and business logic implementation with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.

---

## Overview

StreamDB models the core domain of a video streaming service: users, subscription plans, content catalog, active subscriptions, watch history, and watchlist — with JWT-based authentication and role-based access control (admin vs. regular users).

The goal of this project is to showcase:

- Relational schema design with proper constraints and relationships
- Authentication and authorization with JWT
- Business logic enforced at the API layer (e.g., subscription expiration, plan validation, premium content access)
- Clean separation of concerns using FastAPI routers, dependency injection, and Pydantic schemas
- Database migrations with Alembic

---

## Tech Stack

| Layer       | Technology                                   |
|-------------|----------------------------------------------|
| Language    | Python 3.13.5                                |
| Framework   | FastAPI                                      |
| ORM         | SQLAlchemy 2.x                               |
| Database    | PostgreSQL 17                                |
| Migrations  | Alembic                                      |
| Auth        | JWT (python-jose) + bcrypt (passlib)         |
| Validation  | Pydantic                                     |

---

## Project Structure

```
streamdb/
├── alembic.ini
├── config.py                  # Environment configuration (pydantic-settings)
├── database.py                # SQLAlchemy engine, session, connection check
├── main.py                    # FastAPI app entry point, router registration
├── migrations/                # Alembic migration scripts
├── src/
│   ├── dependencies.py        # Shared dependencies: get_db, get_current_user, is_admin_user, access_premium_content
│   ├── auth/
│   │   └── auth.py            # Password hashing, JWT creation/validation
│   ├── Models/
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   └── schemas.py         # Pydantic request/response schemas
│   └── routers/
│       ├── auth.py            # /register, /login, /me, /user
│       ├── content.py         # /content, /seasons, /episodes
│       ├── genres.py          # /genres
│       ├── subscriptions.py   # /subscription-plans, /subscriptions
│       ├── watch_history.py   # /watch-history
│       └── watchlist.py       # /watchlist
├── requirements.txt
└── .env.example
```

---

## Database Design

The schema covers the full domain of a streaming platform with the following key relationships:

- A **user** can have multiple **subscriptions** over time, but only one active at a time
- A **subscription** references a **subscription plan** which defines pricing, quality, and screen limits
- **Content** can be movies or series; series are organized into **seasons** and **episodes**
- **Content** and **genres** have a many-to-many relationship via a pivot table
- **Admin users** manage content, genres, and subscription plans; regular users manage their own data

### Core entities

**Users** — credentials (hashed passwords), role flag (`is_admin`)

**Subscription Plans** — name, price, quality tier (`SD`, `HD`, `4K`), max simultaneous screens

**Subscriptions** — linked to user and plan, tracks `starts_at`, `ends_at`, and `status` (`active`, `cancelled`, `expired`)

**Content** — movies and series, with `is_premium` flag for access control

**Genres** — many-to-many with content via `content_genres` pivot table

**Seasons / Episodes** — hierarchical structure for series content

**Watch History** — tracks user progress per content/episode, auto-marks as completed at 90% progress

**Watchlist** — users can save content to watch later

---

## Authentication & Authorization

Authentication is handled via **JWT bearer tokens**:

1. Users register with `email`, `password`, and `full_name`
2. Passwords are hashed with **bcrypt** before storage
3. On login, a JWT access token is issued
4. Protected endpoints require an `Authorization: Bearer <token>` header
5. An `is_admin` flag restricts certain endpoints to administrators

---

## API Endpoints

### Authentication

| Method | Endpoint    | Description                  | Auth required |
|--------|-------------|-------------------------------|---------------|
| POST   | `/register` | Register a new user           | No            |
| POST   | `/login`    | Authenticate and get a JWT    | No            |
| GET    | `/me`       | Get current user info         | Yes           |
| PUT    | `/user`     | Update current user's name    | Yes           |
| DELETE | `/user`     | Delete current user account   | Yes           |

### Subscription Plans (admin-managed)

| Method | Endpoint                   | Description              | Auth required |
|--------|----------------------------|--------------------------|---------------|
| GET    | `/subscription-plans`      | List all active plans    | No            |
| GET    | `/subscription-plans/{id}` | Get a specific plan      | No            |
| POST   | `/subscription-plans`      | Create a new plan        | Admin         |
| PUT    | `/subscription-plans/{id}` | Update an existing plan  | Admin         |
| DELETE | `/subscription-plans/{id}` | Delete a plan            | Admin         |

### Subscriptions

| Method | Endpoint                     | Description                                | Auth required |
|--------|------------------------------|--------------------------------------------|---------------|
| POST   | `/subscriptions`             | Subscribe the current user to a plan       | Yes           |
| GET    | `/subscriptions`             | List the current user's subscriptions      | Yes           |
| GET    | `/subscriptions/active`      | Get the current user's active subscription | Yes           |
| PUT    | `/subscriptions/{id}/cancel` | Cancel a subscription                      | Yes           |

### Genres (admin-managed)

| Method | Endpoint        | Description          | Auth required |
|--------|-----------------|----------------------|---------------|
| GET    | `/genres`       | List all genres      | No            |
| GET    | `/genres/{id}`  | Get a specific genre | No            |
| POST   | `/genres`       | Create a genre       | Admin         |
| PUT    | `/genres/{id}`  | Update a genre       | Admin         |

### Content

| Method | Endpoint        | Description                                           | Auth required |
|--------|-----------------|-------------------------------------------------------|---------------|
| GET    | `/content`      | List content (filters: `type`, `genre`, `is_premium`) | No            |
| GET    | `/content/{id}` | Get content detail — requires subscription if premium | Yes           |
| POST   | `/content`      | Create a movie or series                              | Admin         |
| PUT    | `/content/{id}` | Update content                                        | Admin         |

### Seasons & Episodes

| Method | Endpoint                  | Description               | Auth required |
|--------|---------------------------|---------------------------|---------------|
| GET    | `/content/{id}/seasons`   | List seasons of a series  | No            |
| POST   | `/content/{id}/seasons`   | Create a season           | Admin         |
| GET    | `/seasons/{id}/episodes`  | List episodes of a season | No            |
| POST   | `/seasons/{id}/episodes`  | Create an episode         | Admin         |

### Watch History

| Method | Endpoint                    | Description                                        | Auth required |
|--------|-----------------------------|----------------------------------------------------|---------------|
| POST   | `/watch-history`            | Register or update watch progress for content      | Yes           |
| GET    | `/watch-history`            | Get full watch history for the current user        | Yes           |
| GET    | `/watch-history/{content_id}` | Get progress for a specific content              | Yes           |
| DELETE | `/watch-history/{id}`       | Delete a watch history record                      | Yes           |

### Watchlist

| Method | Endpoint              | Description                          | Auth required |
|--------|-----------------------|--------------------------------------|---------------|
| POST   | `/watchlist`          | Add content to the watchlist         | Yes           |
| GET    | `/watchlist`          | Get the current user's watchlist     | Yes           |
| DELETE | `/watchlist/{id}`     | Remove content from the watchlist    | Yes           |

---

## Business Logic Highlights

- **Subscription expiration**: when checking for an active subscription, the API automatically marks it as `expired` if the current date is past `ends_at`
- **Premium content access**: `GET /content/{id}` returns `403` if the content is premium and the user has no active subscription
- **Plan availability**: users cannot subscribe to a plan that has been deactivated by an admin
- **Series validation**: seasons can only be created on content with `type = "series"`
- **Duplicate genre protection**: creating a genre with an existing name returns `400` instead of a database error
- **Watch progress tracking**: updating watch progress auto-marks content as completed when 90% is reached
- **Role-based access**: content and plan management is restricted to users with `is_admin = true`

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

- [x] User authentication with JWT
- [x] Subscription plans and subscriptions with business logic
- [x] Content catalog (movies & series) with genre filtering
- [x] Season and episode management for series
- [x] Modular router structure with shared dependencies
- [x] Premium content access control based on active subscription
- [x] Watch history tracking with progress and completion detection
- [x] Watchlist
- [ ] Deploy

---

## Author

**Bryan Cedeño Cortés**
Software Developer | Backend Development with Python, FastAPI & PostgreSQL

[GitHub](https://github.com/BryanCCortes)