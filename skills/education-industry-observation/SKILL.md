---
name: education-industry-observation
description: "适用于按固定同事版模板制作中国非职业教育行业双周报，自动计算最近完整双周，跟踪上市公司、教育行业其他动态与政策，并生成与基准稿一致的 8 页 4:3《教育行业观察》PPT、PDF、来源清单和质量报告。"
---

# 教育行业观察

## 唯一输出

本 Skill 只生成固定同事版双周报，不再提供研究型扩写、新闻清单或其他视觉模式。基准视觉来自 `教育行业观察20260706-20260719.pdf`；它只定义版式，不定义以后各期内容。

固定模板 ID 为 `colleague-biweekly-v1`：

- 8 页、4:3，不增页、不减页。
- 第 1 页为照片封面；第 2-3 页为“1 行业速览-上市公司”；第 4-6 页为“2 行业速览-其他”；第 7-8 页为“3 行业速览-政策”。
- 正文固定 11 个槽位：上市公司 3 项、其他 3 项、政策 5 项。
- 固定使用浅绿标题栏、绿色左侧竖向标签、白色细绿边正文框。
- 标题栏为楷体 36 号，左侧标签为楷体 18 号，正文为楷体 16 号；封面标题为宋体、日期为 Calibri Light。
- 公开页面不显示来源、评分、行业判断、风险、`core_insights` 或 `tracking`；这些内容保留在 JSON、来源清单或质量报告。

模板几何、颜色、字体和槽位容量以 `assets/colleague-template/layout.json` 为唯一机器可读真值；可编辑空白模板为 `assets/教育行业观察_双周报模板.pptx`。

## 工作边界

覆盖职业教育以外的 K12 学校、K12 培训、教育信息化、高等教育、国际教育、素质教育和 AI+教育。职业教育事项转入 `vocational-education-weekly-report`，除非用户明确要求合并。

正文只收录报告期内新发生、正式披露或正式生效的事项。文章在本期发布但底层事件属于跨期盘点、回顾或历史总结时排除。栏目槽位不足时停止正式出刊并交付缺口说明，不跨期补录、不虚构、不用弱事项凑满模板。

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
4. 按 `report-requirements.md` 选择上市公司 3 项、其他 3 项、政策 5 项，并按固定槽位容量压缩为事实型要点。
5. 按 `report-template.md` 写入 `template_id: colleague-biweekly-v1` 的 JSON；内部保留 `core_insights`、逐项 `analysis` 和 `tracking`。
6. 运行 `scripts/report_quality.py`。任何栏目数量、槽位顺序、双周日期、证据或文本容量不合格时停止生成。
7. 按演示文稿 Skill 初始化 artifact-tool 工作区，再运行 `scripts/build_biweekly_pptx.ps1` 生成 PPT、来源清单和质量报告。
8. 使用 Microsoft PowerPoint 原生导出 PDF；运行 `scripts/validate_template_fidelity.py`，再逐页全尺寸渲染检查字体、溢出、重叠、边框、留白和页数。

不得用旧的“本期主要动态 + 事件深析 + 本期行业小结”结构替代模板，也不得把样稿原有事项保留为新一期内容。

## 默认交付

- `教育行业观察_<报告期>.pptx`
- `教育行业观察_<报告期>.pdf`
- `教育行业观察_<报告期>_来源清单.md`
- `教育行业观察_<报告期>_质量报告.md`
- 质量未通过时：检索底稿、候选池、剔除理由和缺口说明，不交付伪完整 PPT。
