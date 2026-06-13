# BLUESKY Transactions System

A web platform for managing international money transfers. Agents record and track transactions, the admin monitors all activity through a dashboard with charts and statistics.

Bilingual interface (French / English), mobile-first responsive design, dark/light mode.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Django 4.2 LTS |
| Database | MySQL or MariaDB |
| Auth | Custom session-based (no Django auth), bcrypt passwords |
| Frontend | Django templates, vanilla JS, CSS variables (dark/light) |
| Excel export | openpyxl |
| OTP/cache | Django in-memory cache |

---

## Features

- **Transactions** — create, view, edit, delete; types: Send / Withdrawal; statuses: Completed / Pending / Cancelled
- **Fee calculation** — configurable fee percentage per country, auto-calculated on form
- **Admin dashboard** — live stats, monthly charts (Chart.js), top agents, country breakdown donut
- **Agent dashboard** — personal stats, quick actions, recent transactions
- **Agent management** — registration → admin approval workflow; activate / deactivate / promote to admin
- **Country management** — add/edit countries, per-country default fee and currency
- **Direct messaging** — agent ↔ agent and agent ↔ admin real-time-style inbox
- **Support tickets** — agents submit reports to admin; admin can reply
- **Export** — Excel (.xlsx) export for admin (all transactions) and agent (own transactions)
- **Printable receipts** — one-click print view per transaction
- **Profile** — name, phone, photo upload, password change
- **Bilingual** — French / English; language switch persisted in session
- **Dark / light mode** — saved in localStorage; system-preference aware
- **Mobile-friendly** — bottom navigation bar, fluid typography (`clamp()`), 44px touch targets
- **Password reset** — OTP via email, 10-minute expiry

---

## Requirements

- Python 3.10+
- MySQL 8 or MariaDB 10.6+
- pip

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd BlueSky-Transactions-System/bluesky-django
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Create the database

```sql
CREATE DATABASE bluesky_transactions CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure environment

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Minimum required settings in `.env`:

```env
SECRET_KEY=your-secret-key-here
DB_NAME=bluesky_transactions
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=BLUESKY <your@email.com>
```

> The app uses `python-dotenv` — settings are loaded from `.env` at startup.

### 5. Import the database schema

The models use `managed = False`, meaning Django does **not** run migrations to create tables. You must import the schema SQL manually:

```bash
mysql -u root -p bluesky_transactions < schema.sql
```

> If a `schema.sql` file is not present, run `python manage.py inspectdb` after pointing at an existing database, or create the tables from `core/models.py`.

### 6. Start the development server

```bash
python manage.py runserver
```

Open in your browser: **http://localhost:8000**

The root URL redirects to the login page.

---

## Running the System (day-to-day)

### Every time you want to start the app

**Step 1 — Start MySQL** (if not running as a service)

```bash
# Windows (XAMPP)
# Open XAMPP Control Panel and click Start next to MySQL

# Or via command line
net start mysql
```

**Step 2 — Activate the virtual environment**

```bash
# From the bluesky-django/ folder

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

**Step 3 — Start Django**

```bash
python manage.py runserver
```

App is now live at **http://localhost:8000**

To use a different port (e.g. 8080):

```bash
python manage.py runserver 8080
```

### Stop the server

Press `Ctrl + C` in the terminal.

### Verify everything is working

- **http://localhost:8000** → redirects to login page ✅
- **http://localhost:8000/login/** → login form ✅
- **http://localhost:8000/register/** → agent registration form ✅

### Common errors on startup

| Error | Cause | Fix |
|-------|-------|-----|
| `django.db.utils.OperationalError: Can't connect to MySQL` | MySQL is not running | Start MySQL first |
| `ModuleNotFoundError: No module named 'django'` | Virtual environment not activated | Run `.venv\Scripts\activate` |
| `Table 'bluesky_transactions.core_user' doesn't exist` | Schema not imported | Import `schema.sql` into the database |
| `ImproperlyConfigured: SECRET_KEY` | `.env` file missing | Copy `.env.example` to `.env` and fill in values |

