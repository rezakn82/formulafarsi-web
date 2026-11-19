from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.grandprix_calendar.models import Season
from apps.racing.models import Driver, DriverPowerUnitUsage, PowerUnitLimit, Team
from apps.racing.views import _get_pu_cell_meta


class PowerUnitComponentsTests(TestCase):
    def setUp(self):
        self.season = Season.objects.create(year=2026, is_current=True)
        self.limit = PowerUnitLimit.objects.create(season=self.season)
        self.team = Team.objects.create(
            name="فراری",
            base="مارانلو",
            team_chief="فردریک واسور",
            power_unit="فراری",
            color_code="#E80020",
        )
        self.driver = Driver.objects.create(
            first_name="شارل",
            last_name="لکلرک",
            permanent_number=16,
            code="LEC",
            country="موناکو",
            date_of_birth=date(1997, 10, 16),
            team=self.team,
            is_main_driver=True,
        )
        self.usage = DriverPowerUnitUsage.objects.create(
            season=self.season,
            driver=self.driver,
            ice=3,      # مجاز (از 4) -> سفید
            tc=4,       # مرز جریمه (از 4) -> نارنجی
            exh=5,      # جریمه شده (از 4) -> قرمز
            mguk=2,
            es=3,       # مرز جریمه (از 3) -> نارنجی
            pu_ce=4,    # جریمه شده (از 3) -> قرمز
            pu_anc=5,
        )

    def test_pu_cell_color_logic(self):
        self.assertEqual(_get_pu_cell_meta(3, 4)["status"], "ok")
        self.assertIn("text-white", _get_pu_cell_meta(3, 4)["text_class"])

        self.assertEqual(_get_pu_cell_meta(4, 4)["status"], "warning")
        self.assertIn("text-orange-400", _get_pu_cell_meta(4, 4)["text_class"])

        self.assertEqual(_get_pu_cell_meta(5, 4)["status"], "penalty")
        self.assertIn("text-red-500", _get_pu_cell_meta(5, 4)["text_class"])

    def test_pu_components_page_renders(self):
        response = self.client.get(reverse("racing:pu_components"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "شارل لکلرک")
        self.assertContains(response, "فراری")
        self.assertContains(response, "PU-ANC")
        self.assertContains(response, "text-white")
        self.assertContains(response, "text-orange-400")
        self.assertContains(response, "text-red-500")