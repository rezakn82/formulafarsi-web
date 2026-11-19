from django.db.models import OuterRef, Prefetch, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render

from apps.grandprix_calendar.models import Season

from .models import (
    Driver,
    DriverPowerUnitUsage,
    DriverStanding,
    PowerUnitComponentInfo,
    PowerUnitLimit,
    Team,
    TeamStanding,
)
from apps.analytics.utils import record_object_view


def _get_current_season():
    return Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()

# ۱. لیست تمام رانندگان (مرتب‌شده بر اساس جدول رده‌بندی تیمی فصل جاری)
def drivers_list_view(request):
    current_season = _get_current_season()
    drivers = Driver.objects.filter(is_main_driver=True).select_related('team')

    if current_season:
        team_pos_subquery = TeamStanding.objects.filter(
            season=current_season,
            team=OuterRef('team_id'),
        ).values('position')[:1]

        driver_pos_subquery = DriverStanding.objects.filter(
            season=current_season,
            driver=OuterRef('pk'),
        ).values('position')[:1]

        drivers = drivers.annotate(
            team_standing_pos=Coalesce(Subquery(team_pos_subquery), 999),
            driver_standing_pos=Coalesce(Subquery(driver_pos_subquery), 999),
        ).order_by('team_standing_pos', 'driver_standing_pos', 'permanent_number')
    else:
        drivers = drivers.order_by('team__name', 'permanent_number')

    return render(request, 'racing/drivers_list.html', {'drivers': drivers})

# ۲. پروفایل تکی راننده
def driver_detail_view(request, code):
    driver = get_object_or_404(
        Driver.objects.select_related('team'),
        code__iexact=code,
    )

    record_object_view(request, Driver, driver.pk, "drivers")

    teammates = []
    if driver.team:
        teammates = driver.team.drivers.filter(is_main_driver=True).exclude(id=driver.id)

    related_articles = driver.articles.filter(status='published').select_related('category')[:6]

    context = {
        'driver': driver,
        'teammates': teammates,
        'related_articles': related_articles,
    }
    return render(request, 'racing/driver_detail.html', context)


# ۳. لیست تمام تیم‌ها (مرتب‌شده بر اساس جدول رده‌بندی تیمی فصل جاری)
def teams_list_view(request):
    current_season = _get_current_season()
    main_drivers_prefetch = Prefetch(
        'drivers',
        queryset=Driver.objects.filter(is_main_driver=True).order_by('permanent_number'),
    )
    teams = Team.objects.prefetch_related(main_drivers_prefetch)

    if current_season:
        team_pos_subquery = TeamStanding.objects.filter(
            season=current_season,
            team=OuterRef('pk'),
        ).values('position')[:1]

        teams = teams.annotate(
            team_standing_pos=Coalesce(Subquery(team_pos_subquery), 999),
        ).order_by('team_standing_pos', 'name')
    else:
        teams = teams.order_by('name')

    return render(request, 'racing/teams_list.html', {'teams': teams})


# ۴. پروفایل تکی تیم
def team_detail_view(request, pk):
    main_drivers_prefetch = Prefetch(
        'drivers',
        queryset=Driver.objects.filter(is_main_driver=True).order_by('permanent_number'),
    )
    team = get_object_or_404(
        Team.objects.prefetch_related(main_drivers_prefetch),
        pk=pk,
    )

    record_object_view(request, Team, team.pk, "teams")

    related_articles = team.articles.filter(status='published').select_related('category')[:6]

    context = {
        'team': team,
        'drivers': team.drivers.all(),
        'related_articles': related_articles,
    }
    return render(request, 'racing/team_detail.html', context)


def standings_view(request):
    current_season = _get_current_season()

    driver_standings = []
    team_standings = []

    if current_season:
        driver_standings = DriverStanding.objects.filter(
            season=current_season
        ).select_related('driver', 'driver__team').order_by('position')

        team_standings = TeamStanding.objects.filter(
            season=current_season
        ).select_related('team').order_by('position')

    context = {
        'season': current_season,
        'driver_standings': driver_standings,
        'team_standings': team_standings,
    }
    return render(request, 'racing/standings.html', context)


