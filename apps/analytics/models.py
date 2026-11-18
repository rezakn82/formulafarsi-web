from django.db import models


class DailySiteStat(models.Model):
    date = models.DateField(unique=True, db_index=True, verbose_name="تاریخ")
    total_views = models.PositiveIntegerField(default=0, verbose_name="کل بازدید صفحات (Pageviews)")
    unique_visitors = models.PositiveIntegerField(default=0, verbose_name="بازدیدکنندگان یکتا")

    class Meta:
        verbose_name = "آمار روزانه سایت"
        verbose_name_plural = "آمار روزانه سایت"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} — بازدید: {self.total_views} (یکتا: {self.unique_visitors})"


class DailyVisitorHash(models.Model):
    """نگهداری هش ناشناس بازدیدکننده در هر روز برای شمارش دقیق کاربران یکتا بدون ذخیره IP خام."""

    date = models.DateField(db_index=True, verbose_name="تاریخ")
    visitor_hash = models.CharField(max_length=64, verbose_name="هش بازدیدکننده")

    class Meta:
        verbose_name = "نشست یکتای روزانه"
        verbose_name_plural = "نشست‌های یکتای روزانه"
        constraints = [
            models.UniqueConstraint(
                fields=["date", "visitor_hash"],
                name="unique_daily_visitor_hash",
            )
        ]


class SearchQueryStat(models.Model):
    query = models.CharField(max_length=150, unique=True, db_index=True, verbose_name="عبارت جستجوشده")
    search_count = models.PositiveIntegerField(default=1, verbose_name="تعداد دفعات جستجو")
    last_results_count = models.PositiveIntegerField(default=0, verbose_name="تعداد نتایج آخرین جستجو")
    last_searched_at = models.DateTimeField(auto_now=True, verbose_name="آخرین زمان جستجو")

    class Meta:
        verbose_name = "آمار عبارت جستجو"
        verbose_name_plural = "آمار عبارات جستجوشده"
        ordering = ["-search_count", "-last_searched_at"]

    def __str__(self):
        return f"{self.query} ({self.search_count})"