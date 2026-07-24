import importlib.util
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "education-industry-observation"
    / "scripts"
    / "resolve_period.py"
)
SPEC = importlib.util.spec_from_file_location("resolve_period", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class BiweeklyTemplateTests(unittest.TestCase):
    def test_current_date_resolves_to_latest_completed_cycle(self):
        start, end = MODULE.latest_complete_period(date(2026, 7, 24))

        self.assertEqual(date(2026, 7, 6), start)
        self.assertEqual(date(2026, 7, 19), end)

    def test_next_cycle_is_selected_after_it_finishes(self):
        start, end = MODULE.latest_complete_period(date(2026, 8, 3))

        self.assertEqual(date(2026, 7, 20), start)
        self.assertEqual(date(2026, 8, 2), end)

    def test_cycle_does_not_publish_on_its_last_day(self):
        start, end = MODULE.latest_complete_period(date(2026, 8, 2))

        self.assertEqual(date(2026, 7, 6), start)
        self.assertEqual(date(2026, 7, 19), end)

    def test_period_format_is_zero_padded_for_json(self):
        self.assertEqual(
            "2026.07.06-2026.07.19",
            MODULE.format_period(date(2026, 7, 6), date(2026, 7, 19)),
        )


if __name__ == "__main__":
    unittest.main()
