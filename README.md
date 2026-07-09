# Education Weekly Report Skills

This repository mirrors two local Codex skills for producing China education-sector biweekly reports.

## Skills

- `skills/vocational-education-weekly-report`
  - Intended output: `职教行业周报`
  - Scope: vocational education policy, vocational colleges, school-enterprise industrial colleges, listed-company vocational-education events, and non-listed vocational-education company events.

- `skills/education-industry-observation`
  - Intended output: `教育行业观察`
  - Scope: non-vocational education, including K12 schools, K12 training, education informatization, higher education, international education, quality education, listed-company events, AI + education financing/events, and policy.

## Current Diagnostic Context

The first generated public-source report did not meet the user's quality bar. The current hypothesis is that the skills are under-specified or too weak in these areas:

- source discovery strategy and search depth
- reliable public-source retrieval for Chinese education industry media
- handling cases where user prohibits using mailbox material
- minimum item count and item selection criteria
- report-style fidelity versus the downloaded sample PDFs
- quality gate before PPTX generation

This repository is the baseline for debugging and improving the two skills step by step.

## Local Runtime Paths

The live local Codex skills were installed at:

- `C:\Users\maoji\.codex\skills\vocational-education-weekly-report`
- `C:\Users\maoji\.codex\skills\education-industry-observation`

When this repository changes, sync the relevant skill directories back to the local runtime before relying on them in Codex.
