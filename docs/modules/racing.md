# Module: `racing` (`apps.racing`)

`apps.racing` manages the core Formula 1 competition entities: racing circuits (`Circuit`), constructor teams (`Team`), drivers (`Driver`), and per-season championship standings (`DriverStanding`, `TeamStanding`).

---

## 1. Purpose

- Maintain the reference catalog of F1 **Circuits**, **Teams**, and **Drivers**.
- Provide public profile pages for every Driver (`/racing/drivers/<code>/`) and Constructor Team (`/racing/teams/<pk>/`), complete with rich-text biographies, car liveries, teammate comparisons, and tagged news articles from `apps.news`.
- Track and display **Driver Championship** and **Constructor Championship** standings (`/racing/standings/`) per season.
- Provide fast, inline-editable standings tables in Django Admin so editors can update points, positions, and wins immediately after each race weekend.

---

## 2. Models & Database Schema (`apps/racing/models.py`)

### `Circuit`
Represents an F1 racing track used by Grands Prix in `apps.grandprix_calendar`.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `name` | `CharField(max_length=150)` | Required | Circuit name (`نام پیست`) |
| `location` | `CharField(max_length=100)` | Required | City / locality (`شهر / مکان`) |
| `country` | `CharField(max_length=100)` | Required | Host country (`کشور`) |
| `length_km` | `DecimalField(max_digits=5, decimal_places=3)` | Required | Track length in km (e.g., `5.412`) |
| `corners` | `PositiveSmallIntegerField` | Required | Number of turns (`تعداد پیچ‌ها`) |
| `lap_record` | `CharField(max_length=100)` | `blank=True`, `null=True` | Lap record string (`رکورد پیست`) |
| `image` | `ImageField` | `upload_to='circuits/'` | Track layout map image |

### `Team`
Represents an F1 Constructor team.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `name` | `CharField(max_length=100)` | Required | Short team name (`نام تیم`) |
| `full_name` | `CharField(max_length=200)` | `blank=True` | Official commercial entry name |
| `base` | `CharField(max_length=100)` | Required | Team headquarters location |
| `team_chief` | `CharField(max_length=100)` | Required | Team Principal name |
| `power_unit` | `CharField(max_length=100)` | Required | Engine supplier |
| `color_code` | `CharField(max_length=7)` | Default `'#FFFFFF'` | Hex brand color (e.g., `'#E80020'`) used for UI accents |
| `logo` | `ImageField` | `upload_to='teams/logos/'` | Team emblem/logo |
| `car_image` | `ImageField` | `upload_to='teams/cars/'`, `blank=True`, `null=True` | Side-profile car livery image |
| `bio` | `TextField` | `blank=True` | Team history & biography (edited via Summernote in Admin) |

- **`get_absolute_url()`:** Returns `reverse('racing:team_detail', kwargs={'pk': self.pk})`.

### `Driver`
Represents an F1 driver.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `first_name` | `CharField(max_length=50)` | Required | Driver first name |
| `last_name` | `CharField(max_length=50)` | Required | Driver last name |
| `permanent_number` | `PositiveSmallIntegerField` | `unique=True` | FIA permanent race number |
| `code` | `CharField(max_length=3)` | `unique=True` | 3-letter FIA abbreviation (e.g., `VER`, `HAM`, `LEC`) |
| `country` | `CharField(max_length=100)` | Required | Driver nationality |
| `date_of_birth` | `DateField` | Required | Date of birth |
| `team` | `ForeignKey(Team)` | `on_delete=SET_NULL`, `null=True`, `blank=True`, `related_name='drivers'` | Current constructor team |
| `portrait` | `ImageField` | `upload_to='drivers/'` | Driver portrait photo |
| `bio` | `TextField` | `blank=True` | Driver biography (edited via Summernote in Admin) |

- **`full_name` (`@property`):** Returns `f"{self.first_name} {self.last_name}"`.
- **`get_absolute_url()`:** Returns `reverse('racing:driver_detail', kwargs={'code': self.code})`.

### `DriverStanding`
Stores a driver's championship standing for a specific `Season`.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `season` | `ForeignKey('grandprix_calendar.Season')` | `on_delete=CASCADE`, `related_name='driver_standings'` | Championship season |
| `driver` | `ForeignKey(Driver)` | `on_delete=CASCADE`, `related_name='standings'` | Driver |
| `position` | `PositiveSmallIntegerField` | Required | Rank in the table |
| `points` | `DecimalField(max_digits=6, decimal_places=1)` | Default `0.0` | Championship points (supports `.5` half-points) |
| `wins` | `PositiveSmallIntegerField` | Default `0` | Season race wins |

- **Constraints & Ordering:** `unique_together = ('season', 'driver')`, `ordering = ['position', '-points']`.

### `TeamStanding`
Stores a constructor team's championship standing for a specific `Season`.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `season` | `ForeignKey('grandprix_calendar.Season')` | `on_delete=CASCADE`, `related_name='team_standings'` | Championship season |
| `team` | `ForeignKey(Team)` | `on_delete=CASCADE`, `related_name='standings'` | Constructor team |
| `position` | `PositiveSmallIntegerField` | Required | Rank in the table |
| `points` | `DecimalField(max_digits=6, decimal_places=1)` | Default `0.0` | Constructor points |
| `wins` | `PositiveSmallIntegerField` | Default `0` | Season race wins |

