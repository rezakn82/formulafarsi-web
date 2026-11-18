from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.grandprix_calendar.models import GrandPrix, Season, Session, SessionResult
from apps.racing.models import Driver, DriverStanding, Team, TeamStanding

from .models import Article, Category
from apps.analytics.utils import record_object_view, record_search_query


def home_view(request):
    now = timezone.now()

    # ۱. نزدیک‌ترین سشن آینده + تمام جلسات آن گرندپری برای کارت «مسابقه بعدی»
    next_session = (
        Session.objects.filter(start_time__gte=now)
        .select_related('grand_prix', 'grand_prix__circuit', 'grand_prix__season')
        .order_by('start_time')
        .first()
    )
    next_gp_sessions = []
    if next_session:
        next_gp_sessions = list(
            Session.objects.filter(grand_prix=next_session.grand_prix).order_by('start_time')
        )

    # ۲. اخبار اصلی (غیر کوتاه): ۱ خبر ویژه (تیتر یک) + تا ۶ خبر آخر
    main_articles = list(
        Article.objects.filter(status='published', is_short=False)
        .select_related('category', 'author')
        .order_by('-created_at')[:7]
    )
    featured_article = main_articles[0] if main_articles else None
    recent_articles = main_articles[1:7] if len(main_articles) > 1 else []

    # ۳. اخبار کوتاه: تا ۶ خبر کوتاه
    short_articles = list(
        Article.objects.filter(status='published', is_short=True)
        .select_related('category', 'author')
        .order_by('-created_at')[:6]
    )

    # ۴. نوار اخبار فوری (فقط اخباری که ادمین تیک is_breaking آن‌ها را فعال کرده است)
    ticker_items = list(
        Article.objects.filter(status='published', is_breaking=True)
        .only('title', 'slug', 'is_short', 'created_at')
        .order_by('-created_at')[:12]
    )

    # ۵. دریافت فصل جاری[cite: 6]
    current_season = (
        Season.objects.filter(is_current=True).first()
        or Season.objects.order_by('-year').first()
    )

    # ۶. آخرین مسابقه برگزارشده و نتایج آن
    last_gp = None
    last_session = None
    last_gp_results = []

    if current_season:
        last_session = (
            Session.objects.filter(
                grand_prix__season=current_season,
                results__isnull=False,
            )
            .select_related('grand_prix', 'grand_prix__circuit', 'grand_prix__season')
            .order_by('-grand_prix__round_number', '-start_time')
            .distinct()
            .first()
        )

    if not last_session:
        last_session = (
            Session.objects.filter(results__isnull=False)
            .select_related('grand_prix', 'grand_prix__circuit', 'grand_prix__season')
            .order_by('-start_time')
            .distinct()
            .first()
        )

    if last_session:
        last_gp = last_session.grand_prix
        race_session = (
            Session.objects.filter(grand_prix=last_gp, session_type='race', results__isnull=False)
            .first()
        ) or last_session
        last_session = race_session
        last_gp_results = list(
            SessionResult.objects.filter(session=last_session)
            .select_related('driver', 'team')
            .order_by('position')[:10]
        )

    # ۷. جدول قهرمانی (رانندگان و سازندگان)
    top_drivers = []
    top_teams = []
    if current_season:
        top_drivers = list(
            DriverStanding.objects.filter(season=current_season)
            .select_related('driver', 'driver__team')
            .order_by('position')[:10]
        )
        top_teams = list(
            TeamStanding.objects.filter(season=current_season)
            .select_related('team')
            .order_by('position')[:10]
        )

    context = {
        'now': now,
        'next_session': next_session,
        'next_gp_sessions': next_gp_sessions,
        'featured_article': featured_article,
        'recent_articles': recent_articles,
        'short_articles': short_articles,
        'ticker_items': ticker_items,
        'last_gp': last_gp,
        'last_session': last_session,
        'last_gp_results': last_gp_results,
        'top_drivers': top_drivers,
        'top_teams': top_teams,
        'season': current_season,
    }
    return render(request, 'news/home.html', context)


def article_detail_view(request, slug):
    article = get_object_or_404(
        Article.objects.prefetch_related('related_drivers', 'related_teams').select_related(
            'category',
            'author',
            'related_grand_prix',
            'related_grand_prix__season',
        ),
        slug=slug,
        status='published',
    )
    record_object_view(request, Article, article.pk, "articles")
    article.views_count += 1  # برای نمایش لحظه‌ای در همان بارگذاری صفحه در صورت نیاز

    related_articles = Article.objects.filter(
        status='published'
    ).filter(
        Q(related_drivers__in=article.related_drivers.all()) |
        Q(related_teams__in=article.related_teams.all()) |
        Q(category=article.category)
    ).exclude(id=article.id).distinct().select_related('category')[:3]

    context = {
        'article': article,
        'related_articles': related_articles,
    }
    return render(request, 'news/article_detail.html', context)


def articles_list_view(request):
    articles_queryset = Article.objects.filter(status='published').select_related('category', 'author')

    selected_type = request.GET.get('type')
    if selected_type == 'short':
        articles_queryset = articles_queryset.filter(is_short=True)

    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        articles_queryset = articles_queryset.filter(category__slug=category_slug)
        selected_category = category_slug

    search_query = request.GET.get('q')
    if search_query:
        articles_queryset = articles_queryset.filter(
            Q(title__icontains=search_query) |
            Q(lead__icontains=search_query) |
            Q(body__icontains=search_query)
        ).distinct()
        record_search_query(request, search_query, articles_queryset.count())

    paginator = Paginator(articles_queryset, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'selected_type': selected_type,
        'search_query': search_query,
    }
    return render(request, 'news/articles_list.html', context)


def global_search_view(request):
    query = request.GET.get('q', '').strip()

    seasons = []
    grands_prix = []
    drivers = []
    teams = []
    articles = []
    total_results = 0

    if query:
        if query.isdigit():
            seasons = list(Season.objects.filter(year=int(query)))

        grands_prix = list(
            GrandPrix.objects.select_related('season', 'circuit')
            .filter(
                Q(name__icontains=query)
                | Q(circuit__name__icontains=query)
                | Q(circuit__country__icontains=query)
                | Q(circuit__location__icontains=query)
            )
            .order_by('-season__year', 'round_number')[:12]
        )

        driver_q = (
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(code__icontains=query)
            | Q(country__icontains=query)
            | Q(team__name__icontains=query)
        )
        if query.isdigit():
            driver_q |= Q(permanent_number=int(query))

        drivers = list(
            Driver.objects.select_related('team')
            .filter(driver_q)
            .order_by('permanent_number')[:12]
        )

        teams = list(
            Team.objects.prefetch_related('drivers')
            .filter(
                Q(name__icontains=query)
                | Q(full_name__icontains=query)
                | Q(base__icontains=query)
                | Q(team_chief__icontains=query)
                | Q(power_unit__icontains=query)
            )
            .order_by('name')[:10]
        )

        articles = list(
            Article.objects.filter(status='published')
            .select_related('category', 'author')
            .filter(
                Q(title__icontains=query)
                | Q(lead__icontains=query)
                | Q(body__icontains=query)
            )
            .distinct()[:12]
        )

        total_results = (
            len(seasons)
            + len(grands_prix)
            + len(drivers)
            + len(teams)
            + len(articles)
        )
        record_search_query(request, query, total_results)

    context = {
        'search_query': query,
        'seasons': seasons,
        'grands_prix': grands_prix,
        'drivers': drivers,
        'teams': teams,
        'articles': articles,
        'total_results': total_results,
    }
    return render(request, 'news/search_results.html', context)