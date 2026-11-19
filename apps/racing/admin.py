from django.contrib import admin, messages
from django_summernote.admin import SummernoteModelAdmin
from unfold.admin import ModelAdmin

from .models import (
    Circuit,
    Driver,
    DriverPowerUnitUsage,
    DriverStanding,
    PowerUnitComponentInfo,
    PowerUnitLimit,
    Team,
    TeamStanding,
)


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

@admin.register(PowerUnitLimit)
class PowerUnitLimitAdmin(ModelAdmin):
    list_display = (
        'season',
        'ice_limit',
        'tc_limit',
        'exh_limit',
        'mguk_limit',
        'es_limit',
        'pu_ce_limit',
        'pu_anc_limit',
    )
    actions = ['generate_driver_pu_rows']

    @admin.action(description="ایجاد ردیف قطعات PU برای تمام رانندگان اصلی این فصل(ها)")
    def generate_driver_pu_rows(self, request, queryset):
        main_drivers = Driver.objects.filter(is_main_driver=True)
        created_count = 0
        for limit_obj in queryset.select_related('season'):
            for driver in main_drivers:
                _, created = DriverPowerUnitUsage.objects.get_or_create(
                    season=limit_obj.season,
                    driver=driver,
                )
                if created:
                    created_count += 1
        self.message_user(
            request,
            f"{created_count} ردیف جدید برای رانندگان اصلی ایجاد شد.",
            level=messages.SUCCESS,
        )


@admin.register(DriverPowerUnitUsage)
class DriverPowerUnitUsageAdmin(ModelAdmin):
    list_display = (
        'driver',
        'team_name',
        'power_unit_name',
        'season',
        'ice',
        'tc',
        'exh',
        'mguk',
        'es',
        'pu_ce',
        'pu_anc',
    )
    list_display_links = ('driver',)
    list_editable = ('ice', 'tc', 'exh', 'mguk', 'es', 'pu_ce', 'pu_anc')
    list_filter = ('season', 'driver__team')
    search_fields = ('driver__first_name', 'driver__last_name', 'driver__code', 'driver__team__name')
    list_select_related = ('season', 'driver', 'driver__team')
    ordering = ('-season__year', 'driver__team__name', 'driver__permanent_number')

    @admin.display(description="تیم", ordering="driver__team__name")
    def team_name(self, obj):
        return obj.driver.team.name if obj.driver.team else "-"

    @admin.display(description="پیشرانه", ordering="driver__team__power_unit")
    def power_unit_name(self, obj):
        return obj.driver.team.power_unit if obj.driver.team else "-"


@admin.register(PowerUnitComponentInfo)
class PowerUnitComponentInfoAdmin(ModelAdmin):
    list_display = ('display_order', 'code', 'persian_name', 'english_name')
    list_display_links = ('code', 'persian_name')
    list_editable = ('display_order',)
    ordering = ('display_order',)   