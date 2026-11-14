from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render

from apps.grandprix_calendar.models import Season

from .models import Driver, DriverStanding, Team, TeamStanding


def _get_current_season():
    return Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()

# ۱. لیست تمام رانندگان (مرتب‌شده بر اساس جدول رده‌بندی تیمی فصل جاری)
def drivers_list_view(request):
    current_season = _get_current_season()
    drivers = Driver.objects.select_related('team')

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
        code__iexact=code
    )
    
    # هم‌تیمی (سایر رانندگان همین تیم)
    teammates = []
    if driver.team:
        teammates = driver.team.drivers.exclude(id=driver.id)

    # اخباری که این راننده در آن‌ها تگ شده است
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
    teams = Team.objects.prefetch_related('drivers')

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
    team = get_object_or_404(
        Team.objects.prefetch_related('drivers'),
        pk=pk
    )

    # اخباری که این تیم در آن‌ها تگ شده است
    related_articles = team.articles.filter(status='published').select_related('category')[:6]

    context = {
        'team': team,
        'drivers': team.drivers.all(),
        'related_articles': related_articles,
    }
    return render(request, 'racing/team_detail.html', context)


def standings_view(request):
    # دریافت فصل جاری یا آخرین فصل موجود
    current_season = Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()
    
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