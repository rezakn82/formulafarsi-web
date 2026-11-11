from django.db import models
from racing.models import Circuit

class Season(models.Model):
    year = models.PositiveSmallIntegerField(unique=True, verbose_name="سال فصل (مثلا 2026)")
    is_current = models.BooleanField(default=False, verbose_name="فصل جاری است؟")

    class Meta:
        verbose_name = "فصل"
        verbose_name_plural = "فصل‌ها"

    def __str__(self):
        return str(self.year)


class GrandPrix(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='grands_prix', verbose_name="فصل")
    round_number = models.PositiveSmallIntegerField(verbose_name="شماره راند")
    name = models.CharField(max_length=150, verbose_name="نام گرندپری (مثلا گرندپری بحرین)")
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE, related_name='grands_prix', verbose_name="پیست")
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
        ('sprint_shootout', 'شوت‌اوت اسپرینت'),
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