# System Architecture

**FormulaFarsi (PitStop News)** is a monolithic server-rendered Django 5.2 LTS web application providing Persian-language (RTL) Formula 1 news, race calendars, driver/team profiles, and championship standings.

---

## 1. Technology Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Runtime & Packaging** | Python $\ge 3.13$, `uv` | Deterministic dependency management (`pyproject.toml` + `uv.lock`) and virtualenv execution |
| **Web Framework** | Django 5.2 LTS (`>5.2,<5.3`) | URL routing, ORM, server-side template rendering, admin panel, and sitemaps |
| **Environment Loader** | `django-environ` + `python-dotenv` | Strict, typed environment variable loading via `config/env.py` |
| **Rich-Text Editor** | `django-summernote` + `bleach` | Persian RTL WYSIWYG editor (`fa-IR`, Vazirmatn font) with HTML sanitization and media attachments |
| **Image Handling** | `Pillow` | Image validation and storage for circuits, driver portraits, team logos/cars, and article covers |
| **Database** | SQLite 3 (dev) / PostgreSQL (prod-ready) | Configured via `DATABASE_URL` in `config/settings.py` |
| **Frontend UI** | Django Templates + Tailwind CSS CDN + Vazirmatn | Responsive dark-themed (`zinc-950`) RTL layout (`dir="rtl"`, `lang="fa"`) | jdatetime
| **Dev & Testing Tooling** | `pytest`, `pytest-django`, `pytest-cov`, `pytest-xdist`, `factory-boy`, `faker`, `django-debug-toolbar`, `django-extensions`, `werkzeug` | Automated testing, parallel execution, SQL query profiling, and `runserver_plus` |

---

## 2. Repository & Package Layout

```text
formulafarsi-web/
├── .agent/skills/            # Shared Antigravity & Gemini skills for the team
├── apps/                     # Domain Django applications
│   ├── grandprix_calendar/   # Season, GrandPrix, Session (app_label: 'grandprix_calendar')
│   ├── news/                 # Category, Article, sitemaps (app_label: 'news')
│   └── racing/               # Circuit, Team, Driver, Standings (app_label: 'racing')
├── config/                   # Project configuration & entrypoints
│   ├── env.py                # Strict Env(environ.Env) subclass and load_env_files()
│   ├── settings.py           # Environment-driven Django settings
│   ├── urls.py               # Root URLconf, Summernote, sitemaps, and Debug Toolbar
│   ├── asgi.py               # ASGI entrypoint
│   └── wsgi.py               # WSGI entrypoint
├── docs/                     # Technical documentation (kept in sync with code)
│   ├── README.md             # Documentation index and maintenance rules
│   ├── architecture.md       # System architecture (this file)
│   ├── TODO.md               # Bug tracker and feature roadmap
│   └── modules/              # Per-app deep-dive documentation
├── env/                      # Environment configuration files
│   ├── .env.example          # Tracked template
│   └── .env                  # Local environment secrets (git-ignored)
├── media/                    # Uploaded media files (git-ignored)
├── templates/                # Server-rendered RTL HTML templates
│   ├── base.html             # Master layout, desktop nav, mobile drawer, footer
│   ├── grandprix_calendar/   # Calendar list and Grand Prix detail views
│   ├── news/                 # Home page, article archive, and article detail views
│   └── racing/               # Standings, driver list/detail, and team list/detail views
├── GEMINI.md                 # Project rules for Antigravity & Gemini
├── CONTRIBUTING.md           # Git commit and branch conventions
├── manage.py                 # Django management entrypoint
├── pyproject.toml            # Dependencies and pytest configuration
└── uv.lock                   # Locked dependency tree
```

### App Naming vs. App Labels
All domain apps live inside the `apps/` Python package:
- Python import path: `apps.news`, `apps.racing`, `apps.grandprix_calendar`
- `AppConfig.name`: `'apps.news'`, `'apps.racing'`, `'apps.grandprix_calendar'`
- `AppConfig.label` (automatic last segment): `'news'`, `'racing'`, `'grandprix_calendar'`

Because the short `label` is preserved, all database table names (`news_article`, `racing_driver`, `grandprix_calendar_session`), model string references (`'racing.Circuit'`, `'grandprix_calendar.Season'`), and URL namespaces (`news:...`, `racing:...`, `grandprix_calendar:...`) use the short app name.

---

## 3. Environment Configuration (`config/env.py`)