---

## Project Structure

```
bluesky-django/
├── bluesky/
│   ├── settings.py          # Django settings (DB, cache, session, email)
│   ├── urls.py              # Root URL config
│   └── wsgi.py
├── core/
│   ├── models.py            # User, Country, Transaction, DirectMessage, AgentReport
│   ├── decorators.py        # @agent_required, @admin_required, get_auth_user()
│   ├── middleware.py        # AuthMiddleware, LocaleMiddleware
│   ├── context_processors.py# Injects auth_user, locale, active_countries globally
│   ├── translations.py      # EN/FR string dictionaries (t.* in templates)
│   ├── hashers.py           # Laravel-compatible bcrypt hasher
│   ├── urls.py              # All application routes
│   ├── views/
│   │   ├── auth_views.py    # Login, logout, register, OTP password reset
│   │   ├── agent_views.py   # Agent dashboard, transactions CRUD, messaging, export
│   │   ├── admin_views.py   # Admin dashboard, agents, countries, reports, export
│   │   └── profile_views.py # Profile view/update, photo, password
│   └── templatetags/
│       └── bluesky_tags.py  # Custom filters: number_format, limit, initials, etc.
├── templates/
│   ├── layouts/app.html     # Base layout (sidebar, topbar, mob-nav, dark mode)
│   ├── auth/                # login.html, register.html, forgot_password.html, …
│   ├── admin/               # dashboard, agents, transactions, countries, reports, stats
│   └── agent/               # dashboard, transactions/, messages, reports, profile
├── static/
│   ├── css/bluesky.css      # Full design system (CSS variables, dark mode, responsive)
│   └── js/bluesky.js        # Theme toggle, live clock, sidebar, counters, animations
├── media/
│   └── profiles/            # Uploaded profile photos (auto-created)
├── requirements.txt
└── manage.py
```

---

## URL Reference

### Auth

| Method | URL | Name | Description |
|--------|-----|------|-------------|
| GET/POST | `/login/` | `login` | Login form |
| GET | `/logout/` | `logout` | Logout |
| GET/POST | `/register/` | `register` | Agent self-registration |
| GET/POST | `/forgot-password/` | `forgot_password` | Request OTP |
| GET/POST | `/verify-otp/` | `verify_otp` | Enter OTP code |
| GET/POST | `/reset-password/` | `reset_password` | Set new password |
| GET | `/lang/<locale>/` | `lang_switch` | Switch language (en/fr) |

### Agent

| Method | URL | Name | Description |
|--------|-----|------|-------------|
| GET | `/agent/dashboard/` | `agent_dashboard` | Agent home |
| GET | `/agent/transactions/` | `tx_index` | Own transactions list |
| GET/POST | `/agent/transactions/create/` | `tx_create` | New transaction |
| GET | `/agent/transactions/<id>/` | `tx_show` | Transaction detail |
| GET/POST | `/agent/transactions/<id>/edit/` | `tx_edit` | Edit transaction |
| GET | `/agent/transactions/<id>/print/` | `tx_print` | Printable receipt |
| POST | `/agent/transactions/<id>/delete/` | `tx_destroy` | Delete transaction |
| GET | `/network/` | `tx_network` | All network transactions (read-only) |
| GET | `/messages/` | `messages_list` | Inbox |
| GET/POST | `/messages/<user_id>/` | `messages_thread` | Conversation thread |
| GET | `/agent/export/csv/` | `agent_export_csv` | Download own transactions as Excel |
| GET/POST | `/agent/reports/` | `agent_report_store` | Submit support ticket |

### Admin

