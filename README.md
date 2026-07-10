# 教育行业情报双周报 Skill

本仓库包含两个 Codex Skill，用于把公开信息转化为面向产业研究、投资讨论和项目机会发现的教育行业周报或双周报。

## Skill

- `skills/education-industry-observation`
  - 生成《教育行业观察》。
  - 覆盖 K12、教育信息化、高等教育、国际教育、素质教育、AI+教育、教育上市公司和融资交易。
- `skills/vocational-education-weekly-report`
  - 生成《职教行业周报》。
  - 覆盖职教政策、职业本科、职业院校、产业学院、产教融合、技能培训、职教上市公司和融资交易。

## 工作流

```text
检索底稿
  -> 候选池
  -> 事实与来源核验
  -> 五维评分
  -> 事件研究卡
  -> 本期核心观点
  -> 周报 JSON
  -> 自动质量校验
  -> 4:3 PPTX、来源清单与质量报告
  -> 全页渲染复核
```

五维评分包括行业影响、政策重要性、商业价值、技术相关性和投资相关性。每个事项必须写明评分理由、行业判断、受益方、风险和下一期验证问题。

## 出刊门槛

- 至少 5 个高价值正文事项。
- 事项总分不低于 16；或行业影响不低于 4，且其他维度至少一项不低于 4。
- 事项和至少一个直接来源必须处于报告期内；每个正式事项至少有 1 个一手来源或原创直接来源。
- 来源需记录访问核验状态和日期，核验日期不得早于发布日期，不接受保留域名或占位链接。
- 同一来源文件原则上只形成一个事项。
- 检索结论、低价值名单、重复政策和活动宣传不能进入正文。
- 40 分复核中任一维度低于 8 分或总分低于 32 分，不得出刊。

不满足门槛时只交付检索底稿、候选池、剔除理由和缺口说明，不生成伪完整 PPT。

## 报告结构

1. 封面。
2. 本期核心观点，1-3 条。
3. 重点事件，每页 1 个事项。
4. 本期行业判断，100-200 字。

默认页面为 4:3，事件页包含事实、行业判断、后续跟踪和来源；名单或条款对比可使用 2-4 列、最多 3 行的证据表格。完整 URL 单独写入来源清单。

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

生成器会在写入 PPT 前执行质量校验，旧版新闻摘要 JSON 会被拒绝。来源清单和质量报告路径是强制参数，不能只生成 PPT。

## 测试

```powershell
python -m unittest discover -s tests -v

$env:PYTHONUTF8 = "1"
python C:\Users\maoji\.codex\skills\.system\skill-creator\scripts\quick_validate.py `
  skills\education-industry-observation
python C:\Users\maoji\.codex\skills\.system\skill-creator\scripts\quick_validate.py `
  skills\vocational-education-weekly-report
```

测试固定包含：0709 失败样例拒绝、所有读者可见字段的内部标记拒绝、跨期事项拒绝、保留域名拒绝、核验日期关系、所有事项直接来源、低分事项拒绝、重复来源拒绝、文本与表格容量、4:3 页面，以及三件套强制交付。

## 本地部署

- GitHub 镜像：`D:\0GitHub\education-weekly-report-skills`
- 运行时 Skill：
  - `C:\Users\maoji\.codex\skills\education-industry-observation`
  - `C:\Users\maoji\.codex\skills\vocational-education-weekly-report`

修改后需要同步 GitHub 镜像和两个运行时目录，并在同步后重新执行测试与 `quick_validate.py`。
