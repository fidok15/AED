""""Is it accessible right now?" from `godziny_dostepu` (opening_hours syntax of OpenStreetMap).

Mirror of frontend/src/app/pages/aed/aed-hours.ts – keep both in step (the tests share one table of cases).
Only the plain forms are read: 24/7, and rules like "Mo-Fr 08:00-16:00; Sa 09:00-13:00; Su,PH off".
Anything else (months, sunrise, comments, hours past midnight) gives `nieznane` – never a guess.
"""
import datetime
import re

DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
_DAY = "(?:Mo|Tu|We|Th|Fr|Sa|Su|PH)"
_SPAN = "[0-9]{1,2}:[0-9]{2}-[0-9]{1,2}:[0-9]{2}"  # as JS \d: ASCII digits only
RULE = re.compile(r"(?:(%s(?:\s*[-,]\s*%s)*)\s+)?(off|closed|%s(?:\s*,\s*%s)*)" % (_DAY, _DAY, _SPAN, _SPAN))


def _last_sunday(year, month):
    day = datetime.date(year, month, 31)
    return day - datetime.timedelta(days=(day.weekday() + 1) % 7)


def warsaw_now(utc=None):
    """Wall-clock time in Poland (naive datetime). CET, CEST from 01:00 UTC on the last Sunday of March to
    01:00 UTC on the last Sunday of October (EU rule; Python 3.8 has no zoneinfo)."""
    utc = utc or datetime.datetime.utcnow()
    if utc.tzinfo:
        utc = utc.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    start = datetime.datetime.combine(_last_sunday(utc.year, 3), datetime.time(1))
    end = datetime.datetime.combine(_last_sunday(utc.year, 10), datetime.time(1))
    return utc + datetime.timedelta(hours=2 if start <= utc < end else 1)


def _easter(year):
    """Easter Sunday (anonymous Gregorian algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    h = (19 * a + b - b // 4 - (b - (b + 8) // 25 + 1) // 3 + 15) % 30
    l = (32 + 2 * (b % 4) + 2 * (c // 4) - h - c % 4) % 7
    m = (a + 11 * h + 22 * l) // 451
    return datetime.date(year, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)


def is_holiday(day):
    """Public holidays in Poland (24 December since 2025)."""
    fixed = {(1, 1), (1, 6), (5, 1), (5, 3), (8, 15), (11, 1), (11, 11), (12, 25), (12, 26)}
    if day.year >= 2025:
        fixed.add((12, 24))
    if (day.month, day.day) in fixed:
        return True
    since_easter = ((day.date() if isinstance(day, datetime.datetime) else day) - _easter(day.year)).days
    return since_easter in (0, 1, 49, 60)  # Easter, Easter Monday, Pentecost, Corpus Christi


def _day_matches(days, today, holiday):
    for part in days.split(","):
        ends = [d.strip() for d in part.split("-")]
        start, end = ends[0], ends[1] if len(ends) > 1 else ends[0]
        if "PH" in (start, end):
            if holiday and start == end:
                return True
            continue
        first = DAYS.index(start)
        if (DAYS.index(today) - first) % 7 <= (DAYS.index(end) - first) % 7:
            return True
    return False


def _minute(text, end):
    """Minute of the day for "HH:MM", or None when out of range. 24:00 only as the end of a span."""
    h, m = (int(x) for x in text.split(":"))
    if m > 59 or h > 24 or (h == 24 and (m or not end)):
        return None
    return h * 60 + m


def open_now(hours, now=None):
    """'dostepny', 'zamkniety' or 'nieznane' for a `godziny_dostepu` value at `now` (Warsaw wall clock)."""
    value = (hours or "").strip()
    if not value:
        return "nieznane"
    if value == "24/7":
        return "dostepny"
    rules = [RULE.fullmatch(rule.strip()) for rule in value.split(";") if rule.strip()]
    if not all(rules):
        return "nieznane"

    now = now or warsaw_now()
    holiday = is_holiday(now)
    holiday_rules = holiday and any("PH" in (m.group(1) or "") for m in rules)
    today = DAYS[(now.weekday() + 1) % 7]
    minute = now.hour * 60 + now.minute
    is_open = False  # hours are given, so a day without a rule is a closed day

    for match in rules:
        days, times = match.group(1), match.group(2)
        # on a public holiday the PH rules decide, when the value has any
        if holiday_rules:
            if "PH" not in (days or ""):
                continue
        elif days and not _day_matches(days, today, holiday):
            continue
        if times in ("off", "closed"):
            is_open = False
            continue
        spans = [[_minute(t, end) for end, t in enumerate(span.strip().split("-"))] for span in times.split(",")]
        if any(None in span for span in spans):
            return "nieznane"  # 08:75, 25:00, 24:00 as a start: not a time
        if any(to <= start for start, to in spans):
            return "nieznane"  # past midnight: not read
        is_open = any(start <= minute < to for start, to in spans)
    return "dostepny" if is_open else "zamkniety"
