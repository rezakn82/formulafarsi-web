from datetime import timedelta
from decimal import Decimal
import hashlib
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

from apps.analytics.models import DailySiteStat, DailyVisitorHash, SearchQueryStat
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
    help = "تولید دیتای تستی کامل برای وبسایت فرمولافارسی (شامل آمار بازدید سایت، اخبار، رانندگان، تیم‌ها و جستجوها)"

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
            DailyVisitorHash.objects.all().delete()
            DailySiteStat.objects.all().delete()
            SearchQueryStat.objects.all().delete()
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

        # ۳. ساخت ۵ تیم واقعی فرمول یک به همراه آمار کامل تاریخچه و بازدید پروفایل
        teams_data = [
            ("فراری", "Scuderia Ferrari", "مارانلو، ایتالیا", "فردریک واسور", "فراری", "#E80020", 1100, "10240.5", "1 (x248)", "1 (x253)", 253, 825, 16, 4820),
            ("ردبول", "Oracle Red Bull Racing", "میلتون کینز، انگلستان", "کریستین هورنر", "هوندا RBPT", "#3671C6", 395, "7850.0", "1 (x122)", "1 (x103)", 103, 282, 6, 4150),
            ("مک‌لارن", "McLaren Formula 1 Team", "وکینگ، انگلستان", "آندره‌آ استلا", "مرسدس", "#FF8000", 972, "6950.5", "1 (x189)", "1 (x164)", 164, 524, 9, 3690),
            ("مرسدس", "Mercedes-AMG PETRONAS F1", "براکلی، انگلستان", "توتو وولف", "مرسدس", "#27F4D2", 318, "7620.5", "1 (x129)", "1 (x139)", 139, 298, 8, 3120),
            ("آستون مارتین", "Aston Martin Aramco F1", "سیلوراستون، انگلستان", "مایک کرک", "مرسدس", "#229971", 98, "512.0", "2 (x3)", "2 (x1)", 0, 9, 0, 1840),
        ]
        teams = []
        for idx, (name, full_name, base, chief, pu, color, gps, pts, best_race, best_grid, poles, podiums, wcc, views) in enumerate(teams_data, start=1):
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
                    "grands_prix_entered": gps,
                    "career_points": Decimal(pts),
                    "highest_race_finish": best_race,
                    "highest_grid_position": best_grid,
                    "pole_positions": poles,
                    "podiums": podiums,
                    "world_championships": wcc,
                    "views_count": views,
                },
            )
            teams.append(team)

        # ۴. ساخت ۱۰ راننده اصلی + ۱ راننده رزرو تستی (الیور برمن) با آمار کامل و تعداد بازدید
        drivers_data = [
            ("شارل", "لکلرک", 16, "LEC", "موناکو", teams[0], True, 149, "1430.0", "1 (x8)", "1 (x26)", 26, 43, 0, 21, 5420),
            ("لوئیس", "همیلتون", 44, "HAM", "بریتانیا", teams[0], True, 356, "4862.5", "1 (x105)", "1 (x104)", 104, 202, 7, 32, 6890),
            ("مکس", "ورستپن", 1, "VER", "هلند", teams[1], True, 209, "3023.5", "1 (x63)", "1 (x40)", 40, 112, 4, 32, 6310),
            ("لیام", "لاوسون", 30, "LAW", "نیوزیلند", teams[1], True, 11, "6.0", "9 (x3)", "5 (x1)", 0, 0, 0, 1, 1420),
            ("لندو", "نوریس", 4, "NOR", "بریتانیا", teams[2], True, 128, "1007.0", "1 (x4)", "1 (x9)", 9, 26, 0, 11, 4510),
            ("اسکار", "پیاستری", 81, "PIA", "استرالیا", teams[2], True, 46, "389.0", "1 (x2)", "2 (x5)", 0, 10, 0, 3, 2890),
            ("جورج", "راسل", 63, "RUS", "بریتانیا", teams[3], True, 128, "714.0", "1 (x3)", "1 (x5)", 5, 15, 0, 19, 2640),
            ("آندره‌آ کیمی", "آنتونلی", 12, "ANT", "ایتالیا", teams[3], True, 2, "18.0", "4 (x1)", "5 (x1)", 0, 0, 0, 0, 3180),
            ("فرناندو", "آلونسو", 14, "ALO", "اسپانیا", teams[4], True, 404, "2337.0", "1 (x32)", "1 (x22)", 22, 106, 2, 79, 3950),
            ("لنس", "استرول", 18, "STR", "کانادا", teams[4], True, 167, "292.0", "3 (x3)", "1 (x1)", 1, 3, 0, 31, 980),
            ("الیور", "برمن", 87, "BEA", "بریتانیا", teams[0], False, 3, "7.0", "7 (x1)", "10 (x1)", 0, 0, 0, 0, 840),
        ]
        drivers = []
        reserve_driver = None
        for first, last, num, code, country, team, is_main, gps, pts, best_race, best_grid, poles, podiums, wdc, dnfs, views in drivers_data:
            driver, _ = Driver.objects.update_or_create(
                code=code,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "permanent_number": num,
                    "country": country,
                    "date_of_birth": fake.date_of_birth(minimum_age=19, maximum_age=42),
                    "team": team,
                    "is_main_driver": is_main,
                    "bio": f"<h2>زندگینامه {first} {last}</h2><p>{fake.paragraph(nb_sentences=7)}</p>",
                    "portrait": create_placeholder_image(f"driver_{code}.jpg", 500, 500, team.color_code),
                    "grands_prix_entered": gps,
                    "career_points": Decimal(pts),
                    "highest_race_finish": best_race,
                    "highest_grid_position": best_grid,
                    "pole_positions": poles,
                    "podiums": podiums,
                    "world_championships": wdc,
                    "dnfs": dnfs,
                    "views_count": views,
                },
            )
            if is_main:
                drivers.append(driver)
            else:
                reserve_driver = driver

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

        def populate_session_results(session_obj, ordered_drivers):
            race_pts = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
            sprint_pts = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
            s_type = session_obj.session_type

            for pos, drv in enumerate(ordered_drivers, start=1):
                is_qual = s_type in ("qualifying", "sprint_qualifying", "sprint_shootout")
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
            (1, "گرندپری بحرین", "پیست بین‌المللی صخیر", "صخیر", "بحرین", "5.412", 15, -14, False, "مکس ورستپن (ردبول)", 57, 2004, "308.238", 3840),
            (2, "گرندپری عربستان", "پیست خیابانی جده", "جده", "عربستان", "6.174", 27, -7, True, "شارل لکلرک (فراری)", 50, 2021, "308.450", 3290),
            (3, "گرندپری استرالیا", "آلبرت پارک", "ملبورن", "استرالیا", "5.278", 14, 2, False, "لندو نوریس (مک‌لارن)", 58, 1996, "306.124", 4610),
            (4, "گرندپری ژاپن", "پیست سوزوکا", "سوزوکا", "ژاپن", "5.807", 18, 14, True, "مکس ورستپن (ردبول)", 53, 1987, "307.471", 1920),
        ]

        grands_prix = []
        for round_num, gp_name, circuit_name, loc, country, length, corners, offset_days, is_sprint, prev_winner, laps_cnt, first_yr, dist_km, gp_views in gp_configs:
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
                    "previous_winner": prev_winner,
                    "laps_count": laps_cnt,
                    "first_grand_prix_year": first_yr,
                    "race_distance_km": Decimal(dist_km),
                    "views_count": gp_views,
                },
            )
            grands_prix.append(gp)

            session_offsets = (
                [("fp1", -48), ("sprint_qualifying", -44), ("sprint", -24), ("qualifying", -20), ("race", 0)]
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
                    if round_num == 1 and s_type == "fp1" and reserve_driver:
                        shuffled_drivers[1] = reserve_driver
                    elif round_num == 2:
                        shuffled_drivers[0], shuffled_drivers[2] = shuffled_drivers[2], shuffled_drivers[0]
                    populate_session_results(session_obj, shuffled_drivers)

        # ۷. ساخت یک گرندپری آرشیوی در فصل ۲۰۲۵
        old_gp_date = (now - timedelta(days=300)).date()
        gp_2025, _ = GrandPrix.objects.update_or_create(
            season=season_2025,
            round_number=1,
            defaults={
                "name": "گرندپری بحرین ۲۰۲۵",
                "circuit": grands_prix[0].circuit,
                "start_date": old_gp_date - timedelta(days=2),
                "end_date": old_gp_date,
                "previous_winner": "مکس ورستپن (ردبول)",
                "laps_count": 57,
                "first_grand_prix_year": 2004,
                "race_distance_km": Decimal("308.238"),
                "views_count": 1450,
            },
        )
        for s_type, hours_diff in [("qualifying", -20), ("race", 0)]:
            old_session, _ = Session.objects.update_or_create(
                grand_prix=gp_2025,
                session_type=s_type,
                defaults={"start_time": now - timedelta(days=300, hours=-hours_diff)},
            )
            populate_session_results(old_session, list(reversed(drivers)))

        # ۸. ساخت دسته‌بندی‌ها و ۱۲ خبر اصلی با آمار بازدید متنوع
        cat_titles = ["گزارش مسابقه", "تحلیل فنی", "نقل و انتقالات", "مصاحبه اختصاصی", "خبر کوتاه"]
        categories = []
        for title in cat_titles:
            cat, _ = Category.objects.update_or_create(
                slug=slugify(title, allow_unicode=True),
                defaults={"title": title},
            )
            categories.append(cat)

        main_article_views = [8420, 5190, 3840, 2950, 4120, 1890, 2340, 3670, 1540, 2780, 3110, 6250]

        for i in range(1, 13):
            if i == 1:
                title = "پیروزی خیره‌کننده فراری در افتتاحیه فصل ۲۰۲۶ بحرین (تست تگ‌های فصل جاری)"
                target_gp = grands_prix[0]
                tagged_drivers = [drivers[0], drivers[1]]
                tagged_teams = [teams[0]]
            elif i == 2:
                title = "مروری بر آرشیو: نبرد تاریخی ورستپن در بحرین ۲۰۲۵ (تست تگ گرندپری آرشیوی)"
                target_gp = gp_2025
                tagged_drivers = [drivers[2], drivers[3]]
                tagged_teams = [teams[1]]
            else:
                title = f"{fake.sentence(nb_words=6).rstrip('.')} (خبر اصلی {i})"
                target_gp = grands_prix[i % len(grands_prix)]
                tagged_drivers = random.sample(drivers, k=2)
                tagged_teams = random.sample(teams, k=2)

            art, _ = Article.objects.update_or_create(
                slug=f"test-f1-news-{i}",
                defaults={
                    "title": title,
                    "author": admin_user,
                    "category": categories[i % 4],
                    "is_short": False,
                    "is_breaking": i in (1, 12),
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
                    "views_count": main_article_views[i - 1],
                    "related_grand_prix": target_gp,
                },
            )
            art.related_drivers.set(tagged_drivers)
            art.related_teams.set(tagged_teams)

        # ۹. ساخت ۶ خبر کوتاه (is_short=True) با آمار بازدید
        short_news_samples = [
            (
                "بسته آپدیت آیرودینامیکی جدید فراری برای گرندپری استرالیا تایید شد",
                "مهندسان مارانلو اعلام کردند کف جدید خودرو SF-26 در تمرین اول ملبورن روی خودروی شارل لکلرک و لوئیس همیلتون تست خواهد شد.",
                "",
                "#E80020",
                [drivers[0], drivers[1]],
                [teams[0]],
                True,
                3420,
            ),
            (
                "ورستپن: تنظیمات شبیه‌ساز ردبول برای پیست آلبرت پارک امیدوارکننده است",
                "قهرمان چهار دوره جهان پس از جلسات شبیه‌ساز در میلتون کینز ابراز امیدواری کرد که مشکل کم‌فرمانی خودرو در پیچ‌های سرعت متوسط برطرف شده باشد.",
                "",
                "#3671C6",
                [drivers[2]],
                [teams[1]],
                True,
                2890,
            ),
            (
                "پیرلی ترکیبات لاستیک نرم‌تر C3، C4 و C5 را برای آخرهفته ملبورن انتخاب کرد",
                "تامین‌کننده رسمی تایرهای فرمول یک با هدف افزایش تنوع استراتژی پیت‌استاپ، یک پله ترکیبات نرم‌تر نسبت به سال گذشته به استرالیا می‌آورد.",
                "<p>پیرلی رسماً اعلام کرد تیم‌ها در گرندپری استرالیا به ترکیبات C3 (هارد)، C4 (مدیوم) و C5 (سافت) دسترسی خواهند داشت.</p>",
                "#d97706",
                [],
                [],
                False,
                1650,
            ),
            (
                "آندره‌آ استلا: مک‌لارن هنوز به سقف پتانسیل خودروی ۲۰۲۶ نرسیده است",
                "مدیر تیم مک‌لارن تاکید کرد فاصله نزدیک تیم‌ها در تعیین خط نشان می‌دهد کوچک‌ترین جزئیات در مدیریت دمای تایر سرنوشت‌ساز خواهد بود.",
                "",
                "#FF8000",
                [drivers[4], drivers[5]],
                [teams[2]],
                True,
                2140,
            ),
            (
                "رکوردشکنی فروش بلیت گرندپری استرالیا؛ بیش از ۴۵۰ هزار تماشاگر در آلبرت پارک",
                "برگزارکنندگان مسابقه ملبورن از فروش کامل تمامی ظرفیت سکوهای اصلی برای روز یکشنبه خبر دادند.",
                "",
                "#065f46",
                [],
                [],
                False,
                1930,
            ),
            (
                "توتو وولف عملکرد کیمی آنتونلی را در دو راند نخست فصل ستود",
                "مدیر تیم مرسدس معتقد است سرعت تطبیق‌پذیری راننده جوان ایتالیایی با قوانین جدید فراتر از انتظارات مهندسان براکلی بوده است.",
                "<p>توتو وولف در مصاحبه کوتاه خود پس از مسابقه جده گفت آنتونلی هیچ اشتباه بزرگی مرتکب نشده و داده‌های ارزشمندی به تیم داده است.</p>",
                "#27F4D2",
                [drivers[7]],
                [teams[3]],
                False,
                2470,
            ),
        ]

        for idx, (s_title, s_lead, s_body, s_color, s_drivers, s_teams, is_brk, s_views) in enumerate(short_news_samples, start=1):
            short_art, _ = Article.objects.update_or_create(
                slug=f"short-f1-news-{idx}",
                defaults={
                    "title": s_title,
                    "author": admin_user,
                    "category": categories[4],
                    "is_short": True,
                    "is_breaking": is_brk,
                    "lead": s_lead,
                    "body": s_body,
                    "featured_image": create_placeholder_image(f"short_news_{idx}.jpg", 800, 600, s_color),
                    "status": "published",
                    "views_count": s_views,
                    "related_grand_prix": grands_prix[2],
                },
            )
            short_art.related_drivers.set(s_drivers)
            short_art.related_teams.set(s_teams)

        # ۱۰. ساخت آمار ترافیک روزانه سایت (۳۰ روز گذشته) و عبارات جستجوشده
        self.stdout.write("در حال تولید آمار ترافیک ۳۰ روز گذشته و کلمات جستجوشده...")
        today = timezone.localdate()

        for days_ago in range(29, -1, -1):
            stat_date = today - timedelta(days=days_ago)
            # شبیه‌سازی ترافیک بالاتر در روزهای جمعه، شنبه و یکشنبه (آخر هفته‌های مسابقه)
            is_race_weekend = stat_date.weekday() in (4, 5, 6)
            base_unique = random.randint(650, 1200) if is_race_weekend else random.randint(280, 620)
            total_pageviews = int(base_unique * random.uniform(2.6, 4.2))

            DailySiteStat.objects.update_or_create(
                date=stat_date,
                defaults={
                    "total_views": total_pageviews,
                    "unique_visitors": base_unique,
                },
            )

        # ساخت چند هش بازدیدکننده یکتا برای امروز
        for i in range(1, 15):
            sample_hash = hashlib.sha256(f"{today.isoformat()}:192.168.1.{i}:Mozilla/5.0".encode()).hexdigest()
            DailyVisitorHash.objects.get_or_create(
                date=today,
                visitor_hash=sample_hash,
            )

        # ساخت آمار عبارات جستجوشده توسط کاربران
        sample_searches = [
            ("فراری", 142, 6),
            ("ورستپن", 118, 4),
            ("همیلتون", 96, 3),
            ("زمانبندی گرندپری استرالیا", 84, 1),
            ("مک‌لارن", 73, 4),
            ("لکلرک", 65, 3),
            ("قوانین موتور ۲۰۲۶", 51, 2),
            ("آنتونلی", 44, 2),
            ("پیست استانبول پارک", 29, 0),  # نمونه جستجوی بدون نتیجه برای بررسی خلا محتوایی
            ("پخش زنده فرمول یک", 19, 0),
        ]

        for query_text, count, results_cnt in sample_searches:
            SearchQueryStat.objects.update_or_create(
                query=query_text,
                defaults={
                    "search_count": count,
                    "last_results_count": results_cnt,
                },
            )

        self.stdout.write(
            self.style.SUCCESS("✔ آمار ۳۰ روز بازدید سایت، بازدید اخبار/رانندگان/تیم‌ها و کلمات جستجوشده ساخته شد!")
        )
        self.stdout.write(self.style.SUCCESS("✅ دیتای تستی فرمولافارسی با موفقیت ساخته شد!"))
        self.stdout.write(self.style.SUCCESS("👤 یوزر ادمین: admin | رمز عبور: admin1234"))