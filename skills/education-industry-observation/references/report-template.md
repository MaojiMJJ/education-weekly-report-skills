# 报告 JSON 契约与页面映射

## 基础结构

字段名使用英文，内容使用中文。正式报告至少包含 5 个深析事件；默认双层模式还须包含至少 5 个速览事项。

```json
{
  "title": "教育行业观察",
  "period": "2026.06.22-2026.07.05",
  "coverage_mode": "broad_and_deep",
  "core_insights": [
    {"claim": "由至少两个事项支持的内部观点", "evidence_ids": ["E1", "E2"]}
  ],
  "sections": [
    {
      "name": "行业速览-AI教育",
      "items": [
        {
          "id": "E1",
          "content_role": "event",
          "headline": "完整事件标题",
          "short_title": "左侧短标题",
          "event_date": "2026-06-24",
          "subject": "事项主体",
          "event_type": "产品",
          "period_trigger": {
            "type": "product_launched",
            "description": "事项主体于2026年6月24日正式发布产品",
            "source_url": "https://example.gov.cn/direct-source"
          },
          "background": "主体业务、客户、历史和事项上下文。",
          "facts": ["事实一", "事实二", "事实三"],
          "analysis": "说明改变的行业变量、趋势和影响机制。",
          "beneficiaries": ["受益方及机制"],
          "risks": ["风险及失败条件"],
          "tracking": "内部研究使用的验证指标或节点，不进入公开PPT。",
          "scores": {
            "industry_impact": 4,
            "policy_importance": 2,
            "commercial_value": 4,
            "technology_relevance": 5,
            "investment_relevance": 3
          },
          "score_reasons": {
            "industry_impact": "事实理由",
            "policy_importance": "事实理由",
            "commercial_value": "事实理由",
            "technology_relevance": "事实理由",
            "investment_relevance": "事实理由"
          },
          "sources": [
            {
              "name": "来源名称",
              "url": "https://example.gov.cn/direct-source",
              "published_at": "2026-06-24",
              "source_type": "government",
              "is_primary": true,
              "access_status": "verified",
              "access_checked_at": "2026-07-05"
            }
          ]
        }
      ]
    }
  ],
  "weekly_judgment": "100-200字本期行业小结。",
  "quality_review": {
    "information_quality": {"score": 8, "reason": "不少于10字的复核理由。"},
    "analysis_depth": {"score": 8, "reason": "不少于10字的复核理由。"},
    "readability": {"score": 8, "reason": "不少于10字的复核理由。"},
    "strategic_value": {"score": 8, "reason": "不少于10字的复核理由。"}
  }
}
```

示例 URL 只表示字段格式，正式报告必须替换为实际打开并核验的来源。

## 复刻模式契约

`reference_parity` 模式除报告 JSON 外，必须单独生成复刻清单；校验脚本读取下列顶层结构：

```json
{
  "mode": "reference_parity",
  "reference": {
    "file": "用户提供的样稿.pdf",
    "sha256": "64位SHA-256"
  },
  "expected": {
    "page_count": 8,
    "page_size_pts": [720, 540],
    "required_fonts": ["KaiTi", "SimSun", "Calibri-Light"],
    "reference_items": [
      {
        "reference_id": "R01",
        "page": 2,
        "short_title": "样稿左栏标题",
        "content_markers": ["主体名", "关键产品或政策名", "关键数字"],
        "event_date": "2026-06-09",
        "date_scope": "reference_carryover",
        "sources": [
          {
            "name": "直接来源",
            "url": "https://example.gov.cn/direct-source",
            "published_at": "2026-06-10",
            "access_checked_at": "2026-07-23"
          }
        ]
      }
    ]
  },
  "output_items": [
    {"reference_id": "R01", "page": 2}
  ]
}
```

`reference_items` 是样稿内容真值表；`output_items` 是成品页码映射。两个列表中的 `reference_id` 必须一一对应且只出现一次。`content_markers` 必须在指定成品页可见，不能只写进备注或来源清单。

`date_scope` 只允许 `within_period` 或 `reference_carryover`。后者表示因用户明确要求复刻而保留的跨期事项，不改变真实事件日期。

## 速览对象

速览对象与事件对象放在相同 `sections[].items` 中，最小结构如下：

