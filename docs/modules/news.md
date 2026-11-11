# Module: `news` (`apps.news`)

`apps.news` powers the editorial core of FormulaFarsi: Persian-language motorsport news articles, categories, rich-text authoring via `django-summernote`, smart relational tagging to drivers/teams/Grands Prix, the home page dashboard, and the site-wide XML sitemaps.

---

## 1. Purpose

- Publish and categorize Formula 1 news articles (`Article`, `Category`) with draft/published workflow control.
- Connect editorial content to domain entities (`Driver`, `Team`, `GrandPrix`) so related articles automatically appear on driver profiles, team profiles, and article detail pages.
- Serve the main landing page (`/`) combining breaking news, the next upcoming Grand Prix session countdown banner, and the top 5 Driver Championship standings.
- Provide a searchable, filterable, paginated news archive (`/news/`).
- Expose dynamic XML sitemaps (`/sitemap.xml`) for search engine indexing across all public routes.

---

## 2. Models & Database Schema (`apps/news/models.py`)

### `Category`
Represents a topical news category (e.g., Technical Analysis, Race Reports, Driver Market).

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `title` | `CharField(max_length=80)` | Required | Persian category title (`عنوان دسته‌بندی`) |
| `slug` | `SlugField` | `unique=True`, `allow_unicode=True` | URL slug supporting Persian/Unicode characters |

### `Article`
Represents a news article with rich-text HTML body and relational tags.

| Field | Type | Constraints / Options | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-generated ID |
| `title` | `CharField(max_length=250)` | Required | Article headline (`عنوان خبر`) |
| `slug` | `SlugField(max_length=250)` | `unique=True`, `allow_unicode=True` | Unicode-aware URL slug |
| `author` | `ForeignKey(User)` | `on_delete=PROTECT`, `related_name='articles'` | Publishing author |
| `category` | `ForeignKey(Category)` | `on_delete=SET_NULL`, `null=True`, `related_name='articles'` | Primary article category |
| `lead` | `TextField(max_length=500)` | Required | Short summary / lead paragraph (`لید / خلاصه خبر`) |
| `body` | `SummernoteTextField` | Required, sanitized via `bleach` | Full HTML article content (`متن کامل خبر`) |
| `featured_image` | `ImageField` | `upload_to='news/%Y/%m/'` | Cover image |
| `status` | `CharField(max_length=10)` | Choices: `'draft'`, `'published'`; default `'draft'` | Publication state |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Creation timestamp |
| `updated_at` | `DateTimeField` | `auto_now=True` | Last modification timestamp |
| `related_drivers` | `ManyToManyField(Driver)` | `blank=True`, `related_name='articles'` | Tagged F1 drivers |
| `related_teams` | `ManyToManyField(Team)` | `blank=True`, `related_name='articles'` | Tagged constructor teams |
| `related_grand_prix` | `ForeignKey(GrandPrix)` | `on_delete=SET_NULL`, `null=True`, `blank=True`, `related_name='articles'` | Tagged Grand Prix event |

- **Default Ordering:** `ordering = ['-created_at']` (newest articles first).
- **`get_absolute_url()`:** Returns `reverse('news:article_detail', kwargs={'slug': self.slug})`.

---

## 3. File-by-File Architecture

| File | Responsibility |
| :--- | :--- |
| [`apps/news/apps.py`](../../apps/news/apps.py) | `NewsConfig` (`name = 'apps.news'`, `label = 'news'`). |
| [`apps/news/models.py`](../../apps/news/models.py) | Defines `Category` and `Article` models. |
| [`apps/news/views.py`](../../apps/news/views.py) | Implements `home_view`, `articles_list_view`, and `article_detail_view`. |
| [`apps/news/urls.py`](../../apps/news/urls.py) | URL patterns under `app_name = 'news'`. |
| [`apps/news/admin.py`](../../apps/news/admin.py) | Registers `CategoryAdmin` and `ArticleAdmin` (`SummernoteModelAdmin`). |
| [`apps/news/sitemaps.py`](../../apps/news/sitemaps.py) | Defines `ArticleSitemap`, `StaticViewSitemap`, `DriverSitemap`, and `TeamSitemap`. |
| [`apps/news/tests.py`](../../apps/news/tests.py) | Test module for `apps.news`. |

---

## 4. Views, Business Logic & Query Optimization (`apps/news/views.py`)

### `home_view(request)`
Aggregates three domain sections for the landing page (`templates/news/home.html`):
1. **Next Upcoming Session (`next_session`):**
   Queries `Session.objects.filter(start_time__gte=now).select_related('grand_prix', 'grand_prix__circuit').order_by('start_time').first()`.
