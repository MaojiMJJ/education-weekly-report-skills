# 外发同步版双周报实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 将教育与职教双周报的公开页面改为事项同步口径，并彻底隐藏投资部内部跟踪信息。

**架构：** 保留现有研究 JSON 和校验器，避免丢失内部研究字段；只在 PowerPoint 映射层把 `sections` 自动转换为“本期主要动态”，并停止渲染 `tracking`。同步修改中文规则和回归测试，使未来运行保持相同行为。

**技术栈：** Python、python-pptx、unittest、PowerPoint COM、Git。

---

### 任务一：锁定对外页面行为

**文件：**
- 修改：`tests/test_education_pptx_builder.py`
- 修改：`tests/test_vocational_pptx_builder.py`

- [ ] 在两个构建测试中断言第二页包含“本期主要动态”和实际栏目名称。
- [ ] 断言整份 PPT 不含“本期核心观点”“证据事项”“后续跟踪”“下一期验证”。
- [ ] 断言输入 fixture 的 `tracking` 字段仍存在，证明只隐藏输出而未删除内部数据。
- [ ] 运行两个定向测试，确认修改前因旧页面仍可见而失败。

### 任务二：修改两个 PPT 生成器

**文件：**
- 修改：`skills/education-industry-observation/scripts/build_weekly_pptx.py`
- 修改：`skills/vocational-education-weekly-report/scripts/build_weekly_pptx.py`

- [ ] 新增栏目名称清理和主要动态分组函数，从 `sections` 生成第二页。
- [ ] 把 `add_insights_slide` 替换为“本期主要动态”页面，融资栏目保持最前。
- [ ] 删除事件页跟踪框调用并扩大行业判断框。
- [ ] 把末页改为“本期行业小结”，删除下一期验证列表。
- [ ] 运行定向测试，确认两个生成器通过。

### 任务三：同步 Skill 中文规则

**文件：**
- 修改：两个 Skill 的 `SKILL.md`
- 修改：两个 Skill 的 `references/report-requirements.md`
- 修改：两个 Skill 的 `references/report-template.md`
- 修改：两个 Skill 的 `references/quality-check.md`
- 修改：两个 Skill 的 `references/sample-patterns.md`（存在时）

- [ ] 明确公开报告定位为同步本期重要进展。
- [ ] 明确 `core_insights` 和 `tracking` 为内部研究字段，不进入 PPT。
- [ ] 固化“本期主要动态—事件页—本期行业小结”的公开结构。
- [ ] 增加红线：公开页面出现“后续跟踪”或“下一期验证”必须返工。

### 任务四：重生成当前双周报

**文件：**
- 修改：`tmp/weekly_skill_upgrade/build_strict_biweekly_json.py`
- 生成：`输出/教育行业观察双周报_20260627-20260710/教育行业观察_20260627-20260710_外发同步版.pptx`
- 生成：同名 PDF、来源清单、质量报告和逐页稿。

- [ ] 调整质量复核理由，删除下一步验证表述。
- [ ] 用新版 Skill 生成 PPTX，保持融资页在政策页之前。
- [ ] 用 PowerPoint 导出 PDF，逐页检查主要动态、事件页和小结页。
- [ ] 运行溢出检查，确认不存在裁切、孤立标点或内部跟踪文案。

### 任务五：发布

**文件：**
- 同步：`C:/Users/maoji/.codex/skills/education-industry-observation`
- 同步：`C:/Users/maoji/.codex/skills/vocational-education-weekly-report`

- [ ] 运行完整 unittest、两个 Skill 结构校验和运行时自检。
- [ ] 合并到 `main`，核对本地运行目录与仓库哈希一致。
- [ ] 推送 `MaojiMJJ/education-weekly-report-skills` 主分支。
