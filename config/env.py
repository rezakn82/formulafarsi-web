"""Environment loading and strict, typed configuration readers for Django settings."""

from __future__ import annotations

import os
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

SETTINGS_MODULE_ENV_MAP = {
    "local": "local",
    "development": "local",
    "docker": "docker",
    "production": "production",
    "test": "test",
}


class Env(environ.Env):
    """Strict ``django-environ`` subclass that validates environment values explicitly.

    Environment files are loaded into ``os.environ`` via ``load_env_files`` using
    ``python-dotenv`` before reading through ``Env``.
    """

    BOOLEAN_FALSE_STRINGS = ("false", "off", "no", "n", "0")

    def str(self, var: str, default: str = environ.Env.NOTSET) -> str:
        """Read a string value literally without expanding leading ``$`` characters."""
        if var in self.ENVIRON:
            return self.ENVIRON[var]
        return super().str(var, default=default)

    def bool(self, var: str, default: bool = environ.Env.NOTSET) -> bool:
        """Read a boolean value strictly, raising ``ImproperlyConfigured`` on invalid strings."""
        value = self.str(var, default=default)
        if isinstance(value, bool):
            return value
        normalized = value.strip().lower()
        if normalized in self.BOOLEAN_TRUE_STRINGS:
            return True
        if normalized in self.BOOLEAN_FALSE_STRINGS:
            return False
        raise ImproperlyConfigured(f"{var} must be a valid boolean value (true/false, 1/0, yes/no).")

    def list(
        self, var: str, cast: type | None = None, default: list = environ.Env.NOTSET
    ) -> list:
        """Read a comma-separated list, stripping whitespace and ignoring empty entries."""
        items = super().list(var, cast=cast, default=default)
        return [item.strip() if isinstance(item, str) else item for item in items if str(item).strip()]

    def required(self, var: str) -> str:
        """Read a mandatory string variable, raising ``ImproperlyConfigured`` if missing or blank."""
        value = self.str(var)
        if not value.strip():
            raise ImproperlyConfigured(f"The required {var} environment variable is empty.")
        return value


def resolve_django_env(process_env: dict[str, str]) -> str | None:
    """Resolve the active environment profile from OS env or ``DJANGO_SETTINGS_MODULE``."""
    explicit_env = process_env.get("DJANGO_ENV", "").strip()
    if explicit_env:
        return explicit_env

    settings_module = process_env.get("DJANGO_SETTINGS_MODULE", "").strip()
    if settings_module:
        suffix = settings_module.rsplit(".", maxsplit=1)[-1]
        if suffix in SETTINGS_MODULE_ENV_MAP:
            return SETTINGS_MODULE_ENV_MAP[suffix]

    return None


def load_env_files(env_dir: Path) -> None:
    """Load environment files from ``env_dir`` into ``os.environ``.

    Priority (highest to lowest):
    1. Existing process environment variables (``os.environ``)
    2. Environment-specific file (``env/.env.<profile>``)
    3. Optional shared base environment file (``env/.env``)

    The profile is resolved from ``DJANGO_ENV`` in ``os.environ`` first, then from the
    ``DJANGO_SETTINGS_MODULE`` suffix (``local``, ``production``, ``test``), and finally
    from ``env/.env`` or ``"local"``. Test runs only load optional ``env/.env.test`` so
    automated tests remain isolated from local/production environment files.
    """
    process_env = dict(os.environ)
    resolved_env = resolve_django_env(process_env)

    if resolved_env == "test":
        test_env_file = env_dir / ".env.test"
        if test_env_file.exists():
            load_dotenv(test_env_file, override=True)
        os.environ.update(process_env)
        return

    base_env_file = env_dir / ".env"
    if base_env_file.exists():
        load_dotenv(base_env_file)

    django_env = resolved_env or os.environ.get("DJANGO_ENV", "local")
    specific_env_file = env_dir / f".env.{django_env}"
    if specific_env_file.exists():
        load_dotenv(specific_env_file, override=True)

    os.environ.update(process_env)
