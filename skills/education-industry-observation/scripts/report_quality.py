#!/usr/bin/env python3
"""Validate the fixed 8-page education-industry biweekly report contract."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


TEMPLATE_ID = "colleague-biweekly-v1"
ANCHOR_START = date(2026, 7, 6)
SECTION_SLOTS = (
    ("行业速览-上市公司", ("listed_1", "listed_2", "listed_3")),
    ("行业速览-其他", ("other_1", "other_2", "other_3")),
    ("行业速览-政策", ("policy_1", "policy_2", "policy_3", "policy_4", "policy_5")),
)
QUALITY_DIMENSIONS = (
    "information_quality",
    "template_fidelity",
    "readability",
    "strategic_value",
)
QUALITY_LABELS = {
    "information_quality": "信息质量",
    "template_fidelity": "模板一致性",
    "readability": "可读性",
    "strategic_value": "战略价值",
}
TRIGGER_TYPES = {
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
VISIBLE_FORBIDDEN = (
    "检索结论",
    "未检索到",
    "搜索情况",
    "来源不足",
    "缺口说明",
    "候选池",
    "工作底稿",
    "本期主要动态",
    "行业判断",
    "受益：",
    "风险：",
    "本期行业小结",
    "本期核心观点",
    "后续跟踪",
    "下一期",
    "验证重点",
)
RETROSPECTIVE_MARKERS = ("盘点", "回顾", "汇总", "历史梳理")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PERIOD_PATTERN = re.compile(
    r"^(\d{4})[.-](\d{2})[.-](\d{2})\s*-\s*(\d{4})[.-](\d{2})[.-](\d{2})$"
)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LAYOUT = SCRIPT_DIR.parent / "assets" / "colleague-template" / "layout.json"


class ReportQualityError(ValueError):
    """Raised when a report cannot be published in the fixed template."""

    def __init__(self, issues):
        self.issues = list(issues)
        super().__init__("报告质量校验失败：\n- " + "\n- ".join(self.issues))


def _is_text(value, minimum=1):
    return isinstance(value, str) and len(value.strip()) >= minimum


def _check_text(issues, label, value, minimum=1, maximum=None):
    if not _is_text(value, minimum):
        issues.append(f"{label} 至少需要 {minimum} 字")
        return
    if maximum is not None and len(value.strip()) > maximum:
        issues.append(f"{label} 不得超过 {maximum} 字")


def _parse_iso_date(value):
    if not _is_text(value) or not DATE_PATTERN.fullmatch(value.strip()):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _parse_period(value):
    if not _is_text(value):
        return None
    match = PERIOD_PATTERN.fullmatch(value.strip())
    if not match:
        return None
    values = [int(part) for part in match.groups()]
    try:
        start = date(values[0], values[1], values[2])
        end = date(values[3], values[4], values[5])
    except ValueError:
        return None
    return (start, end) if start <= end else None


def _valid_url(url):
    if not _is_text(url):
        return False
    parts = urlsplit(url.strip())
    hostname = (parts.hostname or "").lower().rstrip(".")
    if parts.scheme not in {"http", "https"} or not hostname:
        return False
    return not (
        hostname in {"localhost", "example.com"}
        or hostname.endswith((".localhost", ".invalid", ".test", ".example", ".example.com"))
    )


def _normalise_url(url):
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def _iter_text(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for entry in value.values():
            yield from _iter_text(entry)
    elif isinstance(value, (list, tuple)):
        for entry in value:
            yield from _iter_text(entry)


def _check_visible_markers(issues, label, value):
    text = " ".join(_iter_text(value))
    for marker in VISIBLE_FORBIDDEN:
        if marker in text:
            issues.append(f"{label}包含模板外或内部措辞“{marker}”")
            break


def _date_in_description(event_date, description):
    if not event_date or not _is_text(description):
        return False
    forms = (
        event_date.isoformat(),
        f"{event_date.year}年{event_date.month}月{event_date.day}日",
        f"{event_date.month}月{event_date.day}日",
    )
    return any(form in description for form in forms)


def load_layout(path=DEFAULT_LAYOUT):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def iter_items(report):
    for section in report.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for item in section.get("items") or []:
            yield section.get("name", ""), item


def _validate_source(
    issues,
    item_id,
    source,
    source_number,
    period,
    source_documents,
):
    label = f"事项 {item_id} 的 sources[{source_number}]"
    if not isinstance(source, dict):
        issues.append(f"{label} 必须是对象")
        return None
    _check_text(issues, f"{label}.name", source.get("name"), 2, 60)
    _check_text(issues, f"{label}.source_type", source.get("source_type"), 2, 30)
    url = source.get("url", "")
    if not _valid_url(url):
        issues.append(f"{label}.url 必须是有效的 http/https 地址")
    published_at = _parse_iso_date(source.get("published_at"))
    if not published_at:
        issues.append(f"{label}.published_at 必须是 YYYY-MM-DD")
    checked_at = _parse_iso_date(source.get("access_checked_at"))
    if not checked_at:
        issues.append(f"{label}.access_checked_at 必须是 YYYY-MM-DD")
    elif published_at and checked_at < published_at:
        issues.append(f"{label} 的核验日期不得早于发布日期")
    elif checked_at > date.today():
        issues.append(f"{label} 的核验日期不得晚于当前日期")
    if source.get("access_status") != "verified":
        issues.append(f"{label}.access_status 必须是 verified")
    if not isinstance(source.get("is_primary"), bool):
        issues.append(f"{label}.is_primary 必须是布尔值")
    if _valid_url(url):
        key = _normalise_url(url)
        previous = source_documents.get(key)
        if previous and previous != item_id:
            issues.append(f"事项 {item_id} 与事项 {previous} 使用同一来源文件")
        else:
            source_documents[key] = item_id
    within_period = bool(
        published_at and period and period[0] <= published_at <= period[1]
    )
    return {
        "url": url,
        "verified_primary": bool(
            source.get("access_status") == "verified" and source.get("is_primary")
        ),
        "within_period": within_period,
    }


def validate_report(report, layout=None):
    """Validate a report and return a fixed-template quality summary."""

    issues = []
    if not isinstance(report, dict):
        raise ReportQualityError(["报告根节点必须是对象"])
    layout = layout or load_layout()

    if report.get("template_id") != TEMPLATE_ID:
        issues.append(f"template_id 必须是 {TEMPLATE_ID}")
    if "coverage_mode" in report:
        issues.append("固定模板不允许 coverage_mode；旧的 broad_and_deep/deep_only 模式已停用")
    if "weekly_judgment" in report:
        issues.append("固定模板不包含 weekly_judgment 或本期行业小结")
    if report.get("title") != "教育行业观察":
        issues.append("title 必须是“教育行业观察”")

    period = _parse_period(report.get("period"))
    if not period:
        issues.append("period 必须使用 YYYY.MM.DD-YYYY.MM.DD")
    else:
        start, end = period
        if (end - start).days != 13:
            issues.append("报告期必须恰好包含连续 14 天")
        if start.weekday() != 0 or end.weekday() != 6:
            issues.append("报告期必须从周一开始、到周日结束")
        if (start - ANCHOR_START).days % 14 != 0:
            issues.append("报告期必须与 2026-07-06 起始的双周节奏对齐")

    sections = report.get("sections")
    if not isinstance(sections, list):
        issues.append("sections 必须是列表")
        sections = []
    expected_names = [name for name, _slots in SECTION_SLOTS]
    actual_names = [section.get("name") for section in sections if isinstance(section, dict)]
    if actual_names != expected_names:
        issues.append(f"栏目名称和顺序必须是：{'、'.join(expected_names)}")
    if len(sections) != len(SECTION_SLOTS):
        issues.append("固定模板必须包含 3 个栏目")

    ids = []
    slot_ids = []
    source_documents = {}
    item_by_id = {}
    for section_index, (expected_section, expected_slots) in enumerate(SECTION_SLOTS):
        section = sections[section_index] if section_index < len(sections) else {}
        if not isinstance(section, dict):
            issues.append(f"第 {section_index + 1} 个栏目必须是对象")
            continue
        items = section.get("items")
        if not isinstance(items, list):
            issues.append(f"栏目 {expected_section} 的 items 必须是列表")
            items = []
        if len(items) != len(expected_slots):
            issues.append(f"栏目 {expected_section} 必须包含 {len(expected_slots)} 项")

        for item_index, expected_slot in enumerate(expected_slots):
            if item_index >= len(items):
                continue
            item = items[item_index]
            if not isinstance(item, dict):
                issues.append(f"栏目 {expected_section} 第 {item_index + 1} 项必须是对象")
                continue
            item_id = item.get("id") or f"{expected_section}第{item_index + 1}项"
            ids.append(item.get("id"))
            slot_ids.append(item.get("slot_id"))
            item_by_id[item.get("id")] = item

            if item.get("slot_id") != expected_slot:
                issues.append(f"事项 {item_id} 的 slot_id 必须是 {expected_slot}")
            slot = (layout.get("slots") or {}).get(expected_slot)
            if not isinstance(slot, dict):
                issues.append(f"模板缺少槽位 {expected_slot}")
                continue
            if slot.get("section") != expected_section:
                issues.append(f"模板槽位 {expected_slot} 的栏目配置错误")

            _check_text(issues, f"事项 {item_id} 的 id", item.get("id"), 1, 20)
            _check_text(issues, f"事项 {item_id} 的 headline", item.get("headline"), 8, 70)
            _check_text(issues, f"事项 {item_id} 的 short_title", item.get("short_title"), 2, 24)
            _check_text(issues, f"事项 {item_id} 的 subject", item.get("subject"), 2, 80)
            _check_text(issues, f"事项 {item_id} 的 event_type", item.get("event_type"), 2, 30)
            _check_text(issues, f"事项 {item_id} 的 analysis", item.get("analysis"), 20, 160)
            _check_text(issues, f"事项 {item_id} 的 tracking", item.get("tracking"), 10, 100)
            _check_visible_markers(
                issues,
                f"事项 {item_id} 的公开字段",
                {
                    "headline": item.get("headline"),
                    "short_title": item.get("short_title"),
                    "bullets": item.get("bullets"),
                },
            )

            event_date = _parse_iso_date(item.get("event_date"))
            if not event_date:
                issues.append(f"事项 {item_id} 的 event_date 必须是 YYYY-MM-DD")
            elif period and not period[0] <= event_date <= period[1]:
                issues.append(f"事项 {item_id} 的 event_date 不在报告期内")
            if item.get("date_scope") != "within_period":
                issues.append(f"事项 {item_id} 的 date_scope 必须是 within_period")

            bullets = item.get("bullets")
            minimum = int(slot["min_bullets"])
            maximum = int(slot["max_bullets"])
            if not isinstance(bullets, list) or not minimum <= len(bullets) <= maximum:
                issues.append(
                    f"事项 {item_id} 的 bullets 必须包含 {minimum}-{maximum} 项"
                )
                bullets = []
            for bullet_index, bullet in enumerate(bullets, 1):
                _check_text(
                    issues,
                    f"事项 {item_id} 的 bullets[{bullet_index}]",
                    bullet,
                    12,
                    260,
                )
            total_chars = sum(len(str(bullet).strip()) for bullet in bullets)
            if total_chars > int(slot["max_chars"]):
                issues.append(
                    f"事项 {item_id} 的 bullets 总长度 {total_chars} 字，超过槽位 "
                    f"{expected_slot} 的 {slot['max_chars']} 字上限"
                )

            trigger = item.get("period_trigger")
            if not isinstance(trigger, dict):
                issues.append(f"事项 {item_id} 必须包含 period_trigger")
                trigger = {}
            trigger_type = trigger.get("type")
            if trigger_type not in TRIGGER_TYPES:
                issues.append(f"事项 {item_id} 的 period_trigger.type 无效")
            description = trigger.get("description")
            _check_text(
                issues,
                f"事项 {item_id} 的 period_trigger.description",
                description,
                12,
                140,
            )
            if _is_text(description):
                if any(marker in description for marker in RETROSPECTIVE_MARKERS):
                    issues.append(f"事项 {item_id} 的本期触发不能是盘点或历史回顾")
                if event_date and not _date_in_description(event_date, description):
                    issues.append(f"事项 {item_id} 的本期触发必须写明 event_date")
            trigger_url = trigger.get("source_url", "")
            if not _valid_url(trigger_url):
                issues.append(f"事项 {item_id} 的 period_trigger.source_url 无效")

            sources = item.get("sources")
            if not isinstance(sources, list) or not 1 <= len(sources) <= 2:
                issues.append(f"事项 {item_id} 的 sources 必须包含 1-2 个来源")
                sources = []
            source_results = []
            for source_number, source in enumerate(sources, 1):
                result = _validate_source(
                    issues,
                    item_id,
                    source,
                    source_number,
                    period,
                    source_documents,
                )
                if result:
                    source_results.append(result)
            trigger_match = next(
                (
                    result
                    for result in source_results
                    if _valid_url(trigger_url)
                    and _normalise_url(result["url"]) == _normalise_url(trigger_url)
                ),
                None,
            )
            if not trigger_match or not trigger_match["verified_primary"]:
                issues.append(f"事项 {item_id} 的触发来源必须是 sources 中已核验的一手来源")
            if source_results and not any(result["verified_primary"] for result in source_results):
                issues.append(f"事项 {item_id} 至少需要 1 个已核验的一手来源")
            if (
                source_results
                and trigger_type != "policy_effective"
                and not any(result["within_period"] for result in source_results)
            ):
                issues.append(f"事项 {item_id} 至少需要 1 个发布日期在报告期内的直接来源")

    clean_ids = [value for value in ids if _is_text(value)]
    if len(clean_ids) != 11 or len(clean_ids) != len(set(clean_ids)):
        issues.append("固定模板必须包含 11 个唯一事项 id")
    expected_slot_ids = [slot for _name, slots in SECTION_SLOTS for slot in slots]
    if slot_ids != expected_slot_ids:
        issues.append("11 个 slot_id 必须完整并按模板顺序排列")

    insights = report.get("core_insights")
    if not isinstance(insights, list) or not 1 <= len(insights) <= 3:
        issues.append("报告必须包含 1-3 条 core_insights")
        insights = []
    known_ids = set(clean_ids)
    for index, insight in enumerate(insights, 1):
        if not isinstance(insight, dict):
            issues.append(f"core_insights[{index}] 必须是对象")
            continue
        _check_text(issues, f"core_insights[{index}].claim", insight.get("claim"), 12, 90)
        evidence_ids = insight.get("evidence_ids")
        if not isinstance(evidence_ids, list) or len(set(evidence_ids)) < 2:
            issues.append(f"core_insights[{index}] 至少需要 2 个 evidence_ids")
        else:
            unknown = set(evidence_ids) - known_ids
            if unknown:
                issues.append(
                    f"core_insights[{index}] 引用了不存在的事项：{', '.join(sorted(unknown))}"
                )

    review = report.get("quality_review")
    quality_scores = []
    if not isinstance(review, dict):
        issues.append("报告必须包含 quality_review")
    else:
        for dimension in QUALITY_DIMENSIONS:
            entry = review.get(dimension)
            if not isinstance(entry, dict):
                issues.append(f"quality_review.{dimension} 必须是对象")
                continue
            score = entry.get("score")
            if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 10:
                issues.append(f"quality_review.{dimension}.score 必须是 1-10 的整数")
            else:
                quality_scores.append(score)
                if score < 8:
                    issues.append(f"quality_review.{dimension} 低于 8 分")
            _check_text(
                issues,
                f"quality_review.{dimension}.reason",
                entry.get("reason"),
                10,
                140,
            )
    if len(quality_scores) == 4 and sum(quality_scores) < 32:
        issues.append("quality_review 总分低于 32 分")

    if issues:
        raise ReportQualityError(issues)
    section_counts = Counter(section_name for section_name, _item in iter_items(report))
    return {
        "template_id": TEMPLATE_ID,
        "page_count": 8,
        "item_count": 11,
        "section_counts": dict(section_counts),
        "quality_total": sum(quality_scores),
    }


def _escape_table(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_sources_markdown(report):
    lines = [
        "# 教育行业观察来源清单",
        "",
        f"报告期：{report.get('period', '')}",
        f"模板：{report.get('template_id', '')}",
        "",
        "| 槽位 | 事项ID | 事项 | 事件日期 | 来源 | 发布日期 | 一手来源 | 核验日期 | URL |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _section_name, item in iter_items(report):
        if not isinstance(item, dict):
            continue
        for source in item.get("sources") or []:
            lines.append(
                "| {slot} | {id} | {headline} | {event_date} | {name} | {published} | "
                "{primary} | {checked} | {url} |".format(
                    slot=_escape_table(item.get("slot_id", "")),
                    id=_escape_table(item.get("id", "")),
                    headline=_escape_table(item.get("headline", "")),
                    event_date=_escape_table(item.get("event_date", "")),
                    name=_escape_table(source.get("name", "")),
                    published=_escape_table(source.get("published_at", "")),
                    primary="是" if source.get("is_primary") else "否",
                    checked=_escape_table(source.get("access_checked_at", "")),
                    url=_escape_table(source.get("url", "")),
                )
            )
    return "\n".join(lines) + "\n"


def build_quality_markdown(report):
    review = report.get("quality_review") or {}
    total = sum((review.get(dimension) or {}).get("score", 0) for dimension in QUALITY_DIMENSIONS)
    lines = [
        "# 教育行业观察质量报告",
        "",
        f"报告期：{report.get('period', '')}",
        f"模板：{report.get('template_id', '')}",
        "页面：8 页；事项：11 项（上市公司 3、其他 3、政策 5）",
        f"总分：{total}/40",
        "",
        "| 维度 | 得分 | 复核理由 |",
        "| --- | ---: | --- |",
    ]
    for dimension in QUALITY_DIMENSIONS:
        entry = review.get(dimension) or {}
        lines.append(
            f"| {QUALITY_LABELS[dimension]} | {entry.get('score', '')}/10 | "
            f"{_escape_table(entry.get('reason', ''))} |"
        )
    lines.extend(
        [
            "",
            "结论：通过固定模板内容门槛；仍需完成 PowerPoint 原生 PDF 导出、模板一致性校验和逐页视觉复核。",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="校验固定同事版教育行业双周报 JSON")
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--sources-output", type=Path)
    parser.add_argument("--quality-output", type=Path)
    args = parser.parse_args()

    report = json.loads(args.input_json.read_text(encoding="utf-8"))
    summary = validate_report(report, load_layout(args.layout))
    if args.sources_output:
        args.sources_output.parent.mkdir(parents=True, exist_ok=True)
        args.sources_output.write_text(build_sources_markdown(report), encoding="utf-8")
    if args.quality_output:
        args.quality_output.parent.mkdir(parents=True, exist_ok=True)
        args.quality_output.write_text(build_quality_markdown(report), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
