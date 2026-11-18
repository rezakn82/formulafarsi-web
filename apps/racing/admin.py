from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from unfold.admin import ModelAdmin

from .models import Circuit, Driver, DriverStanding, Team, TeamStanding


@admin.register(Circuit)
class CircuitAdmin(ModelAdmin):
    list_display = ('name', 'country', 'length_km')
    search_fields = ('name', 'country')


@admin.register(Team)
class TeamAdmin(ModelAdmin, SummernoteModelAdmin):
    summernote_fields = ('bio',)
    list_display = ('name', 'team_chief', 'power_unit', 'views_count')
    search_fields = ('name',)
    readonly_fields = ('views_count',)


@admin.register(Driver)
class DriverAdmin(ModelAdmin, SummernoteModelAdmin):
    summernote_fields = ('bio',)
    list_display = ('full_name', 'permanent_number', 'code', 'team', 'is_main_driver', 'views_count')
    list_editable = ('is_main_driver',)
    list_filter = ('is_main_driver', 'team', 'country')
    search_fields = ('first_name', 'last_name', 'code', 'permanent_number')
    readonly_fields = ('views_count',)

@admin.register(DriverStanding)
class DriverStandingAdmin(ModelAdmin):
    list_display = ('position', 'driver', 'season', 'points', 'wins')
    list_display_links = ('driver',)  # کلیک روی نام راننده، فرم ویرایش کامل را باز می‌کند
    list_editable = ('position', 'points', 'wins')  # رتبه، امتیاز و تعداد برد در خود جدول قابل تغییر خواهند بود
    list_filter = ('season',)
    ordering = ('season', 'position')

@admin.register(TeamStanding)
class TeamStandingAdmin(ModelAdmin):
    list_display = ('position', 'team', 'season', 'points', 'wins')
    list_display_links = ('team',)  # کلیک روی نام تیم، فرم ویرایش کامل را باز می‌کند
    list_editable = ('position', 'points', 'wins')  # رتبه، امتیاز و تعداد برد در خود جدول قابل تغییر خواهند بود
    list_filter = ('season',)
    ordering = ('season', 'position')