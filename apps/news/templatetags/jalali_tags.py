from datetime import date, datetime

import jdatetime
from django import template
from django.utils import timezone

register = template.Library()

PERSIAN_MONTHS = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}

PERSIAN_WEEKDAYS = {
    0: "شنبه",
    1: "یکشنبه",
    2: "دوشنبه",
    3: "سه‌شنبه",
    4: "چهارشنبه",
    5: "پنجشنبه",
    6: "جمعه",
}


def _to_jalali(value):
    """Convert Python date/datetime to timezone-aware jdatetime object."""
    if not value:
        return None
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return jdatetime.datetime.fromgregorian(datetime=value)
    if isinstance(value, date):
        return jdatetime.date.fromgregorian(date=value)
    return None


@register.filter(name="jalali_date")
def jalali_date(value, fmt="%Y/%m/%d"):
    """
    فرمت‌بندی تاریخ شمسی:
    - '%Y/%m/%d' -> '1405/08/22'
    - 'j F'      -> '22 آبان'
    - 'j F Y'    -> '22 آبان 1405'
    - 'l j F'    -> 'جمعه 22 آبان'
    - 'l j F Y'  -> 'جمعه 22 آبان 1405'
    """
    j_obj = _to_jalali(value)
    if not j_obj:
        return ""

    if fmt == "j F":
        return f"{j_obj.day} {PERSIAN_MONTHS[j_obj.month]}"
    if fmt == "j F Y":
        return f"{j_obj.day} {PERSIAN_MONTHS[j_obj.month]} {j_obj.year}"
    if fmt == "l j F":
        weekday = PERSIAN_WEEKDAYS[j_obj.weekday()]
        return f"{weekday} {j_obj.day} {PERSIAN_MONTHS[j_obj.month]}"
    if fmt == "l j F Y":
        weekday = PERSIAN_WEEKDAYS[j_obj.weekday()]
        return f"{weekday} {j_obj.day} {PERSIAN_MONTHS[j_obj.month]} {j_obj.year}"

    return j_obj.strftime(fmt)