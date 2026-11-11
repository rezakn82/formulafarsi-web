from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Article, Category
from grandprix_calendar.models import Session
from django.core.paginator import Paginator

def home_view(request):
    now = timezone.now()
    next_session = Session.objects.filter(start_time__gte=now).select_related('grand_prix', 'grand_prix__circuit').order_by('start_time').first()
    articles = Article.objects.filter(status='published').select_related('category', 'author')[:6]

    context = {
        'next_session': next_session,
        'featured_article': articles[0] if articles else None,
        'recent_articles': articles[1:] if len(articles) > 1 else [],
    }
    return render(request, 'news/home.html', context)


def article_detail_view(request, slug):
    # دریافت خبر منتشر شده همراه با تیم‌ها و راننده‌های تگ‌شده با بهینه‌سازی کوئری
    article = get_object_or_404(
        Article.objects.prefetch_related('related_drivers', 'related_teams').select_related('category', 'author', 'related_grand_prix'),
        slug=slug,
        status='published'
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