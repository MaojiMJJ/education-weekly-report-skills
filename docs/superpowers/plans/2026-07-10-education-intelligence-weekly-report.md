# 教育行业情报双周报 Skill 重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让两个教育周报 Skill 稳定输出可用于产业研究和投资讨论的双周报，并机械拒绝新闻拼盘、重复事项和凑数页。

**Architecture:** 每个 Skill 采用检索底稿、五维评分、事件研究卡、周报叙事和自动质量门槛。PPT 生成器只接受通过校验的结构化 JSON，并输出 4:3 PPTX 与来源清单。

**Tech Stack:** Markdown Skill、Python、python-pptx、unittest、PowerPoint/LibreOffice 渲染、Codex quick_validate.py。

---

### Task 1: 固化失败基线和结构测试

**Files:**
- Create: `tests/test_report_quality.py`
- Create: `tests/fixtures/education_0709_failed.json`
- Create: `tests/fixtures/education_valid.json`

- [ ] **Step 1: 保存失败样例**

将 0709 教育 JSON 复制为失败 fixture，不修改内容。

- [ ] **Step 2: 写失败测试**

测试旧样例必须因缺少 `core_insights`、`weekly_judgment`、事件评分、研究解释、跟踪问题及合格来源数组而失败；合格 fixture 必须通过。

- [ ] **Step 3: 运行测试并确认 RED**

Run: `python -m unittest tests.test_report_quality -v`

Expected: FAIL，原因是质量校验模块尚不存在或未实现规则。

### Task 2: 实现教育报告质量模型

**Files:**
- Create: `skills/education-industry-observation/scripts/report_quality.py`
- Modify: `skills/education-industry-observation/scripts/build_weekly_pptx.py`

- [ ] **Step 1: 实现结构校验**

校验 `title`、`period`、`core_insights`、`sections`、`weekly_judgment`、事件事实、分析、跟踪、五维评分和来源。

- [ ] **Step 2: 实现入选和去重规则**

拒绝低于入选阈值、来源不可访问、重复来源文件、正文少于 5 项以及“检索结论”类事项。

- [ ] **Step 3: 运行单元测试并确认 GREEN**

Run: `python -m unittest tests.test_report_quality -v`

Expected: 所有测试通过。

### Task 3: 重构教育 Skill 和研究模板

**Files:**
- Modify: `skills/education-industry-observation/SKILL.md`
- Modify: `skills/education-industry-observation/references/report-requirements.md`
- Modify: `skills/education-industry-observation/references/source-workflow.md`
- Modify: `skills/education-industry-observation/references/sample-patterns.md`
- Create: `skills/education-industry-observation/references/event-analysis-template.md`
- Create: `skills/education-industry-observation/references/report-template.md`
- Create: `skills/education-industry-observation/references/quality-check.md`
- Modify: `skills/education-industry-observation/agents/openai.yaml`

- [ ] **Step 1: 把 Skill 主流程改成情报工作流**

明确候选池、评分、研究卡、叙事、停刊和自评顺序，并禁止检索结论进入正文。

- [ ] **Step 2: 写三个可复用模板**

事件研究卡定义事实、背景、解释、影响和跟踪；报告模板定义四段结构；质量模板定义 40 分验收和返工门槛。

- [ ] **Step 3: 更新默认提示**

默认提示要求先研究、后成稿，并附来源清单和质量报告。

### Task 4: 升级教育 PPT 生成器

**Files:**
- Modify: `skills/education-industry-observation/scripts/build_weekly_pptx.py`

- [ ] **Step 1: 改为 4:3 和四类页面**

实现封面、核心观点、事件、周度判断；事件页保留栏目条、左侧短标题、右侧事实区、行业判断和后续跟踪。

- [ ] **Step 2: 增加证据表格与来源清单**

支持可选 `evidence_table`，并通过 `--sources-output` 写出 Markdown 来源清单。

- [ ] **Step 3: 生成并渲染合格样例**

Run: `python skills/education-industry-observation/scripts/build_weekly_pptx.py tests/fixtures/education_valid.json --output tmp/education_valid.pptx --sources-output tmp/education_sources.md`

Expected: PPTX 和来源清单生成成功，页面无溢出或黑屏。

### Task 5: 独立验证教育 Skill

**Files:**
- Modify only if test reveals gaps: `skills/education-industry-observation/**`

- [ ] **Step 1: 运行 quick_validate**

Run: `python <skill-creator>/scripts/quick_validate.py skills/education-industry-observation`

Expected: `Skill is valid!`

- [ ] **Step 2: 前向测试**

让独立实例使用新 Skill 判断 0709 失败样例是否应出刊，并用合格 fixture 说明输出结构。

- [ ] **Step 3: 修补漏洞并重测**

若独立实例仍允许凑数、重复或无研究解释的事项，收紧规则后重新运行测试。

### Task 6: 迁移并验证职教 Skill

**Files:**
- Modify: `skills/vocational-education-weekly-report/SKILL.md`
- Modify: `skills/vocational-education-weekly-report/references/report-requirements.md`
- Modify: `skills/vocational-education-weekly-report/references/source-workflow.md`
- Modify: `skills/vocational-education-weekly-report/references/sample-patterns.md`
- Create: `skills/vocational-education-weekly-report/references/event-analysis-template.md`
- Create: `skills/vocational-education-weekly-report/references/report-template.md`
- Create: `skills/vocational-education-weekly-report/references/quality-check.md`
- Create: `skills/vocational-education-weekly-report/scripts/report_quality.py`
- Modify: `skills/vocational-education-weekly-report/scripts/build_weekly_pptx.py`
- Modify: `skills/vocational-education-weekly-report/agents/openai.yaml`
- Create: `tests/fixtures/vocational_0709_failed.json`
- Create: `tests/fixtures/vocational_valid.json`

- [ ] **Step 1: 迁移通用质量模型**

保留职教政策、院校、产教融合、上市公司和融资字段，禁止把同一政策拆页或把检索结论放入正文。

- [ ] **Step 2: 增加职教测试**

旧 0709 JSON 必须失败，合格 fixture 必须通过。

- [ ] **Step 3: 生成、渲染并 quick_validate**

Expected: 单元测试、样例生成和 Skill 校验全部通过。

### Task 7: 部署与最终验收

**Files:**
- Modify: `README.md`
- Sync: `C:/Users/maoji/.codex/skills/education-industry-observation/**`
- Sync: `C:/Users/maoji/.codex/skills/vocational-education-weekly-report/**`

- [ ] **Step 1: 更新 README**

说明两个 Skill 的定位、执行顺序、停刊条件和测试命令。

- [ ] **Step 2: 完整验证**

运行两套单元测试、两个 quick_validate、两个样例生成、来源清单检查、PPT 渲染和文本溢出检查。

- [ ] **Step 3: 同步运行时**

只在完整验证通过后覆盖本地运行时 Skill，并再次运行 quick_validate 和自测。

- [ ] **Step 4: 提交并推送 GitHub**

提交范围仅限本次 Skill、测试、设计和说明文件；推送 `main` 后确认本地与 `origin/main` 一致。
