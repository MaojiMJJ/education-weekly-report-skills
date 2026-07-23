import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EDUCATION_SKILL = ROOT / "skills" / "education-industry-observation"


class SkillRoutingTests(unittest.TestCase):
    def test_education_skill_uses_conditional_reference_routing(self):
        text = (EDUCATION_SKILL / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## 按任务读取", text)
        self.assertIn("用已有 JSON 重新生成 PPT", text)
        self.assertIn("调整 Skill 或排查历史失败", text)
        self.assertNotIn("开始任务后按以下顺序读取", text)

    def test_historical_samples_and_listed_companies_are_conditional(self):
        text = (EDUCATION_SKILL / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("涉及上市公司时读 `listed-companies.md`", text)
        self.assertIn("`sample-patterns.md`", text)
        self.assertNotIn("完整生成报告 | `source-workflow.md`、`report-requirements.md`、`event-analysis-template.md`、`report-template.md`、`quality-check.md`、`sample-patterns.md`", text)

    def test_canonical_rules_remain_present(self):
        requirements = (EDUCATION_SKILL / "references" / "report-requirements.md").read_text(
            encoding="utf-8"
        )
        template = (EDUCATION_SKILL / "references" / "report-template.md").read_text(
            encoding="utf-8"
        )
        quality = (EDUCATION_SKILL / "references" / "quality-check.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("楷体 36 号", requirements)
        self.assertIn("`financing_details`", template)
        self.assertIn("`cooperation_details`", template)
        self.assertIn("`policy_details`", template)
        self.assertIn("总分不低于 32 分", quality)
        self.assertIn("外发禁用措辞", quality)

    def test_repository_readme_does_not_repeat_stale_public_structure(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("2. 本期核心观点", text)
        self.assertNotIn("事件页包含事实、行业判断、后续跟踪和来源", text)
        self.assertIn("根目录不重复维护会随版本变化的报告规则", text)


if __name__ == "__main__":
    unittest.main()
