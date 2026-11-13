"""
Base Django settings shared across all FormulaFarsi environments.

Environment variables are loaded from optional ``env/.env`` and environment-specific
``env/.env.<profile>`` files via ``config.env`` using ``django-environ`` and
``python-dotenv``.
"""

from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy

from config.env import Env, load_env_files

# ==============================================================================
# PATHS & ENVIRONMENT
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_DIR = BASE_DIR / "env"

load_env_files(ENV_DIR)
env = Env()

# ==============================================================================
# CORE APPLICATION
# ==============================================================================
ADMIN_URL = env.str("ADMIN_URL", default="admin/")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # Third-party apps
    "django_summernote",
    # Project apps
    "apps.news.apps.NewsConfig",
    "apps.racing.apps.RacingConfig",
    "apps.grandprix_calendar.apps.GrandprixCalendarConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "builtins": [
                "apps.news.templatetags.jalali_tags",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# PASSWORD VALIDATION
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================
LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="fa-ir")
TIME_ZONE = env.str("TIME_ZONE", default="Asia/Tehran")
USE_I18N = True
USE_TZ = True

# ==============================================================================
# STATIC & MEDIA FILES
# ==============================================================================
STATIC_URL = env.str("STATIC_URL", default="/static/")
STATIC_ROOT = Path(env.str("STATIC_ROOT", default=str(BASE_DIR / "staticfiles")))
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = env.str("MEDIA_URL", default="/media/")
MEDIA_ROOT = Path(env.str("MEDIA_ROOT", default=str(BASE_DIR / "media")))

# ==============================================================================
# SUMMERNOTE RICH-TEXT EDITOR
# ==============================================================================
# Required so django-summernote's admin iframe loads on the same origin.
X_FRAME_OPTIONS = "SAMEORIGIN"

SUMMERNOTE_THEME = "bs4"

SUMMERNOTE_CONFIG = {
    "iframe": True,
    "summernote": {
        "airMode": False,
        "width": "100%",
        "height": "480",
        "lang": "fa-IR",
        "styleTags": ["p", "blockquote", "pre", "h2", "h3", "h4"],
        "fontNames": ["Vazirmatn", "Tahoma", "Arial", "Courier New"],
        "fontNamesIgnoreCheck": ["Vazirmatn"],
        "fontSizes": ["12", "14", "16", "18", "20", "24", "28", "32"],
        "toolbar": [
            ["style", ["style"]],
            [
                "font",
                [
                    "bold",
                    "italic",
                    "underline",
                    "strikethrough",
                    "superscript",
                    "subscript",
                    "clear",
                ],
            ],
            ["fontname", ["fontname"]],
            ["fontsize", ["fontsize"]],
            ["color", ["color"]],
            ["para", ["ul", "ol", "paragraph", "height"]],
            ["table", ["table"]],
            ["insert", ["link", "picture", "video", "hr"]],
            ["view", ["fullscreen", "codeview", "undo", "redo", "help"]],
        ],
        "popover": {
            "image": [
                ["image", ["resizeFull", "resizeHalf", "resizeQuarter", "resizeNone"]],
                ["float", ["floatLeft", "floatRight", "floatNone"]],
                ["remove", ["removeMedia"]],
            ],
            "link": [
                ["link", ["linkDialogShow", "unlink"]],
            ],
            "table": [
                ["add", ["addRowDown", "addRowUp", "addColLeft", "addColRight"]],
                ["delete", ["deleteRow", "deleteCol", "deleteTable"]],
            ],
        },
    },
    "css": (
        "https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css",
    ),
    "attachment_upload_to": "news/attachments/%Y/%m/",
    "attachment_filesize_limit": 10 * 1024 * 1024,  # 10 MB max per uploaded media file
    "attachment_require_authentication": True,
}

