# Project TODOs, Known Bugs & Roadmap

This document tracks verified security gaps, bugs, deployment/operational improvements, missed best practices, test coverage gaps, and planned features for **FormulaFarsi**.

> [!NOTE]
> When an item below is fixed or implemented, remove or check it off in this file and update the corresponding module documentation in [`docs/modules/`](modules/) in the same commit.

---

## 🔒 Security Settings & Hardening

- [ ] **Sanitize Rich-Text HTML Before Rendering (`|safe` / Stored XSS Risk):**
  - `SummernoteTextField` is commented out in [`apps/news/models.py`](../apps/news/models.py#L4) and `Article.body`, `Driver.bio`, and `Team.bio` are plain `models.TextField` fields, yet [`templates/news/article_detail.html`](../templates/news/article_detail.html#L55), [`templates/racing/driver_detail.html`](../templates/racing/driver_detail.html#L61), and [`templates/racing/team_detail.html`](../templates/racing/team_detail.html#L87) render them with `|safe`.
  - `ALLOWED_TAGS` and `ATTRIBUTES` in [`config/settings/base.py`](../config/settings/base.py#L194-L273) are never enforced on save, and `bleach` / `nh3` is not in [`pyproject.toml`](../pyproject.toml). Furthermore, `ALLOWED_TAGS` permits arbitrary `<iframe>` (`src`) and `*` `style` attributes.
  - **Fix:** Add `nh3` (or `bleach`), sanitize `Article.body`, `Driver.bio`, and `Team.bio` via a shared helper on save/form validation, and restrict `iframe` `src` to an explicit embed-domain allowlist.
- [ ] **Validate `Team.color_code` to Prevent CSS Injection:**
  - [`apps/racing/models.py`](../apps/racing/models.py#L27) accepts any 7-character string in `color_code`, which is injected into inline `style="background-color: ...;"` across multiple templates (`home.html`, `drivers_list.html`, `driver_detail.html`, `teams_list.html`, `team_detail.html`, `standings.html`, `grandprix_detail.html`, `search_results.html`).
  - **Fix:** Add `RegexValidator(r"^#[0-9A-Fa-f]{6}$")` to `Team.color_code`.
- [ ] **Restrict Summernote Attachment Uploads & Harden `/media/` Serving:**
  - [`config/settings/base.py`](../config/settings/base.py#L190) sets `"attachment_require_authentication": True` without restricting uploads to `is_staff` users or validating allowed file extensions/MIME types (e.g., blocking `.svg` / HTML uploads).
  - [`docker/nginx/default.conf`](../docker/nginx/default.conf#L17-L22) serves `/media/` without `X-Content-Type-Options: nosniff` or blocking script/SVG execution.
  - **Fix:** Enforce staff-only upload checks and strict image extension validation in Summernote, and add `add_header X-Content-Type-Options "nosniff" always;` + safe MIME handling in Nginx.
- [ ] **Replace Play CDN Tailwind & External Font CDNs for Production CSP:**
  - [`templates/base.html`](../templates/base.html#L9-L11) loads `https://cdn.tailwindcss.com` (runtime JS compiler, not production-grade) and `cdn.jsdelivr.net` Vazirmatn CSS without Subresource Integrity (`integrity`/`crossorigin`), and [`static/css/admin-custom.css`](../static/css/admin-custom.css#L2) also imports from `cdn.jsdelivr.net`.
  - **Fix:** Build compiled static Tailwind CSS (`tailwindcss` CLI) and self-host Vazirmatn font files under `static/`, then enforce `Content-Security-Policy` and `Permissions-Policy` headers in [`config/settings/production.py`](../config/settings/production.py) and Nginx.
- [ ] **Add `rel="noopener noreferrer"` on External Links:**
  - [`templates/news/article_detail.html`](../templates/news/article_detail.html#L32-L34) uses `target="_blank"` on the Telegram share link without `rel="noopener noreferrer"`.
- [ ] **Harden Admin Authentication & Seed Command Guardrails:**
  - Add login rate limiting (`django-axes` or Nginx `limit_req` on `ADMIN_URL`) and consider `CSRF_COOKIE_HTTPONLY = True` in [`config/settings/production.py`](../config/settings/production.py).
  - [`apps/racing/management/commands/seed_data.py`](../apps/racing/management/commands/seed_data.py#L68) creates `admin` with hardcoded password `admin1234` and has no guard preventing `--flush` or seeding when `DEBUG` is `False` (production).
  - **Fix:** Refuse to run `seed_data` when `not settings.DEBUG` unless an explicit `--force` flag is passed, and read/generate the seed password securely.

---

## 🐛 Bugs & Codebase Edge Cases to Fix

- [ ] **Mismatched `sprint_qualifying` vs. `sprint_shootout` Session Type:**
  - [`apps/grandprix_calendar/models.py`](../apps/grandprix_calendar/models.py#L54) defines `'sprint_qualifying'`, whereas [`templates/grandprix_calendar/grandprix_detail.html`](../templates/grandprix_calendar/grandprix_detail.html#L59) (and line 112) and [`apps/racing/management/commands/seed_data.py`](../apps/racing/management/commands/seed_data.py#L194) check/insert `'sprint_shootout'`.
  - **Impact:** Sprint Qualifying results do not display Q1/Q2/Q3 columns in `grandprix_detail.html`, and `seed_data` creates invalid choice values.
- [ ] **Unescaped Query Params in News Archive Filters & Share Links:**
  - [`templates/news/articles_list.html`](../templates/news/articles_list.html#L26) (and pagination links on lines 84 and 95) builds `?category={{ cat.slug }}&q={{ search_query }}` without `|urlencode`, and [`templates/news/article_detail.html`](../templates/news/article_detail.html#L32) does not `|urlencode` `request.build_absolute_uri`.
- [ ] **Persian Slug ZWNJ Edge Case in `apps.news`:**
  - [`apps/news/urls.py`](../apps/news/urls.py#L10) uses `re_path(r'^news/(?P<slug>[-\w]+)/$', ...)`. If a Persian slug contains a Zero-Width Non-Joiner (`\u200c`), `reverse()` raises `NoReverseMatch` and requests return `404`.
  - **Fix:** Normalize/strip `\u200c` on `Category.slug` and `Article.slug` clean/save, or update the route pattern.
- [ ] **Unserved `/media/` Uploads in Local `compose.yaml` (`DEBUG = False`):**
  - [`config/urls.py`](../config/urls.py#L48-L49) only serves `MEDIA_URL` when `settings.DEBUG` is `True`. Under [`compose.yaml`](../compose.yaml) (`config.settings.docker`, `DEBUG = False`, no Nginx service), uploaded images under `/media/` return `404`.
  - **Fix:** Add an Nginx service (or media proxy) to [`compose.yaml`](../compose.yaml) so `/media/` works in local Docker runs too.
- [ ] **UTC vs. Local Date Mismatch in `calendar_view`:**
  - [`apps/grandprix_calendar/views.py`](../apps/grandprix_calendar/views.py#L37) uses `timezone.now().date()` (UTC date) instead of `timezone.localdate()` (`Asia/Tehran`), causing race weekend status badges (`در حال برگزاری`) to lag by 3.5 hours around midnight Tehran time.
- [ ] **Unused Querysets / Unrendered Context Data:**
  - **Teammates (`apps.racing`):** [`apps/racing/views.py`](../apps/racing/views.py#L22-L24) queries `teammates` for `driver_detail_view`, but [`templates/racing/driver_detail.html`](../templates/racing/driver_detail.html) never renders them.
  - **Related Grand Prix News (`apps.grandprix_calendar`):** [`apps/grandprix_calendar/views.py`](../apps/grandprix_calendar/views.py#L68) queries `related_articles` for `grandprix_detail_view`, but [`templates/grandprix_calendar/grandprix_detail.html`](../templates/grandprix_calendar/grandprix_detail.html) never renders them.
- [ ] **Null Category Bug & Expensive Distinct Join in `article_detail_view`:**
  - [`apps/news/views.py`](../apps/news/views.py#L55-L61) includes `Q(category=article.category)` even when `article.category` is `None`, matching unrelated uncategorized articles. Also [`templates/news/article_detail.html`](../templates/news/article_detail.html#L121) renders `rel.category.title` without an `{% if rel.category %}` guard.
- [ ] **Invalid `?season=` Query Fallback & Empty Season Title Display:**
  - [`apps/grandprix_calendar/views.py`](../apps/grandprix_calendar/views.py#L7-L13) silently falls back to the current season on unknown `?season=9999` values instead of returning `404`.
  - [`templates/racing/standings.html`](../templates/racing/standings.html#L15) and [`templates/grandprix_calendar/calendar_list.html`](../templates/grandprix_calendar/calendar_list.html#L15) render `"فصل "` when no `Season` exists in the database.
- [ ] **`SeasonAdmin` Bulk `is_current` Update Risk:**
  - [`apps/grandprix_calendar/admin.py`](../apps/grandprix_calendar/admin.py#L49) exposes `list_editable = ('is_current',)`; toggling multiple rows or running queryset `.update(is_current=True)` bypasses `Season.save()` and risks `IntegrityError` from `unique_current_season`.
- [ ] **Frontend JS & Template Bugs:**
  - [`templates/news/home.html`](../templates/news/home.html#L176-L192): `setInterval(updateCountdown, 1000)` never calls `clearInterval()` when `distance < 0`, and lacks an `isNaN(targetDate)` guard.
  - [`templates/base.html`](../templates/base.html#L69): Uses non-existent Tailwind class `text-white-600`, hardcodes `© 2026` on line 135, and lacks `Escape`-key close, `aria-expanded`, and focus management for the mobile drawer.
  - [`templates/racing/drivers_list.html`](../templates/racing/drivers_list.html#L11): Hardcodes `"GRID 2026"` instead of using the active season year.
- [ ] **Container Healthcheck Host & DB Overhead:**
  - [`compose.yaml`](../compose.yaml#L35-L47) and [`compose.prod.yaml`](../compose.prod.yaml#L27-L36) probe `/sitemap.xml` (4 DB queries per probe and fails if `ALLOWED_HOSTS` starts with a leading-dot wildcard like `.formulafarsi.ir`).
  - **Fix:** Add a dedicated lightweight `/healthz/` endpoint checking DB readiness (`SELECT 1`).

---

## 🚢 Deployment Flow & Operations

- [ ] **Add CI/CD Workflow (`.github/workflows/`):**
  - Add GitHub Actions checks on push/PR for `uvx ruff check`, `uv run pytest`, `manage.py check --deploy`, and Docker image builds.
- [ ] **Separate Migrations from App Startup in Multi-Replica Deploys:**
  - [`docker/entrypoint.sh`](../docker/entrypoint.sh#L28-L34) runs `migrate --noinput` and `collectstatic --noinput` on every container start, which can race when running multiple `web` replicas. Add a dedicated release step / lock or document setting `RUN_MIGRATIONS=false` on extra replicas.
- [ ] **Add TLS/HTTPS Automation & Compression in Nginx:**
  - [`docker/nginx/default.conf`](../docker/nginx/default.conf) only listens on port `80` (assuming an external TLS proxy), lacks `gzip on;`, and has no Certbot/Let's Encrypt (`/.well-known/acme-challenge/`) or Caddy TLS profile documented for standalone VPS deploys.
- [ ] **Operational Reliability (Backups, Log Rotation, Error Tracking):**
  - Configure Docker `logging` rotation (`max-size` / `max-file`) in `compose.yaml` / `compose.prod.yaml`.
  - Add automated PostgreSQL backup/restore scripts and optional object storage (`django-storages` for S3/MinIO) for `/media/`.
  - Add optional Sentry integration in `config/settings/production.py` gated by `SENTRY_DSN`.

---

## ⚙️ Code Quality, Performance & Missed Best Practices

- [ ] **Fix 44 Ruff Lint Violations in `apps/`:**
  - `uvx ruff check apps/ config/ manage.py` currently reports 44 issues (`31` `RUF012`, `9` `I001`, `3` `F401`, `1` `RUF059` in `apps/racing/management/commands/seed_data.py#L73`). Clean imports, remove unused boilerplate `TestCase` imports, and decide on `RUF012` annotations/ignores in `pyproject.toml`.
- [ ] **Add Database Indexes & Modern Constraints:**
  - Add `Meta.indexes` on `Article(status, -created_at)`, `Session(start_time)`, `DriverStanding(season, position)`, and `TeamStanding(season, position)`.
  - Migrate deprecated `Meta.unique_together` in `GrandPrix`, `SessionResult`, `DriverStanding`, and `TeamStanding` to `Meta.constraints = [models.UniqueConstraint(...)]`, and add `UniqueConstraint(fields=['grand_prix', 'session_type'])` on `Session`.
- [ ] **Add Model Validation & Normalization (`clean()`):**
  - Validate `GrandPrix.end_date >= GrandPrix.start_date`, `SessionResult.position >= 1`, normalize `Driver.code = self.code.upper()`, and raise `SessionResult.points` `max_digits` from `4` to `5`/`6` for consistency.
  - Keep `standings_view` ordering aligned with `Meta.ordering` (`order_by('position', '-points')`) in [`apps/racing/views.py`](../apps/racing/views.py#L71).
- [ ] **Add Custom Error Pages (`404.html`, `500.html`), `robots.txt`, & SEO Meta Tags:**
  - Create dark RTL `templates/404.html` and `templates/500.html` templates (currently missing in `templates/` when `DEBUG = False`).
  - Add `/robots.txt` referencing `/sitemap.xml`.
  - Add Open Graph (`og:title`, `og:description`, `og:image`), Twitter Card, `<link rel="canonical">`, and favicon tags in [`templates/base.html`](../templates/base.html) and [`templates/news/article_detail.html`](../templates/news/article_detail.html).
- [ ] **Configure Caching (`CACHES`) & Sitemap Optimization:**
  - Add optional Redis cache configuration (`REDIS_URL` / `django.core.cache`) for home page, standings, and `sitemap.xml`, and optimize `sitemaps.py` querysets.
- [ ] **Improve URL State & Pagination UX:**
  - Sync `standings.html` tab state (`?tab=teams` or URL hash) so refreshing or sharing Constructors standings preserves the active tab.
  - Add numbered page links and total result counts in `articles_list.html`.

---

## 🧪 Testing & Quality Assurance

- [ ] **Write Unit & Integration Tests (`pytest`):**
  - `apps/news/tests.py`, `apps/racing/tests.py`, and `apps/grandprix_calendar/tests.py` are currently empty placeholders.
  - **Add tests for:**
    - `apps.news`: Home view context (`next_session`, `featured_article`, `top_drivers`), draft vs. published filtering (`404` on draft `article_detail_view`), search (`?q=`), `global_search_view`, category filtering (`?category=`), Unicode/ZWNJ slug routing, pagination, related articles query (including null category), `jalali_tags`, HTML sanitization, and `/sitemap.xml` generation.
    - `apps.racing`: `Driver.full_name` property, case-insensitive driver code lookup (`/racing/drivers/ver/`), `teammates` exclusion, `Team.color_code` validator, `standings_view` ordering, and unique constraints on `DriverStanding` and `TeamStanding`.
    - `apps.grandprix_calendar`: Active season fallback & `UniqueConstraint` enforcement, `calendar_view` (`timezone.localdate()`), `grandprix_detail_view` `404` handling for invalid rounds/seasons, `sprint_qualifying` rendering, and N+1 query regression assertions (`django_assert_num_queries`).

---

## 🚀 Planned Features & Enhancements

- [ ] **Grand Prix Sitemap (`apps.news.sitemaps`):**
  - Add `GrandPrixSitemap` and implement `GrandPrix.get_absolute_url()` so `/calendar/round-<n>/` pages are indexed in `/sitemap.xml`.
- [ ] **Slug URLs for Teams & Circuits (`apps.racing`):**
  - Add `slug` fields to `Team` and `Circuit` so team URLs use `/racing/teams/<slug>/` (e.g. `/racing/teams/ferrari/`) instead of integer primary keys, and add a dedicated `/racing/circuits/` directory view.
- [ ] **Season Selector on Standings (`apps.racing`):**
  - Allow users to switch seasons via `?season=2025` on `/racing/standings/` to view historical championship results.
- [ ] **Auto-Calculate Standings from `SessionResult`:**
  - Add a Django management command and/or admin action to aggregate points and wins from `race` and `sprint` `SessionResult` records into `DriverStanding` and `TeamStanding` for a season.
- [ ] **F1 Data Sync Command (Jolpica / Ergast / OpenF1 API):**
  - Build a management command to import/update season calendars, session timestamps, qualifying/race results, and standings from an external F1 API to reduce manual data entry.
- [ ] **RSS / Atom Feed & Editorial Publishing Enhancements:**
  - Add `/news/feed/` (`django.contrib.syndication.views.Feed`), scheduled `published_at` timestamps, staff draft preview support, reading-time estimation, and optional Telegram channel auto-posting on publish.
- [ ] **Expanded Driver & Team Stats:**
  - Show season-by-season race results and career totals (wins, poles, podiums, points) on `driver_detail.html` and `team_detail.html`.
