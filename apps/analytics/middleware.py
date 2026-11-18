from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.analytics.models import DailySiteStat, DailyVisitorHash
from apps.analytics.utils import get_visitor_hash, is_bot_request

EXCLUDED_PREFIXES = (
    "/static/",
    "/media/",
    "/summernote/",
    "/__debug__/",
    "/sitemap.xml",
    "/favicon.ico",
    "/robots.txt",
)


class SiteAnalyticsMiddleware:
    """میان‌افزار شمارش بازدید روزانه و بازدیدکنندگان یکتای کل سایت."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method != "GET" or response.status_code != 200:
            return response

        path = request.path
        admin_prefix = f"/{settings.ADMIN_URL.strip('/')}/"
        if path.startswith(admin_prefix) or path.startswith(EXCLUDED_PREFIXES):
            return response

        content_type = response.get("Content-Type", "")
        if "text/html" not in content_type or is_bot_request(request):
            return response

        today = timezone.localdate()
        visitor_hash = get_visitor_hash(request, today.isoformat())

        is_new_unique = False
        if not DailyVisitorHash.objects.filter(date=today, visitor_hash=visitor_hash).exists():
            try:
                with transaction.atomic():
                    DailyVisitorHash.objects.create(date=today, visitor_hash=visitor_hash)
                is_new_unique = True
            except IntegrityError:
                is_new_unique = False

        update_kwargs = {"total_views": F("total_views") + 1}
        if is_new_unique:
            update_kwargs["unique_visitors"] = F("unique_visitors") + 1

        updated = DailySiteStat.objects.filter(date=today).update(**update_kwargs)
        if not updated:
            try:
                with transaction.atomic():
                    DailySiteStat.objects.create(
                        date=today,
                        total_views=1,
                        unique_visitors=1 if is_new_unique else 0,
                    )
            except IntegrityError:
                DailySiteStat.objects.filter(date=today).update(**update_kwargs)

        return response