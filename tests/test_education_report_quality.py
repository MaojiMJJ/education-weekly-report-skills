import copy
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = (
    ROOT
    / "skills"
    / "education-industry-observation"
    / "scripts"
    / "report_quality.py"
)
SPEC = importlib.util.spec_from_file_location("education_report_quality", SCRIPT)
QUALITY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(QUALITY)


def load_report():
    return json.loads((FIXTURES / "education_valid.json").read_text(encoding="utf-8"))


class EducationReportQualityTests(unittest.TestCase):
    def test_accepts_reference_eight_page_plan(self):
        result = QUALITY.validate_report(load_report())

        self.assertEqual("colleague-biweekly-v1", result["template_id"])
        self.assertEqual(8, result["page_count"])
        self.assertEqual(11, result["item_count"])
        self.assertEqual(34, result["quality_total"])

    def test_accepts_dynamic_page_count_within_fifteen_pages(self):
        report = load_report()
        last_page = report["page_plan"].pop()
        report["page_plan"].extend(
            [
                {
                    "section": last_page["section"],
                    "header": last_page["header"],
                    "slot_ids": ["policy_4"],
                },
                {
                    "section": last_page["section"],
                    "header": last_page["header"],
                    "slot_ids": ["policy_5"],
                },
            ]
        )

        result = QUALITY.validate_report(report)

        self.assertEqual(9, result["page_count"])
        self.assertEqual(11, result["item_count"])

    def test_rejects_legacy_coverage_mode(self):
        report = load_report()
        report["coverage_mode"] = "broad_and_deep"

        with self.assertRaises(QUALITY.ReportQualityError) as caught:
            QUALITY.validate_report(report)

        self.assertIn("旧的 broad_and_deep/deep_only 模式已停用", str(caught.exception))

    def test_requires_exact_section_order_and_complete_page_plan(self):
        report = load_report()
        report["sections"][0], report["sections"][1] = report["sections"][1], report["sections"][0]
        report["sections"][2]["items"].pop()

        with self.assertRaises(QUALITY.ReportQualityError) as caught:
            QUALITY.validate_report(report)

        message = str(caught.exception)
        self.assertIn("栏目名称和顺序", message)
        self.assertIn("page_plan", message)

    def test_requires_exact_slot_order(self):
        report = load_report()
        report["sections"][0]["items"][0]["slot_id"] = "listed_2"

        with self.assertRaises(QUALITY.ReportQualityError) as caught:
            QUALITY.validate_report(report)

        self.assertIn("slot_id 必须是 listed_1", str(caught.exception))

    def test_period_must_be_complete_anchor_aligned_biweekly(self):
        for invalid in (
            "2026.07.06-2026.07.18",
            "2026.07.07-2026.07.20",
            "2026.07.13-2026.07.26",
        ):
            with self.subTest(period=invalid):
                report = load_report()
                report["period"] = invalid
                with self.assertRaises(QUALITY.ReportQualityError):
                    QUALITY.validate_report(report)

    def test_rejects_reference_carryover(self):
        report = load_report()
        report["sections"][0]["items"][0]["date_scope"] = "reference_carryover"

        with self.assertRaises(QUALITY.ReportQualityError) as caught:
            QUALITY.validate_report(report)

        self.assertIn("date_scope 必须是 within_period", str(caught.exception))

    def test_rejects_slot_over_capacity(self):
        report = load_report()
        report["sections"][0]["items"][0]["bullets"][0] = "测试事实" * 80

        with self.assertRaises(QUALITY.ReportQualityError) as caught:
            QUALITY.validate_report(report)

        self.assertIn("超过当前分页", str(caught.exception))

    def test_rejects_more_than_fifteen_pages(self):
        report = load_report()
        report["page_plan"] = report["page_plan"] * 3

        with self.assertRaises(QUALITY.ReportQualityError) as caught:
            QUALITY.validate_report(report)

        self.assertIn("不超过 15", str(caught.exception))

    def test_rejects_public_analysis_and_follow_up_labels(self):
        for marker in ("行业判断：", "后续跟踪"):
            with self.subTest(marker=marker):
                report = load_report()
                report["sections"][0]["items"][0]["bullets"][0] = (
                    f"{marker}这是不应进入公开页面的内部表述，必须被自动门槛阻止。"
                )
                with self.assertRaises(QUALITY.ReportQualityError) as caught:
                    QUALITY.validate_report(report)
                self.assertIn("模板外或内部措辞", str(caught.exception))

    def test_rejects_event_outside_period(self):
        report = load_report()
        report["sections"][0]["items"][0]["event_date"] = "2026-06-30"

        with self.assertRaises(QUALITY.ReportQualityError) as caught:
            QUALITY.validate_report(report)

        self.assertIn("event_date 不在报告期内", str(caught.exception))

    def test_rejects_duplicate_source_document(self):
        report = load_report()
        first_source = report["sections"][0]["items"][0]["sources"][0]
        second = report["sections"][0]["items"][1]
        second["sources"][0] = copy.deepcopy(first_source)
        second["period_trigger"]["source_url"] = first_source["url"]

        with self.assertRaises(QUALITY.ReportQualityError) as caught:
            QUALITY.validate_report(report)

        self.assertIn("使用同一来源文件", str(caught.exception))

    def test_builds_sources_and_quality_sidecars(self):
        report = load_report()
        sources = QUALITY.build_sources_markdown(report)
        quality = QUALITY.build_quality_markdown(report)

        self.assertIn("listed_1", sources)
        self.assertIn("政策 5", quality)
        self.assertIn("总分：34/40", quality)
        self.assertNotIn("tracking", sources)


if __name__ == "__main__":
    unittest.main()
