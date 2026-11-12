# Module: `grandprix_calendar` (`apps.grandprix_calendar`)

`apps.grandprix_calendar` manages Formula 1 championship seasons (`Season`), race weekends (`GrandPrix`), and individual track sessions (`Session` — Practice, Qualifying, Sprint, and Main Race).

---

## 1. Purpose

- Track F1 championship seasons (`Season`) and designate the active season (`is_current=True`).
- Organize the season calendar into sequential rounds (`GrandPrix`), linking each round to its host `Circuit` (`apps.racing.models.Circuit`).
- Schedule every weekend session (`Session`: FP1, FP2, FP3, Sprint Shootout, Sprint, Qualifying, Main Race) with UTC timestamps automatically localized to `Asia/Tehran` in templates.
- Power the next-session countdown/banner on the home page (`apps.news.views.home_view`), the season calendar page (`/calendar/`), and individual Grand Prix weekend pages (`/calendar/round-<round_number>/`).

---

## 2. Models & Database Schema (`apps/grandprix_calendar/models.py`)

### `Season`
Represents a Formula 1 championship year (e.g., `2026`).

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `year` | `PositiveSmallIntegerField` | `unique=True` | Championship year (`سال فصل`) |
| `is_current` | `BooleanField` | Default `False` | Marks the currently active season (`فصل جاری است؟`) |

### `GrandPrix`
Represents a single race weekend round within a `Season`.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `season` | `ForeignKey(Season)` | `on_delete=CASCADE`, `related_name='grands_prix'` | Parent championship season |
| `round_number` | `PositiveSmallIntegerField` | Required | Round number in the season calendar (`شماره راند`) |
| `name` | `CharField(max_length=150)` | Required | Grand Prix title (`نام گرندپری`) |
| `circuit` | `ForeignKey('racing.Circuit')` | `on_delete=CASCADE`, `related_name='grands_prix'` | Host racing circuit |
| `start_date` | `DateField` | Required | Opening day of the race weekend |
| `end_date` | `DateField` | Required | Main race day (`تاریخ پایان`) |

- **Constraints & Ordering:** `unique_together = ('season', 'round_number')`, `ordering = ['round_number']`.

### `Session`
Represents an individual on-track session during a `GrandPrix` weekend.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `grand_prix` | `ForeignKey(GrandPrix)` | `on_delete=CASCADE`, `related_name='sessions'` | Parent Grand Prix |
| `session_type` | `CharField(max_length=20)` | Choices: `'fp1'`, `'fp2'`, `'fp3'`, `'qualifying'`, `'sprint_shootout'`, `'sprint'`, `'race'` | Type of session (`نوع جلسه`) |
| `start_time` | `DateTimeField` | Required | Session start timestamp (`زمان شروع`) |

- **Default Ordering:** `ordering = ['start_time']`.

---

## 3. File-by-File Architecture

| File | Responsibility |
| :--- | :--- |
| [`apps/grandprix_calendar/apps.py`](../../apps/grandprix_calendar/apps.py) | `GrandprixCalendarConfig` (`name = 'apps.grandprix_calendar'`, `label = 'grandprix_calendar'`). |
| [`apps/grandprix_calendar/models.py`](../../apps/grandprix_calendar/models.py) | Defines `Season`, `GrandPrix`, and `Session` models. |
| [`apps/grandprix_calendar/views.py`](../../apps/grandprix_calendar/views.py) | Implements `calendar_view` and `grandprix_detail_view`. |
| [`apps/grandprix_calendar/urls.py`](../../apps/grandprix_calendar/urls.py) | URL patterns under `app_name = 'grandprix_calendar'`. |
| [`apps/grandprix_calendar/admin.py`](../../apps/grandprix_calendar/admin.py) | Registers `Season` and `GrandPrixAdmin` with `SessionInline`. |
| [`apps/grandprix_calendar/tests.py`](../../apps/grandprix_calendar/tests.py) | Test module for `apps.grandprix_calendar`. |

---

## 4. Views, Business Logic & Query Optimization (`apps/grandprix_calendar/views.py`)

### `calendar_view(request)`
Serves the full season race calendar (`templates/grandprix_calendar/calendar_list.html`):
- Resolves `current_season` via `Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()`.
- Queries `GrandPrix.objects.filter(season=current_season).select_related('circuit').prefetch_related('sessions').order_by('round_number')`.
- Passes `today = timezone.now().date()` so the template can visually distinguish completed Grands Prix (`end_date < today`) from upcoming ones.

### `grandprix_detail_view(request, round_number)`
Serves the detailed schedule and circuit specifications for a single Grand Prix round (`templates/grandprix_calendar/grandprix_detail.html`):
- Resolves `current_season`.
- Fetches the `GrandPrix` with `select_related('circuit', 'season').prefetch_related('sessions')` matching `(season=current_season, round_number=round_number)` or raises HTTP 404.
- Passes `now = timezone.now()` so the template can mark past sessions vs. upcoming sessions.

---

## 5. URLs & Templates

Namespace: `grandprix_calendar` (mounted under `/calendar/` in `config/urls.py`).

| URL Pattern | View Name | View Function | Template |
| :--- | :--- | :--- | :--- |
| `/calendar/` | `grandprix_calendar:calendar_list` | `calendar_view` | [`templates/grandprix_calendar/calendar_list.html`](../../templates/grandprix_calendar/calendar_list.html) |
| `/calendar/round-<int:round_number>/` | `grandprix_calendar:grandprix_detail` | `grandprix_detail_view` | [`templates/grandprix_calendar/grandprix_detail.html`](../../templates/grandprix_calendar/grandprix_detail.html) |

---

## 6. Django Admin Configuration (`apps/grandprix_calendar/admin.py`)

- **`SessionInline(admin.TabularInline)`:** Embedded inside `GrandPrixAdmin` with `extra = 5` so all 5 weekend sessions (FP1, FP2, FP3/Sprint, Qualifying, Main Race) can be entered on a single screen when creating a Grand Prix.
- **`GrandPrixAdmin`:** Displays `('name', 'season', 'round_number', 'start_date', 'end_date')`, filtered by `season`.
- **`Season`:** Registered via `admin.site.register(Season)`.

---

## 7. Testing

Run tests for this module:
```bash
uv run pytest apps/grandprix_calendar
```

---

## 8. Known Limitations & TODOs

- `Season.is_current` does not yet enforce in `Season.save()` or via a unique partial constraint that only **one** season can have `is_current=True` at a time (tracked in [`docs/TODO.md`](../TODO.md)).
- `grandprix_detail_view` does not yet display related news articles (`grand_prix.articles.filter(status='published')`) even though `Article.related_grand_prix` is linked to `GrandPrix`.
- `GrandPrix` detail URLs are not yet included in `apps/news/sitemaps.py`.
