# SanctiShop

Modern ecommerce web application built with **FastAPI** and **Python**.

Features authentication, RBAC authorization, admin dashboard, shopping cart, order workflow, and backend security practices.

![SanctiShop](https://img.shields.io/badge/SanctiShop-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Tech Stack

### Backend

- **Python 3.13** — Modern type-safe Python
- **FastAPI** — High-performance async web framework
- **SQLModel** — Typed ORM combining SQLAlchemy + Pydantic
- **SQLAlchemy** — Mature relational database toolkit
- **JWT Authentication** — Token-based auth with `python-jose`
- **Pytest** — Testing with 31+ passing tests

### Database

- **SQLite** (development) — Zero-config local database
- **PostgreSQL** (planned production) — Scalable production database

### Frontend

- **Jinja2 Templates** — Server-side rendered HTML
- **TailwindCSS** — Utility-first responsive CSS framework
- **Vanilla JavaScript** — Lightweight client-side interactivity

### Security

- **JWT + HttpOnly Cookies** — Secure token storage, XSS resistant
- **Role-Based Access Control (RBAC)** — Granular permission scopes
- **Rate Limiting** — SlowAPI protection against brute force
- **CORS Protection** — Cross-origin security
- **Password Hashing** — bcrypt via passlib
- **Input Validation** — Pydantic schemas with strict validators

---

## Features

- **User authentication** — Registration and login with JWT tokens
- **Secure sessions** — HttpOnly cookies with Bearer token fallback
- **Role-based access control** — User and admin roles with granular scopes
- **Product catalog** — Paginated listing, category filtering, sorting
- **Shopping cart** — Add, update, remove items with real-time totals
- **Checkout workflow** — Order creation, payment simulation, stock deduction
- **Order tracking** — Status lifecycle: En proceso → Pagada → Lista → Entregada
- **Admin dashboard** — Full product CRUD with modal forms
- **User management** — Role promotion, account activation/deactivation
- **Order management** — Status transitions, detailed order view
- **Dark mode** — Persistent theme with system preference detection
- **Responsive design** — Mobile-first TailwindCSS layout
- **Search & filters** — Product search, category chips, price sorting
- **Brand identity** — Custom SanctiShop logo, favicon, and color palette

---

## Architecture

The project follows a **layered architecture** with clear separation of concerns:

```
/app
├── api/                    # REST API endpoints (JSON)
│   ├── endpoints/          # Route handlers grouped by domain
│   │   ├── auth.py         # Login, register, logout, me
│   │   ├── products.py     # Product CRUD + public listing
│   │   ├── cart.py         # Cart operations
│   │   ├── orders.py       # Checkout, history, admin status
│   │   ├── payments.py     # Payment intents + webhooks
│   │   └── admin_users.py  # User management (admin)
│   ├── dependencies/       # Auth, scopes, DB session
│   └── router.py           # Centralized router registration
├── core/                   # Configuration and security
│   ├── config.py           # Pydantic settings (env vars)
│   ├── security.py         # JWT, bcrypt, scope validation
│   └── limiter.py          # Rate limiting setup
├── db/                     # Database layer
│   ├── models.py           # SQLModel entities
│   ├── session.py          # DB engine and session management
│   └── seed.py             # Initial data seeding
├── schemas/                # Pydantic request/response models
│   ├── products.py
│   ├── auth.py
│   ├── cart.py
│   ├── orders.py
│   ├── payments.py
│   └── users.py
├── services/               # Business logic layer
│   ├── products.py
│   ├── auth.py
│   ├── cart.py
│   ├── orders.py
│   └── payments/
│       ├── service.py       # Payment orchestration
│       ├── adapter.py       # Payment provider interface
│       ├── mock_provider.py # Local development provider
│       └── enzona_provider.py # Enzona integration (Cuba)
├── static/                 # Static assets
│   ├── css/app.css         # Custom styles + dark mode
│   ├── js/app.js           # Client-side interactivity
│   └── images/             # Product images, Sancti Spíritus photos
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Layout with navbar, footer
│   ├── components/         # Reusable UI components
│   └── pages/              # Page templates
│       ├── admin/          # Admin panel pages
│       └── ...             # User-facing pages
├── main.py                 # FastAPI app entry point
└── ...                     # Configuration files

/tests                      # Pytest test suite
```

### Key Design Decisions

| Principle | Implementation |
|-----------|---------------|
| **API / HTML separation** | `/api/*` for JSON, `/views/*` for HTML pages |
| **Dependency injection** | All dependencies use FastAPI `Depends()` |
| **Idempotent seeding** | Seed runs only on empty database |
| **Payment abstraction** | Provider pattern — mock for dev, Enzona for production |
| **Scope-based auth** | RBAC with string scopes, validated by inclusion |

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip
- (Optional) Node.js for TailwindCSS

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/sanctishop.git
cd sanctishop

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

The server starts at **http://localhost:8000**. The database is automatically seeded with demo data on first run.

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@test.com` | `Admin123!` |
| **User** | `user@test.com` | `User1234!` |

### Running Tests

```bash
pytest -x -q
```

## API Overview

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products` | Paginated product listing |
| `GET` | `/api/products/{id}` | Product detail |
| `POST` | `/api/auth/register` | User registration |
| `POST` | `/api/auth/login` | User login |

### Protected Endpoints (User)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/auth/me` | Current user profile |
| `GET` | `/api/cart` | Get cart contents |
| `POST` | `/api/cart/items` | Add item to cart |
| `PUT` | `/api/cart/items/{id}` | Update cart item |
| `DELETE` | `/api/cart` | Clear cart |
| `POST` | `/api/orders/checkout` | Create order from cart |
| `GET` | `/api/orders` | User order history |

### Admin Endpoints

| Method | Endpoint | Scope Required |
|--------|----------|----------------|
| `POST` | `/api/products` | `admin:products` |
| `PUT` | `/api/products/{id}` | `admin:products` |
| `DELETE` | `/api/products/{id}` | `admin:products` |
| `PATCH` | `/api/orders/{id}/status` | `admin:orders` |
| `GET` | `/api/orders/admin` | `admin:orders` |
| `GET` | `/api/admin/users` | `admin:users` |
| `PATCH` | `/api/admin/users/{id}/role` | `admin:users` |
| `PATCH` | `/api/admin/users/{id}/toggle-active` | `admin:users` |

---

## Project Status

- **31+ tests passing** across all modules
- Auth tests: 90%+ coverage
- Fully functional MVP with admin panel
- Ready for production deployment with PostgreSQL + Enzona integration

---

## License

MIT
