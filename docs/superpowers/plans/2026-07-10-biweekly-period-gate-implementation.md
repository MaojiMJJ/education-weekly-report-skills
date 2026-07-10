# Education Biweekly Period Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 阻止本期发布的半年盘点、历史回顾和旧事项进入教育双周报正文，并按严格报告期重做当前报告。

**Architecture:** 在事件卡中增加 `period_trigger`，把本期新增动作与来源发布日期分离。质量校验器负责校验触发类型、触发日期、直接来源、栏目类型匹配和具体动作；Skill 文档负责约束研究判断；空栏目由报告结构自然省略。

**Tech Stack:** Python 3.12、`unittest`、JSON、python-pptx、Markdown、PowerPoint COM、Git。

---

## 文件结构

- 修改 `tests/test_education_report_quality.py`：新增跨期盘点、有效融资、生效政策和触发来源测试。
- 修改 `tests/fixtures/education_valid.json`：为合法样例补齐 `period_trigger`。
- 修改 `skills/education-industry-observation/scripts/report_quality.py`：实现报告期触发硬门槛。
- 修改 `skills/education-industry-observation/SKILL.md`：明确双周报只追踪本期新增事项和空栏目省略规则。
- 修改 `skills/education-industry-observation/references/source-workflow.md`：把报告期触发核验放在来源评分之前。
- 修改 `skills/education-industry-observation/references/report-requirements.md`：增加各栏目的事件日期规则。
- 修改 `skills/education-industry-observation/references/report-template.md`：定义 `period_trigger` JSON 契约。
- 修改 `skills/education-industry-observation/references/quality-check.md`：加入跨期回顾拒绝项。
- 修改 `skills/education-industry-observation/references/sample-patterns.md`：增加“本期文章、跨期事件”的失败模式。
- 修改 `skills/education-industry-observation/scripts/build_weekly_pptx.py`：自检数据补齐触发字段。
- 修改 `D:\0Codexworkspace\教育行业项目\tmp\weekly_skill_upgrade\education_report_20260627_20260710.json`：删除上半年资本盘点并复核全部事项。
- 生成 `D:\0Codexworkspace\教育行业项目\输出\教育行业观察双周报_20260627-20260710\教育行业观察_20260627-20260710_严格双周版.pptx` 及配套文件。
- 同步 `C:\Users\maoji\.codex\skills\education-industry-observation`：让后续运行使用新版本。

### Task 1: 用失败测试固定报告期边界

**Files:**
- Modify: `tests/test_education_report_quality.py`
- Modify: `tests/fixtures/education_valid.json`

- [ ] **Step 1: 为合法样例增加本期触发字段**

在 `education_valid.json` 每个事项中加入：

```json
"period_trigger": {
  "type": "financing_announced",
  "description": "示例公司于2026年6月24日宣布完成本轮融资",
  "source_url": "https://www.cninfo.com.cn/new/disclosure/detail/e1"
}
```

根据事项类型分别使用合法触发类型，并确保 `source_url` 与该事项 `sources` 中的直接来源一致。

- [ ] **Step 2: 写入跨期盘点失败测试**

```python
def test_rejects_current_article_about_old_period_roundup(self):
    quality = load_quality_module()
    report = load_fixture("education_valid.json")
    item = report["sections"][0]["items"][0]
    item["event_type"] = "融资"
    item["event_date"] = "2026-07-03"
    item["period_trigger"] = {
        "type": "media_roundup",
        "description": "媒体于2026年7月3日盘点上半年融资事项",
        "source_url": item["sources"][0]["url"],
    }

    with self.assertRaises(quality.ReportQualityError) as caught:
        quality.validate_report(report)

    self.assertIn("本期触发类型", str(caught.exception))
```

- [ ] **Step 3: 写入栏目类型伪装失败测试**

```python
def test_financing_cannot_use_generic_data_release_as_period_trigger(self):
    quality = load_quality_module()
    report = load_fixture("education_valid.json")
    item = report["sections"][0]["items"][0]
    item["event_type"] = "融资"
    item["period_trigger"]["type"] = "official_data_released"
    item["period_trigger"]["description"] = "媒体发布上半年融资汇总数据"

    with self.assertRaises(quality.ReportQualityError) as caught:
        quality.validate_report(report)

    self.assertIn("与 event_type 不匹配", str(caught.exception))
```

- [ ] **Step 4: 写入触发来源失败测试**

