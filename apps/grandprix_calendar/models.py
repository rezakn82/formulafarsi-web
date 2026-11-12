from django.db import models, transaction
from django.db.models import Q

class Season(models.Model):
    year = models.PositiveSmallIntegerField(unique=True, verbose_name="سال فصل (مثلا 2026)")
    is_current = models.BooleanField(default=False, verbose_name="فصل جاری است؟")

    class Meta:
        verbose_name = "فصل"
        verbose_name_plural = "فصل‌ها"
        ordering = ['-year']
        constraints = [
            models.UniqueConstraint(
                fields=['is_current'],
                condition=Q(is_current=True),
                name='unique_current_season',
            )
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_current:
                # غیرفعال کردن سایر فصل‌های جاری قبل از ذخیره این فصل
                Season.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
            super().save(*args, **kwargs)

    def __str__(self):
        return str(self.year)


class GrandPrix(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='grands_prix', verbose_name="فصل")
    round_number = models.PositiveSmallIntegerField(verbose_name="شماره راند")
    name = models.CharField(max_length=150, verbose_name="نام گرندپری (مثلا گرندپری بحرین)")
    circuit = models.ForeignKey('racing.Circuit', on_delete=models.CASCADE, related_name='grands_prix', verbose_name="پیست")
    start_date = models.DateField(verbose_name="تاریخ شروع آخرهفته")
    end_date = models.DateField(verbose_name="تاریخ پایان (روز مسابقه)")

    class Meta:
        verbose_name = "گرندپری"
        verbose_name_plural = "گرندپری‌ها"
        ordering = ['round_number']
        unique_together = ('season', 'round_number')

    def __str__(self):
        return f"Round {self.round_number}: {self.name} ({self.season.year})"


class Session(models.Model):
    SESSION_TYPES = [
        ('fp1', 'تمرین اول (FP1)'),
        ('fp2', 'تمرین دوم (FP2)'),
        ('fp3', 'تمرین سوم (FP3)'),
        ('qualifying', 'تعیین خط (Qualifying)'),
        ('sprint_qualifying', 'تعیین خط اسپرینت'),
        ('sprint', 'مسابقه اسپرینت'),
        ('race', 'مسابقه اصلی (Main Race)'),
    ]

    grand_prix = models.ForeignKey(GrandPrix, on_delete=models.CASCADE, related_name='sessions', verbose_name="گرندپری")
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, verbose_name="نوع جلسه")
    start_time = models.DateTimeField(verbose_name="زمان شروع (UTC)")

    class Meta:
        verbose_name = "جلسه مسابقه"
        verbose_name_plural = "جلسات مسابقه"
        ordering = ['start_time']

    def __str__(self):
        return f"{self.grand_prix.name} - {self.get_session_type_display()}"


class SessionResult(models.Model):
    STATUS_CHOICES = [
        ('finished', 'پایان یافته (Finished)'),
        ('dnf', 'عدم پایان (DNF)'),
        ('dns', 'عدم شروع (DNS)'),
        ('dsq', 'رد صلاحیت (DSQ)'),
    ]

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name="جلسه مسابقه",
    )
    driver = models.ForeignKey(
        'racing.Driver',
        on_delete=models.CASCADE,
        related_name='session_results',
        verbose_name="راننده",
    )
    team = models.ForeignKey(
        'racing.Team',
        on_delete=models.CASCADE,
        related_name='session_results',
        verbose_name="تیم (در این گرندپری)",
    )
    position = models.PositiveSmallIntegerField(verbose_name="رتبه")
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='finished',
        verbose_name="وضعیت",
    )
    grid_position = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="خط شروع (Grid)",
    )
    laps = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="تعداد دورها",
    )
    time_or_gap = models.CharField(
        max_length=50,
        blank=True,
        help_text="مثال: 1:31:44.742 برای نفر اول یا +2.451s برای نفرات بعدی",
        verbose_name="زمان / فاصله",
    )
    q1_time = models.CharField(max_length=20, blank=True, verbose_name="زمان Q1 / SQ1")
    q2_time = models.CharField(max_length=20, blank=True, verbose_name="زمان Q2 / SQ2")
    q3_time = models.CharField(max_length=20, blank=True, verbose_name="زمان Q3 / SQ3")
    points = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0.0,
        verbose_name="امتیاز",
    )
    fastest_lap = models.BooleanField(default=False, verbose_name="سریع‌ترین دور؟")

    class Meta:
        verbose_name = "نتیجه جلسه"
        verbose_name_plural = "نتایج جلسات"
        ordering = ['position']
        unique_together = ('session', 'driver')

    def __str__(self):
        return f"P{self.position} - {self.driver} ({self.session})"