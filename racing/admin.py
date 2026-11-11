from django.contrib import admin
from .models import Circuit, Team, Driver

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