```json
{
  "id": "B1",
  "content_role": "brief",
  "headline": "完整速览标题",
  "short_title": "速览短标题",
  "event_date": "2026-06-26",
  "subject": "事项主体",
  "event_type": "产品",
  "period_trigger": {
    "type": "product_launched",
    "description": "事项主体于2026年6月26日正式发布产品",
    "source_url": "https://example.gov.cn/direct-source"
  },
  "facts": ["可核验事实一", "可核验事实二"],
  "why_it_matters": "说明该事项补充了哪类供给、需求、政策或场景变化。",
  "sources": [
    {
      "name": "来源名称",
      "url": "https://example.gov.cn/direct-source",
      "published_at": "2026-06-26",
      "source_type": "government",
      "is_primary": true,
      "access_status": "verified",
      "access_checked_at": "2026-07-05"
    }
  ]
}
```

速览限 2-3 条事实、每条最多 80 字、合计最多 180 字；`why_it_matters` 为 15-90 字。每项最多 2 个直接来源。正式 URL 不得使用示例域名。

## 类型化对象

按事项类型在事件对象中增加以下对象；字段不得缺失、为空或推算，未披露写“未披露”，不适用写“不适用”。

- `financing_details`：`amount`、`round`、`currency`、`investors`、`fund_use`、`business_positioning`、`business_domain`、`customer_side`、`delivery_mode`、`offering_type`、`user_type`、`founded_at`、`users`、`stores`、`store_model`、`gross_billing`、`prior_investors`、`revenue`、`profit`。
- `cooperation_details`：`parties`、`party_types`、`action_type`、`cooperation_content`、`business_or_school`、`location`、`implementation_plan`、`commercialization`。
- `policy_details`：`issuing_body`、`policy_name`、`issued_at`、`effective_at`、`scope_level`、`scope_description`、`prohibited_rules`、`restrictive_requirements`、`supportive_measures`。

融资对象的 `investors`、`fund_use`、`prior_investors`，合作对象的 `parties`、`party_types`，以及政策对象的三个条款字段均使用字符串列表；其他字段使用字符串。

`scope_level` 只允许“全国性”或“地方性”。政策三个条款列表允许某类为空，但合计至少一条。

## 触发与来源

`period_trigger.type` 只允许：

- `policy_issued`
- `policy_effective`
- `financing_announced`
- `transaction_signed`
- `filing_published`
- `product_launched`
- `deployment_started`
- `official_data_released`
- `material_business_update`

`description` 写明 `event_date` 和具体新增动作；`source_url` 必须与 `sources` 中已核验的一手或原创直接来源一致。除本期正式生效的旧政策外，至少一个直接来源也必须在报告期内发布。

媒体盘点、半年回顾、季度总结和历史梳理不是合法触发。历史数据只能作为本期事项背景。

## 容量与证据表格

- `background`、`facts`、`analysis`、受益方和风险必须满足生成器的文本容量限制。
- `evidence_table` 可选，限 2-4 列、1-3 行；2 列每格最多 20 字，3 列最多 12 字，4 列最多 8 字。
- 每项最多保留 3 个直接来源；来源名须适合页脚展示。

## 页面映射

1. 封面：`title` 和 `period`。
2. 本期主要动态：按非空 `sections` 的栏目名和 `headline` 自动生成，双层模式最多展示 12 项。
3. 分类速览页：每页通常展示 2 个 `content_role: brief`，包括日期、事实、“为什么重要”和来源。
4. 事件页：每个 `content_role: event` 生成一页；类型化对象优先决定正文结构。
5. 本期行业小结：使用 `weekly_judgment`，写明总覆盖数和深析数。
6. 来源清单：完整输出速览与深析的 `sources`。
7. 质量报告：使用 `quality_review`。

推荐栏目为“行业速览-上市公司”“行业速览-融资与交易”“行业速览-政策”“行业速览-AI教育”“行业速览-其他”。空栏目省略；融资与交易有合格事项时排在事件页最前。

`core_insights` 和 `tracking` 只用于内部研究，不渲染到公开 PPT。

`reference_parity` 不执行上述默认页面映射；它严格执行样稿逐页映射，且不得自动添加“本期主要动态”、事件深析页、本期行业小结或来源页。
