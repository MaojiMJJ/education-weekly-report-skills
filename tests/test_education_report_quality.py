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
    / "education-industry-observation"
    / "scripts"
    / "report_quality.py"
)


def load_quality_module():
    spec = importlib.util.spec_from_file_location("education_report_quality", QUALITY_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class EducationReportQualityTests(unittest.TestCase):
    def test_rejects_0709_news_digest(self):
        quality = load_quality_module()
        report = load_fixture("education_0709_failed.json")

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
        report = load_fixture("education_valid.json")

        result = quality.validate_report(report)

        self.assertEqual(5, result["event_count"])
        self.assertGreaterEqual(result["minimum_score"], 16)

    def test_rejects_low_value_event(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["scores"] = {
            "industry_impact": 2,
            "policy_importance": 1,
            "commercial_value": 2,
            "technology_relevance": 2,
            "investment_relevance": 1,
        }

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("未达到入选阈值", str(caught.exception))

    def test_rejects_internal_content_role(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["name"] = "搜索情况"
        report["sections"][0]["items"][0]["content_role"] = "search_ledger"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("content_role", str(caught.exception))

    def test_rejects_internal_marker_inside_body(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["facts"][0] = "未检索到更多材料，这是检索结论。"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("内部工作内容", str(caught.exception))

    def test_rejects_internal_markers_in_top_level_visible_content(self):
        quality = load_quality_module()
        mutations = (
            ("title", lambda report: report.__setitem__("title", "未检索到事项的教育行业观察")),
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
                report = load_fixture("education_valid.json")
                mutate(report)
                with self.assertRaises(quality.ReportQualityError) as caught:
                    quality.validate_report(report)
                self.assertIn("内部工作内容", str(caught.exception))

    def test_rejects_follow_up_language_in_public_output_fields(self):
        quality = load_quality_module()
        mutations = (
            (
                "weekly_judgment",
                lambda report: report.__setitem__(
                    "weekly_judgment",
                    "本期教育行业已形成多项公开进展，政策、融资和学校服务均有新增动作。"
                    "相关事项的行业影响已经在正文说明，下一期重点跟踪项目落地和经营数据。"
                    "本页用于同步当前进展，不应包含投资部内部任务安排。"
                    "公开材料应围绕已经发生并经过来源核验的事实展开，避免把研究分工和待办事项混入行业结论。",
                ),
            ),
            (
                "analysis",
                lambda report: report["sections"][0]["items"][0].__setitem__(
                    "analysis",
                    "该事项改变了行业供给结构，但后续跟踪仍需由投资部内部安排，不应出现在公开正文。",
                ),
            ),
        )

        for label, mutate in mutations:
            with self.subTest(label=label):
                report = load_fixture("education_valid.json")
                mutate(report)
                with self.assertRaises(quality.ReportQualityError) as caught:
                    quality.validate_report(report)
                self.assertIn("公开报告", str(caught.exception))

    def test_rejects_event_outside_report_period(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["event_date"] = "2026-05-01"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("不在报告期", str(caught.exception))

    def test_rejects_current_article_about_old_period_roundup(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        item = report["sections"][0]["items"][0]
        item["event_type"] = "融资"
        item["event_date"] = "2026-07-03"
        item["period_trigger"] = {
            "type": "media_roundup",
            "description": "媒体于2026年7月3日盘点上半年融资事项",
            "source_url": item["sources"][0]["url"],
        }

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("本期触发类型", str(caught.exception))

    def test_financing_cannot_use_generic_data_release_as_period_trigger(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        item = report["sections"][0]["items"][0]
        item["event_type"] = "融资"
        item["period_trigger"]["type"] = "official_data_released"
        item["period_trigger"]["description"] = "媒体发布上半年融资汇总数据"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("与 event_type 不匹配", str(caught.exception))

    def test_period_trigger_source_must_match_verified_primary_source(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        item = report["sections"][0]["items"][0]
        item["period_trigger"]["source_url"] = "https://news.example.org/roundup"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("触发来源", str(caught.exception))

    def test_accepts_current_financing_announcement(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")

        quality.validate_report(report)

    def test_financing_requires_fixed_details(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0].pop("financing_details")

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("financing_details", str(caught.exception))

    def test_financing_requires_explicit_undisclosed_fields(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["financing_details"]["profit"] = ""

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("financing_details.profit", str(caught.exception))

    def test_policy_requires_source_scope_and_classified_clauses(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        item = report["sections"][1]["items"][0]
        item["policy_details"]["scope_level"] = "区域"
        item["policy_details"]["prohibited_rules"] = []
        item["policy_details"]["restrictive_requirements"] = []
        item["policy_details"]["supportive_measures"] = []

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        message = str(caught.exception)
        self.assertIn("全国性或地方性", message)
        self.assertIn("政策核心条款", message)

    def test_business_cooperation_requires_fixed_details(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        item = report["sections"][2]["items"][0]
        item["event_type"] = "业务合作"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("cooperation_details", str(caught.exception))

    def test_accepts_policy_effective_with_older_official_source(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        item = report["sections"][1]["items"][0]
        item["event_type"] = "政策"
        item["event_date"] = "2026-06-24"
        item["period_trigger"] = {
            "type": "policy_effective",
            "description": "测试省教育厅发布的管理办法于2026年6月24日正式施行",
            "source_url": item["sources"][0]["url"],
        }
        item["sources"][0]["published_at"] = "2026-05-20"

        quality.validate_report(report)

    def test_rejects_unverified_source(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["sources"][0]["access_status"] = "unchecked"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("access_status", str(caught.exception))

    def test_financing_requires_primary_source(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["sources"][0]["is_primary"] = False

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("一手来源", str(caught.exception))

    def test_event_type_alias_cannot_bypass_primary_source(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        item = report["sections"][0]["items"][0]
        item["event_type"] = "资本动态"
        item["sources"][0]["is_primary"] = False

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("一手来源", str(caught.exception))

    def test_rejects_reserved_source_domain(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["sources"][0]["url"] = "https://source.invalid/item"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("URL", str(caught.exception))

    def test_rejects_access_check_before_publication(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["sources"][0]["access_checked_at"] = "2020-01-01"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("不得早于发布日期", str(caught.exception))

    def test_rejects_extra_score_field(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["scores"]["total"] = 99

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("额外字段", str(caught.exception))

    def test_rejects_malformed_evidence_table(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["evidence_table"] = "不是对象"

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("evidence_table", str(caught.exception))

    def test_rejects_evidence_table_beyond_stable_capacity(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["evidence_table"] = {
            "columns": ["机构", "结果"],
            "rows": [[f"测试机构{index}", "合格"] for index in range(8)],
        }

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("最多允许 3 行", str(caught.exception))

    def test_rejects_overlong_fact(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0]["facts"][0] = "过长事实" * 50

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("facts[1]", str(caught.exception))

    def test_rejects_overlong_impact_lists(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        item = report["sections"][0]["items"][0]
        item["beneficiaries"] = ["受益机制描述" * 5] * 3
        item["risks"] = ["风险条件描述" * 5] * 3

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("受益方和风险", str(caught.exception))

    def test_requires_background(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["sections"][0]["items"][0].pop("background")

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("background", str(caught.exception))

    def test_rejects_quality_review_below_eight(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        report["quality_review"]["analysis_depth"]["score"] = 7

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("quality_review.analysis_depth", str(caught.exception))

    def test_rejects_duplicate_source_document(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")
        first_source = report["sections"][0]["items"][0]["sources"][0]
        report["sections"][0]["items"][1]["sources"][0] = copy.deepcopy(first_source)

        with self.assertRaises(quality.ReportQualityError) as caught:
            quality.validate_report(report)

        self.assertIn("同一来源文件", str(caught.exception))

    def test_builds_sources_markdown(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")

        markdown = quality.build_sources_markdown(report)

        self.assertIn("# 教育行业观察来源清单", markdown)
        self.assertIn("E1", markdown)
        self.assertIn("https://www.cninfo.com.cn/new/disclosure/detail/e1", markdown)

    def test_builds_quality_markdown(self):
        quality = load_quality_module()
        report = load_fixture("education_valid.json")

        markdown = quality.build_quality_markdown(report)

        self.assertIn("# 教育行业观察质量报告", markdown)
        self.assertIn("总分：34/40", markdown)


if __name__ == "__main__":
    unittest.main()
