from django.contrib import admin
from .models import Category, Article

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'lead', 'body')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('related_drivers', 'related_teams')