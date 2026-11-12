from datetime import timedelta
from decimal import Decimal
from io import BytesIO
import random

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker
from PIL import Image, ImageDraw

from apps.grandprix_calendar.models import GrandPrix, Season, Session, SessionResult
from apps.news.models import Article, Category
from apps.racing.models import Circuit, Driver, DriverStanding, Team, TeamStanding


def create_placeholder_image(filename: str, width: int, height: int, color: str) -> ContentFile:
    """ساخت تصویر تستی در حافظه رم با Pillow برای جلوگیری از خطای نبود عکس در قالب‌ها."""
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width - 10, height - 10], outline="#ffffff", width=3)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue(), name=filename)


class Command(BaseCommand):
    help = "تولید دیتای تستی کامل برای وبسایت فرمولافارسی (شامل تست تک‌فصلی و آرشیو نتایج)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="پاک کردن کامل دیتای قبلی قبل از ساخت دیتای جدید",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker("fa_IR")

        if options["flush"]:
            self.stdout.write(self.style.WARNING("در حال پاکسازی اطلاعات قبلی..."))
            Article.objects.all().delete()
            Category.objects.all().delete()
            SessionResult.objects.all().delete()
            Session.objects.all().delete()
            GrandPrix.objects.all().delete()
            Season.objects.all().delete()
            Driver.objects.all().delete()
            Team.objects.all().delete()
            Circuit.objects.all().delete()

        # ۱. ساخت کاربر نویسنده / ادمین
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "سردبیر",
                "last_name": "فرمولافارسی",
                "email": "admin@formulafarsi.ir",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("admin1234")
            admin_user.save()

        # ۲. ساخت فصل‌ها و تست خودکار قابلیت Single Active Season Enforcement
        self.stdout.write("در حال تست قابلیت تک‌فصلی (Single Active Season)...")
        season_2024, _ = Season.objects.update_or_create(year=2024, defaults={"is_current": False})
        season_2025, _ = Season.objects.update_or_create(year=2025, defaults={"is_current": True})
        # حالا فصل ۲۰۲۶ را هم با is_current=True ذخیره می‌کنیم تا ببینیم ۲۰۲۵ خودکار False می‌شود یا نه
        season_2026, _ = Season.objects.update_or_create(year=2026, defaults={"is_current": True})

        season_2025.refresh_from_db()
        active_seasons_count = Season.objects.filter(is_current=True).count()
        if not season_2025.is_current and season_2026.is_current and active_seasons_count == 1:
            self.stdout.write(
                self.style.SUCCESS("✔ تست موفق: با فعال شدن فصل ۲۰۲۶، تیک فصل جاری از روی فصل ۲۰۲۵ به صورت خودکار برداشته شد!")
            )
        else:
            self.stdout.write(
                self.style.ERROR("✘ خطا در تست فصل جاری: بیش از یک فصل فعال وجود دارد!")
            )

        # ۳. ساخت ۵ تیم واقعی فرمول یک با رنگ سازمانی دقیق
        teams_data = [
            ("فراری", "Scuderia Ferrari", "مارانلو، ایتالیا", "فردریک واسور", "فراری", "#E80020"),
            ("ردبول", "Oracle Red Bull Racing", "میلتون کینز، انگلستان", "کریستین هورنر", "هوندا RBPT", "#3671C6"),
            ("مک‌لارن", "McLaren Formula 1 Team", "وکینگ، انگلستان", "آندره‌آ استلا", "مرسدس", "#FF8000"),
        ]