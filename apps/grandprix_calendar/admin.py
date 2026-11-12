from django.contrib import admin
from .models import Season, GrandPrix, Session, SessionResult

class SessionInline(admin.TabularInline):
    model = Session
    extra = 5
    show_change_link = True

class SessionResultInline(admin.TabularInline):
    model = SessionResult
    extra = 22  # باز کردن ۲۰ ردیف آماده برای ۲۰ راننده فرمول یک
    autocomplete_fields = ('driver', 'team')
    fields = (
        'position',
        'driver',
        'team',
        'status',
        'grid_position',
        'laps',
        'time_or_gap',
        'q1_time',
        'q2_time',
        'q3_time',
        'points',
        'fastest_lap',
    )


@admin.register(GrandPrix)
class GrandPrixAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'round_number', 'start_date', 'end_date')
    list_filter = ('season',)
    inlines = [SessionInline]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('grand_prix', 'session_type', 'start_time')
    list_filter = ('grand_prix__season', 'session_type', 'grand_prix')
    search_fields = ('grand_prix__name',)
    inlines = [SessionResultInline]


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('year', 'is_current')
    list_editable = ('is_current',)