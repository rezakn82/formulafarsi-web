from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Article
from grandprix_calendar.models import Session

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