```python
def test_period_trigger_source_must_match_verified_primary_source(self):
    quality = load_quality_module()
    report = load_fixture("education_valid.json")
    item = report["sections"][0]["items"][0]
    item["period_trigger"]["source_url"] = "https://news.example.org/roundup"

    with self.assertRaises(quality.ReportQualityError) as caught:
        quality.validate_report(report)

    self.assertIn("触发来源", str(caught.exception))
```

- [ ] **Step 5: 写入有效融资和政策生效测试**

```python
def test_accepts_current_financing_announcement(self):
    quality = load_quality_module()
    report = load_fixture("education_valid.json")
    quality.validate_report(report)


def test_accepts_policy_effective_with_older_official_source(self):
    quality = load_quality_module()
    report = load_fixture("education_valid.json")
    item = report["sections"][0]["items"][0]
    item["event_type"] = "政策"
    item["event_date"] = "2026-06-24"
    item["period_trigger"] = {
        "type": "policy_effective",
        "description": "该办法于2026年6月24日正式施行",
        "source_url": item["sources"][0]["url"],
    }
    item["sources"][0]["published_at"] = "2026-05-20"
    quality.validate_report(report)
```

- [ ] **Step 6: 运行测试确认新增用例失败**

Run:

```powershell
python -m unittest tests.test_education_report_quality -v
```

Expected: 新增测试因 `period_trigger` 尚未被校验而失败，现有测试仍保持原结果。

- [ ] **Step 7: 提交失败测试**

```powershell
git add tests/test_education_report_quality.py tests/fixtures/education_valid.json
git commit -m "测试双周报告期触发边界"
```

### Task 2: 实现报告期触发硬门槛

**Files:**
- Modify: `skills/education-industry-observation/scripts/report_quality.py`

- [ ] **Step 1: 增加触发类型和栏目映射常量**

```python
PERIOD_TRIGGER_TYPES = {
    "policy_issued",
    "policy_effective",
    "financing_announced",
    "transaction_signed",
    "filing_published",
    "product_launched",
    "deployment_started",
    "official_data_released",
    "material_business_update",
}

EVENT_TRIGGER_RULES = (
    (("融资", "资本", "并购", "收购", "交易", "上市", "ipo"),
     {"financing_announced", "transaction_signed", "filing_published"}),
    (("政策", "监管"), {"policy_issued", "policy_effective"}),
    (("产品", "ai教育", "人工智能"), {"product_launched", "deployment_started"}),
)

TRIGGER_ACTION_TERMS = {
    "policy_issued": ("发布", "印发", "出台", "通过"),
    "policy_effective": ("生效", "施行", "实施"),
    "financing_announced": ("融资", "完成", "获得", "获投"),
    "transaction_signed": ("签署", "并购", "收购", "完成交易"),
    "filing_published": ("公告", "递交", "受理", "挂牌", "上市", "披露"),
    "product_launched": ("发布", "上线", "推出"),
    "deployment_started": ("中标", "采购", "部署", "试点", "开通"),
    "official_data_released": ("发布", "披露", "公布"),
    "material_business_update": ("启动", "签约", "落地", "开工"),
}
```

- [ ] **Step 2: 增加栏目匹配辅助函数**

```python
def _allowed_trigger_types(event_type):
    normalized = str(event_type or "").strip().lower()
    for keywords, allowed in EVENT_TRIGGER_RULES:
        if any(keyword in normalized for keyword in keywords):
            return allowed
    return PERIOD_TRIGGER_TYPES
```

- [ ] **Step 3: 校验 `period_trigger`**

在每个事项的 `event_date` 校验之后加入：

```python
trigger = item.get("period_trigger")
if not isinstance(trigger, dict):
    issues.append(f"事项 {item_id} 必须包含 period_trigger")
    trigger = {}

trigger_type = trigger.get("type")
if trigger_type not in PERIOD_TRIGGER_TYPES:
    issues.append(f"事项 {item_id} 的本期触发类型无效")
elif trigger_type not in _allowed_trigger_types(item.get("event_type")):
    issues.append(f"事项 {item_id} 的本期触发类型与 event_type 不匹配")

description = trigger.get("description")
_check_text(issues, f"事项 {item_id} 的 period_trigger.description", description, 12, 120)
if _is_text(description) and trigger_type in TRIGGER_ACTION_TERMS:
    if not any(term in description for term in TRIGGER_ACTION_TERMS[trigger_type]):
        issues.append(f"事项 {item_id} 的本期触发说明缺少具体新增动作")
```

