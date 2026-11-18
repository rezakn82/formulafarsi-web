from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.analytics.models import DailySiteStat, SearchQueryStat


@admin.register(DailySiteStat)
class DailySiteStatAdmin(ModelAdmin):
    list_display = ("date", "jalali_date_display", "total_views", "unique_visitors")
    list_filter = ("date",)
    ordering = ("-date",)
    readonly_fields = ("date", "total_views", "unique_visitors")

    @admin.display(description="تاریخ شمسی")
    def jalali_date_display(self, obj):
        from apps.news.templatetags.jalali_tags import jalali_date
        return jalali_date(obj.date, "l j F Y")

    def has_add_permission(self, request):
        return False


@admin.register(SearchQueryStat)
class SearchQueryStatAdmin(ModelAdmin):
    list_display = ("query", "search_count", "last_results_count", "last_searched_at")
    list_filter = ("last_searched_at",)
    search_fields = ("query",)
    ordering = ("-search_count", "-last_searched_at")
    readonly_fields = ("query", "search_count", "last_results_count", "last_searched_at")

    def has_add_permission(self, request):
        return False