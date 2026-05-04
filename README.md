# Hikvision Attendance System

## Project Description

This project is a robust attendance management system built with Django and Django REST Framework. It is designed to efficiently track and manage attendance records, potentially integrating with Hikvision devices for data collection. The system includes features for user management, event logging, and reporting, leveraging asynchronous tasks with Celery and Redis for improved performance.

## Features

*   **User Authentication & Authorization**: Secure user management with Django REST Framework Simple JWT.
*   **Attendance Tracking**: Core functionality for recording and managing attendance.
*   **Person Management**: Manage individuals whose attendance is being tracked.
*   **Event Logging**: Record various events related to attendance or system activities.
*   **Reporting**: Generate reports (e.g., PDF, Excel) for attendance data.
*   **API Endpoints**: RESTful API for seamless integration with front-end applications or other services.
*   **Asynchronous Task Processing**: Utilizes Celery and Redis for background tasks, improving responsiveness.
*   **Internationalization**: Support for multiple languages using `django-modeltranslation`.
*   **Admin Interface**: Enhanced administrative interface with `django-jazzmin`.
*   **CORS Support**: Configured for cross-origin resource sharing.
*   **API Documentation**: Auto-generated API documentation using DRF Spectacular/drf-yasg.

## Technologies Used

*   **Backend**: Python, Django, Django REST Framework
*   **Database**: PostgreSQL (`psycopg2-binary`)
*   **Asynchronous Tasks**: Celery, Redis
*   **Web Server**: Gunicorn
*   **API Documentation**: `drf-spectacular`, `drf-yasg`
*   **Environment Management**: `python-decouple`
*   **Other Libraries**: `aiohttp`, `openpyxl`, `reportlab`, `pillow_heif`, `lxml`, `PyJWT`, `django-cors-headers`, `django-modeltranslation`, `django-jazzmin`, etc.

## Setup & Installation

Follow these steps to get the project up and running on your local machine.

### Prerequisites

*   Python 3.9+
*   PostgreSQL
*   Redis

### 1. Clone the Repository

```bash
git clone https://github.com/az1mjonovislom77/hikvision.git
cd hikvision
```
### 2. Create a Virtual Environment

It's recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

Install all required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 4. Database Setup

Ensure you have PostgreSQL installed and running. Create a new database for the project.

```sql
CREATE DATABASE hikvision;
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
ALTER ROLE your_db_user SET client_encoding TO 'utf8';
ALTER ROLE your_db_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE your_db_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE hikvision TO your_db_user;
```
*(Note: Replace `hikvision`, `your_db_user`, and `your_db_password` with your desired values.)*

### 5. Environment Variables

Create a `.env` file in the project root directory (where `manage.py` is located) and configure your environment variables.

```
# .env example
SECRET_KEY='your_django_secret_key'
DEBUG=True

# Database Configuration
DB_NAME=hikvision
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration for Celery
REDIS_URL=redis://localhost:6379/0

# Allowed Hosts for Django
ALLOWED_HOSTS=localhost,127.0.0.1

# Other settings
# EMAIL_HOST=smtp.example.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your_email@example.com
# EMAIL_HOST_PASSWORD=your_email_password
```
*(Make sure to replace placeholder values with your actual settings.)*

### 6. Run Migrations

Apply database migrations to create the necessary tables:

```bash
python manage.py migrate
```

### 7. Create a Superuser

Create an administrative user to access the Django admin panel:

```bash
python manage.py createsuperuser
```
Follow the prompts to set up your superuser credentials.

### 8. Running the Development Server

Start the Django development server:

```bash
python manage.py runserver
```
The application will be accessible at `http://127.0.0.1:8000/`.

### 9. Celery Worker Setup

For asynchronous tasks, you need to run a Celery worker. Open a new terminal and navigate to your project root.

```bash
celery -A config worker -l info
```
*(Note: `config` is assumed to be your main Django project directory containing `celery.py` or similar configuration.)*

### 10. Gunicorn (for Production)

For production deployment, you would typically use Gunicorn.

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```
*(Note: `config` is assumed to be your main Django project directory.)*

## API Documentation

The project includes auto-generated API documentation. Once the development server is running, you can access:

*   **Swagger UI**: `http://127.0.0.1:8000/swagger/`
*   **ReDoc**: `http://127.0.0.1:8000/redoc/`

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.