`config/settings.py` never reads `os.environ` directly or hardcodes secrets. Instead, it delegates to [`config/env.py`](../config/env.py):

1. **`load_env_files(ENV_DIR)`** loads environment files from `env/` using `python-dotenv` with the following precedence (highest to lowest):
   - Real OS process environment variables (`os.environ`)
   - Environment-specific file: `env/.env.<DJANGO_ENV>` (defaults to `env/.env.local` if present)
   - Base file: `env/.env`
2. **`Env(environ.Env)`** provides strict, typed readers:
   - `env.required("SECRET_KEY")`: Raises `ImproperlyConfigured` if missing or blank.
   - `env.str(var, default=...)`: Reads literal string values without expanding leading `$` characters.
   - `env.bool(var, default=...)`: Accepts only valid boolean strings (`true`/`false`, `1`/`0`, `yes`/`no`, `on`/`off`) and raises `ImproperlyConfigured` on typos.
   - `env.list(var, default=...)`: Strips whitespace around items and drops empty segments.
   - `env.db("DATABASE_URL", default=...)`: Parses database connection URLs into Django `DATABASES` dictionaries.

---

## 4. Application Dependency Map

```mermaid
flowchart TD
    subgraph Config ["config/"]
        URLS["config.urls"]
        SETTINGS["config.settings"]
    end

    subgraph Apps ["apps/"]
        NEWS["apps.news<br/>(Articles, Categories, Sitemaps)"]
        RACING["apps.racing<br/>(Circuits, Teams, Drivers, Standings)"]
        CALENDAR["apps.grandprix_calendar<br/>(Seasons, GrandsPrix, Sessions)"]
    end

    URLS --> NEWS
    URLS --> RACING
    URLS --> CALENDAR

    NEWS -->|"Imports Driver, Team, DriverStanding"| RACING
    NEWS -->|"Imports GrandPrix, Season, Session"| CALENDAR
    RACING -->|"Imports Season & FK 'grandprix_calendar.Season'"| CALENDAR
    CALENDAR -->|"FK 'racing.Circuit'"| RACING
```

- **`apps.news`** is the top-level editorial aggregator:
  - Its models link to `apps.racing.models.Driver`, `apps.racing.models.Team`, and `apps.grandprix_calendar.models.GrandPrix`.
  - Its home view aggregates the next upcoming `Session` (`apps.grandprix_calendar`) and the top 5 `DriverStanding` rows (`apps.racing`).
  - Its `sitemaps.py` generates sitemaps for `Article`, `Driver`, `Team`, and static views across all three apps.
- **`apps.racing`** and **`apps.grandprix_calendar`** share a mutual domain link:
  - `GrandPrix.circuit` points to `'racing.Circuit'` via a lazy string `ForeignKey` (preventing circular Python imports between `models.py` files).
  - `DriverStanding.season` and `TeamStanding.season` point to `'grandprix_calendar.Season'` via lazy string `ForeignKey`s.

---

