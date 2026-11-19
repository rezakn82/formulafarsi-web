from django.db import models
from django.urls import reverse

class Circuit(models.Model):
    name = models.CharField(max_length=150, verbose_name="نام پیست")
    location = models.CharField(max_length=100, verbose_name="شهر / مکان")
    country = models.CharField(max_length=100, verbose_name="کشور")
    length_km = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="طول پیست (کیلومتر)")
    corners = models.PositiveSmallIntegerField(verbose_name="تعداد پیچ‌ها")
    lap_record = models.CharField(max_length=100, blank=True, null=True, verbose_name="رکورد پیست")
    image = models.ImageField(upload_to='circuits/', verbose_name="تصویر یا نقشه پیست")

    class Meta:
        verbose_name = "پیست"
        verbose_name_plural = "پیست‌ها"

    def __str__(self):
        return f"{self.name} ({self.country})"


class Team(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام تیم")
    full_name = models.CharField(max_length=200, blank=True, verbose_name="نام رسمی تجاری")
    base = models.CharField(max_length=100, verbose_name="مقر تیم")
    team_chief = models.CharField(max_length=100, verbose_name="مدیر تیم")
    power_unit = models.CharField(max_length=100, verbose_name="پیشرانه / موتور")
    color_code = models.CharField(max_length=7, default="#FFFFFF", help_text="کد هگز رنگ مثلا #E80020", verbose_name="رنگ سازمانی")
    logo = models.ImageField(upload_to='teams/logos/', verbose_name="لوگوی تیم")
    car_image = models.ImageField(upload_to='teams/cars/', blank=True, null=True, verbose_name="تصویر خودرو")
    bio = models.TextField(blank=True, verbose_name="بیوگرافی و تاریخچه")

    # آمار عملکرد تیم (مورد ۷)
    grands_prix_entered = models.PositiveIntegerField(default=0, verbose_name="تعداد گرندپری وارد شده")
    career_points = models.DecimalField(max_digits=8, decimal_places=1, default=0.0, verbose_name="کل امتیازات کسب شده")
    highest_race_finish = models.CharField(max_length=50, blank=True, help_text="مثال: 1 (x15)", verbose_name="بهترین رده مسابقه (تعداد دفعات)")
    highest_grid_position = models.CharField(max_length=50, blank=True, help_text="مثال: 1 (x12)", verbose_name="بهترین خط شروع (تعداد دفعات)")
    pole_positions = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد پول پوزیشن")
    podiums = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد پودیوم")
    world_championships = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد قهرمانی جهان")
    views_count = models.PositiveIntegerField(default=0, db_index=True, verbose_name="تعداد بازدید پروفایل")

    class Meta:
        verbose_name = "تیم"
        verbose_name_plural = "تیم‌ها"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('racing:team_detail', kwargs={'pk': self.pk})


class Driver(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="نام")
    last_name = models.CharField(max_length=50, verbose_name="نام خانوادگی")
    permanent_number = models.PositiveSmallIntegerField(unique=True, verbose_name="شماره راننده")
    code = models.CharField(max_length=3, unique=True, help_text="کد سه حرفی مثل VER یا HAM", verbose_name="کد اختصاری")
    country = models.CharField(max_length=100, verbose_name="کشور")
    date_of_birth = models.DateField(verbose_name="تاریخ تولد")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers', verbose_name="تیم فعلی")
    is_main_driver = models.BooleanField(
        default=True,
        help_text="اگر تیک نخورد (راننده رزرو / تمرینی)، در صفحه رانندگان و لیست رانندگان تیم نمایش داده نمی‌شود اما در نتایج جلسات و جدول رده‌بندی قابل انتخاب است.",
        verbose_name="راننده اصلی فصل؟",
    )
    portrait = models.ImageField(upload_to='drivers/', verbose_name="تصویر راننده")
    bio = models.TextField(blank=True, verbose_name="بیوگرافی")

    # آمار عملکرد راننده (مورد ۶)
    grands_prix_entered = models.PositiveIntegerField(default=0, verbose_name="تعداد گرندپری وارد شده")
    career_points = models.DecimalField(max_digits=7, decimal_places=1, default=0.0, verbose_name="کل امتیازات دوران حرفه‌ای")
    highest_race_finish = models.CharField(max_length=50, blank=True, help_text="مثال: 1 (x62)", verbose_name="بهترین رده مسابقه (تعداد دفعات)")
    highest_grid_position = models.CharField(max_length=50, blank=True, help_text="مثال: 1 (x40)", verbose_name="بهترین خط شروع (تعداد دفعات)")
    pole_positions = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد پول پوزیشن")
    podiums = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد پودیوم")
    world_championships = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد قهرمانی جهان")
    dnfs = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد DNF")
    views_count = models.PositiveIntegerField(default=0, db_index=True, verbose_name="تعداد بازدید پروفایل")

    class Meta:
        verbose_name = "راننده"
        verbose_name_plural = "رانندگان"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        role = "" if self.is_main_driver else " [رزرو]"
        return f"{self.full_name} (#{self.permanent_number}){role}"

    def get_absolute_url(self):
        return reverse('racing:driver_detail', kwargs={'code': self.code})


class DriverStanding(models.Model):
    season = models.ForeignKey('grandprix_calendar.Season', on_delete=models.CASCADE, related_name='driver_standings', verbose_name="فصل")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='standings', verbose_name="راننده")
    position = models.PositiveSmallIntegerField(verbose_name="رتبه در جدول")
    points = models.DecimalField(max_digits=6, decimal_places=1, default=0.0, verbose_name="امتیاز")
    wins = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد بردها")

    class Meta:
        verbose_name = "رده‌بندی راننده"
        verbose_name_plural = "جدول رده‌بندی رانندگان"
        ordering = ['position', '-points']
        unique_together = ('season', 'driver')

    def __str__(self):
        return f"{self.position}. {self.driver.full_name} ({self.points} pts) - {self.season.year}"


