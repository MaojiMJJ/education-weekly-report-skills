# 固定模板 JSON 契约

## 顶层结构

字段名使用英文，内容使用中文。`template_id` 只能是 `colleague-biweekly-v1`。

```json
{
  "title": "教育行业观察",
  "period": "2026.07.06-2026.07.19",
  "template_id": "colleague-biweekly-v1",
  "core_insights": [
    {"claim": "由至少两个事项支持的内部观点", "evidence_ids": ["L1", "P1"]}
  ],
  "sections": [
    {
      "name": "行业速览-上市公司",
      "items": [
        {
          "id": "L1",
          "slot_id": "listed_1",
          "headline": "完整事件标题",
          "short_title": "左侧短标题",
          "event_date": "2026-07-08",
          "date_scope": "within_period",
          "subject": "事项主体",
          "event_type": "上市公司业务",
          "period_trigger": {
            "type": "material_business_update",
            "description": "事项主体于2026年7月8日正式披露新增业务动作",
            "source_url": "https://example.gov.cn/direct-source"
          },
          "bullets": [
            "第一条写本期正式发生或披露的动作、时间和关键数字。",
            "第二条补充主体、产品、客户、条款、规模或实施细节。"
          ],
          "analysis": "内部使用的影响机制判断，不进入公开 PPT。",
          "tracking": "内部使用的可验证节点，不进入公开 PPT。",
          "sources": [
            {
              "name": "来源名称",
              "url": "https://example.gov.cn/direct-source",
              "published_at": "2026-07-08",
              "source_type": "company",
              "is_primary": true,
              "access_status": "verified",
              "access_checked_at": "2026-07-20"
            }
          ]
        }
      ]
    }
  ],
  "quality_review": {
    "information_quality": {"score": 8, "reason": "不少于10字的复核理由。"},
    "template_fidelity": {"score": 8, "reason": "不少于10字的复核理由。"},
    "readability": {"score": 8, "reason": "不少于10字的复核理由。"},
    "strategic_value": {"score": 8, "reason": "不少于10字的复核理由。"}
  }
}
```

示例域名只表示字段格式，正式报告必须替换为实际打开并核验的 URL。

## 固定栏目与槽位

`sections` 必须严格按下列顺序，`items` 必须严格按槽位顺序：

```text
行业速览-上市公司: listed_1, listed_2, listed_3
行业速览-其他:     other_1, other_2, other_3
行业速览-政策:     policy_1, policy_2, policy_3, policy_4, policy_5
```

页面映射：

| 槽位 | 页面 | 项目符号数量 | 总字数上限 |
| --- | ---: | ---: | ---: |
| `listed_1` | 2 | 2 | 240 |
| `listed_2` | 2 | 2 | 220 |
| `listed_3` | 3 | 3-4 | 650 |
| `other_1` | 4 | 2-3 | 420 |
| `other_2` | 5 | 3-4 | 560 |
| `other_3` | 6 | 3-4 | 760 |
| `policy_1` | 7 | 2 | 260 |
| `policy_2` | 7 | 1-2 | 210 |
| `policy_3` | 7 | 2 | 220 |
| `policy_4` | 8 | 2 | 330 |
| `policy_5` | 8 | 2-3 | 500 |

单条项目符号不超过 260 字；先压缩重复背景，再减少次要细节，不得缩小字号。

## 字段约束

- `period` 为与基准节奏对齐的 14 天，格式为 `YYYY.MM.DD-YYYY.MM.DD`。
- `date_scope` 只能是 `within_period`。基准稿旧事项不得以 `reference_carryover` 进入新一期。
- `period_trigger.type` 只允许 `policy_issued`、`policy_effective`、`financing_announced`、`transaction_signed`、`filing_published`、`product_launched`、`deployment_started`、`official_data_released`、`material_business_update`。
- `period_trigger.description` 写明 `event_date` 和具体动作；`source_url` 必须出现在已核验直接来源中。
- 每项 1-2 个直接来源；至少一个 `is_primary: true` 且 `access_status: verified`。
- `short_title` 为左侧竖向标签。汉字按字竖排，连续英文和数字保留为一个词组。
- `analysis` 和 `tracking` 只用于内部数据，不渲染到 PPT。
- `core_insights` 为 1-3 条，每条至少回指 2 个真实事项。

## 页面映射

1. 封面：固定照片与绿色色块，只替换 `title` 和 `period`。
2. 第 2-8 页：按 `assets/colleague-template/layout.json` 的槽位几何写入 `short_title` 和 `bullets`。
3. 不生成“本期主要动态”、事件深析页、本期行业小结、来源页或任何额外页面。
4. 来源清单与质量报告为独立文件，不进入 PPT。