- [ ] **Step 4: 校验触发来源**

在来源循环完成后加入：

```python
trigger_url = trigger.get("source_url", "")
matching_source = None
if _valid_url(trigger_url):
    trigger_key = _normalise_url(trigger_url)
    for source in sources:
        if isinstance(source, dict) and _valid_url(source.get("url", "")):
            if _normalise_url(source["url"]) == trigger_key:
                matching_source = source
                break
if not matching_source:
    issues.append(f"事项 {item_id} 的触发来源必须出现在 sources 中")
elif matching_source.get("access_status") != "verified" or not matching_source.get("is_primary"):
    issues.append(f"事项 {item_id} 的触发来源必须是已核验的一手或原创直接来源")
```

- [ ] **Step 5: 调整报告期来源规则**

```python
if sources and not has_period_source and trigger_type != "policy_effective":
    issues.append(f"事项 {item_id} 至少需要 1 个发布日期在报告期内的直接来源")
```

`policy_effective` 仍必须满足 `event_date` 在报告期内，且触发来源是已核验官方直接来源。

- [ ] **Step 6: 运行教育质量测试**

Run:

```powershell
python -m unittest tests.test_education_report_quality -v
```

Expected: 全部通过。

- [ ] **Step 7: 运行完整测试集**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: 教育和职教测试全部通过，无回归。

- [ ] **Step 8: 提交校验器**

```powershell
git add skills/education-industry-observation/scripts/report_quality.py
git commit -m "增加双周报告期触发校验"
```

### Task 3: 更新 Skill 契约和研究流程

**Files:**
- Modify: `skills/education-industry-observation/SKILL.md`
- Modify: `skills/education-industry-observation/references/source-workflow.md`
- Modify: `skills/education-industry-observation/references/report-requirements.md`
- Modify: `skills/education-industry-observation/references/report-template.md`
- Modify: `skills/education-industry-observation/references/quality-check.md`
- Modify: `skills/education-industry-observation/references/sample-patterns.md`
- Modify: `skills/education-industry-observation/scripts/build_weekly_pptx.py`

- [ ] **Step 1: 在主 Skill 中加入不可绕过的报告期规则**

增加以下原则：

```markdown
双周报只追踪报告期内新发生、正式披露或正式生效的事项。来源发布日期在报告期内，不代表来源所总结的历史事项属于本期。媒体盘点、半年回顾、季度总结和历史梳理不能作为正文事项。

栏目在报告期内没有合格事项时直接省略。融资与交易有本期事项时排在重点事件最前；没有时不生成空页，也不跨期补录。
```

- [ ] **Step 2: 在来源流程中增加本期触发核验**

把核验顺序前两项改为：

```markdown
1. 识别本期新增动作，不先看文章发布日期：发生、正式披露、签约、上市、发布、生效、中标或部署。
2. 填写 `period_trigger`，确认触发日期在报告期内，并找到直接支持该动作的来源。
```

- [ ] **Step 3: 在报告要求中写明各栏目日期口径**

融资按融资宣布/完成、交易签约/完成和IPO递交/受理日期；政策按发布、决定或生效日期；产品按上线、采购、部署日期；上市公司按正式公告或交易所文件日期。

- [ ] **Step 4: 更新 JSON 契约**

在 `event_date` 后加入 `period_trigger` 示例，并说明 `source_url` 必须匹配已核验直接来源。

- [ ] **Step 5: 更新质量清单和失败样例**

新增检查项：

```markdown
□ 每个事项是否有报告期内的新增动作，而不是本期发布的历史总结？
□ `period_trigger` 是否由直接来源支持？
□ 空栏目是否省略，而非跨期补页？
```

- [ ] **Step 6: 更新生成器自检数据**

给 `self_test_spec()` 的每个事项加入合法 `period_trigger`，确保自检仍能运行。

- [ ] **Step 7: 运行 Skill 自检和完整测试**

Run:

```powershell
python skills/education-industry-observation/scripts/build_weekly_pptx.py --self-test `
  --output tests/output/education_period_gate.pptx `
  --sources-output tests/output/education_period_gate_sources.md `
  --quality-output tests/output/education_period_gate_quality.md
