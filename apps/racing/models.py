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
    portrait = models.ImageField(upload_to='drivers/', verbose_name="تصویر راننده")
    bio = models.TextField(blank=True, verbose_name="بیوگرافی")

    class Meta:
        verbose_name = "راننده"
        verbose_name_plural = "رانندگان"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} (#{self.permanent_number})"

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