import hashlib
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.analytics.models import DailySiteStat, DailyVisitorHash, SearchQueryStat

BOT_KEYWORDS = (
    "bot",
    "crawl",
    "spider",
    "slurp",
    "lighthouse",
    "headless",
    "python-requests",
    "httpx",
    "urllib",
    "curl",
    "wget",
    "facebookexternalhit",
    "telegrambot",
    "whatsapp",
)


def is_bot_request(request) -> bool:
    user_agent = (request.META.get("HTTP_USER_AGENT") or "").lower()
    if not user_agent:
        return True
    return any(keyword in user_agent for keyword in BOT_KEYWORDS)


def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or "0.0.0.0"


def get_visitor_hash(request, today_str: str) -> str:
    ip = get_client_ip(request)
    user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:200]
    raw = f"{today_str}:{ip}:{user_agent}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def record_object_view(request, model_cls, object_pk: int, session_key_prefix: str) -> None:
    """
    افزایش اتمیک تعداد بازدید یک شیء (خبر، راننده، تیم یا گرندپری)
    فقط یک‌بار در هر نشست کاربر و با نادیده گرفتن ربات‌ها.
    """
    if request.method != "GET" or is_bot_request(request):
        return

    session_key = f"viewed_{session_key_prefix}"
    viewed_ids = request.session.get(session_key, [])

    if object_pk in viewed_ids:
        return

    model_cls.objects.filter(pk=object_pk).update(views_count=F("views_count") + 1)

    # نگهداری حداکثر ۱۰۰ آیتم آخر در سشن برای جلوگیری از حجیم شدن کوکی/سشن
    viewed_ids.append(object_pk)
    request.session[session_key] = viewed_ids[-100:]


def record_search_query(request, query: str, results_count: int) -> None:
    """ثبت عبارت جستجوشده و تعداد نتایج آن در دیتابیس."""
    cleaned = (query or "").strip()[:150].lower()
    if len(cleaned) < 2 or is_bot_request(request):
        return

    updated = SearchQueryStat.objects.filter(query=cleaned).update(
        search_count=F("search_count") + 1,
        last_results_count=results_count,
        last_searched_at=timezone.now(),
    )
    if not updated:
        try:
            with transaction.atomic():
                SearchQueryStat.objects.create(
                    query=cleaned,
                    search_count=1,
                    last_results_count=results_count,
                )
        except IntegrityError:
            SearchQueryStat.objects.filter(query=cleaned).update(
                search_count=F("search_count") + 1,
                last_results_count=results_count,
                last_searched_at=timezone.now(),
            )