- **Constraints & Ordering:** `unique_together = ('season', 'team')`, `ordering = ['position', '-points']`.

---

## 3. File-by-File Architecture

| File | Responsibility |
| :--- | :--- |
| [`apps/racing/apps.py`](../../apps/racing/apps.py) | `RacingConfig` (`name = 'apps.racing'`, `label = 'racing'`). |
| [`apps/racing/models.py`](../../apps/racing/models.py) | Defines `Circuit`, `Team`, `Driver`, `DriverStanding`, and `TeamStanding`. |
| [`apps/racing/views.py`](../../apps/racing/views.py) | Implements driver list/detail, team list/detail, and championship standings views. |
| [`apps/racing/urls.py`](../../apps/racing/urls.py) | URL patterns under `app_name = 'racing'`. |
| [`apps/racing/admin.py`](../../apps/racing/admin.py) | Admin configurations with `SummernoteModelAdmin` and inline-editable standings. |
| [`apps/racing/tests.py`](../../apps/racing/tests.py) | Test module for `apps.racing`. |

---

## 4. Views, Business Logic & Query Optimization (`apps/racing/views.py`)

### `drivers_list_view(request)`
- Queries `Driver.objects.select_related('team').order_by('team__name', 'permanent_number')`.
- Renders [`templates/racing/drivers_list.html`](../../templates/racing/drivers_list.html) with team color accents and driver portraits.

### `driver_detail_view(request, code)`
- Case-insensitive lookup by 3-letter FIA code: `get_object_or_404(Driver.objects.select_related('team'), code__iexact=code)`.
- Computes `teammates`: `driver.team.drivers.exclude(id=driver.id)` when the driver belongs to a team.
- Fetches up to 6 latest published news articles tagged with the driver: `driver.articles.filter(status='published').select_related('category')[:6]`.
- Renders [`templates/racing/driver_detail.html`](../../templates/racing/driver_detail.html).

### `teams_list_view(request)`
- Queries `Team.objects.prefetch_related('drivers').order_by('name')`.
- Renders [`templates/racing/teams_list.html`](../../templates/racing/teams_list.html) showing each constructor, its car livery, and its current drivers without N+1 queries.

### `team_detail_view(request, pk)`
- Fetches `get_object_or_404(Team.objects.prefetch_related('drivers'), pk=pk)`.
- Fetches up to 6 latest published news articles tagged with the team: `team.articles.filter(status='published').select_related('category')[:6]`.
- Renders [`templates/racing/team_detail.html`](../../templates/racing/team_detail.html).

### `standings_view(request)`
- Resolves `current_season` (`Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()`).
- Fetches `driver_standings` with `select_related('driver', 'driver__team').order_by('position')`.
- Fetches `team_standings` with `select_related('team').order_by('position')`.
- Renders [`templates/racing/standings.html`](../../templates/racing/standings.html) with tabbed/dual tables for Drivers and Constructors.

---

## 5. URLs & Templates

Namespace: `racing` (mounted under `/racing/` in `config/urls.py`).

| URL Pattern | View Name | View Function | Template |
| :--- | :--- | :--- | :--- |
| `/racing/standings/` | `racing:standings` | `standings_view` | [`templates/racing/standings.html`](../../templates/racing/standings.html) |
| `/racing/drivers/` | `racing:drivers_list` | `drivers_list_view` | [`templates/racing/drivers_list.html`](../../templates/racing/drivers_list.html) |
| `/racing/drivers/<str:code>/` | `racing:driver_detail` | `driver_detail_view` | [`templates/racing/driver_detail.html`](../../templates/racing/driver_detail.html) |
| `/racing/teams/` | `racing:teams_list` | `teams_list_view` | [`templates/racing/teams_list.html`](../../templates/racing/teams_list.html) |
| `/racing/teams/<int:pk>/` | `racing:team_detail` | `team_detail_view` | [`templates/racing/team_detail.html`](../../templates/racing/team_detail.html) |

---

## 6. Django Admin Configuration (`apps/racing/admin.py`)

- **`CircuitAdmin`:** Displays `('name', 'country', 'length_km')` and searches `('name', 'country')`.
- **`TeamAdmin(SummernoteModelAdmin)`:** Enables Summernote rich-text editor on `bio`; displays `('name', 'team_chief', 'power_unit')`.
- **`DriverAdmin(SummernoteModelAdmin)`:** Enables Summernote rich-text editor on `bio`; displays `('full_name', 'permanent_number', 'code', 'team', 'country')` with team and country filters.
- **`DriverStandingAdmin` & `TeamStandingAdmin`:**
  - `list_editable = ('position', 'points', 'wins')` allows bulk-updating standings directly in the changelist view.
  - Filtered by `season` and ordered by `('season', 'position')`.

---

## 7. Testing

Run tests for this module:
```bash
uv run pytest apps/racing
```

---

## 8. Known Limitations & TODOs

- `driver_detail_view` computes `teammates` in the context, but [`templates/racing/driver_detail.html`](../../templates/racing/driver_detail.html) does not yet render a teammate comparison card (tracked in [`docs/TODO.md`](../TODO.md)).
- `Team` detail URLs currently use integer primary keys (`/racing/teams/<int:pk>/`) rather than a human-readable `slug` field.
- Standings view always shows `current_season` and does not yet accept a `?season=<year>` query parameter to browse historical seasons.
