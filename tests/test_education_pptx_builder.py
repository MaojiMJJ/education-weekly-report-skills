import importlib.util
import json
import unittest
from pathlib import Path

from pptx import Presentation


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
        report["sections"][1]["items"][1]["evidence_table"] = {
            "columns": ["机构", "年检结果"],
            "rows": [["测试机构甲", "合格"], ["测试机构乙", "合格"]],
        }

        builder.build(report, self.output, self.sources, self.quality)

        self.assertTrue(self.output.exists())
        self.assertTrue(self.sources.exists())
        self.assertTrue(self.quality.exists())
        presentation = Presentation(self.output)
        self.assertAlmostEqual(10.0, presentation.slide_width / 914400, places=2)
        self.assertAlmostEqual(7.5, presentation.slide_height / 914400, places=2)
        self.assertEqual(8, len(presentation.slides))
        self.assertIn("本期核心观点", slide_text(presentation.slides[1]))
        self.assertIn("行业判断", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("后续跟踪", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("主体背景", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("受益", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("风险", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("测试教育科技公司甲", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("2026-06-24", "\n".join(slide_text(slide) for slide in presentation.slides))
        self.assertIn("本期行业判断", slide_text(presentation.slides[-1]))
        self.assertTrue(
            any(
                getattr(shape, "has_table", False)
                for slide in presentation.slides
                for shape in slide.shapes
            )
        )
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

    def test_rejects_old_news_digest_before_building(self):
        builder = load_builder_module()
        report = load_fixture("education_0709_failed.json")

        with self.assertRaises(Exception) as caught:
            builder.build(report, self.rejected_output)

        self.assertIn("core_insights", str(caught.exception))
        self.assertFalse(self.rejected_output.exists())


if __name__ == "__main__":
    unittest.main()
