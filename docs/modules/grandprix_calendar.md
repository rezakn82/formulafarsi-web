# Module: `grandprix_calendar` (`apps.grandprix_calendar`)

`apps.grandprix_calendar` manages Formula 1 championship seasons (`Season`), race weekends (`GrandPrix`), individual track sessions (`Session` — Practice, Qualifying, Sprint, and Main Race), and official session classification results (`SessionResult`).

---

## 1. Purpose

- Track F1 championship seasons (`Season`) and designate the active season (`is_current=True`).
- Organize the season calendar into sequential rounds (`GrandPrix`), linking each round to its host `Circuit` (`apps.racing.models.Circuit`).
- Schedule every weekend session (`Session`: FP1, FP2, FP3, Sprint Shootout, Sprint, Qualifying, Main Race) with UTC timestamps automatically localized to `Asia/Tehran` in templates.
- Store and display full driver/team classification results (`SessionResult`) for completed sessions, supporting both Qualifying (`Q1`/`Q2`/`Q3`) and Race/Sprint (`grid_position`, `laps`, `time_or_gap`, `points`, `fastest_lap`) formats.
- Power the next-session countdown/banner on the home page (`apps.news.views.home_view`), the season calendar & archive page (`/calendar/`), and individual Grand Prix weekend pages (`/calendar/round-<round_number>/`).

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

- **Constraints & Ordering:** `unique_together = ('grand_prix', 'session_type')`, `ordering = ['start_time']`.

### `SessionResult`
Stores an individual driver's classification result for a specific `Session`.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `session` | `ForeignKey(Session)` | `on_delete=CASCADE`, `related_name='results'` | Parent track session |
| `driver` | `ForeignKey('racing.Driver')` | `on_delete=CASCADE`, `related_name='session_results'` | Participating driver |
| `team` | `ForeignKey('racing.Team')` | `on_delete=CASCADE`, `related_name='session_results'` | Constructor team for that session |
| `position` | `PositiveSmallIntegerField` | Required | Finishing / classification order (`رتبه`) |
| `status` | `CharField(max_length=15)` | Choices: `'finished'`, `'dnf'`, `'dns'`, `'dsq'`; default `'finished'` | Classification status (`وضعیت`) |
| `grid_position` | `PositiveSmallIntegerField` | `null=True`, `blank=True` | Starting grid slot (`خط شروع`) |
| `laps` | `PositiveSmallIntegerField` | Default `0` | Completed laps (`تعداد دورها`) |
| `time_or_gap` | `CharField(max_length=50)` | `blank=True` | Race time or gap to leader (`زمان / فاصله`) |
| `q1_time` | `CharField(max_length=20)` | `blank=True` | Q1 / SQ1 lap time (`زمان Q1 / SQ1`) |
| `q2_time` | `CharField(max_length=