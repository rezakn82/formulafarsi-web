# Project TODOs, Known Bugs & Roadmap

This document tracks verified issues in the current codebase, missing test coverage, and planned enhancements for **FormulaFarsi**.

> [!NOTE]
> When an item below is fixed or implemented, remove it from this file and update the corresponding module documentation in [`docs/modules/`](modules/) in the same commit.

---

## 🐛 Bugs & Codebase Edge Cases to Fix

- [ ] **Clickable Relational Tags on Article Detail (`apps.news`):**
  - In [`templates/news/article_detail.html`](../templates/news/article_detail.html#L75-L91), tagged `related_drivers`, `related_teams`, and `related_grand_prix` are rendered as non-clickable `<span>` elements.
  - **Fix:** Convert them into `<a>` links pointing to `{% url 'racing:driver_detail' driver.code %}`, `{% url 'racing:team_detail' team.pk %}`, and `{% url 'grandprix_calendar:grandprix_detail' article.related_grand_prix.round_number %}`.

- [ ] **Render Teammate Comparison on Driver Detail (`apps.racing`):**
  - [`apps/racing/views.py`](../apps/racing/views.py#L19-L21) queries `teammates` and passes it in the `driver_detail_view` context, but [`templates/racing/driver_detail.html`](../templates/racing/driver_detail.html) never renders `teammates`.
  - **Fix:** Add a "هم‌تیمی (Teammate)" section/card to `driver_detail.html`.

---

## 🧪 Testing & Quality Assurance

- [ ] **Write Unit & Integration Tests (`pytest`):**
  - `apps/news/tests.py`, `apps/racing/tests.py`, and `apps/grandprix_calendar/tests.py` are currently empty placeholders.
  - **Add tests for:**
    - `apps.news`: Home view context (`next_session`, `featured_article`, `top_drivers`), draft vs. published filtering (`404` on draft `article_detail_view`), search (`?q=`), category filtering (`?category=`), pagination, related articles query, and `/sitemap.xml` generation.
    - `apps.racing`: `Driver.full_name` property, case-insensitive driver code lookup (`/racing/drivers/ver/`), `teammates` exclusion, `standings_view` ordering, and `unique_together` constraints on `DriverStanding` and `TeamStanding`.
    - `apps.grandprix_calendar`: Active season fallback logic (`is_current=True` vs. latest `year`), `calendar_view`, and `grandprix_detail_view` 404 handling for invalid rounds.

---

## 🚀 Planned Features & Enhancements

- [ ] **Grand Prix Sitemap (`apps.news.sitemaps`):**
  - Add `GrandPrixSitemap` and implement `GrandPrix.get_absolute_url()` so `/calendar/round-<n>/` pages are indexed in `/sitemap.xml`.
- [ ] **Slug URLs for Teams & Circuits (`apps.racing`):**
  - Add `slug` fields to `Team` and `Circuit` so team URLs use `/racing/teams/<slug>/` (e.g. `/racing/teams/ferrari/`) instead of integer primary keys.
- [ ] **Season Selector on Standings & Calendar (`apps.racing` & `apps.grandprix_calendar`):**
  - Allow users to switch seasons via `?season=2025` on `/racing/standings/` and `/calendar/` to view historical championship results and calendars.
- [ ] **Persian (Jalali / Solar Hijri) Date Filter:**
  - Add `jdatetime` or custom template filters to display Persian Solar Hijri dates alongside Gregorian dates for news articles and race sessions.
- [ ] **Production Static & Media Serving:**
  - Add `whitenoise` for compressed static file serving and `Dockerfile` / `compose.yaml` for containerized deployment with PostgreSQL.