2. **Latest Published News (`featured_article` & `recent_articles`):**
   Fetches the 6 most recent published articles with `select_related('category', 'author')`. The first article becomes `featured_article` (hero card) and the remaining up to 5 become `recent_articles`.
3. **Top 5 Driver Standings (`top_drivers`):**
   Resolves the active `Season` (`is_current=True` or latest `year`) and fetches the top 5 `DriverStanding` rows with `select_related('driver', 'driver__team').order_by('position')[:5]`.

### `articles_list_view(request)`
Serves the full news archive (`templates/news/articles_list.html`):
- Starts with `Article.objects.filter(status='published').select_related('category', 'author')`.
- **Category Filter (`?category=<slug>`):** Filters by `category__slug`.
- **Full-Text Search (`?q=<query>`):** Filters across `title__icontains`, `lead__icontains`, and `body__icontains` with `.distinct()`.
- **Pagination (`?page=<n>`):** Paginates 9 articles per page (`Paginator(articles_queryset, 9)`).
- Passes all `Category` objects for the filter bar.

### `article_detail_view(request, slug)`
Serves a single published article (`templates/news/article_detail.html`):
- Fetches the `Article` with `status='published'` using `prefetch_related('related_drivers', 'related_teams')` and `select_related('category', 'author', 'related_grand_prix')`. Returns HTTP 404 if not found or still in `'draft'` status.
- **Smart Related Articles (`related_articles`):**
  Finds up to 3 other published articles sharing any tagged driver (`related_drivers__in`), tagged team (`related_teams__in`), or the same `category`, excluding the current article (`exclude(id=article.id).distinct().select_related('category')[:3]`).

---

## 5. Sitemaps (`apps/news/sitemaps.py`)

Mounted at `/sitemap.xml` in `config/urls.py`:

| Sitemap Class | Key | Priority | Changefreq | Queryset / Items |
| :--- | :--- | :--- | :--- | :--- |
| `ArticleSitemap` | `'articles'` | `0.9` | `daily` | `Article.objects.filter(status='published').order_by('-created_at')` (uses `updated_at` for `lastmod`) |
| `StaticViewSitemap` | `'static'` | `0.8` | `weekly` | `'news:home'`, `'news:articles_list'`, `'racing:standings'`, `'grandprix_calendar:calendar_list'`, `'racing:drivers_list'`, `'racing:teams_list'` |
| `DriverSitemap` | `'drivers'` | `0.7` | `weekly` | `Driver.objects.all().order_by('permanent_number')` |
| `TeamSitemap` | `'teams'` | `0.6` | `monthly` | `Team.objects.all().order_by('name')` |

---

## 6. URLs & Templates

Namespace: `news` (included at root `''` in `config/urls.py`).

| URL Pattern | View Name | View Function | Template |
| :--- | :--- | :--- | :--- |
| `/` | `news:home` | `home_view` | [`templates/news/home.html`](../../templates/news/home.html) |
| `/news/` | `news:articles_list` | `articles_list_view` | [`templates/news/articles_list.html`](../../templates/news/articles_list.html) |
| `/news/<slug>/` (`re_path(r'^news/(?P<slug>[-\w]+)/$')`) | `news:article_detail` | `article_detail_view` | [`templates/news/article_detail.html`](../../templates/news/article_detail.html) |

---

## 7. Django Admin Configuration (`apps/news/admin.py`)

- **`CategoryAdmin`:** Auto-populates `slug` from `title`.
- **`ArticleAdmin(SummernoteModelAdmin)`:**
  - `summernote_fields = ('body',)` renders the RTL Persian Summernote editor.
  - `list_display = ('title', 'category', 'author', 'status', 'created_at')`
  - `list_filter = ('status', 'category', 'created_at')`
  - `search_fields = ('title', 'lead', 'body')`
  - `prepopulated_fields = {'slug': ('title',)}`
  - `filter_horizontal = ('related_drivers', 'related_teams')` for convenient multi-select tagging.

---

## 8. Testing

Run tests for this module:
```bash
uv run pytest apps/news
```

---

## 9. Known Limitations & TODOs

- Tagged drivers/teams/Grand Prix badges in [`templates/news/article_detail.html`](../../templates/news/article_detail.html) currently render as static `<span>` badges rather than clickable `<a>` links to their respective detail pages (tracked in [`docs/TODO.md`](../TODO.md)).
- Category slugs in `articles_list.html` are not yet clickable from article cards.