class TeamStanding(models.Model):
    season = models.ForeignKey('grandprix_calendar.Season', on_delete=models.CASCADE, related_name='team_standings', verbose_name="فصل")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='standings', verbose_name="تیم")
    position = models.PositiveSmallIntegerField(verbose_name="رتبه در جدول")
    points = models.DecimalField(max_digits=6, decimal_places=1, default=0.0, verbose_name="امتیاز")
    wins = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد بردها")

    class Meta:
        verbose_name = "رده‌بندی تیمی"
        verbose_name_plural = "جدول رده‌بندی تیمی (سازندگان)"
        ordering = ['position', '-points']
        unique_together = ('season', 'team')

    def __str__(self):
        return f"{self.position}. {self.team.name} ({self.points} pts) - {self.season.year}"


class PowerUnitLimit(models.Model):
    """سقف مجاز استفاده از قطعات PU برای هر فصل (پیش‌فرض بر اساس قوانین ۲۰۲۶)."""

    season = models.OneToOneField(
        'grandprix_calendar.Season',
        on_delete=models.CASCADE,
        related_name='pu_limit',
        verbose_name="فصل",
    )
    ice_limit = models.PositiveSmallIntegerField(default=4, verbose_name="سقف مجاز ICE")
    tc_limit = models.PositiveSmallIntegerField(default=4, verbose_name="سقف مجاز TC")
    exh_limit = models.PositiveSmallIntegerField(default=4, verbose_name="سقف مجاز EXH")
    mguk_limit = models.PositiveSmallIntegerField(default=3, verbose_name="سقف مجاز MGU-K")
    es_limit = models.PositiveSmallIntegerField(default=3, verbose_name="سقف مجاز ES")
    pu_ce_limit = models.PositiveSmallIntegerField(default=3, verbose_name="سقف مجاز PU-CE")
    pu_anc_limit = models.PositiveSmallIntegerField(default=6, verbose_name="سقف مجاز PU-ANC")

    class Meta:
        verbose_name = "سقف مجاز قطعات PU"
        verbose_name_plural = "سقف‌های مجاز قطعات PU"
        ordering = ['-season__year']

    def __str__(self):
        return f"سقف مجاز قطعات PU فصل {self.season.year}"


class DriverPowerUnitUsage(models.Model):
    """تعداد قطعات PU استفاده‌شده توسط هر راننده در یک فصل."""

    season = models.ForeignKey(
        'grandprix_calendar.Season',
        on_delete=models.CASCADE,
        related_name='pu_usages',
        verbose_name="فصل",
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='pu_usages',
        verbose_name="راننده",
    )
    ice = models.PositiveSmallIntegerField(default=0, verbose_name="ICE")
    tc = models.PositiveSmallIntegerField(default=0, verbose_name="TC")
    exh = models.PositiveSmallIntegerField(default=0, verbose_name="EXH")
    mguk = models.PositiveSmallIntegerField(default=0, verbose_name="MGU-K")
    es = models.PositiveSmallIntegerField(default=0, verbose_name="ES")
    pu_ce = models.PositiveSmallIntegerField(default=0, verbose_name="PU-CE")
    pu_anc = models.PositiveSmallIntegerField(default=0, verbose_name="PU-ANC")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "مصرف قطعات PU راننده"
        verbose_name_plural = "جدول قطعات PU رانندگان"
        unique_together = ('season', 'driver')
        ordering = ['driver__team__name', 'driver__permanent_number']

    def __str__(self):
        return f"{self.driver.full_name} - فصل {self.season.year}"


class PowerUnitComponentInfo(models.Model):
    """توضیح وظیفه هر یک از قطعات پیشرانه برای نمایش در زیر جدول."""

    COMPONENT_CHOICES = [
        ('ICE', 'ICE'),
        ('TC', 'TC'),
        ('EXH', 'EXH'),
        ('MGU-K', 'MGU-K'),
        ('ES', 'ES'),
        ('PU-CE', 'PU-CE'),
        ('PU-ANC', 'PU-ANC'),
    ]

    code = models.CharField(
        max_length=10,
        choices=COMPONENT_CHOICES,
        unique=True,
        verbose_name="کد قطعه",
    )
    english_name = models.CharField(max_length=120, verbose_name="نام کامل انگلیسی")
    persian_name = models.CharField(max_length=120, verbose_name="نام فارسی")
    description = models.TextField(verbose_name="وظیفه و توضیحات قطعه")
    display_order = models.PositiveSmallIntegerField(default=1, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "معرفی قطعه PU"
        verbose_name_plural = "معرفی و وظایف قطعات PU"
        ordering = ['display_order', 'code']

    def __str__(self):
        return f"{self.code} — {self.persian_name}"