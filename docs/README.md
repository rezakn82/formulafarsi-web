# FormulaFarsi Documentation

Technical documentation for the **FormulaFarsi (PitStop News)** platform.

> [!IMPORTANT]
> **The Code is the Single Source of Truth.**
> Every document in `docs/` must accurately reflect the real, current codebase—never outdated designs, assumptions, or unimplemented plans (unfinished items belong strictly in [`TODO.md`](TODO.md)). Whenever a conflict exists between documentation and code, the code is authoritative and the documentation must be updated immediately.

---

## 📁 Documentation Structure

```text
docs/
├── README.md                        # Documentation index, formatting rules, and update workflow
├── architecture.md                  # System-wide architecture, ER diagram, dependency graph, and request flow
├── TODO.md                          # Known bugs, technical debt, and planned features
└── modules/
    ├── news.md                      # Editorial articles, categories, Summernote integration, and sitemaps
    ├── racing.md                    # Circuits, constructor teams, drivers, and championship standings
    └── grandprix_calendar.md        # F1 seasons, Grands Prix, and weekend session schedules
```

| Document | Scope & Purpose |
| :--- | :--- |
| [`architecture.md`](architecture.md) | High-level stack, directory layout, `config/env.py` loading priority, cross-app dependency map, Entity-Relationship diagram, request lifecycle, and RTL frontend architecture. |
| [`TODO.md`](TODO.md) | Verified bugs/edge cases in the current codebase, missing test coverage, security/production hardening tasks, and planned product features. |
| [`modules/news.md`](modules/news.md) | Deep dive into `apps.news`: `Category` and `Article` models, smart relational tagging, search/filter/pagination, Summernote rich-text setup, and XML sitemaps. |
| [`modules/racing.md`](modules/racing.md) | Deep dive into `apps.racing`: `Circuit`, `Team`, `Driver`, `DriverStanding`, and `TeamStanding` models, views, queryset optimizations, and inline-editable Admin tables. |
| [`modules/grandprix_calendar.md`](modules/grandprix_calendar.md) | Deep dive into `apps.grandprix_calendar`: `Season`, `GrandPrix`, and `Session` models, active season resolution, weekend timetables, and inline session Admin. |

---

## 📐 Module Documentation Format (`docs/modules/<app_name>.md`)

Every Django app inside `apps/` must have a corresponding `<app_name>.md` file in `docs/modules/` containing the following standardized sections:

1. **Overview & Purpose:** What domain problem the app solves and how other apps interact with it.
2. **Models & Database Schema:** Field-by-field breakdown, relationships (`ForeignKey`, `ManyToManyField`), constraints (`unique_together`, `ordering`), and helper methods/properties.
3. **File-by-File Architecture:** Every file in `apps/<app_name>/` and its exact responsibility.
4. **Views, Business Logic & Query Optimization:** How each view queries the database (`select_related`, `prefetch_related`), filters data, and builds template context.
5. **URLs & Templates:** Exact route patterns, URL namespaces (`app_name:view_name`), parameters, and rendered templates.
6. **Django Admin Configuration:** Registered `ModelAdmin` classes, `SummernoteModelAdmin` fields, inlines, `list_editable`, `prepopulated_fields`, and filters.
7. **Testing:** Existing tests, how to run them (`uv run pytest apps/<app_name>`), and key scenarios to test.
8. **Known Limitations & TODOs:** Current edge cases specific to that module (linked to [`TODO.md`](TODO.md)).

---

## 🔄 How and When to Update Documentation

**Rule:** Any code change that alters models, views, URLs, admin behavior, settings, or templates **must update the corresponding documentation in the same change**.

### Checklist After Making Code Changes
1. **Added or modified a model field, relation, or constraint?**
   - Update `docs/modules/<app_name>.md` (Models section).
   - Update the ER diagram in [`docs/architecture.md`](architecture.md) if relationships or entities changed.
2. **Added or modified a view, queryset, URL route, or template?**
   - Update `docs/modules/<app_name>.md` (Views, URLs & Templates sections).
   - Update [`README.md`](../README.md) if a top-level user-facing route was added or changed.
3. **Added a new Django app under `apps/`?**
   - Create `docs/modules/<new_app>.md` following the standard template above.
   - Register the new module in this index (`docs/README.md`), [`docs/architecture.md`](architecture.md), and [`GEMINI.md`](../GEMINI.md).
4. **Changed environment variables or third-party integrations in `config/`?**
   - Update [`docs/architecture.md`](architecture.md), [`env/.env.example`](../env/.env.example), and [`README.md`](../README.md).
5. **Fixed a bug or implemented a feature listed in `docs/TODO.md`?**
   - Remove or check off the completed item in [`docs/TODO.md`](TODO.md) and document the new behavior in the relevant module page.
