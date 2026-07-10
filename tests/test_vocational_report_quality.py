import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
QUALITY_MODULE = (
    ROOT
    / "skills"
    / "vocational-education-weekly-report"
    / "scripts"
    / "report_quality.py"
)


def load_quality_module():
    spec = importlib.util.spec_from_file_location("vocational_report_quality", QUALITY_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class VocationalReportQualityTests(unittest.TestCase):
    def test_rejects_0709_news_digest(self):
        quality = load_quality_module()
        report = load_fixture("vocational_0709_failed.json")

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        message = str(caught.exception)
        for expected in (
            "core_insights",
            "weekly_judgment",
            "analysis",
            "tracking",
            "scores",
            "检索结论",
        ):
            self.assertIn(expected, message)

    def test_accepts_research_report(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")

        result = quality.validate_report(report)

        self.assertEqual(5, result["event_count"])
        self.assertGreaterEqual(result["minimum_score"], 16)

    def test_rejects_low_value_event(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")
        report["sections"][0]["items"][0]["scores"] = {
            "industry_impact": 2,
            "policy_importance": 2,
            "commercial_value": 1,
            "technology_relevance": 1,
            "investment_relevance": 1,
        }

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("未达到入选阈值", str(caught.exception))

    def test_rejects_out_of_period_and_unverified_source(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")
        item = report["sections"][0]["items"][0]
        item["event_date"] = "2026-05-01"
        item["sources"][0]["access_status"] = "unchecked"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        message = str(caught.exception)
        self.assertIn("不在报告期", message)
        self.assertIn("access_status", message)

    def test_rejects_duplicate_source_document(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")
        first_source = report["sections"][0]["items"][0]["sources"][0]
        report["sections"][0]["items"][1]["sources"][0] = copy.deepcopy(first_source)

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("同一来源文件", str(caught.exception))

    def test_builds_sources_markdown(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")

        markdown = quality.build_sources_markdown(report)

        self.assertIn("# 职教行业周报来源清单", markdown)
        self.assertIn("V1", markdown)
        self.assertIn("https://example.com/vocational/v1", markdown)

    def test_builds_quality_markdown(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")

        markdown = quality.build_quality_markdown(report)

        self.assertIn("# 职教行业周报质量报告", markdown)
        self.assertIn("总分：34/40", markdown)


if __name__ == "__main__":
    unittest.main()
