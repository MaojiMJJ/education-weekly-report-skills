# 报告模板与 JSON 契约

## 报告结构

1. 封面。
2. 本期主要动态，按非空栏目自动列出正式事项。
3. 重点事件，至少 5 个；本期融资与交易非空时排在最前，空栏目省略。
4. 本期行业小结，100-200 字，不含下一期任务。

## JSON 示例

字段名保持英文，内容使用中文。

```json
{
  "title": "教育行业观察",
  "period": "2026.06.22-2026.07.05",
  "core_insights": [
    {
      "claim": "AI教育正在进入教学和作业流程",
      "evidence_ids": ["E1", "E3"]
    }
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
          "event_type": "融资",
          "period_trigger": {
            "type": "financing_announced",
            "description": "事项主体于2026年6月24日宣布完成本轮融资",
            "source_url": "https://www.cninfo.com.cn/new/disclosure/detail/education-round"
          },
          "background": "20-140字主体背景，说明业务、客户、历史和本次事项的上下文。",
          "financing_details": {
            "amount": "近千万元",
            "round": "天使轮",
            "currency": "人民币",
            "investors": ["投资方甲"],
            "fund_use": ["产品研发", "市场推广"],
            "business_positioning": "大学生备考教育Agent",
            "business_domain": "大学生考试培训",
            "customer_side": "C端为主，兼有B端SaaS",
            "delivery_mode": "线上",
            "offering_type": "软件与服务",
            "user_type": "成人",
            "founded_at": "2025年",
            "users": "未披露",
            "stores": "不适用",
            "store_model": "不适用",
            "gross_billing": "未披露",
            "prior_investors": ["未披露"],
            "revenue": "未披露",
            "profit": "未披露"
          },
          "facts": ["事实一", "事实二", "事实三"],
          "analysis": "说明事件改变的行业变量、趋势和影响机制。",
          "beneficiaries": ["受益方及机制"],
          "risks": ["风险及失败条件"],
          "tracking": "内部研究使用的下一期验证指标或节点，不进入公开PPT。",
          "scores": {
            "industry_impact": 4,
            "policy_importance": 2,
            "commercial_value": 5,
            "technology_relevance": 5,
            "investment_relevance": 4
          },
          "score_reasons": {
            "industry_impact": "理由",
            "policy_importance": "理由",
            "commercial_value": "理由",
            "technology_relevance": "理由",
            "investment_relevance": "理由"
          },
          "sources": [
            {
              "name": "来源名称",
              "url": "https://www.cninfo.com.cn/new/disclosure/detail/education-round",
              "published_at": "2026-06-24",
              "source_type": "company",
              "is_primary": true,
              "access_status": "verified",
              "access_checked_at": "2026-07-05"
            }
          ],
          "evidence_table": {
            "columns": ["指标", "数据"],
            "rows": [["用户数", "已披露数据"]]
          }
        }
      ]
    }
  ],
  "weekly_judgment": "100-200字行业判断。",
  "quality_review": {
    "information_quality": {"score": 8, "reason": "不少于10字的复核理由。"},
    "analysis_depth": {"score": 8, "reason": "不少于10字的复核理由。"},
    "readability": {"score": 8, "reason": "不少于10字的复核理由。"},
    "strategic_value": {"score": 8, "reason": "不少于10字的复核理由。"}
  }
}
```

按事项类型使用以下附加对象：

- 融资：必须填写 `financing_details` 示例中的全部字段。
- 业务合作、新业务、新学校筹备或设立：填写 `cooperation_details`，字段为 `parties`、`party_types`、`action_type`、`cooperation_content`、`business_or_school`、`location`、`implementation_plan`、`commercialization`。
- 政策或监管：填写 `policy_details`，字段为 `issuing_body`、`policy_name`、`issued_at`、`effective_at`、`scope_level`、`scope_description`、`prohibited_rules`、`restrictive_requirements`、`supportive_measures`。

附加对象进入公开事件页。未披露字段使用“未披露”；不适用字段使用“不适用”。不能省略字段、使用空字符串或根据其他数据推算。

`evidence_table` 可选，只在名单、交易条款、数据对比或政策清单比文字更清楚时使用。表格限 2-4 列、1-3 行；2 列每格最多 20 字，3 列最多 12 字，4 列最多 8 字。

每个事项至少包含 1 个 `is_primary: true` 的一手来源或原创直接来源。`access_checked_at` 必须是实际打开页面的日期，且不得早于 `published_at`；保留域名、占位链接和搜索摘要不能标记为已核验。

`period_trigger.type` 只允许：`policy_issued`、`policy_effective`、`financing_announced`、`transaction_signed`、`filing_published`、`product_launched`、`deployment_started`、`official_data_released`、`material_business_update`。`description` 必须写明 `event_date` 和具体新增动作；`source_url` 必须与该事项 `sources` 中已核验的一手或原创直接来源一致。

媒体盘点、半年回顾、季度总结和历史梳理不是合法触发类型。历史数据只能作为本期事项的背景或补充事实，不能独立生成事件页。

## 页面映射

- `core_insights` 用于内部分析一致性校验，不直接进入公开 PPT。
- `sections` 的栏目名和 `headline` 自动生成“本期主要动态”页，最多展示 8 个正式事项。
- 每个 `item` 生成 1 个事件页。
- `subject`、`event_date` 和 `event_type` 进入元数据行，`period_trigger` 用于出刊前校验，`background` 进入主体背景区。
- 融资页优先渲染 `financing_details`，业务合作页优先渲染 `cooperation_details`，政策页优先渲染 `policy_details`；其他事项使用 `facts` 和 `background`。
- `analysis`、`beneficiaries` 和 `risks` 进入行业判断区；`tracking` 仅保留在内部研究数据中。
- `sources` 在页脚显示来源名和日期，完整 URL 进入独立来源清单。
- `weekly_judgment` 生成“本期行业小结”页，不得包含下一期任务或内部跟踪安排。
- `quality_review` 生成独立质量报告；任一得分低于 8 或总分低于 32 时拒绝生成。
- 事件页顶部标题栏使用楷体 36 号，左侧短标题使用楷体 18 号竖排，正文使用楷体 16 号并两端对齐。
