import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "education-industry-observation"


class SkillRoutingTests(unittest.TestCase):
    def test_skill_declares_one_visual_template_with_dynamic_pagination(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("本 Skill 只生成同事版视觉语言的双周报", text)
        self.assertIn("colleague-biweekly-v1", text)
        self.assertIn("最多 15 页", text)
        self.assertIn("每个内容页放 1-3 项", text)
        self.assertIn("不固定 11 个槽位", text)

    def test_legacy_modes_are_not_default_or_optional(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        requirements = (SKILL / "references" / "report-requirements.md").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("reference_parity", text)
        self.assertNotIn("coverage_mode: broad_and_deep", text)
        self.assertNotIn("深析层", requirements)
        self.assertIn("不得用旧的“本期主要动态 + 事件深析 + 本期行业小结”", text)

    def test_skill_routes_template_generation_to_presentation_and_pdf_skills(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("同时读取演示文稿与 PDF 制作 Skill", text)
        self.assertIn("build_biweekly_pptx.ps1", text)
        self.assertIn("validate_template_fidelity.py", text)

    def test_openai_metadata_matches_dynamic_colleague_template(self):
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("教育行业观察双周报", text)
        self.assertIn("15页以内", text)
        self.assertIn("$education-industry-observation", text)

    def test_repository_readme_does_not_repeat_stale_public_structure(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("2. 本期核心观点", text)
        self.assertNotIn("事件页包含事实、行业判断、后续跟踪和来源", text)
        self.assertIn("根目录不重复维护会随版本变化的报告规则", text)


if __name__ == "__main__":
    unittest.main()
