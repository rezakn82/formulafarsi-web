from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from unfold.admin import ModelAdmin

from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Article)
class ArticleAdmin(ModelAdmin, SummernoteModelAdmin):
    summernote_fields = ('body',)
    list_display = ('title', 'category', 'author', 'is_short', 'is_breaking', 'status', 'created_at')
    list_editable = ('is_short', 'is_breaking', 'status')
    list_filter = ('is_breaking', 'is_short', 'status', 'category', 'created_at')
    search_fields = ('title', 'lead', 'body')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('related_drivers', 'related_teams')