from django.shortcuts import render
from django.utils import timezone
from .models import Article
from grandprix_calendar.models import Session

def home_view(request):
    now = timezone.now()

    # پیدا کردن نزدیک‌ترین سشن آینده (تمرین، تعیین خط یا مسابقه)
    next_session = Session.objects.filter(start_time__gte=now).select_related('grand_prix', 'grand_prix__circuit').order_by('start_time').first()

    # دریافت آخرین اخبار منتشر شده (بهینه شده با select_related برای جلوگیری از کوئری‌های تکراری)
    articles = Article.objects.filter(status='published').select_related('category', 'author')[:6]

    # مهم‌ترین خبر (خبر اول) و سایر اخبار
    featured_article = articles[0] if articles else None
    recent_articles = articles[1:] if len(articles) > 1 else []

    context = {
        'next_session': next_session,
        'featured_article': featured_article,
        'recent_articles': recent_articles,
    }
    return render(request, 'news/home.html', context)