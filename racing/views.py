from django.shortcuts import render, get_object_or_404
from .models import Driver, Team

# ۱. لیست تمام رانندگان
def drivers_list_view(request):
    drivers = Driver.objects.select_related('team').order_by('team__name', 'permanent_number')
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


# ۳. لیست تمام تیم‌ها
def teams_list_view(request):
    teams = Team.objects.prefetch_related('drivers').order_by('name')
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