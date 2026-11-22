"""aed_standard.hours against the table shared with aed-hours.spec.ts."""
import datetime
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from aed_standard.hours import is_holiday, open_now, warsaw_now  # noqa: E402

CASES = os.path.join(ROOT, "frontend", "src", "app", "pages", "aed", "aed-hours.cases.json")


class HoursTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CASES, encoding="utf-8") as f:
            cls.cases = json.load(f)

    def test_open_now_table(self):
        for hours, at, expected in self.cases["open_now"]:
            with self.subTest(hours=hours, at=at):
                self.assertEqual(open_now(hours, datetime.datetime.fromisoformat(at)), expected)

    def test_holidays_table(self):
        for day, expected in self.cases["holiday"]:
            with self.subTest(day=day):
                self.assertEqual(is_holiday(datetime.date.fromisoformat(day)), expected)

    def test_warsaw_time_on_both_sides_of_the_clock_change(self):
        utc = datetime.datetime
        # spring 2026: last Sunday of March is 29 March, clocks go forward at 01:00 UTC
        self.assertEqual(warsaw_now(utc(2026, 3, 29, 0, 59)), utc(2026, 3, 29, 1, 59))
        self.assertEqual(warsaw_now(utc(2026, 3, 29, 1, 0)), utc(2026, 3, 29, 3, 0))
        # autumn 2026: last Sunday of October is 25 October, clocks go back at 01:00 UTC
        self.assertEqual(warsaw_now(utc(2026, 10, 25, 0, 59)), utc(2026, 10, 25, 2, 59))
        self.assertEqual(warsaw_now(utc(2026, 10, 25, 1, 0)), utc(2026, 10, 25, 2, 0))
        self.assertEqual(warsaw_now(utc(2026, 11, 22, 12, 0, tzinfo=datetime.timezone.utc)), utc(2026, 11, 22, 13, 0))
        # 07:30 UTC is 09:30 in July (open) and 08:30 in January (still closed for a 09:00 start)
        self.assertEqual(open_now("Mo-Fr 09:00-16:00", warsaw_now(utc(2026, 7, 1, 7, 30))), "dostepny")
        self.assertEqual(open_now("Mo-Fr 09:00-16:00", warsaw_now(utc(2026, 1, 7, 7, 30))), "zamkniety")


if __name__ == "__main__":
    unittest.main()
