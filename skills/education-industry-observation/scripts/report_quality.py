#!/usr/bin/env python3
"""校验教育行业研究周报的结构、价值和来源质量。"""

from __future__ import annotations

import math
import re
from collections import Counter
from urllib.parse import urlsplit, urlunsplit


SCORE_FIELDS = (
    "industry_impact",
    "policy_importance",
    "commercial_value",
    "technology_relevance",
    "investment_relevance",
)

PRIMARY_REQUIRED_TYPES = {
    "政策",
    "监管",
    "收购",
    "再融资",
    "非公开发行",
    "上市公司事项",
    "院校设置",
}

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ReportQualityError(ValueError):
    """报告没有达到正式出刊门槛。"""

    def __init__(self, issues):
        self.issues = list(issues)
        super().__init__("报告质量校验失败：\n- " + "\n- ".join(self.issues))


def _is_text(value, minimum=1):
    return isinstance(value, str) and len(value.strip()) >= minimum


def _normalise_url(url):
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def _valid_url(url):
    if not _is_text(url):
        return False
    parts = urlsplit(url.strip())
    return parts.scheme in {"http", "https"} and bool(parts.netloc)


def iter_events(report):
    for section in report.get("sections") or []:
        section_name = section.get("name", "") if isinstance(section, dict) else ""
        items = section.get("items") or [] if isinstance(section, dict) else []
        for item in items:
            yield section_name, item


def _validate_list(issues, item_id, field, value, minimum, maximum=None):
    if not isinstance(value, list) or len(value) < minimum:
        issues.append(f"事项 {item_id} 的 {field} 至少需要 {minimum} 项")
        return
    if maximum is not None and len(value) > maximum:
        issues.append(f"事项 {item_id} 的 {field} 最多允许 {maximum} 项")
    for index, entry in enumerate(value, 1):
        if not _is_text(entry):
            issues.append(f"事项 {item_id} 的 {field}[{index}] 不能为空")


