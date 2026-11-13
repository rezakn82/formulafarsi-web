"""Local development Django settings for FormulaFarsi."""

from importlib.util import find_spec

from .base import *

# ==============================================================================
# SECURITY & DEBUG
# ==============================================================================
SECRET_KEY = env.required("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://localhost:8000", "http://127.0.0.1:8000"],
)

# ==============================================================================
# DEVELOPMENT EXTENSIONS & DEBUG TOOLBAR
# ==============================================================================
if find_spec("django_extensions") is not None:
    INSTALLED_APPS.append("django_extensions")

if DEBUG and find_spec("debug_toolbar") is not None:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1", "localhost"])

# ==============================================================================
# DATABASE & EMAIL
# ==============================================================================
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}

EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
