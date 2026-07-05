# BLUESKY Transactions System

> **International money transfer management platform for Africa**

**Live demo:** [pascal02.pythonanywhere.com](https://pascal02.pythonanywhere.com)

---

## About

**BLUESKY Transactions** is a complete web platform for managing international money transfers across African countries. Agents record and track transactions while admins monitor all activity through a real-time dashboard with charts and statistics.

---

## Author

Created by **Pascal Mutaka**

- GitHub: [github.com/PascalMTK](https://github.com/PascalMTK)
- Email: vandervloger@gmail.com
- Deployed: [pascal02.pythonanywhere.com](https://pascal02.pythonanywhere.com)

Used [Claude Code](https://claude.com/claude-code) as an assistant for some debugging along the way.

---

## Features

| Feature | Description |
|---------|-------------|
| **Transactions** | Create, edit, delete, print receipts — types: Send / Withdrawal |
| **Fee calculation** | Configurable percentage per country, auto-calculated on input |
| **Admin Dashboard** | Live statistics, monthly charts, top agents, breakdown by country |
| **Agent Dashboard** | Personal statistics, quick actions, recent transactions |
| **Agent management** | Registration → admin validation; activate / deactivate / promote to admin / archive |
| **Country management** | Add/edit countries, currency and default fees |
| **Reports** | Agents submit tickets; admin can reply |
| **Excel export** | .xlsx export for admin (all transactions) and agent (own transactions) |
| **Printable receipts** | Print view per transaction |
| **Profile** | Name, phone, profile photo, password change |
| **Bilingual FR/EN** | French / English; language persisted in session |
| **Dark/light mode** | Saved in localStorage; automatic system theme detection |
| **Mobile-first** | Bottom navigation bar, fluid typography (`clamp()`), 44px touch targets |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, Django 4.2 LTS |
| Database | SQLite (production) or MySQL / MariaDB |
| Auth | Custom session auth (no Django auth), bcrypt passwords |
| Frontend | Django templates, Vanilla JS, CSS Variables (dark/light) |
| Export | openpyxl (.xlsx) |
| Hosting | PythonAnywhere |

---

## Local Setup

### 1. Clone the project

```bash
git clone https://github.com/PascalMTK/BlueSky-Transaction-System.git
cd BlueSky-Transaction-System
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure the `.env` file

Create a `.env` file at the root with the following variables:

```env
USE_SQLITE=True
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Create the tables

```bash
python manage.py migrate
```

> Models use `managed = True` — Django creates the tables automatically.

### 5. Start the server

```bash
python manage.py runserver
```

Open in your browser: **http://localhost:8000**

---

## PythonAnywhere Deployment

The project is deployed on PythonAnywhere (paid plan).

**Production `.env` variables:**

```env
USE_SQLITE=True
DEBUG=False
ALLOWED_HOSTS=pascal02.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://pascal02.pythonanywhere.com
SECRET_KEY=your-secret-key
```

**Update the server:**

```bash
cd ~/BlueSky-Transaction-System
git pull origin main
```

Then click **Web → Reload** in the PythonAnywhere dashboard.

---

## Project Structure

```
BlueSky-Transaction-System/
├── bluesky/
│   ├── settings.py          # Django configuration (DB, session)
│   ├── urls.py              # Root routes
│   └── wsgi.py
├── core/
│   ├── models.py            # User, Country, Transaction, AgentReport
│   ├── decorators.py        # @agent_required, @admin_required, get_auth_user()
│   ├── middleware.py        # AuthMiddleware, LocaleMiddleware
│   ├── context_processors.py# auth_user, locale, active_countries (global)
│   ├── translations.py      # FR/EN dictionaries ({{ t.* }} in templates)
│   ├── hashers.py           # bcrypt hasher compatible with Laravel
│   ├── urls.py              # All application routes
│   ├── views/
│   │   ├── auth_views.py    # Login, logout, registration
│   │   ├── agent_views.py   # Agent dashboard, transactions, reports, export
│   │   ├── admin_views.py   # Admin dashboard, agents, countries, reports, export
│   │   └── profile_views.py # Profile, photo, password
│   └── templatetags/
│       └── bluesky_tags.py  # Custom filters: number_format, initials, limit…
├── templates/
│   ├── layouts/app.html     # Base layout (sidebar, topbar, mob-nav, dark mode)
│   ├── auth/                # login, register
│   ├── admin/               # dashboard, agents, transactions, countries, reports, stats
│   └── agent/               # dashboard, transactions/, reports
├── static/
│   ├── css/bluesky.css      # Design system (CSS variables, dark mode, responsive)
│   └── js/bluesky.js        # Theme toggle, clock, sidebar, animations
├── media/
│   └── profiles/            # Uploaded profile photos
├── requirements.txt
└── manage.py
```

---

## Main URLs

### Authentication

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/login/` | Sign in |
| GET | `/logout/` | Sign out |
| GET/POST | `/register/` | Agent registration |
| GET | `/lang/<locale>/` | Switch language (fr/en) |

### Agent Area

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/agent/dashboard/` | Agent dashboard |
| GET | `/agent/transactions/` | Transaction list |
| GET/POST | `/agent/transactions/create/` | New transaction |
| GET | `/agent/transactions/<id>/` | Transaction detail |
| GET/POST | `/agent/transactions/<id>/edit/` | Edit transaction |
| GET | `/agent/transactions/<id>/print/` | Printable receipt |
| POST | `/agent/transactions/<id>/delete/` | Delete transaction |
| GET | `/network/` | All network transactions |
| GET | `/agent/export/csv/` | Personal Excel export |

### Admin Area

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/admin/dashboard/` | Admin dashboard |
| GET | `/admin/agents/` | Agent management (cards) |
| GET/POST | `/admin/agents/<id>/edit/` | Edit an agent |
| POST | `/admin/agents/<id>/status/` | Activate / deactivate |
| POST | `/admin/agents/<id>/promote/` | Promote to admin |
| POST | `/admin/agents/<id>/password/` | Change password |
| POST | `/admin/agents/<id>/delete/` | Archive (soft delete) |
| GET | `/admin/transactions/` | All transactions |
| GET | `/admin/countries/` | Operational countries |
| GET | `/admin/statistics/` | Advanced statistics |
| GET | `/admin/export/csv/` | Full Excel export |

---

## Security

- **Sessions** — `request.session['user_id']` set on login; cleared on logout
- **Decorators** — `@agent_required` checks user is logged in **and active**; `@admin_required` additionally checks `role == 'admin'`
- **Passwords** — bcrypt (cost 10), compatible with Laravel hashes
- **CSRF** — Django middleware on all POST endpoints
- **Statuses** — Inactive / pending / archived agents are automatically logged out
- **Soft delete** — Archived agents retain their transaction data; they cannot log in

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
| status | Enum | `active` / `pending` / `inactive` / `deleted` |
| agent_code | Varchar unique | e.g. `BSK-CD-A3F9B2` |
| country_id | FK → Country | Agent's operating country |
| profile_photo | Varchar | Relative path under `/media/` |

### Transaction

| Field | Type | Notes |
|-------|------|-------|
| transaction_number | Varchar unique | e.g. `BSK-20260618-XA91B3` |
| transaction_type | Enum | `send` / `withdrawal` |
| status | Enum | `completed` / `pending` / `cancelled` |
| payment_method | Enum | `cash` / `mobile_money` / `bank` |
| amount | Decimal | Base amount |
| fee_percentage | Decimal | Applied fee % |
| fee_amount | Decimal | Calculated fee amount |
| total_amount | Decimal | `amount + fee_amount` |
| origin_country_id | FK → Country | |
| destination_country_id | FK → Country | |
| agent_id | FK → User | Agent who recorded the transaction |

### Country

| Field | Notes |
|-------|-------|
| code | 2-letter ISO code |
| name | Display name |
| flag_emoji | Stored emoji |
| currency_code | ISO currency code |
| default_fee_percentage | Default fee for outgoing transfers |
| is_active | Visible to agents or not |

---

## License

MIT — Created by **Pascal Mutaka**, 2026
