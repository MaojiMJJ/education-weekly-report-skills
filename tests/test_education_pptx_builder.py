import importlib.util
import json
import unittest
from pathlib import Path

from pptx import Presentation
from pptx.enum.text import PP_ALIGN


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
BUILDER_MODULE = (
    ROOT
    / "skills"
    / "education-industry-observation"
    / "scripts"
    / "build_weekly_pptx.py"
)
OUTPUT_DIR = ROOT / "tests" / "output"


def load_builder_module():
    spec = importlib.util.spec_from_file_location("education_pptx_builder", BUILDER_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def slide_text(slide):
    return "\n".join(shape.text for shape in slide.shapes if hasattr(shape, "text"))


def add_broad_coverage(report):
    report["coverage_mode"] = "broad_and_deep"
    dates = ["2026-06-23", "2026-06-24", "2026-06-25", "2026-06-26", "2026-06-27"]
    sections = [
        ("行业速览-学校与高教", 2),
        ("行业速览-国际教育", 1),
        ("行业速览-AI产品", 2),
    ]
    number = 0
    for section_name, count in sections:
        items = []
        for _ in range(count):
            number += 1
            event_date = dates[number - 1]
            url = f"https://www.moe.gov.cn/test/b{number}.html"
            items.append(
                {
                    "id": f"B{number}",
                    "content_role": "brief",
                    "headline": f"测试教育主体发布第{number}项本期教育产品动态",
                    "short_title": f"速览动态{number}",
                    "event_date": event_date,
                    "subject": f"测试教育主体{number}",
                    "event_type": "产品",
                    "period_trigger": {
                        "type": "product_launched",
                        "description": f"测试教育主体于{event_date}正式发布第{number}项教育产品",
                        "source_url": url,
                    },
                    "facts": [
                        f"该主体于{event_date}正式发布教育产品。",
                        "产品覆盖课堂教学与学习反馈两个场景。",
                    ],
                    "why_it_matters": "该事项补充了本期学校与教育产品供给的覆盖宽度，并提供可核验的落地动作。",
                    "sources": [
                        {
                            "name": f"测试直接来源{number}",
                            "url": url,
                            "published_at": event_date,
                            "source_type": "government",
                            "is_primary": True,
                            "access_status": "verified",
                            "access_checked_at": "2026-07-05",
                        }
                    ],
                }
            )
        report["sections"].append({"name": section_name, "items": items})
    return report


class EducationPptxBuilderTests(unittest.TestCase):
    def setUp(self):
        self.output = OUTPUT_DIR / "education_valid.pptx"
        self.sources = OUTPUT_DIR / "education_sources.md"
        self.quality = OUTPUT_DIR / "education_quality.md"
        self.rejected_output = OUTPUT_DIR / "should_not_exist.pptx"
        for path in (self.output, self.sources, self.quality, self.rejected_output):
            if path.exists():
                path.unlink()

    def test_builds_four_by_three_research_deck_and_sources(self):
        builder = load_builder_module()
        report = load_fixture("education_valid.json")
        report["sections"][2]["items"][0]["evidence_table"] = {
            "columns": ["机构", "年检结果"],
            "rows": [["测试机构甲", "合格"], ["测试机构乙", "合格"], ["测试机构丙", "合格"]],
        }

        builder.build(report, self.output, self.sources, self.quality)

        self.assertTrue(self.output.exists())
        self.assertTrue(self.sources.exists())
        self.assertTrue(self.quality.exists())
        presentation = Presentation(self.output)
        self.assertAlmostEqual(10.0, presentation.slide_width / 914400, places=2)
        self.assertAlmostEqual(7.5, presentation.slide_height / 914400, places=2)
        self.assertEqual(8, len(presentation.slides))
        self.assertIn("本期主要动态", slide_text(presentation.slides[1]))
        self.assertIn("行业判断", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertNotIn("后续跟踪", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("主体背景", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("受益", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("风险", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("测试教育科技公司甲", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("2026-06-24", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("本期行业小结", slide_text(presentation.slides[-1]))
        self.assertTrue(
            any(
                getattr(shape, "has_table", False)
                for slide in presentation.slides
                for shape in slide.shapes
            )
        )
        table_slide = next(
            slide for slide in presentation.slides if any(getattr(shape, "has_table", False) for shape in slide.shapes)
        )
        table_shape = next(shape for shape in table_slide.shapes if getattr(shape, "has_table", False))
        analysis_label = next(
            shape
            for shape in table_slide.shapes
            if hasattr(shape, "text") and shape.text.strip().startswith("行业判断：")
        )
        self.assertLessEqual(table_shape.top + table_shape.height, analysis_label.top)
        self.assertIn(
            "# 教育行业观察来源清单",
            self.sources.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "总分：34/40",
            self.quality.read_text(encoding="utf-8"),
        )
        for slide in presentation.slides:
            for shape in slide.shapes:
                self.assertGreaterEqual(shape.left, 0)
                self.assertGreaterEqual(shape.top, 0)
                self.assertLessEqual(shape.left + shape.width, presentation.slide_width)
                self.assertLessEqual(shape.top + shape.height, presentation.slide_height)

    def test_builds_broad_quick_scan_without_removing_deep_pages(self):
        builder = load_builder_module()
        report = add_broad_coverage(load_fixture("education_valid.json"))

        builder.build(report, self.output, self.sources, self.quality)

        presentation = Presentation(self.output)
        all_text = "\n".join(slide_text(slide) for slide in presentation.slides)
        self.assertEqual(11, len(presentation.slides))
        self.assertIn("行业速览 - 学校与高教", all_text)
        self.assertIn("为什么重要：", all_text)
        self.assertEqual(5, all_text.count("价值评分"))
        self.assertIn("B1", self.sources.read_text(encoding="utf-8"))

    def test_rejects_old_news_digest_before_building(self):
        builder = load_builder_module()
        report = load_fixture("education_0709_failed.json")

        with self.assertRaises(Exception) as caught:
            builder.build(report, self.rejected_output)

        self.assertIn("core_insights", str(caught.exception))
        self.assertFalse(self.rejected_output.exists())

    def test_requires_sources_and_quality_delivery_paths(self):
        builder = load_builder_module()
        report = load_fixture("education_valid.json")

        with self.assertRaises(ValueError) as caught:
            builder.build(report, self.output)

        self.assertIn("来源清单", str(caught.exception))
        self.assertIn("质量报告", str(caught.exception))
        self.assertFalse(self.output.exists())

    def test_uses_required_kaiti_36_18_16_typography(self):
        builder = load_builder_module()
        report = load_fixture("education_valid.json")

        builder.build(report, self.output, self.sources, self.quality)

        presentation = Presentation(self.output)
        header = next(
            shape
            for slide in presentation.slides
            for shape in slide.shapes
            if hasattr(shape, "text") and shape.text.startswith("1  行业速览 - ")
        )
        side_label = next(
            shape
            for slide in presentation.slides
            for shape in slide.shapes
            if hasattr(shape, "text")
            and shape.text.replace("\v", "\n").startswith("AI\n备\n考")
        )
        body = next(
            shape
            for slide in presentation.slides
            for shape in slide.shapes
            if hasattr(shape, "text") and "投融资：" in shape.text
        )

        self.assertEqual("KaiTi", header.text_frame.paragraphs[0].font.name)
        self.assertEqual(36.0, header.text_frame.paragraphs[0].font.size.pt)
        self.assertEqual("KaiTi", side_label.text_frame.paragraphs[0].font.name)
        self.assertEqual(18.0, side_label.text_frame.paragraphs[0].font.size.pt)
        self.assertIn("\v", side_label.text)
        self.assertEqual("KaiTi", body.text_frame.paragraphs[0].font.name)
        self.assertEqual(16.0, body.text_frame.paragraphs[0].font.size.pt)
        self.assertEqual(PP_ALIGN.JUSTIFY, body.text_frame.paragraphs[0].alignment)

    def test_policy_page_classifies_core_clauses(self):
        builder = load_builder_module()
        report = load_fixture("education_valid.json")

        builder.build(report, self.output, self.sources, self.quality)

        presentation = Presentation(self.output)
        all_text = "\n".join(slide_text(slide) for slide in presentation.slides)
        self.assertIn("政策来源：测试省教育厅", all_text)
        self.assertIn("限制性要求：", all_text)
        self.assertIn("倡导性/支持性内容：", all_text)
        self.assertNotIn("。。", all_text)

    def test_includes_native_powerpoint_pdf_exporter(self):
        exporter = BUILDER_MODULE.parent / "export_pptx_pdf.ps1"

        self.assertTrue(exporter.exists())
        exporter_text = exporter.read_text(encoding="utf-8")
        self.assertIn("SaveAs", exporter_text)
        self.assertIn("ppSaveAsPDF", exporter_text)

    def test_public_deck_uses_update_digest_and_hides_internal_tracking(self):
        builder = load_builder_module()
        report = load_fixture("education_valid.json")

        builder.build(report, self.output, self.sources, self.quality)

        presentation = Presentation(self.output)
        digest_text = slide_text(presentation.slides[1])
        all_text = "\n".join(slide_text(slide) for slide in presentation.slides)
        self.assertIn("本期主要动态", digest_text)
        self.assertIn("融资与交易", digest_text)
        self.assertIn("政策", digest_text)
        self.assertIn(report["sections"][0]["items"][0]["headline"], digest_text)
        self.assertIn("本期行业小结", slide_text(presentation.slides[-1]))
        for internal_label in ("本期核心观点", "证据事项", "后续跟踪", "下一期验证"):
            self.assertNotIn(internal_label, all_text)
        self.assertIn("tracking", report["sections"][0]["items"][0])


if __name__ == "__main__":
    unittest.main()
