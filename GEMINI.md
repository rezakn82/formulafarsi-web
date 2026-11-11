# FormulaFarsi (PitStop News) — Project Guidelines for Gemini & Antigravity

FormulaFarsi is a Persian-language (RTL) Formula 1 and motorsport editorial, race calendar, and championship standings web application built with **Django 5.2 LTS** and managed with **`uv`**.

---

## 1. Architecture & Directory Structure

- **`apps/`**: All Django applications live inside the `apps/` package.
  - **`apps.news`** (`apps/news/`): News articles (`Article`), categories (`Category`), Summernote rich-text content (`SummernoteTextField`), and dynamic XML sitemaps (`ArticleSitemap`, `StaticViewSitemap`, `DriverSitemap`, `TeamSitemap`).
  - **`apps.racing`** (`apps/racing/`): F1 `Circuit`, `Team`, `Driver`, `DriverStanding`, and `TeamStanding` models, views, and admin configurations.
  - **`apps.grandprix_calendar`** (`apps/grandprix_calendar/`): `Season`, `GrandPrix`, and weekend `Session` schedules (FP1, FP2, FP3, Sprint Shootout, Sprint, Qualifying, Main Race).
- **`config/`**: Project configuration package.
  - `config/env.py`: Strict `Env(environ.Env)` wrapper and `load_env_files()` loader (`django-environ` + `python-dotenv`).
  - `config/settings.py`: Environment-driven Django settings.
  - `config/urls.py`: Root URL configuration and sitemap routing.
- **`env/`**: Environment variable files.
  - `env/.env.example`: Tracked template for environment variables.
  - `env/.env`: Local environment file (git-ignored).
- **`docs/`**: Project documentation (`docs/README.md`, `docs/architecture.md`, `docs/TODO.md`, and per-app pages in `docs/modules/<app_name>.md`).
- **`templates/`**: Django HTML templates styled with **Tailwind CSS** and the **Vazirmatn** Persian font (`dir="rtl"`, `lang="fa"`).
- **`.agent/skills/`**: Shared Antigravity/Gemini skills for the team.

---

## 2. Package Management & Commands (`uv`)

Always use **`uv`** to run Python/Django commands and manage dependencies:

- **Install / sync dependencies:** `uv sync`
- **Add a package:** `uv add <package>`
- **Remove a package:** `uv remove <package>`
- **Run Django management commands:** `uv run python manage.py <command>`
- **Run system checks:** `uv run python manage.py check`
- **Run tests (pytest):** `uv run pytest -n auto`
- **Run Django test runner:** `uv run python manage.py test`

Never commit virtual environments (`.venv/`, `venv/`), `db.sqlite3`, `__pycache__/`, or uploaded `media/` files to Git.

---

## 3. Documentation Maintenance Rule (`docs/`)

**The codebase is the single source of truth.** Documentation in [`docs/`](docs/README.md) must never conflict with or drift from the real implementation.

Whenever you add a feature, fix a bug, or modify models, views, URLs, admin configurations, templates, or settings, you **MUST** update the corresponding documentation in the same change:

1. **Per-App Documentation (`docs/modules/<app_name>.md`):**
   - Update [`docs/modules/news.md`](docs/modules/news.md), [`docs/modules/racing.md`](docs/modules/racing.md), or [`docs/modules/grandprix_calendar.md`](docs/modules/grandprix_calendar.md) whenever that app's models, views, querysets, routes, templates, or admin classes change.
   - If you create a new Django app under `apps/`, create a matching `docs/modules/<new_app>.md` following the structure defined in [`docs/README.md`](docs/README.md).
2. **System Architecture (`docs/architecture.md`):**
   - Update [`docs/architecture.md`](docs/architecture.md) (including its Mermaid dependency and ER diagrams) whenever cross-app relationships, model schemas, middleware, environment loading, or tech stack dependencies change.
3. **TODOs & Known Issues (`docs/TODO.md`):**
   - When fixing a bug or completing a feature listed in [`docs/TODO.md`](docs/TODO.md), remove or check off the item in `docs/TODO.md`.
   - When discovering new edge cases or technical debt, record them in `docs/TODO.md`.

---

## 4. Coding & Django Conventions

1. **Top-Level Imports:** Always place imports at the top of Python files, never inside functions or methods.
2. **App Imports & Labels:**
   - Import project apps via the `apps.` prefix (e.g., `from apps.racing.models import Driver, Team`).
   - Keep `AppConfig.name = 'apps.<app_name>'` in `apps.py`. The app label remains `<app_name>` (`news`, `racing`, `grandprix_calendar`), so model string references (e.g., `'racing.Circuit'`, `'grandprix_calendar.Season'`) and URL namespaces (`news:...`, `racing:...`, `grandprix_calendar:...`) use the short label.
3. **Environment Configuration:**
   - Never hardcode secrets, hostnames, or database credentials in `config/settings.py`.
   - Read environment variables through `env` in `config/settings.py` (defined via `config/env.py`) and document any new variables in `env/.env.example`.
4. **Rich-Text Content (`django-summernote`):**
   - Rich-text fields use `django_summernote` (`SummernoteTextField` / `SummernoteModelAdmin`).
   - Ensure admin classes for rich-text models inherit from `SummernoteModelAdmin` and declare `summernote_fields`.
5. **Query Optimization:**
   - Always use `select_related()` for `ForeignKey` relations and `prefetch_related()` for `ManyToManyField` / reverse relations in views and sitemaps to avoid N+1 queries.
6. **Persian RTL & UI Consistency:**
   - All user-facing templates extend `templates/base.html`, use Persian `verbose_name`s on models/fields, and follow the dark motorsport theme (`bg-zinc-950`, `bg-zinc-900`, `border-zinc-800`, `text-red-500`/`bg-red-600`).

---

## 5. Git & Commit Conventions (`CONTRIBUTING.md`)

All commits must strictly follow the structure defined in [`CONTRIBUTING.md`](CONTRIBUTING.md):

```text
[TAG] (app_name) Capitalized short summary (50 chars or less)

[+] Detail about what was added
[-] Detail about what was removed
[*] Detail about what was changed/refactored
```

- **Allowed Tags:** `[INIT]`, `[ADD]`, `[DEL]`, `[FIX]`, `[REFACTOR]`, `[PERF]`, `[STYLE]`, `[CHORE]`
- **Header Mood & Length:** Imperative mood ("Add", "Fix", "Move"), maximum 50 characters.
- **Branch Naming:** `feat/<app>-<description>`, `fix/<app>-<description>`, `hotfix/<description>`, `chore/<description>`.
