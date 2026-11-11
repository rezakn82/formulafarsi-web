# 🏎️ FormulaFarsi (PitStop News)

**FormulaFarsi** is a Persian-language Formula 1 and motorsport news, race calendar, and championship standings web application built with **Django 5.2 LTS** and managed with **`uv`**.

It provides an editorial publishing workflow with RTL CKEditor 5 support, smart relational tagging between news articles, drivers, teams, and Grands Prix, live season countdown/session tracking, championship standings tables, and dynamic SEO sitemaps.

---

## ✨ Key Features

- **📰 Motorsport Editorial & News (`apps.news`)**
  - Rich-text Persian (RTL) article authoring powered by **CKEditor 5** (`django-ckeditor-5`) with inline image uploads, headings, tables, and media embeds.
  - Smart relational tagging: link articles to specific **Drivers**, **Teams**, and **Grands Prix** so related news automatically surfaces on driver/team profiles and article detail pages.
  - Full news archive with category filtering, keyword search (across title, lead, and body), and pagination.
  - Dynamic XML sitemaps (`/sitemap.xml`) covering published articles, drivers, teams, and static routes.

- **🏁 Drivers, Teams & Championship Standings (`apps.racing`)**
  - Detailed **Driver** profiles (permanent number, 3-letter FIA code, team affiliation, biography, teammate comparison, and tagged articles).
  - **Constructor (Team)** profiles with custom brand color codes, car liveries, power unit details, driver lineups, and team news.
  - **Circuit** directory with track length, corner count, lap records, and circuit layout maps.
  - **Driver & Constructor Standings** tables per season with inline-editable positions, points, and win counts in Django Admin.

- **📅 Grand Prix Calendar & Sessions (`apps.grandprix_calendar`)**
  - Multi-season support with active season tracking (`is_current`).
  - Full Grand Prix weekend schedules covering **FP1, FP2, FP3, Sprint Shootout, Sprint, Qualifying, and Main Race** sessions.
  - Next upcoming session highlight on the home page.

- **🎨 Responsive RTL Frontend**
  - Built with **Tailwind CSS** and the **Vazirmatn** Persian typeface in a dark motorsport theme (`zinc-950`).
  - Mobile-friendly responsive layout with an animated slide-out hamburger drawer.

---

## 📁 Repository Layout

```text
formulafarsi-web/
├── apps/
│   ├── grandprix_calendar/   # Seasons, Grands Prix, and weekend race sessions
│   ├── news/                 # Articles, categories, CKEditor 5 integration, and sitemaps
│   └── racing/               # Circuits, Teams, Drivers, and Championship Standings
├── config/
│   ├── env.py                # Strict django-environ + python-dotenv loader
│   ├── settings.py           # Project settings driven by environment variables
│   ├── urls.py               # Root URL routing and sitemap registration
│   ├── asgi.py               # ASGI entrypoint
│   └── wsgi.py               # WSGI entrypoint
├── env/
│   ├── .env.example          # Template for environment variables
│   └── .env                  # Local environment configuration (git-ignored)
├── templates/
│   ├── base.html             # Master RTL layout, navigation bar, and mobile drawer
│   ├── grandprix_calendar/   # Calendar list and Grand Prix weekend detail templates
│   ├── news/                 # Home page, article archive, and article detail templates
│   └── racing/               # Standings, drivers list/detail, and teams list/detail templates
├── media/                    # Uploaded images for circuits, drivers, teams, and news (git-ignored)
├── manage.py                 # Django CLI utility
├── pyproject.toml            # Project metadata and dependencies (uv)
├── uv.lock                   # Deterministic dependency lockfile
├── CONTRIBUTING.md           # Commit message and branching conventions
└── LICENSE                   # MIT License
```

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python $\ge 3.13$ |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) |
| **Web Framework** | Django 5.2 LTS (`>5.2,<5.3`) |
| **Environment Config** | `django-environ` + `python-dotenv` |
| **Rich Text Editor** | `django-ckeditor-5` (configured for Persian RTL) |
| **Image Processing** | `Pillow` (WebP, AVIF, PNG, JPEG) |
| **Database** | SQLite 3 (local default) / PostgreSQL ready via `DATABASE_URL` |
| **Frontend Styling** | Django Templates + Tailwind CSS + Vazirmatn Font |

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd formulafarsi-web
```

### 2. Configure Environment Variables
Copy the example environment file to `env/.env` and customize values if needed:
```bash
cp env/.env.example env/.env
```

Key variables in [`env/.env`](env/.env.example):
| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DJANGO_ENV` | Active environment profile (`local`, `docker`, `production`) | `local` |
| `SECRET_KEY` | Mandatory Django cryptographic secret key | *(required)* |
| `DEBUG` | Enable Django debug mode (`True` / `False`) | `True` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins | `http://localhost:8000` |
| `DATABASE_URL` | Database connection URL (`sqlite://` or `postgres://`) | `sqlite:///db.sqlite3` |
| `TIME_ZONE` | Server timezone | `Asia/Tehran` |

### 3. Install Dependencies
Sync the virtual environment (`.venv`) from `uv.lock`:
```bash
uv sync
```

### 4. Apply Database Migrations & Create a Superuser
```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

### 5. Run the Development Server
```bash
uv run python manage.py runserver
```
- **Web Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **XML Sitemap:** [http://127.0.0.1:8000/sitemap.xml](http://127.0.0.1:8000/sitemap.xml)

---

## 🌐 Main Routes

| URL Pattern | App & View | Description |
| :--- | :--- | :--- |
| `/` | `news:home` | Home page with featured story, latest news, next session banner, and top 5 driver standings |
| `/news/` | `news:articles_list` | Full news archive with search (`?q=`), category filter (`?category=`), and pagination |
| `/news/<slug>/` | `news:article_detail` | Article detail page with tagged drivers/teams and related articles |
| `/racing/standings/` | `racing:standings` | Full Driver and Constructor Championship standings for the active season |
| `/racing/drivers/` | `racing:drivers_list` | Grid of all F1 drivers grouped by team |
| `/racing/drivers/<code>/` | `racing:driver_detail` | Driver profile by 3-letter code (e.g., `/racing/drivers/VER/`) |
| `/racing/teams/` | `racing:teams_list` | Constructor teams directory |
| `/racing/teams/<pk>/` | `racing:team_detail` | Constructor profile, car livery, driver lineup, and related news |
| `/calendar/` | `grandprix_calendar:calendar_list` | Full season Grand Prix calendar |
| `/calendar/round-<n>/` | `grandprix_calendar:grandprix_detail` | Grand Prix weekend circuit specs and session timetable |
| `/sitemap.xml` | `django.contrib.sitemaps` | Dynamic SEO sitemap for search engines |

---

## 🧪 Running Checks & Tests

```bash
# Run Django system checks
uv run python manage.py check

# Run test suite across all apps
uv run python manage.py test

# Lint and format Python files with Ruff (excluding migrations)
uvx ruff check apps/ config/ --exclude "*/migrations/*"
```

---

## 🤝 Contributing

We follow a strict commit message and branching convention. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes:

```text
[TAG] (app_name) Capitalized short summary (50 chars or less)

[+] Detail about what was added
[-] Detail about what was removed
[*] Detail about what was changed/refactored
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
