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
    help = "تولید دیتای تستی کامل برای وبسایت فرمولافارسی (شامل تست تک‌فصلی، آرشیو نتایج و تگ‌های کلیکی اخبار)"

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
        season_2026, _ = Season.objects.update_or_create(year=2026, defaults={"is_current": True})

        season_2025.refresh_from_db()
        active_seasons_count = Season.objects.filter(is_current=True).count()
        if not season_2025.is_current and season_2026.is_current and active_seasons_count == 1:
            self.stdout.write(
                self.style.SUCCESS("✔ تست ۱ موفق: با فعال شدن فصل ۲۰۲۶، تیک فصل جاری از روی فصل ۲۰۲۵ خودکار برداشته شد!")
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

        # ۴. ساخت ۱۰ راننده (۲ راننده برای هر تیم)
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

        # ۵. ساخت جدول رده‌بندی رانندگان و تیم‌ها برای هر دو فصل ۲۰۲۵ و ۲۰۲۶
        points_scale_2026 = [44, 36, 30, 24, 20, 16, 12, 8, 4, 1]
        points_scale_2025 = [410, 385, 340, 290, 250, 190, 140, 95, 60, 22]

        for pos, driver in enumerate(drivers, start=1):
            DriverStanding.objects.update_or_create(
                season=season_2026,
                driver=driver,
                defaults={
                    "position": pos,
                    "points": Decimal(str(points_scale_2026[pos - 1])),
                    "wins": 1 if pos in (1, 2) else 0,
                },
            )
            DriverStanding.objects.update_or_create(
                season=season_2025,
                driver=driver,
                defaults={
                    "position": pos,
                    "points": Decimal(str(points_scale_2025[pos - 1])),
                    "wins": 8 if pos == 1 else (4 if pos == 2 else 1),
                },
            )

        for pos, team in enumerate(teams, start=1):
            TeamStanding.objects.update_or_create(
                season=season_2026,
                team=team,
                defaults={
                    "position": pos,
                    "points": Decimal(str(80 - (pos * 12))),
                    "wins": 1 if pos in (1, 2) else 0,
                },
            )
            TeamStanding.objects.update_or_create(
                season=season_2025,
                team=team,
                defaults={
                    "position": pos,
                    "points": Decimal(str(650 - (pos * 90))),
                    "wins": 10 if pos == 1 else 4,
                },
            )

        # تابع کمکی برای پر کردن نتایج یک سشن
        def populate_session_results(session_obj, ordered_drivers):
            race_pts = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
            sprint_pts = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
            s_type = session_obj.session_type

            for pos, drv in enumerate(ordered_drivers, start=1):
                is_qual = s_type in ("qualifying", "sprint_shootout")
                is_race_or_sprint = s_type in ("race", "sprint")
                status = "dnf" if (is_race_or_sprint and pos == 10) else "finished"

                pts = Decimal("0.0")
                if s_type == "race" and status == "finished":
                    pts = Decimal(str(race_pts[pos - 1]))
                elif s_type == "sprint" and status == "finished":
                    pts = Decimal(str(sprint_pts[pos - 1]))

                if is_qual:
                    time_gap = ""
                    laps = random.randint(12, 18)
                elif s_type in ("fp1", "fp2", "fp3"):
                    time_gap = "1:30.412" if pos == 1 else f"+0.{pos * 115:03d}s"
                    laps = random.randint(20, 28)
                else:
                    time_gap = (
                        "1:32:15.412"
                        if pos == 1
                        else ("DNF (نقص فنی)" if status == "dnf" else f"+{pos * 2.341:.3f}s")
                    )
                    laps = 57 if s_type == "race" else 19
                    if status == "dnf":
                        laps -= 12

                SessionResult.objects.update_or_create(
                    session=session_obj,
                    driver=drv,
                    defaults={
                        "team": drv.team,
                        "position": pos,
                        "status": status,
                        "grid_position": pos if is_race_or_sprint else None,
                        "laps": laps,
                        "time_or_gap": time_gap,
                        "q1_time": f"1:30.{pos}12" if is_qual else "",
                        "q2_time": f"1:29.{pos}85" if (is_qual and pos <= 8) else "",
                        "q3_time": f"1:29.{pos}10" if (is_qual and pos <= 5) else "",
                        "points": pts,
                        "fastest_lap": (pos == 2 and s_type == "race"),
                    },
                )

        # ۶. ساخت پیست‌ها، گرندپری‌ها و سشن‌ها برای فصل جاری (۲۰۲۶)
        now = timezone.now()
        gp_configs = [
            (1, "گرندپری بحرین", "پیست بین‌المللی صخیر", "صخیر", "بحرین", "5.412", 15, -14, False),
            (2, "گرندپری عربستان", "پیست خیابانی جده", "جده", "عربستان", "6.174", 27, -7, True),
            (3, "گرندپری استرالیا", "آلبرت پارک", "ملبورن", "استرالیا", "5.278", 14, 2, False),
            (4, "گرندپری ژاپن", "پیست سوزوکا", "سوزوکا", "ژاپن", "5.807", 18, 14, True),
        ]

        grands_prix = []
        for round_num, gp_name, circuit_name, loc, country, length, corners, offset_days, is_sprint in gp_configs:
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
                season=season_2026,
                round_number=round_num,
                defaults={
                    "name": gp_name,
                    "circuit": circuit,
                    "start_date": race_day - timedelta(days=2),
                    "end_date": race_day,
                },
            )
            grands_prix.append(gp)

            session_offsets = (
                [("fp1", -48), ("sprint_shootout", -44), ("sprint", -24), ("qualifying", -20), ("race", 0)]
                if is_sprint
                else [("fp1", -48), ("fp2", -44), ("fp3", -24), ("qualifying", -20), ("race", 0)]
            )

            for s_type, hours_diff in session_offsets:
                session_obj, _ = Session.objects.update_or_create(
                    grand_prix=gp,
                    session_type=s_type,
                    defaults={
                        "start_time": now + timedelta(days=offset_days, hours=hours_diff),
                    },
                )

                if offset_days < 0:
                    shuffled_drivers = list(drivers)
                    if round_num == 2:
                        shuffled_drivers[0], shuffled_drivers[2] = shuffled_drivers[2], shuffled_drivers[0]
                    populate_session_results(session_obj, shuffled_drivers)

        # ۷. ساخت یک گرندپری آرشیوی در فصل ۲۰۲۵ (برای تست تغییر فصل ?season=2025)
        old_gp_date = (now - timedelta(days=300)).date()
        gp_2025, _ = GrandPrix.objects.update_or_create(
            season=season_2025,
            round_number=1,
            defaults={
                "name": "گرندپری بحرین ۲۰۲۵",
                "circuit": grands_prix[0].circuit,
                "start_date": old_gp_date - timedelta(days=2),
                "end_date": old_gp_date,
            },
        )
        for s_type, hours_diff in [("qualifying", -20), ("race", 0)]:
            old_session, _ = Session.objects.update_or_create(
                grand_prix=gp_2025,
                session_type=s_type,
                defaults={"start_time": now - timedelta(days=300, hours=-hours_diff)},
            )
            populate_session_results(old_session, list(reversed(drivers)))

        # ۸. ساخت دسته‌بندی‌ها و ۱۲ خبر فارسی (با تگ‌های هدفمند برای تست کلیک‌پذیری تگ‌ها)
        cat_titles = ["گزارش مسابقه", "تحلیل فنی", "نقل و انتقالات", "مصاحبه اختصاصی"]
        categories = []
        for title in cat_titles:
            cat, _ = Category.objects.update_or_create(
                slug=slugify(title, allow_unicode=True),
                defaults={"title": title},
            )
            categories.append(cat)

        for i in range(1, 13):
            if i == 1:
                title = "پیروزی خیره‌کننده فراری در افتتاحیه فصل ۲۰۲۶ بحرین (تست تگ‌های فصل جاری)"
                target_gp = grands_prix[0]  # گرندپری بحرین ۲۰۲۶
                tagged_drivers = [drivers[0], drivers[1]]  # لکلرک و همیلتون
                tagged_teams = [teams[0]]  # فراری
            elif i == 2:
                title = "مروری بر آرشیو: نبرد تاریخی ورستپن در بحرین ۲۰۲۵ (تست تگ گرندپری آرشیوی)"
                target_gp = gp_2025  # گرندپری بحرین ۲۰۲۵ (فصل گذشته)
                tagged_drivers = [drivers[2], drivers[3]]  # ورستپن و لاوسون
                tagged_teams = [teams[1]]  # ردبول
            else:
                title = f"{fake.sentence(nb_words=6).rstrip('.')} (خبر آزمایشی {i})"
                target_gp = grands_prix[i % len(grands_prix)]
                tagged_drivers = random.sample(drivers, k=2)
                tagged_teams = random.sample(teams, k=2)

            art, _ = Article.objects.update_or_create(
                slug=f"test-f1-news-{i}",
                defaults={
                    "title": title,
                    "author": admin_user,
                    "category": categories[i % len(categories)],
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
                    "related_grand_prix": target_gp,
                },
            )
            art.related_drivers.set(tagged_drivers)
            art.related_teams.set(tagged_teams)

        self.stdout.write(
            self.style.SUCCESS("✔ تست ۲ آماده است: تگ‌های کلیکی راننده، تیم و گرندپری در اخبار ۱ تا ۱۲ ثبت شدند!")
        )
        self.stdout.write(self.style.SUCCESS("✅ دیتای تستی فرمولافارسی با موفقیت ساخته شد!"))
        self.stdout.write(self.style.SUCCESS("👤 یوزر ادمین: admin | رمز عبور: admin1234"))