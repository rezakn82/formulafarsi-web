"""Docker container Django settings for FormulaFarsi with PostgreSQL."""

from .production import *

# ==============================================================================
# CONTAINER HTTP / REVERSE-PROXY DEFAULTS
# ==============================================================================
# Allow local Docker Compose runs over plain HTTP while keeping TLS flags
# configurable via env/.env.docker when sitting behind a TLS reverse proxy.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)

# ==============================================================================
# EMAIL
# ==============================================================================
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
