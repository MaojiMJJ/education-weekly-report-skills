# 报告模板与 JSON 契约

## 报告结构

1. 封面。
2. 本期核心观点，1-3 条。
3. 重点事件，至少 5 个。
4. 本期行业判断，100-200 字。

## JSON 示例

字段名保持英文，内容使用中文。

```json
{
  "title": "职教行业周报",
  "period": "2026.06.22-2026.07.05",
  "core_insights": [
    {
      "claim": "职业本科扩容正在与产业链专业调整同步推进",
      "evidence_ids": ["E1", "E3"]
    }
  ],
  "sections": [
    {
      "name": "职业教育-产业学院",
      "items": [
        {
          "id": "E1",
          "headline": "完整事件标题",
          "short_title": "左侧短标题",
          "event_date": "2026-06-24",
          "subject": "事项主体",
          "event_type": "产业学院",
          "facts": ["事实一", "事实二", "事实三"],
          "analysis": "说明事件改变的行业变量、趋势和影响机制。",
          "beneficiaries": ["受益方及机制"],
          "risks": ["风险及失败条件"],
          "tracking": "下一期要验证的指标或节点。",
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
              "url": "https://example.com/source",
              "published_at": "2026-06-24",
              "source_type": "company",
              "is_primary": true
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
  "weekly_judgment": "100-200字行业判断。"
}
```

`evidence_table` 可选，只在名单、交易条款、数据对比或政策清单比文字更清楚时使用。

## 页面映射

- `core_insights` 生成本期核心观点页。
- 每个 `item` 生成 1 个事件页。
- `facts` 进入事实区，`analysis` 进入行业判断框，`tracking` 进入后续跟踪框。
- `sources` 在页脚显示来源名和日期，完整 URL 进入独立来源清单。
- `weekly_judgment` 生成结尾页。
