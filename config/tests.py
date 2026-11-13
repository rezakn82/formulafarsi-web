"""Tests for environment file resolution and split settings configuration."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import load_env_files, resolve_django_env


def test_resolve_django_env_prefers_explicit_env() -> None:
    """Explicit ``DJANGO_ENV`` takes precedence over ``DJANGO_SETTINGS_MODULE``."""
    env_map = {
        "DJANGO_ENV": "staging",
        "DJANGO_SETTINGS_MODULE": "config.settings.production",
    }
    assert resolve_django_env(env_map) == "staging"


def test_resolve_django_env_from_settings_module_suffix() -> None:
    """Profile is inferred from known ``DJANGO_SETTINGS_MODULE`` suffixes."""
    assert resolve_django_env({"DJANGO_SETTINGS_MODULE": "config.settings.local"}) == "local"
    assert resolve_django_env({"DJANGO_SETTINGS_MODULE": "config.settings.development"}) == "local"
    assert resolve_django_env({"DJANGO_SETTINGS_MODULE": "config.settings.docker"}) == "docker"
    assert (
        resolve_django_env({"DJANGO_SETTINGS_MODULE": "config.settings.production"})
        == "production"
    )
    assert resolve_django_env({"DJANGO_SETTINGS_MODULE": "config.settings.test"}) == "test"
    assert resolve_django_env({}) is None


def test_load_env_files_precedence_and_production_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``DJANGO_SETTINGS_MODULE=config.settings.production`` loads ``.env.production`` over ``.env``."""
    (tmp_path / ".env").write_text("DJANGO_ENV=local\nFOO=from_base\nBAR=from_base\n")
    (tmp_path / ".env.local").write_text("FOO=from_local\nLOCAL_ONLY=1\n")
    (tmp_path / ".env.production").write_text("FOO=from_production\n")

    monkeypatch.delenv("DJANGO_ENV", raising=False)
    monkeypatch.delenv("BAR", raising=False)
    monkeypatch.delenv("LOCAL_ONLY", raising=False)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.production")
    monkeypatch.setenv("FOO", "from_process")

    load_env_files(tmp_path)

    assert os.environ["FOO"] == "from_process"
    assert os.environ["BAR"] == "from_base"
    assert "LOCAL_ONLY" not in os.environ


def test_load_env_files_test_mode_ignores_local_and_base_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test runs never load ``.env`` or ``.env.local`` automatically."""
    (tmp_path / ".env").write_text("LEAKED_BASE=1\n")
    (tmp_path / ".env.local").write_text("LEAKED_LOCAL=1\n")
    (tmp_path / ".env.test").write_text("TEST_VAR=from_test\n")

    monkeypatch.delenv("DJANGO_ENV", raising=False)
    monkeypatch.delenv("LEAKED_BASE", raising=False)
    monkeypatch.delenv("LEAKED_LOCAL", raising=False)
    monkeypatch.delenv("TEST_VAR", raising=False)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.test")

    load_env_files(tmp_path)

    assert "LEAKED_BASE" not in os.environ
    assert "LEAKED_LOCAL" not in os.environ
    assert os.environ["TEST_VAR"] == "from_test"


def test_production_settings_validation_and_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production settings enforce ``ALLOWED_HOSTS``, ``DATABASE_URL``, and ``DEBUG = False``."""
    monkeypatch.setenv("SECRET_KEY", "test-production-secret-key-0123456789")
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    sys.modules.pop("config.settings.production", None)
    with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS"):
        importlib.import_module("config.settings.production")

    monkeypatch.setenv("ALLOWED_HOSTS", "formulafarsi.ir")
    sys.modules.pop("config.settings.production", None)
    with pytest.raises(ImproperlyConfigured):
        importlib.import_module("config.settings.production")

    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost:5432/formulafarsi")
    sys.modules.pop("config.settings.production", None)
    prod = importlib.import_module("config.settings.production")

    assert prod.DEBUG is False
    assert prod.ALLOWED_HOSTS == ["formulafarsi.ir"]
    assert prod.X_FRAME_OPTIONS == "SAMEORIGIN"
    assert prod.SECURE_SSL_REDIRECT is True
    assert prod.DATABASES["default"]["CONN_MAX_AGE"] == 60
    assert (
        prod.STORAGES["staticfiles"]["BACKEND"]
        == "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )
    sys.modules.pop("config.settings.production", None)


def test_docker_settings_inherits_production_with_http_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Docker settings enforce PostgreSQL & ``DEBUG = False`` with local-HTTP TLS defaults."""
    monkeypatch.setenv("SECRET_KEY", "test-docker-secret-key-0123456789")
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost,web")
    monkeypatch.setenv("DATABASE_URL", "postgres://formulafarsi:formulafarsi@db:5432/formulafarsi")
    monkeypatch.delenv("SECURE_SSL_REDIRECT", raising=False)
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("CSRF_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("EMAIL_BACKEND", raising=False)

    sys.modules.pop("config.settings.production", None)
    sys.modules.pop("config.settings.docker", None)
    docker_settings = importlib.import_module("config.settings.docker")

    assert docker_settings.DEBUG is False
    assert docker_settings.SECURE_SSL_REDIRECT is False
    assert docker_settings.SESSION_COOKIE_SECURE is False
    assert docker_settings.CSRF_COOKIE_SECURE is False
    assert docker_settings.SECURE_HSTS_SECONDS == 0
    assert docker_settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert docker_settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"
    sys.modules.pop("config.settings.docker", None)
    sys.modules.pop("config.settings.production", None)
