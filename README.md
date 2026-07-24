# 教育行业情报双周报 Skills

本仓库包含两个可独立部署的 Codex Skill：

- [`education-industry-observation`](skills/education-industry-observation/SKILL.md)：按固定同事版 8 页模板生成非职教教育行业双周报。
- [`vocational-education-weekly-report`](skills/vocational-education-weekly-report/SKILL.md)：职业教育行业周报或双周报。

具体范围、字段、评分、公开页面边界和版式规则以各 Skill 的 `SKILL.md`、按任务路由的 `references/` 及生成器校验为准。根目录不重复维护会随版本变化的报告规则。

## 教育行业观察生成

教育行业观察使用 `@oai/artifact-tool` 固定生成 8 页 4:3 PPTX。先按演示文稿 Skill 初始化 artifact-tool 工作区，再运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/education-industry-observation/scripts/build_biweekly_pptx.ps1 `
  -InputJson report.json `
  -Output 教育行业观察.pptx `
  -SourcesOutput 教育行业观察_来源清单.md `
  -QualityOutput 教育行业观察_质量报告.md `
  -SlidesSkillDir <presentations-skill-directory>
```

生成器先执行固定模板质量校验；不合格 JSON 不生成正式 PPT。PPT、来源清单和质量报告是同一交付批次。PDF 必须使用 Microsoft PowerPoint 原生导出。

职业教育 Skill 继续使用其独立生成命令。

## 验证

```powershell
python -m unittest discover -s tests -v

python <skill-creator>\scripts\quick_validate.py `
  skills\education-industry-observation

python <skill-creator>\scripts\quick_validate.py `
  skills\vocational-education-weekly-report
```

修改教育行业观察模板后，还必须使用真实 JSON 完成 artifact-tool 生成、PowerPoint PDF 导出、8 页全页渲染、溢出检查、字体检查和外发措辞扫描。

## 同步

正式变更必须同时同步：

- GitHub 镜像：`D:\0GitHub\education-weekly-report-skills`
- 运行时 Skill：
  - `D:\CodexData\home\skills\education-industry-observation`
  - `D:\CodexData\home\skills\vocational-education-weekly-report`

同步后重新执行测试和 Skill 校验，并核对运行时与镜像文件哈希。