def validate_report(report):
    """校验报告并返回可供生成器使用的质量摘要。"""

    issues = []
    if not isinstance(report, dict):
        raise ReportQualityError(["报告根节点必须是对象"])

    for field in ("title", "period"):
        if not _is_text(report.get(field)):
            issues.append(f"报告必须包含 {field}")

    sections = report.get("sections")
    if not isinstance(sections, list) or not sections:
        issues.append("报告必须包含非空 sections")
        sections = []

    events = list(iter_events(report))
    if len(events) < 5:
        issues.append("正式出刊至少需要 5 个高价值正文事项，不能用低价值信息凑数")

    ids = []
    source_documents = {}
    score_totals = []
    section_counts = Counter()

    for event_number, (section_name, item) in enumerate(events, 1):
        if not isinstance(item, dict):
            issues.append(f"第 {event_number} 个事项必须是对象")
            continue

        item_id = item.get("id") or f"第{event_number}项"
        ids.append(item.get("id"))
        section_counts[section_name] += 1

        if "检索结论" in section_name or "未检索到" in str(item.get("headline", "")):
            issues.append(f"事项 {item_id} 属于检索结论，只能进入底稿，不能进入 PPT 正文")

        for field in ("id", "headline", "short_title", "event_date", "subject", "event_type"):
            if not _is_text(item.get(field)):
                issues.append(f"事项 {item_id} 必须包含 {field}")

        event_date = item.get("event_date")
        if _is_text(event_date) and not DATE_PATTERN.fullmatch(event_date.strip()):
            issues.append(f"事项 {item_id} 的 event_date 必须使用 YYYY-MM-DD")

        _validate_list(issues, item_id, "facts", item.get("facts"), 3, 5)
        if not _is_text(item.get("analysis"), 20):
            issues.append(f"事项 {item_id} 必须包含不少于 20 字的 analysis")
        _validate_list(issues, item_id, "beneficiaries", item.get("beneficiaries"), 1, 3)
        _validate_list(issues, item_id, "risks", item.get("risks"), 1, 3)
        if not _is_text(item.get("tracking"), 10):
            issues.append(f"事项 {item_id} 必须包含不少于 10 字的 tracking")

        scores = item.get("scores")
        score_reasons = item.get("score_reasons")
        score_values = []
        if not isinstance(scores, dict):
            issues.append(f"事项 {item_id} 必须包含 scores")
        else:
            for field in SCORE_FIELDS:
                value = scores.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
                    issues.append(f"事项 {item_id} 的 scores.{field} 必须是 1-5 的整数")
                else:
                    score_values.append(value)

        if not isinstance(score_reasons, dict):
            issues.append(f"事项 {item_id} 必须包含 score_reasons")
        else:
            for field in SCORE_FIELDS:
                if not _is_text(score_reasons.get(field), 5):
                    issues.append(f"事项 {item_id} 必须说明 score_reasons.{field}")

        if len(score_values) == len(SCORE_FIELDS):
            total = sum(score_values)
            score_totals.append(total)
            high_impact_exception = scores["industry_impact"] >= 4 and any(
                scores[field] >= 4 for field in SCORE_FIELDS[1:]
            )
            if total < 16 and not high_impact_exception:
                issues.append(f"事项 {item_id} 总分 {total}，未达到入选阈值")

        sources = item.get("sources")
        if not isinstance(sources, list) or not sources:
            issues.append(f"事项 {item_id} 必须包含 sources")
            sources = []

        has_primary = False
        for source_number, source in enumerate(sources, 1):
            if not isinstance(source, dict):
                issues.append(f"事项 {item_id} 的 sources[{source_number}] 必须是对象")
                continue
            for field in ("name", "url", "published_at", "source_type"):
                if not _is_text(source.get(field)):
                    issues.append(f"事项 {item_id} 的来源必须包含 {field}")
            url = source.get("url", "")
            if _is_text(url) and not _valid_url(url):
                issues.append(f"事项 {item_id} 的来源 URL 必须是可访问格式的 http/https 地址")
            published_at = source.get("published_at", "")
            if _is_text(published_at) and not DATE_PATTERN.fullmatch(published_at.strip()):
                issues.append(f"事项 {item_id} 的来源日期必须使用 YYYY-MM-DD")
            if not isinstance(source.get("is_primary"), bool):
                issues.append(f"事项 {item_id} 的来源必须声明 is_primary")
            elif source["is_primary"]:
                has_primary = True

            if _valid_url(url):
                document_key = _normalise_url(url)
                previous = source_documents.get(document_key)
                if previous and previous != item_id:
                    issues.append(f"事项 {item_id} 与事项 {previous} 使用同一来源文件，必须合并或说明独立新增事实")
                else:
                    source_documents[document_key] = item_id

        if item.get("event_type") in PRIMARY_REQUIRED_TYPES and sources and not has_primary:
            issues.append(f"事项 {item_id} 属于重大事项，至少需要 1 个一手来源")

    clean_ids = [item_id for item_id in ids if _is_text(item_id)]
    if len(clean_ids) != len(set(clean_ids)):
        issues.append("事项 id 必须唯一")

    if events:
        maximum_per_section = math.floor(len(events) / 2)
        for section_name, count in section_counts.items():
            if count > maximum_per_section:
                issues.append(f"栏目 {section_name} 占 {count}/{len(events)}，超过正文事项的一半")

    insights = report.get("core_insights")
    if not isinstance(insights, list) or not 1 <= len(insights) <= 3:
        issues.append("报告必须包含 1-3 条 core_insights")
        insights = []
    known_ids = set(clean_ids)
    for index, insight in enumerate(insights, 1):
        if not isinstance(insight, dict):
            issues.append(f"core_insights[{index}] 必须是对象")
            continue
        if not _is_text(insight.get("claim"), 12):
            issues.append(f"core_insights[{index}] 必须包含明确 claim")
        evidence_ids = insight.get("evidence_ids")
        if not isinstance(evidence_ids, list) or len(set(evidence_ids)) < 2:
            issues.append(f"core_insights[{index}] 至少需要 2 个 evidence_ids")
        else:
            unknown = set(evidence_ids) - known_ids
            if unknown:
                issues.append(f"core_insights[{index}] 引用了不存在的事项：{', '.join(sorted(unknown))}")

    weekly_judgment = report.get("weekly_judgment")
    if not _is_text(weekly_judgment, 100):
        issues.append("报告必须包含 100-200 字的 weekly_judgment")
    elif len(weekly_judgment.strip()) > 200:
        issues.append("weekly_judgment 不得超过 200 字")

    if issues:
        raise ReportQualityError(issues)

    return {
        "event_count": len(events),
        "minimum_score": min(score_totals),
        "maximum_score": max(score_totals),
        "insight_count": len(insights),
    }


def _escape_table(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_sources_markdown(report):
    """按事项生成可独立交付的 Markdown 来源清单。"""

    lines = [
        f"# {report.get('title', '报告')}来源清单",
        "",
        f"报告期：{report.get('period', '')}",
        "",
        "| 事项ID | 事项 | 来源 | 日期 | 类型 | 一手来源 | URL |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _section_name, item in iter_events(report):
        for source in item.get("sources") or []:
            lines.append(
                "| {id} | {headline} | {name} | {date} | {kind} | {primary} | {url} |".format(
                    id=_escape_table(item.get("id", "")),
                    headline=_escape_table(item.get("headline", "")),
                    name=_escape_table(source.get("name", "")),
                    date=_escape_table(source.get("published_at", "")),
                    kind=_escape_table(source.get("source_type", "")),
                    primary="是" if source.get("is_primary") else "否",
                    url=_escape_table(source.get("url", "")),
                )
            )
    return "\n".join(lines) + "\n"
