---
name: education-industry-observation
description: "适用于按固定同事版视觉模板制作中国非职业教育行业双周报，自动计算最近完整双周，跟踪上市公司、教育行业其他动态与政策，并按当期有效内容动态编排为不超过 15 页的 4:3《教育行业观察》PPT、PDF、来源清单和质量报告。"
---

# 教育行业观察

## 唯一视觉模板

本 Skill 只生成同事版视觉语言的双周报，不再提供研究型扩写、新闻清单或其他视觉模式。基准视觉来自 `教育行业观察20260706-20260719.pdf`；它只定义封面、颜色、字体、标题栏、左侧标签和正文框，不固定以后各期的页数与事项数量。

固定模板 ID 为 `colleague-biweekly-v1`：

- 4:3，含封面总页数按当期有效内容动态确定，最少 2 页、最多 15 页。
- 第 1 页固定为照片封面；内容页保持“1 行业速览-上市公司”“2 行业速览-其他”“3 行业速览-政策”的顺序，只为有合格事项的栏目生成页面。
- 每个内容页放 1-3 项；事项较长时单独成页，简短事项可同页并列，不固定 11 个槽位。
- 固定使用浅绿标题栏、绿色左侧竖向标签、白色细绿边正文框。
- 标题栏为楷体 36 号，左侧标签为楷体 18 号，正文为楷体 16 号；封面标题为宋体、日期为 Calibri Light。
- 公开页面不显示来源、评分、行业判断、风险、`core_insights` 或 `tracking`；这些内容保留在 JSON、来源清单或质量报告。

模板几何、颜色、字体、动态分页容量和 15 页上限以 `assets/colleague-template/layout.json` 为唯一机器可读真值；可编辑 8 页基准示例为 `assets/教育行业观察_双周报模板.pptx`，不是页数上限。

## 工作边界

覆盖职业教育以外的 K12 学校、K12 培训、教育信息化、高等教育、国际教育、素质教育和 AI+教育。职业教育事项转入 `vocational-education-weekly-report`，除非用户明确要求合并。

正文只收录报告期内新发生、正式披露或正式生效的事项。文章在本期发布但底层事件属于跨期盘点、回顾或历史总结时排除。事项数量服从证据质量：不跨期补录、不虚构、不用弱事项凑页；全部栏目合计不足 5 个合格事项时停止正式出刊并交付缺口说明。

除非用户明确允许，不读取、不摘要、不引用邮箱、邮箱附件、内部转发正文或其他未公开材料。

## 按任务读取

只读取当前任务需要的文件；选中的文件必须完整读完后再行动。

| 任务 | 必读文件 | 条件文件 |
| --- | --- | --- |
| 从公开信息完整生成双周报 | `source-workflow.md`、`report-requirements.md`、`report-template.md`、`quality-check.md` | 涉及上市公司时读 `listed-companies.md`；同时读取演示文稿与 PDF 制作 Skill |
| 检索、候选池或证据核验 | `source-workflow.md`、`report-requirements.md` | 涉及上市公司时读 `listed-companies.md` |
| 基于已核验材料起草或修改 JSON | `report-requirements.md`、`report-template.md` | 事实、日期或来源需要补查时读 `source-workflow.md` |
| 用已有 JSON 重新生成 PPT | `report-template.md`、`quality-check.md` | 同时读取演示文稿与 PDF 制作 Skill |
| 审核现有报告 | `report-requirements.md`、`quality-check.md`、`sample-patterns.md` | 发现事实或来源问题时读 `source-workflow.md` |
| 调整 Skill 或排查历史失败 | `sample-patterns.md`、`quality-check.md` 和相关测试 | 按问题读取其他文件 |

引用文件均位于 `references/`。

## 完整生成流程

1. 用户未指定区间时，运行 `scripts/resolve_period.py`，按 2026-07-06 开始的周一至周日双周节奏，选择截至当天最近已经完整结束的 14 天。
2. 按 `source-workflow.md` 跑完政策、上市公司、融资与交易、业务合作、AI+教育和行业媒体模块，形成候选池。
3. 严格核验事件日期、主体、动作和直接来源，排除跨期盘点、重复事项和无落地信息。
4. 按 `report-requirements.md` 选择全部达到门槛且足以代表本期变化的重要事项，不预设上市公司、其他或政策数量。
5. 依据文本长度把事项编入 1-3 项/页的 `page_plan`，栏目连续、顺序固定，含封面总页数不超过 15 页。
6. 按 `report-template.md` 写入 `template_id: colleague-biweekly-v1` 的 JSON；内部保留 `core_insights`、逐项 `analysis` 和 `tracking`。
7. 运行 `scripts/report_quality.py`。双周日期、证据、分页顺序、总页数或文本容量不合格时停止生成。
8. 按演示文稿 Skill 初始化 artifact-tool 工作区，再运行 `scripts/build_biweekly_pptx.ps1` 生成 PPT、来源清单和质量报告。
9. 使用 Microsoft PowerPoint 原生导出 PDF；运行 `scripts/validate_template_fidelity.py`，再逐页全尺寸渲染检查字体、溢出、重叠、边框、留白和页数。

不得用旧的“本期主要动态 + 事件深析 + 本期行业小结”结构替代模板，也不得把样稿原有事项保留为新一期内容。

## 默认交付

- `教育行业观察_<报告期>.pptx`
- `教育行业观察_<报告期>.pdf`
- `教育行业观察_<报告期>_来源清单.md`
- `教育行业观察_<报告期>_质量报告.md`
- 质量未通过时：检索底稿、候选池、剔除理由和缺口说明，不交付伪完整 PPT。
