from django.contrib import admin
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django_summernote.admin import SummernoteModelAdmin
from unfold.admin import ModelAdmin

from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "slug", "articles_count", "total_views")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _articles_count=Count("articles", distinct=True),
            _total_views=Coalesce(Sum("articles__views_count"), 0),
        )

    @admin.display(description="تعداد اخبار", ordering="_articles_count")
    def articles_count(self, obj):
        return obj._articles_count

    @admin.display(description="مجموع بازدید اخبار", ordering="_total_views")
    def total_views(self, obj):
        return f"{obj._total_views:,}"


@admin.register(Article)
class ArticleAdmin(ModelAdmin, SummernoteModelAdmin):
    summernote_fields = ("body",)
    list_display = (
        "title",
        "category",
        "author",
        "views_count",
        "is_short",
        "is_breaking",
        "status",
        "created_at",
    )
    list_editable = ("is_short", "is_breaking", "status")
    list_filter = ("is_breaking", "is_short", "status", "category", "created_at")
    search_fields = ("title", "lead", "body")
    readonly_fields = ("views_count", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("related_drivers", "related_teams")