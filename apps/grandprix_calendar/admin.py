from django.contrib import admin
from .models import Season, GrandPrix, Session

class SessionInline(admin.TabularInline):
    model = Session
    extra = 5  # به‌طور پیش‌فرض ۵ ردیف برای سشن‌ها باز می‌کند

@admin.register(GrandPrix)
class GrandPrixAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'round_number', 'start_date', 'end_date')
    list_filter = ('season',)
    inlines = [SessionInline]

admin.site.register(Season)