PU_COMPONENT_DEFS = [
    ("ice", "ICE", "ice_limit", 4),
    ("tc", "TC", "tc_limit", 4),
    ("exh", "EXH", "exh_limit", 4),
    ("mguk", "MGU-K", "mguk_limit", 3),
    ("es", "ES", "es_limit", 3),
    ("pu_ce", "PU-CE", "pu_ce_limit", 3),
    ("pu_anc", "PU-ANC", "pu_anc_limit", 6),
]

# توضیحات پیش‌فرض فارسی (در صورتی که از پنل ادمین ثبت نشده باشد نمایش داده می‌شود)
DEFAULT_PU_DESCRIPTIONS = [
    {
        "code": "ICE",
        "english_name": "Internal Combustion Engine",
        "persian_name": "موتور احتراق داخلی",
        "description": "موتور ۱.۶ لیتری V6 توربوشارژ که با سوخت پایدار کار می‌کند و بخش مکانیکی اصلی تولید قدرت در خودروی فرمول یک است.",
    },
    {
        "code": "TC",
        "english_name": "Turbocharger",
        "persian_name": "توربوشارژر",
        "description": "از انرژی گازهای خروجی اگزوز برای فشرده‌سازی هوای ورودی به موتور استفاده می‌کند تا راندمان احتراق و توان خروجی موتور افزایش یابد.",
    },
    {
        "code": "EXH",
        "english_name": "Exhaust System",
        "persian_name": "سیستم اگزوز",
        "description": "مجموعه لوله‌ها و منیفولدهای تخلیه گازهای داغ ناشی از احتراق از سیلندرها به سمت توربوشارژر و خروجی عقب خودرو.",
    },
    {
        "code": "MGU-K",
        "english_name": "Motor Generator Unit – Kinetic",
        "persian_name": "واحد موتور-ژنراتور جنبشی",
        "description": "انرژی جنبشی تلف‌شده هنگام ترمزگیری را به انرژی الکتریکی تبدیل کرده و هنگام شتاب‌گیری تا ۳۵۰ کیلووات توان الکتریکی به خودرو اضافه می‌کند.",
    },
    {
        "code": "ES",
        "english_name": "Energy Store",
        "persian_name": "ذخیره‌ساز انرژی (باتری)",
        "description": "مجموعه باتری‌های ولتاژ بالا که انرژی الکتریکی بازیابی‌شده توسط MGU-K را ذخیره کرده و در زمان نیاز در اختیار موتور الکتریکی قرار می‌دهد.",
    },
    {
        "code": "PU-CE",
        "english_name": "Power Unit Control Electronics",
        "persian_name": "الکترونیک کنترل پیشرانه",
        "description": "واحدهای کنترلی و الکترونیک قدرت که هماهنگی دقیق میان موتور احتراق داخلی، MGU-K و باتری (ES) را مدیریت می‌کنند.",
    },
    {
        "code": "PU-ANC",
        "english_name": "Power Unit Ancillary Components",
        "persian_name": "قطعات جانبی پیشرانه",
        "description": "مجموعه قطعات و تجهیزات جانبی متصل به پیشرانه که در مقررات فصل ۲۰۲۶ فیا به صورت مستقل دارای سقف استفاده در طول فصل هستند.",
    },
]


def _get_pu_cell_meta(used: int, limit: int) -> dict:
    """تعیین وضعیت و کلاس رنگ فونت بر اساس تعداد استفاده نسبت به سقف مجاز."""
    if used > limit:
        return {
            "used": used,
            "limit": limit,
            "status": "penalty",
            "text_class": "text-red-500 font-black",
            "bg_class": "bg-red-500/10 border-red-500/30",
        }
    if used == limit:
        return {
            "used": used,
            "limit": limit,
            "status": "warning",
            "text_class": "text-orange-400 font-extrabold",
            "bg_class": "bg-orange-500/10 border-orange-500/30",
        }
    return {
        "used": used,
        "limit": limit,
        "status": "ok",
        "text_class": "text-white font-bold",
        "bg_class": "bg-zinc-950/60 border-zinc-800/80",
    }


