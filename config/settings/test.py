"""Isolated, fast Django settings for automated test runs."""

from .base import *

# ==============================================================================
# SECURITY & TEST ISOLATION
# ==============================================================================
SECRET_KEY = env.str("SECRET_KEY", default="django-insecure-test-key-for-pytest-only")
DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
CSRF_TRUSTED_ORIGINS = []

# ==============================================================================
# DATABASE, HASHERS & EMAIL
# ==============================================================================
DATABASES = {
    "default": env.db(
        "TEST_DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
