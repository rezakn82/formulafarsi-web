from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field

from apps.grandprix_calendar.models import GrandPrix
from apps.racing.models import Driver, Team


class Category(models.Model):
    title = models.CharField(max_length=80, verbose_name="عنوان دسته‌بندی")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="اسلاگ (URL)")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.title


class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('published', 'منتشر شده'),
    ]

    title = models.CharField(max_length=250, verbose_name="عنوان خبر")
    slug = models.SlugField(max_length=250, unique=True, allow_unicode=True, verbose_name="اسلاگ (URL)")
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name='articles', verbose_name="نویسنده")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles', verbose_name="دسته‌بندی")
    lead = models.TextField(max_length=500, verbose_name="لید / خلاصه خبر")
    body = CKEditor5Field(verbose_name="متن کامل خبر", config_name='news_editor')
    featured_image = models.ImageField(upload_to='news/%Y/%m/', verbose_name="تصویر شاخص")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="وضعیت انتشار")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین به‌روزرسانی")

    # روابط هوشمند برای فیلتر خبرها در صفحه اختصاصی راننده، تیم یا گرندپری
    related_drivers = models.ManyToManyField(Driver, blank=True, related_name='articles', verbose_name="رانندگان مرتبط")
    related_teams = models.ManyToManyField(Team, blank=True, related_name='articles', verbose_name="تیم‌های مرتبط")
    related_grand_prix = models.ForeignKey(GrandPrix, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles', verbose_name="گرندپری مرتبط")

    class Meta:
        verbose_name = "خبر"
        verbose_name_plural = "اخبار"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:article_detail', kwargs={'slug': self.slug})