# Hikvision Attendance System

## Project Description

Attendance management system built with Django and Django REST Framework. It syncs access
events and employee records from Hikvision ISAPI devices, calculates daily/monthly attendance
(late arrivals, early leaves, overtime, penalties and bonuses) and forwards access events to
Telegram channels.

## Features

*   **User Authentication & Authorization**: JWT via `djangorestframework-simplejwt`; the refresh
    token is stored in an httponly cookie.
*   **Hikvision Integration**: Employee and access-event sync over ISAPI (HTTP Digest auth),
    including face image download and remote user create/delete.
*   **Attendance Tracking**: Daily absence records (`sbk` / `szk`) and a monthly report with
    per-day breakdown.
*   **Reporting**: Monthly attendance and daily access exports to Excel (`openpyxl`).
    There is no PDF export.
*   **Telegram Notifications**: Access events are pushed to the Telegram channels bound to a device.
*   **API Documentation**: Auto-generated OpenAPI schema with `drf-spectacular`.
*   **Admin Interface**: `django-jazzmin`.
*   **CORS Support**: Configured through `TRUSTED_ORIGINS`.

## Technologies Used

*   **Backend**: Python 3.12, Django 5.2, Django REST Framework
*   **Database**: PostgreSQL in production (`psycopg2-binary`), SQLite locally
*   **Cache**: Redis (`django-redis`) — required outside of tests
*   **Asynchronous Tasks**: Celery (see the caveat under *Celery Worker Setup*)
*   **Web Server**: Gunicorn
*   **API Documentation**: `drf-spectacular`
*   **Environment Management**: `python-decouple`
*   **Other Libraries**: `openpyxl`, `pillow`, `requests`, `django-cors-headers`, `django-jazzmin`

## Setup & Installation

### Prerequisites

*   Python 3.12 (CI and the lint/type configuration target 3.12)
*   Redis — required for the cache backend even in local mode
*   PostgreSQL — only when `ENVIRON=production`; otherwise SQLite is used

### 1. Clone the Repository

```bash
git clone https://github.com/az1mjonovislom77/hikvision.git
cd hikvision
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
# For development (lint, types, tests):
pip install -r requirements-dev.txt
```

### 4. Environment Variables

Copy the sample file and fill it in:

```bash
cp .env.example .env
```

`SECRET_KEY` and `BOT_TOKEN` are mandatory — both are read at import time, so even
`python manage.py check` fails without them. See `.env.example` for the full list.

### 5. Database Setup

With the default `ENVIRON=local` no setup is needed; SQLite is created automatically.

For production (`ENVIRON=production`) create the PostgreSQL database first:

```sql
CREATE DATABASE hikvision;
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
ALTER ROLE your_db_user SET client_encoding TO 'utf8';
ALTER ROLE your_db_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE hikvision TO your_db_user;
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create a Superuser

```bash
python manage.py createsuperuser
```

### 8. Running the Development Server

```bash
python manage.py runserver
```

The application will be accessible at `http://127.0.0.1:8000/`.

### 9. Celery Worker Setup

The Celery app lives in `config/celery_config.py`:

```bash
celery -A config worker -l info
```

**Caveat:** no `CELERY_BEAT_SCHEDULE` is configured and no code path calls `.delay()`, so the
declared tasks (`attendance.tasks.mark_attendance`, `event.tasks`, `utils.tasks`) never run on
their own today. Event syncing currently happens inline inside the HTTP request.

### 10. Real-time Event Listener

Access events are pushed to Telegram by a long-running management command:

```bash
python manage.py real_time
```

### 11. Gunicorn (for Production)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Development Checks

The same chain runs in CI (`.github/workflows/ci.yml`):

```bash
ruff check .
ruff format --check .
mypy .
python manage.py check
python manage.py makemigrations --check --dry-run
coverage run manage.py test
coverage report
```

`pre-commit install` wires ruff into the commit hook.

## API Documentation

Once the development server is running:

*   **Swagger UI**: `http://127.0.0.1:8000/api/swagger/`
*   **OpenAPI schema**: `http://127.0.0.1:8000/api/schema/`

## Contributing

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.
