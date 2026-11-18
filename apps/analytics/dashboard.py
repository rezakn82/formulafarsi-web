from datetime import timedelta
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.analytics.models import DailySiteStat, SearchQueryStat
from apps.grandprix_calendar.models import GrandPrix
from apps.news.models import Article
from apps.racing.models import Driver, Team


def dashboard_callback(request, context):
    today = timezone.localdate()
    last_7_days = today - timedelta(days=6)
    last_30_days = today - timedelta(days=29)

    today_stat = DailySiteStat.objects.filter(date=today).first()
    totals = DailySiteStat.objects.aggregate(
        all_time_views=Coalesce(Sum("total_views"), 0),
        all_time_unique=Coalesce(Sum("unique_visitors"), 0),
    )
    week_totals = DailySiteStat.objects.filter(date__gte=last_7_days).aggregate(
        views=Coalesce(Sum("total_views"), 0),
        unique=Coalesce(Sum("unique_visitors"), 0),
    )
    month_totals = DailySiteStat.objects.filter(date__gte=last_30_days).aggregate(
        views=Coalesce(Sum("total_views"), 0),
    )
    total_article_views = Article.objects.filter(status="published").aggregate(
        total=Coalesce(Sum("views_count"), 0)
    )["total"]

    context.update(
        {
            "kpi_cards": [
                {
                    "title": "بازدید کل سایت (از ابتدا)",
                    "metric": f"{totals['all_time_views']:,}",
                    "footer": f"مجموع بازدیدکنندگان یکتای روزانه: {totals['all_time_unique']:,}",
                },
                {
                    "title": "بازدید امروز",
                    "metric": f"{today_stat.total_views if today_stat else 0:,}",
                    "footer": f"کاربران یکتای امروز: {today_stat.unique_visitors if today_stat else 0:,}",
                },
                {
                    "title": "بازدید ۷ روز گذشته",
                    "metric": f"{week_totals['views']:,}",
                    "footer": f"۳۰ روز گذشته: {month_totals['views']:,} بازدید",
                },
                {
                    "title": "مجموع بازدید اخبار",
                    "metric": f"{total_article_views:,}",
                    "footer": f"تعداد کل اخبار منتشرشده: {Article.objects.filter(status='published').count()}",
                },
            ],
            "top_articles": Article.objects.filter(status="published")
            .select_related("category")
            .order_by("-views_count")[:8],
            "top_drivers": Driver.objects.select_related("team").order_by("-views_count")[:5],
            "top_teams": Team.objects.order_by("-views_count")[:5],
            "top_grands_prix": GrandPrix.objects.select_related("season").order_by("-views_count")[:5],
            "top_searches": SearchQueryStat.objects.order_by("-search_count")[:8],
            "recent_daily_stats": DailySiteStat.objects.order_by("-date")[:10],
        }
    )
    return context