python -m unittest discover -s tests -v
```

Expected: PPTX、来源清单和质量报告生成；全部测试通过。

- [ ] **Step 8: 提交 Skill 文档和自检数据**

```powershell
git add skills/education-industry-observation
git commit -m "固化教育双周报报告期规则"
```

### Task 4: 按新规则重做当前双周报

**Files:**
- Modify: `D:\0Codexworkspace\教育行业项目\tmp\weekly_skill_upgrade\education_report_20260627_20260710.json`
- Create: `D:\0Codexworkspace\教育行业项目\输出\教育行业观察双周报_20260627-20260710\教育行业观察_20260627-20260710_严格双周版.pptx`
- Create: `D:\0Codexworkspace\教育行业项目\输出\教育行业观察双周报_20260627-20260710\教育行业观察_20260627-20260710_严格双周版_来源清单.md`
- Create: `D:\0Codexworkspace\教育行业项目\输出\教育行业观察双周报_20260627-20260710\教育行业观察_20260627-20260710_严格双周版_质量报告.md`
- Create: `D:\0Codexworkspace\教育行业项目\输出\教育行业观察双周报_20260627-20260710\教育行业观察_20260627-20260710_严格双周版_检索底稿.txt`

- [ ] **Step 1: 重新检索报告期融资、并购和IPO事项**

检索区间固定为2026-06-27至2026-07-10。只有融资宣布/完成、并购签约/完成、IPO递交/受理或正式上市日期落在区间内才进入候选池。

- [ ] **Step 2: 用同一规则复核现有政策和其他事项**

逐项确认 E1-E6 的 `event_date` 是政策发布、正式会议决定、行动启动或新增披露日期，而不是媒体转载日期。为每项补齐 `period_trigger`。

- [ ] **Step 3: 删除跨期资本事项**

删除 E7 及全部上半年资本明细。若检索不到本期合格交易，整个融资栏目省略。

- [ ] **Step 4: 重写核心观点和行业判断**

删除“资本仍追逐AI学习工具、硬件与底层能力”等上半年结论。每条核心观点至少引用两个保留事项。

- [ ] **Step 5: 运行新校验器生成严格双周版**

Run:

```powershell
python skills/education-industry-observation/scripts/build_weekly_pptx.py report.json `
  --output 教育行业观察_20260627-20260710_严格双周版.pptx `
  --sources-output 教育行业观察_20260627-20260710_严格双周版_来源清单.md `
  --quality-output 教育行业观察_20260627-20260710_严格双周版_质量报告.md
```

Expected: 校验通过，正文只包含报告期内事项。

- [ ] **Step 6: 用 PowerPoint 渲染全页检查**

导出 PDF 和逐页 PNG，检查黑屏、重叠、裁切、表格和来源页脚。发现问题必须修订并重新渲染。

### Task 5: 同步本地运行时与 GitHub

**Files:**
- Sync: `D:\0GitHub\education-weekly-report-skills\skills\education-industry-observation`
- Sync: `C:\Users\maoji\.codex\skills\education-industry-observation`

- [ ] **Step 1: 比较镜像和运行时目录**

Run:

```powershell
git diff --check
```

确认只包含本次报告期门槛相关修改。

- [ ] **Step 2: 将 GitHub 版本同步到运行时目录**

复制 Skill 主文件、references、scripts 和 agents，排除 `__pycache__`。

- [ ] **Step 3: 在运行时目录执行自检**

Run:

```powershell
python C:\Users\maoji\.codex\skills\education-industry-observation\scripts\build_weekly_pptx.py --self-test `
  --output tests/output/runtime_period_gate.pptx `
  --sources-output tests/output/runtime_period_gate_sources.md `
  --quality-output tests/output/runtime_period_gate_quality.md
```

Expected: 运行时版本独立通过。

- [ ] **Step 4: 提交实现和报告样例说明**

```powershell
git add skills tests docs
git commit -m "修复教育双周报跨期事项入选"
```

- [ ] **Step 5: 推送 GitHub**

```powershell
git push origin main
```

Expected: `main` 与 `origin/main` 同步，工作区干净。

- [ ] **Step 6: 最终验收**

确认：

- 跨期半年盘点测试失败后已转为被校验器拒绝。
- 合法本期融资和本期生效政策可以通过。
- 当前严格双周版没有上半年融资专题。
- 空融资栏目未生成空页。
- 本地运行时和 GitHub 使用相同文件哈希。
