from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Article
from racing.models import Driver, Team

# ۱. سایت‌مپ اخبار منتشر شده (با اولویت بالا)
class ArticleSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Article.objects.filter(status='published').order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at


# ۲. سایت‌مپ صفحات ثابت و اصلی سایت
class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            'news:home',
            'news:articles_list',
            'racing:standings',
            'grandprix_calendar:calendar_list',
            'racing:drivers_list',
            'racing:teams_list',
        ]

    def location(self, item):
        return reverse(item)


# ۳. سایت‌مپ رانندگان
class DriverSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Driver.objects.all().order_by('permanent_number')


# ۴. سایت‌مپ تیم‌ها
class TeamSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Team.objects.all().order_by('name')