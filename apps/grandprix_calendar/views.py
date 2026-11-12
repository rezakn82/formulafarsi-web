from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Season, GrandPrix

def calendar_view(request):
    # دریافت فصل جاری (اگر تنظیمی نبود، جدیدترین فصل)
    current_season = Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()
    
    grands_prix = []
    if current_season:
        grands_prix = GrandPrix.objects.filter(season=current_season).select_related('circuit').prefetch_related('sessions').order_by('round_number')

    today = timezone.now().date()

    context = {
        'season': current_season,
        'grands_prix': grands_prix,
        'today': today,
    }
    return render(request, 'grandprix_calendar/calendar_list.html', context)


def grandprix_detail_view(request, round_number):
    current_season = Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()
    
    grand_prix = get_object_or_404(
        GrandPrix.objects.select_related('circuit', 'season').prefetch_related('sessions'),
        season=current_season,
        round_number=round_number
    )

    now = timezone.now()

    context = {
        'grand_prix': grand_prix,
        'sessions': grand_prix.sessions.all().order_by('start_time'),
        'now': now,
    }
    return render(request, 'grandprix_calendar/grandprix_detail.html', context)