from django.contrib import admin
from .models import Circuit, Team, Driver, DriverStanding, TeamStanding

@admin.register(Circuit)
class CircuitAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'length_km')
    search_fields = ('name', 'country')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_chief', 'power_unit')
    search_fields = ('name',)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'permanent_number', 'code', 'team', 'country')
    list_filter = ('team', 'country')
    search_fields = ('first_name', 'last_name', 'code')

@admin.register(DriverStanding)
class DriverStandingAdmin(admin.ModelAdmin):
    list_display = ('position', 'driver', 'season', 'points', 'wins')
    list_display_links = ('driver',)  # کلیک روی نام راننده، فرم ویرایش کامل را باز می‌کند
    list_editable = ('position', 'points', 'wins')  # رتبه، امتیاز و تعداد برد در خود جدول قابل تغییر خواهند بود
    list_filter = ('season',)
    ordering = ('season', 'position')

@admin.register(TeamStanding)
class TeamStandingAdmin(admin.ModelAdmin):
    list_display = ('position', 'team', 'season', 'points', 'wins')
    list_display_links = ('team',)  # کلیک روی نام تیم، فرم ویرایش کامل را باز می‌کند
    list_editable = ('position', 'points', 'wins')  # رتبه، امتیاز و تعداد برد در خود جدول قابل تغییر خواهند بود
    list_filter = ('season',)
    ordering = ('season', 'position')