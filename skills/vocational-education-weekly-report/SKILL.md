---
name: vocational-education-weekly-report
description: Generate China vocational education industry weekly reports as PPT-style decks or slide-ready outlines. Use when the user asks for 职业教育行业周报, 职教行业周报, vocational-education weekly scans, vocational college policy/company/financing updates, school-enterprise industrial college updates, or a two-week vocational education industry report based on current sources and prior sample PDFs.
---

# Vocational Education Weekly Report

## Core Contract

Produce a biweekly vocational education industry report in PPT form: one cover slide plus one event per content slide. Each content slide must have a clear title and concise body bullets. Use the sample PDFs only as style and structure references; use current source verification for new reports.

Before drafting, read:

- `references/report-requirements.md` for scope, item taxonomy, and required fields.
- `references/source-workflow.md` for source hierarchy, search procedure, and verification gates.
- `references/listed-companies.md` when screening listed-company events.
- `references/sample-patterns.md` for observed slide structure from the downloaded PDFs.

## Workflow

1. Confirm or infer the report period. Default to the latest completed two-week window if the user does not specify dates.
2. Collect candidate events from the source workflow. Search both broad vocational education terms and specific listed-company / policy / college terms.
3. Classify every candidate into one of: policy, vocational college, school-enterprise industrial college, listed company, unlisted company / financing, or other vocational education.
4. Keep only material events with enough facts to explain what happened, who is involved, and why it matters.
5. Enrich each kept item with the required fields in `report-requirements.md`; if a material field is not disclosed, say it is not disclosed in working notes rather than inventing it.
6. Draft slides in the sample order: cover, policy cluster, college / industrial college cluster, company / financing cluster, other cluster when needed.
7. Generate a PPTX if the user asks for a deliverable. Use `scripts/build_weekly_pptx.py` with a JSON spec, then inspect the output manually or with the Presentations workflow if available.
8. Keep a source log with title, URL, publisher, publish date, accessed date, and why the source supports the slide.

## Output Rules

- Do not include non-vocational education items unless they directly affect vocational education.
- Prefer official policy, school, company, stock-exchange, and CNInfo announcements over secondary summaries.
- For company transactions, separate facts from interpretation. Do not treat media speculation as confirmed.
- Keep slide body concise: usually 3-5 bullets, each bullet one fact or one implication.
- Use Chinese report prose unless the user asks otherwise.
- If producing only a text draft, format it as slide-ready content: `Slide N / 分类 / 标题 / 正文要点 / 来源`.

## PPTX Helper

Use the bundled script after preparing a JSON file:

```bash
python scripts/build_weekly_pptx.py input.json --output 职教行业周报.pptx
```

JSON shape:

```json
{
  "title": "职教行业周报",
  "period": "2026.06.15-2026.06.28",
  "sections": [
    {
      "name": "职业教育-政策",
      "items": [
        {
          "headline": "教育发展十五五规划提出加快职业教育新双高建设",
          "bullets": ["国务院印发相关规划。", "文件提出布局市域产教联合体和行业产教融合共同体。"],
          "source": "国务院 / 教育部",
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
- Every kept event belongs to the vocational education scope.
- Listed-company items were checked against the listed-company reference.
- Policy items identify the issuing authority and effective / implementation point when disclosed.
- School-enterprise cooperation items identify both sides and the cooperation content.
- Sources are current, reachable, and recorded.
