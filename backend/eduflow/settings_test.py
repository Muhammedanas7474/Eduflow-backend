"""
Test-specific Django settings.
Used only for pytest.
"""

from pathlib import Path

# --------------------------------------------------
# Base
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "test-secret-key"
DEBUG = False
ALLOWED_HOSTS = []

# --------------------------------------------------
# Applications
# --------------------------------------------------

INSTALLED_APPS = [
    # Django core
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project apps
    "apps.tenants",
    "apps.accounts",
    "apps.courses",
    "apps.enrollments",
    "apps.notifications",
]


# --------------------------------------------------
# Middleware (minimal & safe for tests)
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# --------------------------------------------------
# Database (FAST & ISOLATED)
# --------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# --------------------------------------------------
# Passwords (fast hashing for tests)
# --------------------------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# --------------------------------------------------
# Internationalization
# --------------------------------------------------

USE_TZ = True
TIME_ZONE = "UTC"

# --------------------------------------------------
# Static files (required by Django)
# --------------------------------------------------

STATIC_URL = "/static/"

# --------------------------------------------------
# Redis / Celery (DISABLED FOR UNIT TESTS)
# --------------------------------------------------

REDIS_URL = "redis://localhost:6379/0"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
