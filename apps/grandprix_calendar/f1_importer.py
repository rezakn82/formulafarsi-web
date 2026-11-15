import re
from decimal import Decimal, InvalidOperation

import httpx
from bs4 import BeautifulSoup
from django.db import transaction

from apps.grandprix_calendar.models import Session, SessionResult
from apps.racing.models import Driver

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _parse_int(val: str, default: int = 0) -> int:
    digits = re.findall(r"\d+", val or "")
    return int(digits[0]) if digits else default


def _parse_decimal(val: str) -> Decimal:
    cleaned = re.sub(r"[^\d.]", "", val or "")
    if not cleaned:
        return Decimal("0.0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0.0")


def _match_driver(no_text: str, driver_cell_text: str, drivers_by_num: dict, drivers_by_code: dict):
    # ۱. تطبیق بر اساس شماره راننده (دقیق‌ترین روش در جداول رسمی F1)
    if no_text and no_text.isdigit():
        drv = drivers_by_num.get(int(no_text))
        if drv:
            return drv

    # ۲. تطبیق بر اساس کد ۳ حرفی در انتهای نام راننده (مثل Max Verstappen VER)
    tokens = _clean(driver_cell_text).split(" ")
    if tokens:
        last_token = re.sub(r"[^A-Za-z]", "", tokens[-1]).upper()
        if len(last_token) == 3 and last_token in drivers_by_code:
            return drivers_by_code[last_token]

    for code, drv in drivers_by_code.items():
        if code in driver_cell_text.upper():
            return drv

    return None


@transaction.atomic
def import_f1_session_results(session: Session, url: str = "", raw_html: str = "") -> tuple[int, list[str]]:
    """
    دریافت صفحه نتایج از سایت رسمی formula1.com (یا HTML کپی‌شده) و ثبت خودکار SessionResult.
    برمی‌گرداند: (تعداد ردیف‌های ثبت‌شده, لیست هشدارها برای راننده‌های یافت‌نشده)
    """
    html_content = raw_html.strip()
    if not html_content and url:
        with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=20.0) as client:
            resp = client.get(url.strip())
            resp.raise_for_status()
            html_content = resp.text

    if not html_content:
        raise ValueError("آدرس URL یا کد HTML وارد نشده است.")

    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")
    if not table:
        raise ValueError("جدولی در این صفحه یافت نشد. از صحت لینک نتیجه جلسه در formula1.com مطمئن شوید.")

    # استخراج نام ستون‌ها از thead
    headers = [_clean(th.get_text()).lower() for th in table.select("thead th")]
    rows = table.select("tbody tr")
    if not rows:
        raise ValueError("هیچ ردیفی در جدول نتایج یافت نشد.")

    drivers_all = list(Driver.objects.select_related("team").all())
    drivers_by_num = {d.permanent_number: d for d in drivers_all}
    drivers_by_code = {d.code.upper(): d for d in drivers_all}

    def col_idx(*names):
        for n in names:
            for idx, h in enumerate(headers):
                if n in h:
                    return idx
        return None

    idx_pos = col_idx("pos")
    idx_no = col_idx("no")
    idx_driver = col_idx("driver")
    idx_laps = col_idx("laps")
    idx_time = col_idx("time", "retired", "gap")
    idx_pts = col_idx("pts", "points")
    idx_q1 = col_idx("q1", "sq1")
    idx_q2 = col_idx("q2", "sq2")
    idx_q3 = col_idx("q3", "sq3")

    imported_count = 0
    warnings = []

    for row_num, tr in enumerate(rows, start=1):
        cells = [_clean(td.get_text()) for td in tr.find_all(["td", "th"])]
        if len(cells) < 3:
            continue

        pos_raw = cells[idx_pos] if idx_pos is not None and idx_pos < len(cells) else str(row_num)
        no_raw = cells[idx_no] if idx_no is not None and idx_no < len(cells) else ""
        drv_raw = cells[idx_driver] if idx_driver is not None and idx_driver < len(cells) else ""

        driver = _match_driver(no_raw, drv_raw, drivers_by_num, drivers_by_code)
        if not driver:
            warnings.append(f"ردیف {row_num}: راننده «{drv_raw}» (شماره {no_raw}) در دیتابیس یافت نشد.")
            continue

        if not driver.team:
            warnings.append(f"ردیف {row_num}: برای راننده «{driver.full_name}» تیمی در دیتابیس ثبت نشده است.")
            continue

        pos_upper = pos_raw.upper()
        time_raw = cells[idx_time] if idx_time is not None and idx_time < len(cells) else ""
        time_upper = time_raw.upper()

        status = "finished"
        if "DQ" in pos_upper or "DSQ" in pos_upper or "DSQ" in time_upper:
            status = "dsq"
        elif "DNS" in pos_upper or "DNS" in time_upper:
            status = "dns"
        elif "NC" in pos_upper or "DNF" in pos_upper or "DNF" in time_upper or "RET" in pos_upper:
            status = "dnf"

        position = int(pos_raw) if pos_raw.isdigit() else row_num
        laps = _parse_int(cells[idx_laps]) if idx_laps is not None and idx_laps < len(cells) else 0
        points = _parse_decimal(cells[idx_pts]) if idx_pts is not None and idx_pts < len(cells) else Decimal("0.0")

        q1 = cells[idx_q1] if idx_q1 is not None and idx_q1 < len(cells) else ""
        q2 = cells[idx_q2] if idx_q2 is not None and idx_q2 < len(cells) else ""
        q3 = cells[idx_q3] if idx_q3 is not None and idx_q3 < len(cells) else ""

        SessionResult.objects.update_or_create(
            session=session,
            driver=driver,
            defaults={
                "team": driver.team,
                "position": position,
                "status": status,
                "laps": laps,
                "time_or_gap": "" if session.session_type in ("qualifying", "sprint_qualifying", "sprint_shootout") else time_raw,
                "q1_time": q1,
                "q2_time": q2,
                "q3_time": q3,
                "points": points,
            },
        )
        imported_count += 1

    return imported_count, warnings