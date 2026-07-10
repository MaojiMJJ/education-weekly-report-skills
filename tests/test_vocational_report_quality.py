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

    def test_rejects_internal_marker_inside_body(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")
        report["sections"][0]["items"][0]["analysis"] = "这是检索结论，未检索到更多材料。"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("内部工作内容", str(caught.exception))

    def test_rejects_internal_markers_in_top_level_visible_content(self):
        quality = load_quality_module()
        mutations = (
            ("title", lambda report: report.__setitem__("title", "未检索到事项的职教行业周报")),
            (
                "core_insights",
                lambda report: report["core_insights"][0].__setitem__("claim", "本期检索结论尚无重要变化"),
            ),
            (
                "weekly_judgment",
                lambda report: report.__setitem__("weekly_judgment", "未检索到更多事项，这是检索结论。" * 8),
            ),
            (
                "quality_review",
                lambda report: report["quality_review"]["information_quality"].__setitem__(
                    "reason", "未检索到更多来源，这是检索结论。"
                ),
            ),
        )

        for label, mutate in mutations:
            with self.subTest(label=label):
                report = load_fixture("vocational_valid.json")
                mutate(report)
                with self.assertRaises(quality.ReportQualityError) as caught:
                    quality.validate_report(report)
                self.assertIn("内部工作内容", str(caught.exception))

    def test_rejects_follow_up_language_in_public_output_fields(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")
        report["weekly_judgment"] = (
            "本期职业教育政策、院校和企业均有正式进展，正文已经说明公开事实及行业影响。"
            "下一期重点跟踪项目投入、招生和就业数据属于投资部内部安排，不应进入对外材料。"
            "本页只用于同步当前行业变化。"
            "公开材料应围绕已经发生并经过来源核验的事实展开，避免把研究分工和待办事项混入行业结论。"
        )

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("公开报告", str(caught.exception))

    def test_event_type_alias_cannot_bypass_primary_source(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")
        item = report["sections"][0]["items"][0]
        item["event_type"] = "资本动态"
        item["sources"][0]["is_primary"] = False

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("一手来源", str(caught.exception))

    def test_rejects_reserved_domain_and_stale_access_check(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")
        source = report["sections"][0]["items"][0]["sources"][0]
        source["url"] = "https://source.invalid/item"
        source["access_checked_at"] = "2020-01-01"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        message = str(caught.exception)
        self.assertIn("URL", message)
        self.assertIn("不得早于发布日期", message)

    def test_rejects_evidence_table_beyond_stable_capacity(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")
        report["sections"][0]["items"][0]["evidence_table"] = {
            "columns": ["院校", "结果"],
            "rows": [[f"测试院校{index}", "通过"] for index in range(8)],
        }

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("最多允许 3 行", str(caught.exception))

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
        self.assertIn("https://jyt.jiangsu.gov.cn/art/v1.html", markdown)

    def test_builds_quality_markdown(self):
        quality = load_quality_module()
        report = load_fixture("vocational_valid.json")

        markdown = quality.build_quality_markdown(report)

        self.assertIn("# 职教行业周报质量报告", markdown)
        self.assertIn("总分：34/40", markdown)


if __name__ == "__main__":
    unittest.main()