## 5. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    USER ||--o{ ARTICLE : "authors (PROTECT)"
    CATEGORY ||--o{ ARTICLE : "categorizes (SET_NULL)"
    GRAND_PRIX ||--o{ ARTICLE : "related_grand_prix (SET_NULL)"
    DRIVER }o--o{ ARTICLE : "related_drivers (M2M)"
    TEAM }o--o{ ARTICLE : "related_teams (M2M)"

    TEAM ||--o{ DRIVER : "drivers (SET_NULL)"
    SEASON ||--o{ DRIVER_STANDING : "driver_standings (CASCADE)"
    DRIVER ||--o{ DRIVER_STANDING : "standings (CASCADE)"
    SEASON ||--o{ TEAM_STANDING : "team_standings (CASCADE)"
    TEAM ||--o{ TEAM_STANDING : "standings (CASCADE)"
    SESSION ||--o{ SESSION_RESULT : "results (CASCADE)"
    DRIVER ||--o{ SESSION_RESULT : "session_results (CASCADE)"
    TEAM ||--o{ SESSION_RESULT : "session_results (CASCADE)"

    SEASON ||--o{ GRAND_PRIX : "grands_prix (CASCADE)"
    CIRCUIT ||--o{ GRAND_PRIX : "grands_prix (CASCADE)"
    GRAND_PRIX ||--o{ SESSION : "sessions (CASCADE)"

    CATEGORY {
        bigint id PK
        varchar title
        slug slug UK
    }
    ARTICLE {
        bigint id PK
        varchar title
        slug slug UK
        bigint author_id FK
        bigint category_id FK
        text lead
        text body "SummernoteTextField"
        varchar featured_image
        varchar status "draft | published"
        datetime created_at
        datetime updated_at
        bigint related_grand_prix_id FK
    }
    CIRCUIT {
        bigint id PK
        varchar name
        varchar location
        varchar country
        decimal length_km
        smallint corners
        varchar lap_record
        varchar image
    }
    TEAM {
        bigint id PK
        varchar name
        varchar full_name
        varchar base
        varchar team_chief
        varchar power_unit
        varchar color_code
        varchar logo
        varchar car_image
        text bio
    }
    DRIVER {
        bigint id PK
        varchar first_name
        varchar last_name
        smallint permanent_number UK
        varchar code UK "3-char FIA code"
        varchar country
        date date_of_birth
        bigint team_id FK
        varchar portrait
        text bio
    }
    DRIVER_STANDING {
        bigint id PK
        bigint season_id FK
        bigint driver_id FK
        smallint position
        decimal points
        smallint wins
    }
    TEAM_STANDING {
        bigint id PK
        bigint season_id FK
        bigint team_id FK
        smallint position
        decimal points
        smallint wins
    }
    SEASON {
        bigint id PK
        smallint year UK
        boolean is_current
    }
    GRAND_PRIX {
        bigint id PK
        bigint season_id FK
        smallint round_number
        varchar name
        bigint circuit_id FK
        date start_date
        date end_date
    }
    SESSION {
        bigint id PK
        bigint grand_prix_id FK
        varchar session_type
        datetime start_time
    }
    SESSION_RESULT {
        bigint id PK
        bigint session_id FK
        bigint driver_id FK
        bigint team_id FK
        smallint position
        varchar status "finished | dnf | dns | dsq"
        smallint grid_position
        smallint laps
        varchar time_or_gap
        varchar q1_time
        varchar q2_time
        varchar q3_time
        decimal points
        boolean fastest_lap
    }
```

---

## 6. Request Lifecycle

```mermaid
sequenceDiagram
    participant Browser
    participant URLs as config/urls.py
    participant View as App View (FBV)
    participant ORM as Django ORM (SQLite/PostgreSQL)
    participant Tpl as RTL Django Template

    Browser->>URLs: HTTP GET (e.g. /, /news/, /racing/drivers/VER/)
    URLs->>View: Dispatch to apps.<app>.views
    View->>ORM: Query with select_related / prefetch_related
    ORM-->>View: Model instances
    View->>Tpl: render(request, '<app>/<template>.html', context)
    Tpl->>Tpl: Extend templates/base.html (RTL, Vazirmatn, Tailwind)
    Tpl-->>Browser: Rendered HTML response
```

1. **URL Routing (`config/urls.py`):**
   - `/admin/` $\rightarrow$ Django Admin (with `SummernoteModelAdmin` and inline-editable standings/sessions).
   - `/` and `/news/...` $\rightarrow$ `apps.news.urls` (`namespace='news'`).
   - `/calendar/...` $\rightarrow$ `apps.grandprix_calendar.urls` (`namespace='grandprix_calendar'`).
   - `/racing/...` $\rightarrow$ `apps.racing.urls` (`namespace='racing'`).
   - `/summernote/...` $\rightarrow$ `django_summernote.urls` (editor iframe and authenticated image/file uploads).
   - `/sitemap.xml` $\rightarrow$ `django.contrib.sitemaps.views.sitemap`.
   - `/__debug__/...` $\rightarrow$ `debug_toolbar.urls` (only when `DEBUG=True` and `django-debug-toolbar` is installed).
2. **Active Season Resolution Pattern:**
   Views in `apps.news`, `apps.racing`, and `apps.grandprix_calendar` resolve the active season using:
   ```python
   current_season = (
       Season.objects.filter(is_current=True).first()
       or Season.objects.order_by('-year').first()
   )
   ```
   This guarantees graceful fallback to the most recent season year if no season has `is_current=True`.
3. **ORM Query Optimization:**
   Every view preloads foreign keys (`select_related`) and reverse/many-to-many relations (`prefetch_related`) before rendering templates to prevent N+1 queries.
4. **Template Rendering (`templates/`):**
   All templates extend `templates/base.html`, which sets `<html lang="fa" dir="rtl">`, loads Tailwind CSS and the Vazirmatn font, and provides the sticky header, mobile drawer navigation, and footer.