# Allowed HTML tags and attributes when sanitizing SummernoteTextField via bleach
ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "br",
    "caption",
    "cite",
    "code",
    "col",
    "colgroup",
    "dd",
    "del",
    "details",
    "div",
    "dl",
    "dt",
    "em",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "iframe",
    "img",
    "ins",
    "kbd",
    "li",
    "mark",
    "ol",
    "p",
    "pre",
    "q",
    "s",
    "samp",
    "small",
    "span",
    "strike",
    "strong",
    "sub",
    "summary",
    "sup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
    "var",
    "video",
    "source",
]

ATTRIBUTES = {
    "*": ["class", "style", "dir", "lang", "id", "title", "align"],
    "a": ["href", "target", "rel", "title"],
    "img": ["src", "alt", "width", "height", "loading"],
    "iframe": [
        "src",
        "width",
        "height",
        "frameborder",
        "allow",
        "allowfullscreen",
    ],
    "video": ["src", "controls", "width", "height", "poster", "preload"],
    "source": ["src", "type"],
    "td": ["colspan", "rowspan", "width", "height"],
    "th": ["colspan", "rowspan", "width", "height", "scope"],
}

# ==============================================================================
# UNFOLD ADMIN PANEL
# ==============================================================================
UNFOLD = {
    "SITE_TITLE": "مدیریت فرمولافارسی",
    "SITE_HEADER": "پیت‌وال فرمولافارسی",
    "SITE_SUBHEADER": "پنل تحریریه و مدیریت نتایج F1",
    "SITE_URL": "/",
    "SITE_SYMBOL": "sports_motorsports",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "THEME": "dark",
    "STYLES": [
        lambda request: static("css/admin-custom.css"),
    ],
    "COLORS": {
        "primary": {
            "50": "254 242 242",
            "100": "254 226 226",
            "200": "254 202 202",
            "300": "252 165 165",
            "400": "248 113 113",
            "500": "239 68 68",
            "600": "225 6 0",
            "700": "185 28 28",
            "800": "153 27 27",
            "900": "127 29 29",
            "950": "69 10 10",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "تحریریه و اخبار",
                "separator": True,
                "items": [
                    {
                        "title": "اخبار و مقالات",
                        "icon": "newspaper",
                        "link": reverse_lazy("admin:news_article_changelist"),
                    },
                    {
                        "title": "دسته‌بندی‌ها",
                        "icon": "category",
                        "link": reverse_lazy("admin:news_category_changelist"),
                    },
                ],
            },
            {
                "title": "مسابقات و تقویم",
                "separator": True,
                "items": [
                    {
                        "title": "فصل‌ها",
                        "icon": "calendar_month",
                        "link": reverse_lazy("admin:grandprix_calendar_season_changelist"),
                    },
                    {
                        "title": "گرندپری‌ها",
                        "icon": "flag",
                        "link": reverse_lazy("admin:grandprix_calendar_grandprix_changelist"),
                    },
                    {
                        "title": "سشن‌ها و زمان‌بندی",
                        "icon": "timer",
                        "link": reverse_lazy("admin:grandprix_calendar_session_changelist"),
                    },
                ],
            },
            {
                "title": "اطلاعات فصل و جدول قهرمانی",
                "separator": True,
                "items": [
                    {
                        "title": "رانندگان",
                        "icon": "sports_motorsports",
                        "link": reverse_lazy("admin:racing_driver_changelist"),
                    },
                    {
                        "title": "تیم‌ها (سازندگان)",
                        "icon": "groups",
                        "link": reverse_lazy("admin:racing_team_changelist"),
                    },
                    {
                        "title": "پیست‌ها",
                        "icon": "route",
                        "link": reverse_lazy("admin:racing_circuit_changelist"),
                    },
                    {
                        "title": "رده‌بندی رانندگان",
                        "icon": "leaderboard",
                        "link": reverse_lazy("admin:racing_driverstanding_changelist"),
                    },
                    {
                        "title": "رده‌بندی تیم‌ها",
                        "icon": "emoji_events",
                        "link": reverse_lazy("admin:racing_teamstanding_changelist"),
                    },
                ],
            },
        ],
    },
}
