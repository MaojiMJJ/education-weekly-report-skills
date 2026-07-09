# 教育行业双周报 Skill 仓库

本仓库用于镜像两个本地 Codex Skill，目标是生成符合既有样例和 Word 要求的教育行业双周报。

## Skill 清单

- `skills/vocational-education-weekly-report`
  - 生成《职教行业周报》
  - 覆盖职业教育政策、职业院校动态、校企合作产业学院、职教上市公司事项、职教非上市企业事项。

- `skills/education-industry-observation`
  - 生成《教育行业观察》
  - 覆盖职业教育以外的教育行业，包括 K12 学校、K12 培训、教育信息化、高等教育、国际教育、素质教育、AI+教育、上市公司事项、融资交易和政策。

## 当前诊断背景

第一次公开来源版报告没有达到要求，主要问题不是 PPTX 生成脚本，而是 Skill 和执行流程的约束不够硬：

- 没有强制逐个跑完指定信息源。
- 没有设置最低事项数量和不足时的停止规则。
- 没有区分“邮箱材料可用”和“只能用公开来源”两种流程。
- 没有把检索底稿、候选池、剔除理由作为生成前质量门槛。
- PPT 生成前没有要求先确认事项池质量。

后续改动应先修复 Skill 的检索、筛选和质量门槛，再优化 PPT 样式。

## 本地路径

- GitHub 镜像：`D:\0GitHub\education-weekly-report-skills`
- 本地运行时 Skill：
  - `C:\Users\maoji\.codex\skills\vocational-education-weekly-report`
  - `C:\Users\maoji\.codex\skills\education-industry-observation`

修改本仓库后，需要同步回本地运行时目录，并重新运行 `quick_validate.py`。
