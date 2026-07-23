---
name: education-industry-observation
description: "适用于制作中国教育行业观察、教育行业周报或双周报，尤其是需要跟踪非职教教育政策、K12、教育信息化、AI+教育、上市公司交易、融资合作，并形成产业研究、投资讨论或项目机会判断的场景。"
---

# 教育行业观察

## 工作边界

生成面向领导、同事和业务人员的行业情报，不生成新闻清单。正文只收录报告期内新发生、正式披露或正式生效的事项；栏目没有合格事项时省略，不跨期补录或用弱事项凑页。

默认采用“广覆盖速览 + 高价值深析”的双层结构：速览用于补足政策、学校、产品和国际合作等本期重要动态，深析用于展开至少 5 个高价值事项。两层都必须满足严格日期、直接来源和去重要求；速览不是降低证据标准的新闻摘抄。

本 Skill 覆盖职业教育以外的 K12 学校、K12 培训、教育信息化、高等教育、国际教育和素质教育。职业教育事项转入 `vocational-education-weekly-report`，除非用户明确要求合并。

内部数据保留 `core_insights` 和 `tracking` 用于分析一致性与后续研究，但不得进入公开 PPT。来源未披露的固定字段写“未披露”，不适用时写“不适用”，不得省略或推测补造。

除非用户明确允许，不读取、不摘要、不引用邮箱、邮箱附件、内部转发正文或其他未公开材料。

## 按任务读取

只读取当前任务需要的文件；选中的文件必须完整读完后再行动。

| 任务 | 必读文件 | 条件文件 |
| --- | --- | --- |
| 从公开信息完整生成报告 | `source-workflow.md`、`report-requirements.md`、`event-analysis-template.md`、`report-template.md`、`quality-check.md` | 涉及上市公司时读 `listed-companies.md` |
| 检索、候选池或证据核验 | `source-workflow.md`、`event-analysis-template.md` | 需要判断行业边界或类型化信息时读 `report-requirements.md`；涉及上市公司时读 `listed-companies.md` |
| 基于已核验材料起草或修改 JSON | `report-requirements.md`、`event-analysis-template.md`、`report-template.md` | 事实、日期或来源需要补查时读 `source-workflow.md` |
| 用已有 JSON 重新生成 PPT | `report-template.md`、`quality-check.md` | JSON 未通过校验时再读对应业务要求或来源规则 |
| 审核现有报告 | `report-requirements.md`、`report-template.md`、`quality-check.md` | 发现事实或来源问题时读 `source-workflow.md` |
| 调整 Skill 或排查历史失败 | `sample-patterns.md`、`quality-check.md` 和相关测试 | 按问题读取其他文件，不默认加载全部参考材料 |

引用文件均位于 `references/`。不要把其中的详细字段、阈值或版式要求再次复制到本文件。

## 完整生成流程

1. 确认报告期、读者和资料边界；用户未指定时，使用截至当天的最近完整双周区间。
2. 按 `source-workflow.md` 完成各模块检索，记录查询、候选和空结果，先识别本期新增动作。
3. 建立候选池，补齐本期触发、主体、事实、来源、缺失字段及入选或剔除理由。
4. 通过事实和来源门槛后，先判定进入速览层还是深析层；深析事项按 `event-analysis-template.md` 评分并填写研究卡，合并重复事项。
5. 按 `report-requirements.md` 补齐两层事项及类型化信息，归纳内部核心观点和本期行业小结。
6. 按 `report-template.md` 生成 JSON，再用生成器执行 `quality-check.md` 对应的自动门槛。
7. 生成 PPT、来源清单和质量报告，使用 PowerPoint 原生导出 PDF，渲染全部页面检查溢出、黑屏、重叠、字体、来源和页码；PDF 必须实际保留楷体，不接受仅在 PPT 属性中声明楷体但导出时被替换。

生成器校验失败时修复研究内容，不删除校验或降低阈值。事项不足时停止出刊，交付检索底稿、候选池、剔除理由和缺口说明。

## 生成命令

```powershell
python scripts/build_weekly_pptx.py report.json `
  --output 教育行业观察.pptx `
  --sources-output 教育行业观察_来源清单.md `
  --quality-output 教育行业观察_质量报告.md
```

## 默认交付

- `教育行业观察_<报告期>.pptx`
- `教育行业观察_<报告期>.pdf`
- `教育行业观察_<报告期>_来源清单.md`
- `教育行业观察_<报告期>_质量报告.md`
- 质量未通过时：检索底稿、候选池、剔除理由和缺口说明，不交付伪完整 PPT。