def pu_components_view(request):
    season_year = request.GET.get('season')
    current_season = None
    if season_year and season_year.isdigit():
        current_season = Season.objects.filter(year=int(season_year)).first()
    if not current_season:
        current_season = _get_current_season()

    seasons = Season.objects.order_by('-year')

    # خواندن سقف مجاز فصل از دیتابیس یا استفاده از مقادیر پیش‌فرض ۲۰۲۶
    limit_obj = PowerUnitLimit.objects.filter(season=current_season).first() if current_season else None
    limits_map = {}
    component_headers = []
    for field_name, code, limit_field, default_limit in PU_COMPONENT_DEFS:
        limit_val = getattr(limit_obj, limit_field, default_limit) if limit_obj else default_limit
        limits_map[code] = limit_val
        component_headers.append({
            "field": field_name,
            "code": code,
            "limit": limit_val,
        })

    rows = []
    if current_season:
        usages_qs = (
            DriverPowerUnitUsage.objects.filter(season=current_season)
            .select_related('driver', 'driver__team')
        )
        usage_by_driver_id = {u.driver_id: u for u in usages_qs}

        # مرتب‌سازی رانندگان بر اساس رده‌بندی تیمی و رانندگان همان فصل (بدون N+1 Query)
        team_pos_subquery = TeamStanding.objects.filter(
            season=current_season,
            team=OuterRef('team_id'),
        ).values('position')[:1]

        driver_pos_subquery = DriverStanding.objects.filter(
            season=current_season,
            driver=OuterRef('pk'),
        ).values('position')[:1]

        drivers_qs = Driver.objects.select_related('team')
        if usage_by_driver_id:
            # نمایش تمام رانندگان دارای رکورد مصرف + رانندگان اصلی فصل جاری
            if current_season.is_current:
                drivers_qs = drivers_qs.filter(
                    pk__in=list(usage_by_driver_id.keys())
                ) | Driver.objects.filter(is_main_driver=True).select_related('team')
                drivers_qs = drivers_qs.distinct()
            else:
                drivers_qs = drivers_qs.filter(pk__in=list(usage_by_driver_id.keys()))
        else:
            drivers_qs = drivers_qs.filter(is_main_driver=True)

        drivers_ordered = drivers_qs.annotate(
            team_standing_pos=Coalesce(Subquery(team_pos_subquery), 999),
            driver_standing_pos=Coalesce(Subquery(driver_pos_subquery), 999),
        ).order_by('team_standing_pos', 'driver_standing_pos', 'permanent_number')

        for driver in drivers_ordered:
            usage = usage_by_driver_id.get(driver.pk)
            components_cells = []
            has_penalty = False
            for field_name, code, _, _ in PU_COMPONENT_DEFS:
                used_val = getattr(usage, field_name, 0) if usage else 0
                cell = _get_pu_cell_meta(used_val, limits_map[code])
                cell["code"] = code
                if cell["status"] == "penalty":
                    has_penalty = True
                components_cells.append(cell)

            rows.append({
                "driver": driver,
                "team": driver.team,
                "power_unit": driver.team.power_unit if driver.team else "-",
                "cells": components_cells,
                "has_penalty": has_penalty,
            })

    # خواندن توضیحات قطعات از دیتابیس (با جایگزین پیش‌فرض در صورت خالی بودن)
    db_infos = list(PowerUnitComponentInfo.objects.all())
    if db_infos:
        component_infos = [
            {
                "code": info.code,
                "english_name": info.english_name,
                "persian_name": info.persian_name,
                "description": info.description,
                "limit": limits_map.get(info.code),
            }
            for info in db_infos
        ]
    else:
        component_infos = [
            {**item, "limit": limits_map.get(item["code"])}
            for item in DEFAULT_PU_DESCRIPTIONS
        ]

    context = {
        "season": current_season,
        "seasons": seasons,
        "component_headers": component_headers,
        "rows": rows,
        "component_infos": component_infos,
    }
    return render(request, 'racing/pu_components.html', context)