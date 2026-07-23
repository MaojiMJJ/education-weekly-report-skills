# 教育行业情报双周报 Skills

本仓库包含两个可独立部署的 Codex Skill：

- [`education-industry-observation`](skills/education-industry-observation/SKILL.md)：非职业教育行业周报或双周报。
- [`vocational-education-weekly-report`](skills/vocational-education-weekly-report/SKILL.md)：职业教育行业周报或双周报。

具体范围、字段、评分、公开页面边界和版式规则以各 Skill 的 `SKILL.md`、按任务路由的 `references/` 及生成器校验为准。根目录不重复维护会随版本变化的报告规则。

## 生成

```powershell
python skills/education-industry-observation/scripts/build_weekly_pptx.py report.json `
  --output 教育行业观察.pptx `
  --sources-output 教育行业观察_来源清单.md `
  --quality-output 教育行业观察_质量报告.md

python skills/vocational-education-weekly-report/scripts/build_weekly_pptx.py report.json `
  --output 职教行业周报.pptx `
  --sources-output 职教行业周报_来源清单.md `
  --quality-output 职教行业周报_质量报告.md
```

生成器先执行质量校验；不合格 JSON 不生成正式 PPT。PPT、来源清单和质量报告是同一交付批次。

## 验证

```powershell
python -m unittest discover -s tests -v

python <skill-creator>\scripts\quick_validate.py `
  skills\education-industry-observation

python <skill-creator>\scripts\quick_validate.py `
  skills\vocational-education-weekly-report
```

修改后还应使用真实报告 JSON 完成 PPT/PDF 回归、全页渲染、溢出检查和外发措辞扫描。

## 同步

正式变更必须同时同步：

- GitHub 镜像：`D:\0GitHub\education-weekly-report-skills`
- 运行时 Skill：
  - `D:\CodexData\home\skills\education-industry-observation`
  - `D:\CodexData\home\skills\vocational-education-weekly-report`

同步后重新执行测试和 Skill 校验，并核对运行时与镜像文件哈希。
