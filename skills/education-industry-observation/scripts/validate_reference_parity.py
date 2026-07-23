#!/usr/bin/env python3
"""Validate content and structural parity between a reference PDF and output PDF."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


class ParityError(ValueError):
    """Raised when reference-parity validation fails."""


def _is_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_iso_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_manifest(manifest: dict) -> list[str]:
    issues: list[str] = []
    if manifest.get("mode") != "reference_parity":
        issues.append("mode 必须是 reference_parity")

    reference = manifest.get("reference")
    if not isinstance(reference, dict):
        issues.append("reference 必须是对象")
    else:
        if not isinstance(reference.get("file"), str) or not reference.get("file"):
            issues.append("reference.file 必须是非空字符串")
        sha256 = reference.get("sha256")
        if not isinstance(sha256, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", sha256):
            issues.append("reference.sha256 必须是 64 位 SHA-256")

    expected = manifest.get("expected")
    if not isinstance(expected, dict):
        return issues + ["expected 必须是对象"]

    page_count = expected.get("page_count")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        issues.append("expected.page_count 必须是正整数")

    page_size = expected.get("page_size_pts")
    if (
        not isinstance(page_size, list)
        or len(page_size) != 2
        or not all(isinstance(value, (int, float)) and value > 0 for value in page_size)
    ):
        issues.append("expected.page_size_pts 必须是两个正数")

    fonts = expected.get("required_fonts")
    if not isinstance(fonts, list) or not fonts or not all(isinstance(font, str) and font for font in fonts):
        issues.append("expected.required_fonts 必须是非空字符串列表")

    reference_items = expected.get("reference_items")
    if not isinstance(reference_items, list) or not reference_items:
        issues.append("expected.reference_items 必须是非空列表")
        reference_items = []

    output_items = manifest.get("output_items")
    if not isinstance(output_items, list) or not output_items:
        issues.append("output_items 必须是非空列表")
        output_items = []

    reference_ids: list[str] = []
    reference_pages: dict[str, int] = {}
    for index, item in enumerate(reference_items, 1):
        label = f"reference_items[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} 必须是对象")
            continue
        reference_id = item.get("reference_id")
        if not isinstance(reference_id, str) or not reference_id:
            issues.append(f"{label}.reference_id 必须是非空字符串")
            continue
        reference_ids.append(reference_id)
        item_page = item.get("page")
        if not isinstance(item_page, int) or isinstance(item_page, bool) or item_page < 1:
            issues.append(f"{label}.page 必须是正整数")
        elif isinstance(page_count, int) and item_page > page_count:
            issues.append(f"{label}.page 超出总页数")
        else:
            reference_pages[reference_id] = item_page

        markers = item.get("content_markers")
        if (
            not isinstance(markers, list)
            or len(markers) < 2
            or not all(isinstance(marker, str) and marker.strip() for marker in markers)
        ):
            issues.append(f"{label}.content_markers 至少需要 2 个非空标记")

        if not _is_iso_date(item.get("event_date")):
            issues.append(f"{label}.event_date 必须是 YYYY-MM-DD")
        if item.get("date_scope") not in {"within_period", "reference_carryover"}:
            issues.append(f"{label}.date_scope 必须是 within_period 或 reference_carryover")

        sources = item.get("sources")
        if not isinstance(sources, list) or not sources:
            issues.append(f"{label}.sources 必须是非空列表")
            sources = []
        for source_index, source in enumerate(sources, 1):
            source_label = f"{label}.sources[{source_index}]"
            if not isinstance(source, dict):
                issues.append(f"{source_label} 必须是对象")
                continue
            if not isinstance(source.get("name"), str) or not source.get("name"):
                issues.append(f"{source_label}.name 必须是非空字符串")
            if not _is_url(source.get("url")):
                issues.append(f"{source_label}.url 必须是有效的 http/https 地址")
            if not _is_iso_date(source.get("published_at")):
                issues.append(f"{source_label}.published_at 必须是 YYYY-MM-DD")
            if not _is_iso_date(source.get("access_checked_at")):
                issues.append(f"{source_label}.access_checked_at 必须是 YYYY-MM-DD")

    if len(reference_ids) != len(set(reference_ids)):
        issues.append("reference_items 的 reference_id 必须唯一")

    output_ids: list[str] = []
    for index, item in enumerate(output_items, 1):
        label = f"output_items[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} 必须是对象")
            continue
        reference_id = item.get("reference_id")
        if not isinstance(reference_id, str) or not reference_id:
            issues.append(f"{label}.reference_id 必须是非空字符串")
            continue
        output_ids.append(reference_id)
        item_page = item.get("page")
        if not isinstance(item_page, int) or isinstance(item_page, bool) or item_page < 1:
            issues.append(f"{label}.page 必须是正整数")
        elif reference_pages.get(reference_id) not in {None, item_page}:
            issues.append(f"{label}.page 与样稿页码不一致")

    if len(output_ids) != len(set(output_ids)):
        issues.append("output_items 的 reference_id 必须唯一")
    missing = sorted(set(reference_ids) - set(output_ids))
    extra = sorted(set(output_ids) - set(reference_ids))
    if missing:
        issues.append(f"成品缺少样稿事项：{', '.join(missing)}")
    if extra:
        issues.append(f"成品包含未登记事项：{', '.join(extra)}")
    return issues


def _resolve_tool(env_name: str, candidates: tuple[str, ...]) -> str:
    configured = os.environ.get(env_name)
    if configured and Path(configured).is_file():
        return configured
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    raise ParityError(f"找不到工具：{env_name}")


def _run(tool: str, args: list[str]) -> bytes:
    completed = subprocess.run([tool, *args], check=False, capture_output=True)
    if completed.returncode:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ParityError(message or f"{Path(tool).name} 执行失败")
    return completed.stdout


def _pdf_info(pdfinfo: str, pdf_path: Path) -> tuple[int, tuple[float, float]]:
    output = _run(pdfinfo, [str(pdf_path)]).decode("utf-8", errors="replace")
    pages = re.search(r"^Pages:\s+(\d+)", output, flags=re.MULTILINE)
    size = re.search(r"^Page size:\s+([\d.]+)\s+x\s+([\d.]+)\s+pts", output, flags=re.MULTILINE)
    if not pages or not size:
        raise ParityError(f"无法读取 PDF 页数或页面尺寸：{pdf_path}")
    return int(pages.group(1)), (float(size.group(1)), float(size.group(2)))


def _page_text(pdftotext: str, pdf_path: Path, page_number: int) -> str:
    output = _run(
        pdftotext,
        ["-f", str(page_number), "-l", str(page_number), "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
    )
    return output.decode("utf-8", errors="replace")


def _font_text(pdffonts: str, pdf_path: Path) -> str:
    return _run(pdffonts, [str(pdf_path)]).decode("utf-8", errors="replace")


def validate_pdfs(manifest: dict, reference_pdf: Path, output_pdf: Path) -> list[str]:
    issues: list[str] = []
    pdfinfo = _resolve_tool("PDFINFO_BIN", ("pdfinfo", "pdfinfo.exe"))
    pdftotext = _resolve_tool("PDFTOTEXT_BIN", ("pdftotext", "pdftotext.exe"))
    pdffonts = _resolve_tool("PDFFONTS_BIN", ("pdffonts", "pdffonts.exe"))

    reference_pages, reference_size = _pdf_info(pdfinfo, reference_pdf)
    output_pages, output_size = _pdf_info(pdfinfo, output_pdf)
    expected = manifest["expected"]
    expected_pages = expected["page_count"]
    expected_size = tuple(float(value) for value in expected["page_size_pts"])

    if reference_pages != expected_pages:
        issues.append(f"样稿页数 {reference_pages} 与清单 {expected_pages} 不一致")
    if output_pages != expected_pages:
        issues.append(f"成品页数 {output_pages} 与样稿 {expected_pages} 不一致")
    if any(abs(actual - target) > 0.5 for actual, target in zip(reference_size, expected_size)):
        issues.append(f"样稿页面尺寸 {reference_size} 与清单 {expected_size} 不一致")
    if any(abs(actual - target) > 0.5 for actual, target in zip(output_size, expected_size)):
        issues.append(f"成品页面尺寸 {output_size} 与样稿 {expected_size} 不一致")

    output_font_text = _font_text(pdffonts, output_pdf)
    for font in expected["required_fonts"]:
        if font.lower() not in output_font_text.lower():
            issues.append(f"成品 PDF 缺少字体：{font}")

    page_cache: dict[int, str] = {}
    for item in expected["reference_items"]:
        page_number = item["page"]
        if page_number not in page_cache:
            page_cache[page_number] = _page_text(pdftotext, output_pdf, page_number)
        compact_text = re.sub(r"\s+", "", page_cache[page_number])
        for marker in item["content_markers"]:
            compact_marker = re.sub(r"\s+", "", marker)
            if compact_marker not in compact_text:
                issues.append(f"{item['reference_id']} 第 {page_number} 页缺少内容标记：{marker}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="校验样稿复刻的事项、页码、页数、尺寸和字体")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--reference-pdf", type=Path)
    parser.add_argument("--output-pdf", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    issues = validate_manifest(manifest)
    if not issues and args.reference_pdf and args.output_pdf:
        issues.extend(validate_pdfs(manifest, args.reference_pdf, args.output_pdf))
    if issues:
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("reference_parity: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
