from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.grandprix_calendar.models import GrandPrix, Season, Session
from apps.racing.models import Driver, DriverStanding, Team

from .models import Article, Category


def home_view(request):
    now = timezone.now()

    # ۱. نزدیک‌ترین سشن آینده
    next_session = Session.objects.filter(start_time__gte=now).select_related('grand_prix', 'grand_prix__circuit').order_by('start_time').first()

    # ۲. آخرین اخبار منتشر شده
    articles = Article.objects.filter(status='published').select_related('category', 'author')[:6]
    featured_article = articles[0] if articles else None
    recent_articles = articles[1:] if len(articles) > 1 else []

    # ۳. دریافت فصل جاری و ۵ راننده برتر
    current_season = Season.objects.filter(is_current=True).first() or Season.objects.order_by('-year').first()
    top_drivers = []
    if current_season:
        top_drivers = DriverStanding.objects.filter(
            season=current_season
        ).select_related('driver', 'driver__team').order_by('position')[:5]

    context = {
        'next_session': next_session,
        'featured_article': featured_article,
        'recent_articles': recent_articles,
        'top_drivers': top_drivers,
        'season': current_season,
    }
    return render(request, 'news/home.html', context)


def article_detail_view(request, slug):
    # دریافت خبر منتشر شده همراه با تیم‌ها و راننده‌های تگ‌شده با بهینه‌سازی کوئری
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

    # پیدا کردن اخبار مرتبط بر اساس راننده یا تیم مشترک (بدون احتساب خود این خبر)
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

    # ۱. فیلتر بر اساس دسته‌بندی (در صورت انتخاب کاربر)
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        articles_queryset = articles_queryset.filter(category__slug=category_slug)
        selected_category = category_slug

    # ۲. موتور جستجو در عنوان، لید و متن
    search_query = request.GET.get('q')
    if search_query:
        articles_queryset = articles_queryset.filter(
            Q(title__icontains=search_query) |
            Q(lead__icontains=search_query) |
            Q(body__icontains=search_query)
        ).distinct()

    # ۳. صفحه‌بندی (هر صفحه ۹ خبر)
    paginator = Paginator(articles_queryset, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # دریافت تمام دسته‌بندی‌ها برای نمایش در نوار بالای آرشیو
    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
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
        # ۱. جستجو در فصل‌ها (اگر کاربر سال را به صورت عدد وارد کرده باشد، مثلا 2026)
        if query.isdigit():
            seasons = list(Season.objects.filter(year=int(query)))

        # ۲. جستجو در گرندپری‌ها، پیست‌ها و کشورها
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

        # ۳. جستجو در رانندگان (نام، نام خانوادگی، کد سه حرفی، کشور، تیم یا شماره راننده)
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

        # ۴. جستجو در تیم‌ها (نام، نام تجاری، مقر، مدیر تیم، پیشرانه)
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

        # ۵. جستجو در اخبار و مقالات منتشر شده
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