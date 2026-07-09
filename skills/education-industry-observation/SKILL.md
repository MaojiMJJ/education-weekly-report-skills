---
name: education-industry-observation
description: Generate China education industry observation reports as PPT-style decks or slide-ready outlines. Use when the user asks for 教育行业观察, 教育行业周报, education-industry biweekly observations, non-vocational China education company/policy/AI education scans, or a two-week education industry report based on current sources and prior sample PDFs.
---

# Education Industry Observation

## Core Contract

Produce a biweekly China education industry observation in PPT form: one cover slide plus one event per content slide. The scope is education outside vocational education, with special attention to AI + education, listed-company transactions/cooperation, non-listed financing, and policy.

Before drafting, read:

- `references/report-requirements.md` for scope, item taxonomy, required fields, and exclusions.
- `references/source-workflow.md` for source hierarchy, search procedure, and verification gates.
- `references/listed-companies.md` when screening listed-company events.
- `references/sample-patterns.md` for observed slide structure from the downloaded PDFs.

## Workflow

1. Confirm or infer the report period. Default to the latest completed two-week window if the user does not specify dates.
2. Collect candidate events from the source workflow. Search both broad education terms and specific AI education / listed-company / policy terms.
3. Exclude vocational education items unless the user explicitly asks to merge both reports.
4. Classify every candidate into one of: listed company, financing and transaction, policy, AI + education, or other non-vocational education.
5. Keep only material events with enough facts to explain what happened, who is involved, transaction or cooperation terms where disclosed, and why it matters.
6. Enrich each kept item with the required fields in `report-requirements.md`; if a material field is not disclosed, say it is not disclosed in working notes rather than inventing it.
7. Draft slides in the sample order: cover, listed company or financing / transaction cluster, other industry cluster, policy cluster.
8. Generate a PPTX if the user asks for a deliverable. Use `scripts/build_weekly_pptx.py` with a JSON spec, then inspect the output manually or with the Presentations workflow if available.
9. Keep a source log with title, URL, publisher, publish date, accessed date, and why the source supports the slide.

## Output Rules

- Use Chinese report prose unless the user asks otherwise.
- Do not include vocational education items in this report; route them to `vocational-education-weekly-report`.
- Prefer official policy, exchange, CNInfo, company announcement, investor-relations, and primary financing disclosure over secondary summaries.
- For transactions, separate disclosed facts from interpretation. Do not infer undisclosed valuation, revenue, profit, or commitment terms.
- Keep slide body concise: usually 3-5 bullets, each bullet one fact or one implication.
- If producing only a text draft, format it as slide-ready content: `Slide N / 分类 / 标题 / 正文要点 / 来源`.

## PPTX Helper

Use the bundled script after preparing a JSON file:

```bash
python scripts/build_weekly_pptx.py input.json --output 教育行业观察.pptx
```

JSON shape:

```json
{
  "title": "教育行业观察",
  "period": "2026.06.22-2026.07.05",
  "sections": [
    {
      "name": "行业速览-融资与交易",
      "items": [
        {
          "headline": "某 AI 教育公司完成新一轮融资",
          "bullets": [
            "公司披露完成新一轮融资，投资方和融资金额以公告为准。",
            "业务聚焦 AI 学习场景，面向 B 端学校或 C 端家庭提供产品。",
            "后续关注产品落地、用户规模、营收表现及与上市公司的协同可能。"
          ],
          "source": "公司公告 / 媒体披露",
          "source_url": "https://..."
        }
      ]
    }
  ]
}
```

## Quality Gate

Before final delivery, verify:

- The period is visible on the cover.
- Every content slide has exactly one main event.
- Every kept event belongs to non-vocational education scope.
- Listed-company items were checked against the listed-company reference and primary announcements where available.
- Acquisition, private placement, cooperation, and financing items include the required transaction fields when disclosed.
- AI + education items identify the scenario category and customer / product type.
- Policy items identify the issuing authority and AI education relevance when applicable.
- Sources are current, reachable, and recorded.
