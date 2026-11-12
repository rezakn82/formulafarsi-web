from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import GrandPrix, Season, Session, SessionResult


def _resolve_season(request):
    season_year = request.GET.get('season')
    if season_year and season_year.isdigit():
        season = Season.objects.filter(year=int(season_year)).first()
        if season:
            return season
    return Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()


def calendar_view(request):
    current_season = _resolve_season(request)
    seasons = Season.objects.order_by('-year')

    grands_prix = []
    if current_season:
        race_results_prefetch = Prefetch(
            'results',
            queryset=SessionResult.objects.filter(position__lte=3).select_related('driver', 'team').order_by('position'),
        )
        sessions_prefetch = Prefetch(
            'sessions',
            queryset=Session.objects.prefetch_related(race_results_prefetch),
        )
        grands_prix = (
            GrandPrix.objects.filter(season=current_season)
            .select_related('circuit')
            .prefetch_related(sessions_prefetch)
            .order_by('round_number')
        )

    today = timezone.now().date()

    context = {
        'season': current_season,
        'seasons': seasons,
        'grands_prix': grands_prix,
        'today': today,
    }
    return render(request, 'grandprix_calendar/calendar_list.html', context)


def grandprix_detail_view(request, round_number):
    current_season = _resolve_season(request)

    results_prefetch = Prefetch(
        'results',
        queryset=SessionResult.objects.select_related('driver', 'team').order_by('position'),
    )
    sessions_prefetch = Prefetch(
        'sessions',
        queryset=Session.objects.prefetch_related(results_prefetch),
    )

    grand_prix = get_object_or_404(
        GrandPrix.objects.select_related('circuit', 'season').prefetch_related(sessions_prefetch),
        season=current_season,
        round_number=round_number,
    )

    sessions = list(grand_prix.sessions.all())
    sessions_with_results = [s for s in sessions if s.results.all()]
    related_articles = grand_prix.articles.filter(status='published').select_related('category')[:6]

    context = {
        'grand_prix': grand_prix,
        'sessions': sessions,
        'sessions_with_results': sessions_with_results,
        'related_articles': related_articles,
        'now': timezone.now(),
    }
    return render(request, 'grandprix_calendar/grandprix_detail.html', context)