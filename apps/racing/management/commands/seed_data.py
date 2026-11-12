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

from apps.grandprix_calendar.models import GrandPrix, Season, Session
from apps.news.models import Article, Category
from apps.racing.models import Circuit, Driver, DriverStanding, Team, TeamStanding

# اگر مدل SessionResult را در مرحله قبل اضافه کرده‌اید، خودکار شناسایی می‌شود
try:
    from apps.grandprix_calendar.models import SessionResult
    HAS_SESSION_RESULT = True
except ImportError:
    HAS_SESSION_RESULT = False


def create_placeholder_image(filename: str, width: int, height: int, color: str) -> ContentFile:
    """ساخت تصویر تستی در حافظه رم با Pillow برای جلوگیری از خطای نبود عکس در قالب‌ها."""
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width - 10, height - 10], outline="#ffffff", width=3)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue(), name=filename)


class Command(BaseCommand):
    help = "تولید دیتای تستی کامل برای وبسایت فرمولافارسی با استفاده از Faker"

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

        # ۲. ساخت فصل جاری
        season, _ = Season.objects.update_or_create(
            year=2026,
            defaults={"is_current": True},
        )

        # ۳. ساخت ۵ تیم واقعی فرمول یک با رنگ سازمانی دقیق
        teams_data = [
            ("فراری", "Scuderia Ferrari", "مارانلو، ایتالیا", "فردریک واسور", "فراری", "#E80020"),
            ("ردبول", "Oracle Red Bull Racing", "میلتون کینز، انگلستان", "کریستین هورنر", "هوندا RBPT", "#3671C6"),
            ("مک‌لارن", "McLaren Formula 1 Team", "وکینگ، انگلستان", "آندره‌آ استلا", "مرسدس", "#FF8000"),
            ("مرسدس", "Mercedes-AMG PETRONAS F1", "براکلی، انگلستان", "توتو وولف", "مرسدس", "#27F4D2"),
            ("آستون مارتین", "Aston Martin Aramco F1", "سیلوراستون، انگلستان", "مایک کرک", "مرسدس", "#229971"),
        ]
        teams = []
        for idx, (name, full_name, base, chief, pu, color) in enumerate(teams_data, start=1):
            team, _ = Team.objects.update_or_create(
                name=name,
                defaults={
                    "full_name": full_name,
                    "base": base,
                    "team_chief": chief,
                    "power_unit": pu,
                    "color_code": color,
                    "bio": f"<p>{fake.paragraph(nb_sentences=6)}</p><p>{fake.paragraph(nb_sentences=5)}</p>",
                    "logo": create_placeholder_image(f"team_logo_{idx}.jpg", 200, 200, color),
                    "car_image": create_placeholder_image(f"team_car_{idx}.jpg", 800, 300, color),
                },
            )
            teams.append(team)

        # ۴. ساخت ۱۰ راننده (۲ راننده برای هر تیم تا بخش هم‌تیمی هم تست شود)
        drivers_data = [
            ("شارل", "لکلرک", 16, "LEC", "موناکو", teams[0]),
            ("لوئیس", "همیلتون", 44, "HAM", "بریتانیا", teams[0]),
            ("مکس", "ورستپن", 1, "VER", "هلند", teams[1]),
            ("لیام", "لاوسون", 30, "LAW", "نیوزیلند", teams[1]),
            ("لندو", "نوریس", 4, "NOR", "بریتانیا", teams[2]),
            ("اسکار", "پیاستری", 81, "PIA", "استرالیا", teams[2]),
            ("جورج", "راسل", 63, "RUS", "بریتانیا", teams[3]),
            ("آندره‌آ کیمی", "آنتونلی", 12, "ANT", "ایتالیا", teams[3]),
            ("فرناندو", "آلونسو", 14, "ALO", "اسپانیا", teams[4]),
            ("لنس", "استرول", 18, "STR", "کانادا", teams[4]),
        ]
        drivers = []
        for first, last, num, code, country, team in drivers_data:
            driver, _ = Driver.objects.update_or_create(
                code=code,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "permanent_number": num,
                    "country": country,
                    "date_of_birth": fake.date_of_birth(minimum_age=19, maximum_age=42),
                    "team": team,
                    "bio": f"<h2>زندگینامه {first} {last}</h2><p>{fake.paragraph(nb_sentences=7)}</p>",
                    "portrait": create_placeholder_image(f"driver_{code}.jpg", 500, 500, team.color_code),
                },
            )
            drivers.append(driver)

        # ۵. ساخت جدول رده‌بندی رانندگان و تیم‌ها (DriverStanding & TeamStanding)
        points_scale = [75, 62, 54, 48, 40, 32, 24, 18, 10, 4]
        for pos, driver in enumerate(drivers, start=1):
            DriverStanding.objects.update_or_create(
                season=season,
                driver=driver,
                defaults={
                    "position": pos,
                    "points": Decimal(str(points_scale[pos - 1])),
                    "wins": 2 if pos == 1 else (1 if pos in (2, 3) else 0),
                },
            )

        for pos, team in enumerate(teams, start=1):
            TeamStanding.objects.update_or_create(
                season=season,
                team=team,
                defaults={
                    "position": pos,
                    "points": Decimal(str(130 - (pos * 20))),
                    "wins": 2 if pos == 1 else (1 if pos == 2 else 0),
                },
            )

        # ۶. ساخت پیست‌ها، گرندپری‌ها (گذشته، در حال برگزاری، آینده) و سشن‌ها
        now = timezone.now()
        gp_configs = [
            (1, "گرندپری بحرین", "پیست بین‌المللی صخیر", "صخیر", "بحرین", "5.412", 15, -14),  # ۲ هفته پیش (پایان یافته)
            (2, "گرندپری عربستان", "پیست خیابانی جده", "جده", "عربستان", "6.174", 27, -7),     # ۱ هفته پیش (پایان یافته)
            (3, "گرندپری استرالیا", "آلبرت پارک", "ملبورن", "استرالیا", "5.278", 14, 2),      # ۲ روز دیگر (برای تست تایمر معکوس صفحه اصلی!)
            (4, "گرندپری ژاپن", "پیست سوزوکا", "سوزوکا", "ژاپن", "5.807", 18, 14),             # ۲ هفته دیگر
        ]

        grands_prix = []
        for round_num, gp_name, circuit_name, loc, country, length, corners, offset_days in gp_configs:
            circuit, _ = Circuit.objects.update_or_create(
                name=circuit_name,
                defaults={
                    "location": loc,
                    "country": country,
                    "length_km": Decimal(length),
                    "corners": corners,
                    "lap_record": "1:31.447 - پدرو دلا روسا",
                    "image": create_placeholder_image(f"circuit_{round_num}.jpg", 800, 500, "#18181b"),
                },
            )

            race_day = (now + timedelta(days=offset_days)).date()
            gp, _ = GrandPrix.objects.update_or_create(
                season=season,
                round_number=round_num,
                defaults={
                    "name": gp_name,
                    "circuit": circuit,
                    "start_date": race_day - timedelta(days=2),
                    "end_date": race_day,
                },
            )
            grands_prix.append(gp)

            # ساخت ۵ سشن برای هر گرندپری
            session_offsets = [
                ("fp1", -48),
                ("fp2", -44),
                ("fp3", -24),
                ("qualifying", -20),
                ("race", 0),
            ]
            for s_type, hours_diff in session_offsets:
                session_obj, _ = Session.objects.update_or_create(
                    grand_prix=gp,
                    session_type=s_type,
                    defaults={
                        "start_time": now + timedelta(days=offset_days, hours=hours_diff),
                    },
                )

                # اگر گرندپری در گذشته برگزار شده و مدل SessionResult وجود دارد، نتایجش را هم پر کن
                if HAS_SESSION_RESULT and offset_days < 0:
                    race_pts = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
                    for pos, drv in enumerate(drivers, start=1):
                        SessionResult.objects.update_or_create(
                            session=session_obj,
                            driver=drv,
                            defaults={
                                "team": drv.team,
                                "position": pos,
                                "status": "finished" if pos < 10 else "dnf",
                                "grid_position": pos,
                                "laps": 57 if pos < 10 else 41,
                                "time_or_gap": "1:32:15.412" if pos == 1 else f"+{pos * 2.341:.3f}s",
                                "q1_time": f"1:30.{pos}12" if s_type == "qualifying" else "",
                                "q2_time": f"1:29.{pos}85" if s_type == "qualifying" else "",
                                "q3_time": f"1:29.{pos}10" if s_type == "qualifying" else "",
                                "points": Decimal(str(race_pts[pos - 1])) if s_type == "race" else Decimal("0.0"),
                                "fastest_lap": (pos == 1 and s_type == "race"),
                            },
                        )

        # ۷. ساخت دسته‌بندی‌ها و ۱۲ خبر فارسی (برای تست صفحه‌بندی ۹تایی، جستجو و تگ‌های هوشمند)
        cat_titles = ["گزارش مسابقه", "تحلیل فنی", "نقل و انتقالات", "مصاحبه اختصاصی"]
        categories = []
        for idx, title in enumerate(cat_titles, start=1):
            cat, _ = Category.objects.update_or_create(
                slug=slugify(title, allow_unicode=True),
                defaults={"title": title},
            )
            categories.append(cat)

        for i in range(1, 13):
            title = f"{fake.sentence(nb_words=6).rstrip('.')} (خبر آزمایشی {i})"
            art, _ = Article.objects.update_or_create(
                slug=f"test-f1-news-{i}",
                defaults={
                    "title": title,
                    "author": admin_user,
                    "category": random.choice(categories),
                    "lead": fake.paragraph(nb_sentences=3),
                    "body": (
                        f"<h2>{fake.sentence(nb_words=5)}</h2>"
                        f"<p>{fake.paragraph(nb_sentences=8)}</p>"
                        f"<blockquote>{fake.sentence(nb_words=10)}</blockquote>"
                        f"<h3>بررسی عملکرد تیم‌ها</h3>"
                        f"<p>{fake.paragraph(nb_sentences=8)}</p>"
                    ),
                    "featured_image": create_placeholder_image(
                        f"news_{i}.jpg", 1200, 675, random.choice(["#991b1b", "#1e3a8a", "#065f46", "#3f3f46"])
                    ),
                    "status": "published",
                    "related_grand_prix": random.choice(grands_prix),
                },
            )
            art.related_drivers.set(random.sample(drivers, k=2))
            art.related_teams.set(random.sample(teams, k=2))

        self.stdout.write(self.style.SUCCESS("✅ دیتای تستی فرمولافارسی با موفقیت ساخته شد!"))
        self.stdout.write(self.style.SUCCESS("👤 یوزر ادمین: admin | رمز عبور: admin1234"))