| Method | URL | Name | Description |
|--------|-----|------|-------------|
| GET | `/admin/dashboard/` | `admin_dashboard` | Admin home |
| GET | `/admin/transactions/` | `admin_transactions` | All transactions |
| GET | `/admin/agents/` | `admin_agents` | Agent list |
| POST | `/admin/agents/<id>/status/` | `admin_agent_status` | Activate / deactivate |
| POST | `/admin/agents/<id>/promote/` | `admin_agent_promote` | Promote to admin |
| POST | `/admin/agents/<id>/delete/` | `admin_agent_destroy` | Delete agent |
| GET | `/admin/countries/` | `admin_countries` | Country list |
| GET/POST | `/admin/countries/create/` | `admin_countries_create` | Add country |
| GET/POST | `/admin/countries/<id>/edit/` | `admin_countries_edit` | Edit country |
| POST | `/admin/countries/<id>/toggle/` | `admin_countries_toggle` | Enable/disable country |
| GET | `/admin/export/csv/` | `admin_export_csv` | Download all transactions as Excel |
| GET | `/admin/statistics/` | `admin_statistics` | Statistics page |
| GET | `/admin/reports/` | `admin_reports` | Support tickets |

### API

| Method | URL | Name | Description |
|--------|-----|------|-------------|
| GET | `/api/countries/<id>/fee/` | `api_country_fee` | Returns `{fee, currency}` for a country |

---

## Authentication & Security

- **Session-based auth** — `request.session['user_id']` set on login; cleared on logout
- **Decorators** — `@agent_required` redirects to `/login/` if unauthenticated; `@admin_required` additionally checks `user.role == 'admin'`
- **Passwords** — bcrypt with cost factor 10; compatible with Laravel bcrypt hashes (for migration)
- **CSRF** — Django's built-in CSRF middleware on all POST endpoints
- **OTP** — 6-digit code stored in Django's local-memory cache, expires in 10 minutes

---

## Data Model

### User
| Field | Type | Notes |
|-------|------|-------|
| id | BigInt PK | |
| name | Varchar | |
| email | Varchar unique | |
| phone | Varchar | |
| password | Varchar | bcrypt hash |
| role | Enum | `admin` / `agent` |
| status | Enum | `active` / `pending` / `inactive` |
| agent_code | Varchar unique | Auto-generated: `BSK-{COUNTRY}-{6HEX}` |
| country_id | FK → Country | Agent's home country |
| profile_photo | Varchar | Relative path under `/media/` |

### Transaction
| Field | Type | Notes |
|-------|------|-------|
| id | BigInt PK | |
| transaction_number | Varchar unique | `BSK-YYYYMMDD-XXXXXX` |
| transaction_type | Enum | `send` / `withdrawal` |
| status | Enum | `completed` / `pending` / `cancelled` |
| payment_method | Enum | `cash` / `mobile_money` / `bank` |
| amount | Decimal | Base amount |
| fee_percentage | Decimal | Applied fee % |
| fee_amount | Decimal | Calculated fee |
| total_amount | Decimal | `amount + fee_amount` |
| currency | Varchar | ISO code from origin country |
| origin_country_id | FK → Country | |
| destination_country_id | FK → Country | |
| agent_id | FK → User | Agent who recorded it |
| sender_name / phone | Varchar | |
| receiver_name / phone | Varchar | nullable |

### Country
| Field | Notes |
|-------|-------|
| code | ISO 2-letter code (PK-style) |
| name | Display name |
| flag_emoji | Stored emoji |
| currency_code | ISO currency |
| default_fee_percentage | Default fee for outgoing transfers |
| is_active | Whether shown to agents |

---

## Configuration Notes

- `USE_TZ = False` — all datetimes are naive (Africa/Kinshasa timezone)
- `managed = False` on all models — Django never creates or alters tables
- Session cookie: `bluesky_session`, 24-hour lifetime
- OTP cache: in-memory (`LocMemCache`) — **restarts clear pending OTPs**; replace with Redis for production
- `DEBUG = True` in the repo — set to `False` and configure `ALLOWED_HOSTS` before deploying

---

## License

MIT
