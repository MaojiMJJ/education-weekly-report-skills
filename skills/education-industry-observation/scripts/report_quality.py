#!/usr/bin/env python3
"""校验教育行业研究周报的结构、价值、来源和页面容量。"""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import date
from urllib.parse import urlsplit, urlunsplit


SCORE_FIELDS = (
    "industry_impact",
    "policy_importance",
    "commercial_value",
    "technology_relevance",
    "investment_relevance",
)

QUALITY_DIMENSIONS = (
    "information_quality",
    "analysis_depth",
    "readability",
    "strategic_value",
)

QUALITY_LABELS = {
    "information_quality": "信息质量",
    "analysis_depth": "分析深度",
    "readability": "可读性",
    "strategic_value": "战略价值",
}

INTERNAL_MARKERS = (
    "检索结论",
    "未检索到",
    "搜索情况",
    "检索情况",
    "来源不足",
    "缺口说明",
    "候选池",
    "工作底稿",
)

PUBLIC_OUTPUT_MARKERS = (
    "本期核心观点",
    "证据事项",
    "后续跟踪",
    "下一期",
    "重点跟踪",
    "验证重点",
)

PERIOD_TRIGGER_TYPES = {
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

EVENT_TRIGGER_RULES = (
    (
        ("融资", "资本", "并购", "收购", "交易", "上市", "ipo"),
        {"financing_announced", "transaction_signed", "filing_published"},
    ),
    (
        ("政策", "监管"),
        {"policy_issued", "policy_effective", "official_data_released"},
    ),
    (
        ("采购", "中标", "部署", "试点"),
        {"deployment_started", "filing_published"},
    ),
    (
        ("产品", "ai教育", "人工智能", "技术"),
        {"product_launched", "deployment_started", "official_data_released"},
    ),
)

TRIGGER_ACTION_TERMS = {
    "policy_issued": ("发布", "印发", "出台", "通过"),
    "policy_effective": ("生效", "施行", "实施"),
    "financing_announced": ("融资", "完成", "获得", "获投"),
    "transaction_signed": ("签署", "签订", "签约", "并购", "收购", "完成交易", "公告"),
    "filing_published": ("公告", "递交", "受理", "挂牌", "上市", "披露"),
    "product_launched": ("发布", "上线", "推出"),
    "deployment_started": ("中标", "采购", "部署", "试点", "开通", "启动"),
    "official_data_released": ("发布", "披露", "公布"),
    "material_business_update": ("启动", "签约", "落地", "开工"),
}

RETROSPECTIVE_TRIGGER_MARKERS = ("盘点", "回顾", "汇总", "历史梳理")

FINANCING_TEXT_FIELDS = (
    "amount",
    "round",
    "currency",
    "business_positioning",
    "business_domain",
    "customer_side",
    "delivery_mode",
    "offering_type",
    "user_type",
    "founded_at",
    "users",
    "stores",
    "store_model",
    "gross_billing",
    "revenue",
    "profit",
)

FINANCING_LIST_FIELDS = (
    "investors",
    "fund_use",
    "prior_investors",
)

COOPERATION_TEXT_FIELDS = (
    "action_type",
    "cooperation_content",
    "business_or_school",
    "location",
    "implementation_plan",
    "commercialization",
)

COOPERATION_LIST_FIELDS = (
    "parties",
    "party_types",
)

POLICY_TEXT_FIELDS = (
    "issuing_body",
    "policy_name",
    "issued_at",
    "effective_at",
    "scope_level",
    "scope_description",
)

POLICY_LIST_FIELDS = (
    "prohibited_rules",
    "restrictive_requirements",
    "supportive_measures",
)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PERIOD_PATTERN = re.compile(
    r"^(\d{4})[.-](\d{2})[.-](\d{2})\s*-\s*(\d{4})[.-](\d{2})[.-](\d{2})$"
)


class ReportQualityError(ValueError):
    """报告没有达到正式出刊门槛。"""

    def __init__(self, issues):
        self.issues = list(issues)
        super().__init__("报告质量校验失败：\n- " + "\n- ".join(self.issues))


def _is_text(value, minimum=1):
    return isinstance(value, str) and len(value.strip()) >= minimum


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
    numbers = [int(part) for part in match.groups()]
    try:
        start = date(numbers[0], numbers[1], numbers[2])
        end = date(numbers[3], numbers[4], numbers[5])
    except ValueError:
        return None
    return (start, end) if start <= end else None


def _normalise_url(url):
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def _valid_url(url):
    if not _is_text(url):
        return False
    parts = urlsplit(url.strip())
    hostname = (parts.hostname or "").lower().rstrip(".")
    if parts.scheme not in {"http", "https"} or not hostname:
        return False
    if hostname in {"localhost", "example.com"} or hostname.endswith(
        (".localhost", ".invalid", ".test", ".example", ".example.com")
    ):
        return False
    return True


def _check_text(issues, label, value, minimum=1, maximum=None):
    if not _is_text(value, minimum):
        issues.append(f"{label} 至少需要 {minimum} 字")
        return
    if maximum is not None and len(value.strip()) > maximum:
        issues.append(f"{label} 不得超过 {maximum} 字")


def iter_items(report):
    for section in report.get("sections") or []:
        section_name = section.get("name", "") if isinstance(section, dict) else ""
        items = section.get("items") or [] if isinstance(section, dict) else []
        for item in items:
            yield section_name, item


def iter_events(report):
    for section_name, item in iter_items(report):
        if isinstance(item, dict) and item.get("content_role") == "event":
            yield section_name, item


def iter_briefs(report):
    for section_name, item in iter_items(report):
        if isinstance(item, dict) and item.get("content_role") == "brief":
            yield section_name, item


def _validate_list(issues, item_id, field, value, minimum, maximum=None, max_chars=None):
    if not isinstance(value, list) or len(value) < minimum:
        issues.append(f"事项 {item_id} 的 {field} 至少需要 {minimum} 项")
        return
    if maximum is not None and len(value) > maximum:
        issues.append(f"事项 {item_id} 的 {field} 最多允许 {maximum} 项")
    for index, entry in enumerate(value, 1):
        if not _is_text(entry):
            issues.append(f"事项 {item_id} 的 {field}[{index}] 不能为空")
        elif max_chars is not None and len(entry.strip()) > max_chars:
            issues.append(f"事项 {item_id} 的 {field}[{index}] 不得超过 {max_chars} 字")


def _validate_evidence_table(issues, item_id, evidence):
    if evidence is None:
        return
    if not isinstance(evidence, dict):
        issues.append(f"事项 {item_id} 的 evidence_table 必须是对象")
        return

    columns = evidence.get("columns")
    rows = evidence.get("rows")
    if not isinstance(columns, list) or not 2 <= len(columns) <= 4:
        issues.append(f"事项 {item_id} 的 evidence_table.columns 必须包含 2-4 列")
        return
    for index, column in enumerate(columns, 1):
        if not _is_text(column) or len(column.strip()) > 10:
            issues.append(f"事项 {item_id} 的 evidence_table.columns[{index}] 必须为 1-10 字文本")

    if not isinstance(rows, list) or not rows:
        issues.append(f"事项 {item_id} 的 evidence_table.rows 至少需要 1 行")
        return
    if len(rows) > 3:
        issues.append(f"事项 {item_id} 的 evidence_table.rows 最多允许 3 行")
    cell_limit = {2: 20, 3: 12, 4: 8}[len(columns)]
    for row_index, row in enumerate(rows, 1):
        if not isinstance(row, list) or len(row) != len(columns):
            issues.append(f"事项 {item_id} 的 evidence_table.rows[{row_index}] 列数必须与表头一致")
            continue
        for column_index, cell in enumerate(row, 1):
            if not isinstance(cell, (str, int, float)) or isinstance(cell, bool):
                issues.append(f"事项 {item_id} 的 evidence_table.rows[{row_index}][{column_index}] 类型不支持")
            elif len(str(cell)) > cell_limit:
                issues.append(
                    f"事项 {item_id} 的 evidence_table.rows[{row_index}][{column_index}] "
                    f"在 {len(columns)} 列表格中不得超过 {cell_limit} 字"
                )


def _iter_text_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for entry in value.values():
            yield from _iter_text_values(entry)
    elif isinstance(value, (list, tuple)):
        for entry in value:
            yield from _iter_text_values(entry)


def _check_internal_markers(issues, label, value):
    searchable_text = " ".join(_iter_text_values(value))
    for marker in INTERNAL_MARKERS:
        if marker in searchable_text:
            issues.append(f"{label}包含内部工作内容“{marker}”，不能进入正式交付")
            break


def _check_public_output_markers(issues, label, value):
    searchable_text = " ".join(_iter_text_values(value))
    for marker in PUBLIC_OUTPUT_MARKERS:
        if marker in searchable_text:
            issues.append(f"{label}包含投资部内部措辞“{marker}”，不能进入公开报告")
            break


def _validate_required_text_fields(issues, item_id, object_name, value, field_names):
    if not isinstance(value, dict):
        issues.append(f"事项 {item_id} 必须包含 {object_name}")
        return None
    for field in field_names:
        _check_text(
            issues,
            f"事项 {item_id} 的 {object_name}.{field}",
            value.get(field),
            2,
            120,
        )
    return value


def _validate_financing_details(issues, item_id, details):
    details = _validate_required_text_fields(
        issues,
        item_id,
        "financing_details",
        details,
        FINANCING_TEXT_FIELDS,
    )
    if details is None:
        return
    for field in FINANCING_LIST_FIELDS:
        _validate_list(
            issues,
            item_id,
            f"financing_details.{field}",
            details.get(field),
            1,
            5,
            45,
        )


def _validate_cooperation_details(issues, item_id, details):
    details = _validate_required_text_fields(
        issues,
        item_id,
        "cooperation_details",
        details,
        COOPERATION_TEXT_FIELDS,
    )
    if details is None:
        return
    for field in COOPERATION_LIST_FIELDS:
        _validate_list(
            issues,
            item_id,
            f"cooperation_details.{field}",
            details.get(field),
            1,
            5,
            45,
        )


def _validate_policy_details(issues, item_id, details):
    details = _validate_required_text_fields(
        issues,
        item_id,
        "policy_details",
        details,
        POLICY_TEXT_FIELDS,
    )
    if details is None:
        return

    if details.get("scope_level") not in {"全国性", "地方性"}:
        issues.append(f"事项 {item_id} 的 policy_details.scope_level 必须是全国性或地方性")

    clause_count = 0
    for field in POLICY_LIST_FIELDS:
        value = details.get(field)
        if not isinstance(value, list):
            issues.append(f"事项 {item_id} 的 policy_details.{field} 必须是列表")
            continue
        _validate_list(
            issues,
            item_id,
            f"policy_details.{field}",
            value,
            0,
            5,
            80,
        )
        clause_count += sum(1 for entry in value if _is_text(entry))
    if clause_count < 1:
        issues.append(f"事项 {item_id} 的政策核心条款至少需要 1 条")


def _allowed_trigger_types(event_type):
    normalized = str(event_type or "").strip().lower()
    for keywords, allowed in EVENT_TRIGGER_RULES:
        if any(keyword in normalized for keyword in keywords):
            return allowed
    return PERIOD_TRIGGER_TYPES


def _date_appears_in_text(value, text):
    if not value or not _is_text(text):
        return False
    forms = (
        value.isoformat(),
        f"{value.year}年{value.month}月{value.day}日",
        f"{value.month}月{value.day}日",
    )
    return any(form in text for form in forms)


def _validate_brief(
    issues,
    section_name,
    item,
    period,
    period_start,
    period_end,
    source_documents,
):
    """校验宽覆盖速览层，确保它不是无日期、无来源的新闻摘抄。"""

    item_id = item.get("id") or "未命名速览"
    _check_internal_markers(issues, f"速览 {item_id} ", [section_name, item])
    _check_public_output_markers(
        issues,
        f"速览 {item_id} 的公开字段",
        {
            "section": section_name,
            "headline": item.get("headline"),
            "facts": item.get("facts"),
            "why_it_matters": item.get("why_it_matters"),
        },
    )
    _check_text(issues, f"速览 {item_id} 的 id", item.get("id"), 1, 20)
    _check_text(issues, f"速览 {item_id} 的 headline", item.get("headline"), 8, 62)
    _check_text(issues, f"速览 {item_id} 的 short_title", item.get("short_title"), 4, 24)
    _check_text(issues, f"速览 {item_id} 的 subject", item.get("subject"), 2, 80)
    _check_text(issues, f"速览 {item_id} 的 event_type", item.get("event_type"), 2, 20)
    _validate_list(issues, item_id, "facts", item.get("facts"), 2, 3, 80)
    facts = item.get("facts")
    if isinstance(facts, list) and sum(len(str(value)) for value in facts) > 180:
        issues.append(f"速览 {item_id} 的 facts 总长度不得超过 180 字")
    _check_text(issues, f"速览 {item_id} 的 why_it_matters", item.get("why_it_matters"), 15, 90)

    event_date = _parse_iso_date(item.get("event_date"))
    if not event_date:
        issues.append(f"速览 {item_id} 的 event_date 必须使用有效的 YYYY-MM-DD")
    elif period and not period_start <= event_date <= period_end:
        issues.append(f"速览 {item_id} 的 event_date 不在报告期内")

    trigger = item.get("period_trigger")
    if not isinstance(trigger, dict):
        issues.append(f"速览 {item_id} 必须包含 period_trigger")
        trigger = {}
    trigger_type = trigger.get("type")
    if trigger_type not in PERIOD_TRIGGER_TYPES:
        issues.append(f"速览 {item_id} 的本期触发类型无效")
    elif trigger_type not in _allowed_trigger_types(item.get("event_type")):
        issues.append(f"速览 {item_id} 的本期触发类型与 event_type 不匹配")
    trigger_description = trigger.get("description")
    _check_text(issues, f"速览 {item_id} 的 period_trigger.description", trigger_description, 12, 120)
    if _is_text(trigger_description):
        if any(marker in trigger_description for marker in RETROSPECTIVE_TRIGGER_MARKERS):
            issues.append(f"速览 {item_id} 的本期触发说明不能是跨期盘点或历史回顾")
        if event_date and not _date_appears_in_text(event_date, trigger_description):
            issues.append(f"速览 {item_id} 的本期触发说明必须写明 event_date")
        if trigger_type in TRIGGER_ACTION_TERMS and not any(
            term in trigger_description for term in TRIGGER_ACTION_TERMS[trigger_type]
        ):
            issues.append(f"速览 {item_id} 的本期触发说明缺少具体新增动作")

    trigger_url = trigger.get("source_url", "")
    if not _valid_url(trigger_url):
        issues.append(f"速览 {item_id} 的触发来源 URL 无效")

    sources = item.get("sources")
    if not isinstance(sources, list) or not sources:
        issues.append(f"速览 {item_id} 必须包含 sources")
        sources = []
    elif len(sources) > 2:
        issues.append(f"速览 {item_id} 的 sources 最多保留 2 个直接来源")

    has_primary = False
    has_period_source = False
    matching_trigger_source = None
    for source_number, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            issues.append(f"速览 {item_id} 的 sources[{source_number}] 必须是对象")
            continue
        _check_text(issues, f"速览 {item_id} 的来源 name", source.get("name"), 2, 60)
        _check_text(issues, f"速览 {item_id} 的来源 source_type", source.get("source_type"), 2, 30)
        url = source.get("url", "")
        if not _valid_url(url):
            issues.append(f"速览 {item_id} 的来源 URL 必须是有效的 http/https 地址")
        published_at = _parse_iso_date(source.get("published_at"))
        if not published_at:
            issues.append(f"速览 {item_id} 的来源日期必须使用有效的 YYYY-MM-DD")
        elif period and period_start <= published_at <= period_end:
            has_period_source = True
        if source.get("access_status") != "verified":
            issues.append(f"速览 {item_id} 的来源 access_status 必须是 verified")
        checked_at = _parse_iso_date(source.get("access_checked_at"))
        if not checked_at:
            issues.append(f"速览 {item_id} 的来源 access_checked_at 必须使用有效的 YYYY-MM-DD")
        elif published_at and checked_at < published_at:
            issues.append(f"速览 {item_id} 的来源核验日期不得早于发布日期")
        elif checked_at > date.today():
            issues.append(f"速览 {item_id} 的来源核验日期不得晚于当前日期")
        if not isinstance(source.get("is_primary"), bool):
            issues.append(f"速览 {item_id} 的来源必须声明 is_primary")
        elif source["is_primary"]:
            has_primary = True
        if _valid_url(url):
            document_key = _normalise_url(url)
            previous = source_documents.get(document_key)
            if previous and previous != item_id:
                issues.append(f"速览 {item_id} 与事项 {previous} 使用同一来源文件，必须合并或更换独立来源")
            else:
                source_documents[document_key] = item_id
            if _valid_url(trigger_url) and document_key == _normalise_url(trigger_url):
                matching_trigger_source = source

    if not matching_trigger_source:
        issues.append(f"速览 {item_id} 的触发来源必须出现在 sources 中")
    elif (
        matching_trigger_source.get("access_status") != "verified"
        or not matching_trigger_source.get("is_primary")
    ):
        issues.append(f"速览 {item_id} 的触发来源必须是已核验的一手或原创直接来源")
    if sources and not has_period_source and trigger_type != "policy_effective":
        issues.append(f"速览 {item_id} 至少需要 1 个发布日期在报告期内的直接来源")
    if sources and not has_primary:
        issues.append(f"速览 {item_id} 至少需要 1 个一手来源或原创直接来源")


def validate_report(report):
    """校验报告并返回可供生成器使用的质量摘要。"""

    issues = []
    if not isinstance(report, dict):
        raise ReportQualityError(["报告根节点必须是对象"])

    _check_internal_markers(
        issues,
        "报告顶层可见字段",
        {
            "title": report.get("title"),
            "core_insights": report.get("core_insights"),
            "weekly_judgment": report.get("weekly_judgment"),
            "quality_review": report.get("quality_review"),
        },
    )
    _check_public_output_markers(
        issues,
        "报告顶层公开字段",
        {
            "title": report.get("title"),
            "weekly_judgment": report.get("weekly_judgment"),
            "quality_review": report.get("quality_review"),
        },
    )

    _check_text(issues, "title", report.get("title"), 2, 30)
    period = _parse_period(report.get("period"))
    if not period:
        issues.append("period 必须使用 YYYY.MM.DD-YYYY.MM.DD 且起止日期有效")
    period_start, period_end = period if period else (None, None)

    sections = report.get("sections")
    if not isinstance(sections, list) or not sections:
        issues.append("报告必须包含非空 sections")
        sections = []
    is_vocational_report = "职业教育" in str(report.get("title") or "") or any(
        isinstance(section, dict) and str(section.get("name") or "").startswith("职业教育-")
        for section in sections
    )

    all_items = list(iter_items(report))
    for section_name, item in all_items:
        if not isinstance(item, dict):
            issues.append(f"栏目 {section_name} 中的事项必须是对象")
            continue
        if item.get("content_role") not in {"event", "brief"}:
            item_id = item.get("id") or "未命名事项"
            issues.append(f"事项 {item_id} 的 content_role 必须是 event 或 brief")

    coverage_mode = report.get("coverage_mode", "deep_only")
    if coverage_mode not in {"deep_only", "broad_and_deep"}:
        issues.append("coverage_mode 必须是 deep_only 或 broad_and_deep")

    events = [
        (section_name, item)
        for section_name, item in all_items
        if isinstance(item, dict) and item.get("content_role") != "brief"
    ]
    briefs = list(iter_briefs(report))
    if len(events) < 5:
        issues.append("正式出刊至少需要 5 个高价值正文事项，不能用低价值信息凑数")
    if coverage_mode == "broad_and_deep":
        if len(briefs) < 5:
            issues.append("broad_and_deep 模式至少需要 5 个严格核验的速览事项")
        if len(events) + len(briefs) < 10:
            issues.append("broad_and_deep 模式的总覆盖事项不得少于 10 个")

    ids = []
    source_documents = {}
    score_totals = []
    section_counts = Counter()
    brief_section_counts = Counter()

    for event_number, (section_name, item) in enumerate(events, 1):
        if not isinstance(item, dict):
            issues.append(f"第 {event_number} 个事项必须是对象")
            continue

        item_id = item.get("id") or f"第{event_number}项"
        ids.append(item.get("id"))
        section_counts[section_name] += 1

        if item.get("content_role") != "event":
            issues.append(f"事项 {item_id} 的 content_role 必须是 event")
        _check_internal_markers(issues, f"事项 {item_id} ", [section_name, item])
        _check_public_output_markers(
            issues,
            f"事项 {item_id} 的公开字段",
            {
                "section": section_name,
                "headline": item.get("headline"),
                "short_title": item.get("short_title"),
                "background": item.get("background"),
                "facts": item.get("facts"),
                "analysis": item.get("analysis"),
                "beneficiaries": item.get("beneficiaries"),
                "risks": item.get("risks"),
                "financing_details": item.get("financing_details"),
                "cooperation_details": item.get("cooperation_details"),
                "policy_details": item.get("policy_details"),
            },
        )

        _check_text(issues, f"事项 {item_id} 的 id", item.get("id"), 1, 20)
        _check_text(issues, f"事项 {item_id} 的 headline", item.get("headline"), 8, 70)
        _check_text(issues, f"事项 {item_id} 的 short_title", item.get("short_title"), 4, 28)
        _check_text(issues, f"事项 {item_id} 的 subject", item.get("subject"), 2, 80)
        _check_text(issues, f"事项 {item_id} 的 event_type", item.get("event_type"), 2, 20)
        _check_text(issues, f"事项 {item_id} 的 background", item.get("background"), 20, 100)

        event_date = _parse_iso_date(item.get("event_date"))
        if not event_date:
            issues.append(f"事项 {item_id} 的 event_date 必须使用有效的 YYYY-MM-DD")
        elif period and not period_start <= event_date <= period_end:
            issues.append(f"事项 {item_id} 的 event_date 不在报告期内")

        trigger = item.get("period_trigger")
        if not isinstance(trigger, dict):
            issues.append(f"事项 {item_id} 必须包含 period_trigger")
            trigger = {}

        trigger_type = trigger.get("type")
        if trigger_type not in PERIOD_TRIGGER_TYPES:
            issues.append(f"事项 {item_id} 的本期触发类型无效")
        elif trigger_type not in _allowed_trigger_types(item.get("event_type")):
            issues.append(f"事项 {item_id} 的本期触发类型与 event_type 不匹配")

        trigger_description = trigger.get("description")
        _check_text(
            issues,
            f"事项 {item_id} 的 period_trigger.description",
            trigger_description,
            12,
            120,
        )
        if _is_text(trigger_description):
            if any(marker in trigger_description for marker in RETROSPECTIVE_TRIGGER_MARKERS):
                issues.append(f"事项 {item_id} 的本期触发说明不能是跨期盘点或历史回顾")
            if event_date and not _date_appears_in_text(event_date, trigger_description):
                issues.append(f"事项 {item_id} 的本期触发说明必须写明 event_date")
            if trigger_type in TRIGGER_ACTION_TERMS and not any(
                term in trigger_description for term in TRIGGER_ACTION_TERMS[trigger_type]
            ):
                issues.append(f"事项 {item_id} 的本期触发说明缺少具体新增动作")

        trigger_url = trigger.get("source_url", "")
        if not _valid_url(trigger_url):
            issues.append(f"事项 {item_id} 的触发来源 URL 无效")

        if not is_vocational_report:
            normalized_event_type = str(item.get("event_type") or "").strip().lower()
            if any(keyword in normalized_event_type for keyword in ("融资", "投融资")):
                _validate_financing_details(issues, item_id, item.get("financing_details"))
            if any(
                keyword in normalized_event_type
                for keyword in ("业务合作", "新业务", "学校筹备", "学校设立", "新学校", "合作")
            ):
                _validate_cooperation_details(issues, item_id, item.get("cooperation_details"))
            if (
                any(keyword in normalized_event_type for keyword in ("政策", "监管", "法规"))
                or trigger_type in {"policy_issued", "policy_effective"}
            ):
                _validate_policy_details(issues, item_id, item.get("policy_details"))

        facts = item.get("facts")
        _validate_list(issues, item_id, "facts", facts, 3, 5, 90)
        if isinstance(facts, list) and sum(len(str(value)) for value in facts) > 240:
            issues.append(f"事项 {item_id} 的 facts 总长度不得超过 240 字")
        _check_text(issues, f"事项 {item_id} 的 analysis", item.get("analysis"), 20, 120)
        beneficiaries = item.get("beneficiaries")
        risks = item.get("risks")
        _validate_list(issues, item_id, "beneficiaries", beneficiaries, 1, 3, 45)
        _validate_list(issues, item_id, "risks", risks, 1, 3, 45)
        if isinstance(beneficiaries, list) and isinstance(risks, list):
            impact_length = sum(len(str(value)) for value in beneficiaries + risks)
            if impact_length > 90:
                issues.append(f"事项 {item_id} 的受益方和风险合计不得超过 90 字")
        _check_text(issues, f"事项 {item_id} 的 tracking", item.get("tracking"), 10, 70)

        scores = item.get("scores")
        score_reasons = item.get("score_reasons")
        score_values = []
        if not isinstance(scores, dict):
            issues.append(f"事项 {item_id} 必须包含 scores")
        else:
            unexpected = set(scores) - set(SCORE_FIELDS)
            missing = set(SCORE_FIELDS) - set(scores)
            if unexpected:
                issues.append(f"事项 {item_id} 的 scores 包含额外字段：{', '.join(sorted(unexpected))}")
            if missing:
                issues.append(f"事项 {item_id} 的 scores 缺少字段：{', '.join(sorted(missing))}")
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
                _check_text(issues, f"事项 {item_id} 的 score_reasons.{field}", score_reasons.get(field), 5, 80)

        if len(score_values) == len(SCORE_FIELDS):
            total = sum(score_values)
            score_totals.append(total)
            high_impact_exception = scores["industry_impact"] >= 4 and any(
                scores[field] >= 4 for field in SCORE_FIELDS[1:]
            )
            if total < 16 and not high_impact_exception:
                issues.append(f"事项 {item_id} 总分 {total}，未达到入选阈值")

        _validate_evidence_table(issues, item_id, item.get("evidence_table"))

        sources = item.get("sources")
        if not isinstance(sources, list) or not sources:
            issues.append(f"事项 {item_id} 必须包含 sources")
            sources = []
        elif len(sources) > 3:
            issues.append(f"事项 {item_id} 的 sources 最多保留 3 个直接来源")

        has_primary = False
        has_period_source = False
        footer_length = 0
        for source_number, source in enumerate(sources, 1):
            if not isinstance(source, dict):
                issues.append(f"事项 {item_id} 的 sources[{source_number}] 必须是对象")
                continue

            _check_text(issues, f"事项 {item_id} 的来源 name", source.get("name"), 2, 60)
            _check_text(issues, f"事项 {item_id} 的来源 source_type", source.get("source_type"), 2, 30)
            footer_length += len(str(source.get("name", ""))) + len(str(source.get("published_at", "")))

            url = source.get("url", "")
            if not _valid_url(url):
                issues.append(f"事项 {item_id} 的来源 URL 必须是有效的 http/https 地址")
            elif len(url) > 500:
                issues.append(f"事项 {item_id} 的来源 URL 不得超过 500 字符")

            published_at = _parse_iso_date(source.get("published_at"))
            if not published_at:
                issues.append(f"事项 {item_id} 的来源日期必须使用有效的 YYYY-MM-DD")
            elif period and period_start <= published_at <= period_end:
                has_period_source = True

            if source.get("access_status") != "verified":
                issues.append(f"事项 {item_id} 的来源 access_status 必须是 verified")
            checked_at = _parse_iso_date(source.get("access_checked_at"))
            if not checked_at:
                issues.append(f"事项 {item_id} 的来源 access_checked_at 必须使用有效的 YYYY-MM-DD")
            elif published_at and checked_at < published_at:
                issues.append(f"事项 {item_id} 的来源核验日期不得早于发布日期")
            elif checked_at > date.today():
                issues.append(f"事项 {item_id} 的来源核验日期不得晚于当前日期")

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

        matching_trigger_source = None
        if _valid_url(trigger_url):
            trigger_key = _normalise_url(trigger_url)
            for source in sources:
                if isinstance(source, dict) and _valid_url(source.get("url", "")):
                    if _normalise_url(source["url"]) == trigger_key:
                        matching_trigger_source = source
                        break
        if not matching_trigger_source:
            issues.append(f"事项 {item_id} 的触发来源必须出现在 sources 中")
        elif (
            matching_trigger_source.get("access_status") != "verified"
            or not matching_trigger_source.get("is_primary")
        ):
            issues.append(f"事项 {item_id} 的触发来源必须是已核验的一手或原创直接来源")

        if sources and not has_period_source and trigger_type != "policy_effective":
            issues.append(f"事项 {item_id} 至少需要 1 个发布日期在报告期内的直接来源")
        if footer_length > 110:
            issues.append(f"事项 {item_id} 的来源名称过长，页脚无法稳定展示")
        if sources and not has_primary:
            issues.append(f"事项 {item_id} 至少需要 1 个一手来源或原创直接来源")

    for section_name, item in briefs:
        item_id = item.get("id") or "未命名速览"
        ids.append(item.get("id"))
        brief_section_counts[section_name] += 1
        _validate_brief(
            issues,
            section_name,
            item,
            period,
            period_start,
            period_end,
            source_documents,
        )

    if coverage_mode == "broad_and_deep" and len(brief_section_counts) < 3:
        issues.append("broad_and_deep 模式的速览事项至少覆盖 3 个栏目")

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
        _check_text(issues, f"core_insights[{index}].claim", insight.get("claim"), 12, 70)
        evidence_ids = insight.get("evidence_ids")
        if not isinstance(evidence_ids, list) or len(set(evidence_ids)) < 2:
            issues.append(f"core_insights[{index}] 至少需要 2 个 evidence_ids")
        else:
            unknown = set(evidence_ids) - known_ids
            if unknown:
                issues.append(f"core_insights[{index}] 引用了不存在的事项：{', '.join(sorted(unknown))}")

    _check_text(issues, "weekly_judgment", report.get("weekly_judgment"), 100, 200)

    quality_review = report.get("quality_review")
    quality_scores = []
    if not isinstance(quality_review, dict):
        issues.append("报告必须包含 quality_review")
    else:
        for dimension in QUALITY_DIMENSIONS:
            review = quality_review.get(dimension)
            if not isinstance(review, dict):
                issues.append(f"quality_review.{dimension} 必须是对象")
                continue
            score = review.get("score")
            if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 10:
                issues.append(f"quality_review.{dimension}.score 必须是 1-10 的整数")
            else:
                quality_scores.append(score)
                if score < 8:
                    issues.append(f"quality_review.{dimension} 低于 8 分，必须返工")
            _check_text(issues, f"quality_review.{dimension}.reason", review.get("reason"), 10, 120)
    if len(quality_scores) == len(QUALITY_DIMENSIONS) and sum(quality_scores) < 32:
        issues.append("quality_review 总分低于 32 分，必须返工")

    if issues:
        raise ReportQualityError(issues)

    return {
        "event_count": len(events),
        "brief_count": len(briefs),
        "coverage_count": len(events) + len(briefs),
        "minimum_score": min(score_totals),
        "maximum_score": max(score_totals),
        "insight_count": len(insights),
        "quality_total": sum(quality_scores),
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
        "| 事项ID | 事项 | 来源 | 日期 | 类型 | 一手来源 | 访问核验 | URL |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _section_name, item in iter_items(report):
        if not isinstance(item, dict):
            continue
        for source in item.get("sources") or []:
            lines.append(
                "| {id} | {headline} | {name} | {date} | {kind} | {primary} | {checked} | {url} |".format(
                    id=_escape_table(item.get("id", "")),
                    headline=_escape_table(item.get("headline", "")),
                    name=_escape_table(source.get("name", "")),
                    date=_escape_table(source.get("published_at", "")),
                    kind=_escape_table(source.get("source_type", "")),
                    primary="是" if source.get("is_primary") else "否",
                    checked=_escape_table(source.get("access_checked_at", "")),
                    url=_escape_table(source.get("url", "")),
                )
            )
    return "\n".join(lines) + "\n"


def build_quality_markdown(report):
    """生成可审计的 40 分质量报告。"""

    review = report.get("quality_review") or {}
    total = sum((review.get(dimension) or {}).get("score", 0) for dimension in QUALITY_DIMENSIONS)
    lines = [
        f"# {report.get('title', '报告')}质量报告",
        "",
        f"报告期：{report.get('period', '')}",
        f"深度事项：{sum(1 for _ in iter_events(report))} 个；速览事项：{sum(1 for _ in iter_briefs(report))} 个",
        f"总分：{total}/40",
        "",
        "| 维度 | 得分 | 复核理由 |",
        "| --- | ---: | --- |",
    ]
    for dimension in QUALITY_DIMENSIONS:
        item = review.get(dimension) or {}
        lines.append(
            f"| {QUALITY_LABELS[dimension]} | {item.get('score', '')}/10 | {_escape_table(item.get('reason', ''))} |"
        )
    lines.extend(["", "结论：通过自动门槛；仍需完成全页渲染复核。", ""])
    return "\n".join(lines)
