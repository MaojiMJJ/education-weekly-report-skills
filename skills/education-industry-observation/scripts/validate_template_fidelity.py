#!/usr/bin/env python3
"""Validate the exported PDF against the fixed colleague-template contract."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


FORBIDDEN = (
    "本期主要动态",
    "行业判断",
    "受益：",
    "风险：",
    "本期行业小结",
    "后续跟踪",
    "下一期验证",
)


class FidelityError(ValueError):
    pass


def _resolve_tool(env_name, candidates):
    configured = os.environ.get(env_name)
    if configured and Path(configured).is_file():
        return configured
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    raise FidelityError(f"找不到工具：{env_name}")


def _run(tool, args):
    completed = subprocess.run([tool, *args], check=False, capture_output=True)
    if completed.returncode:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise FidelityError(message or f"{Path(tool).name} 执行失败")
    return completed.stdout


def _pdf_info(pdfinfo, pdf_path):
    output = _run(pdfinfo, [str(pdf_path)]).decode("utf-8", errors="replace")
    pages = re.search(r"^Pages:\s+(\d+)", output, flags=re.MULTILINE)
    size = re.search(
        r"^Page size:\s+([\d.]+)\s+x\s+([\d.]+)\s+pts",
        output,
        flags=re.MULTILINE,
    )
    if not pages or not size:
        raise FidelityError(f"无法读取 PDF 页数或页面尺寸：{pdf_path}")
    return int(pages.group(1)), (float(size.group(1)), float(size.group(2)))


def _page_text(pdftotext, pdf_path, page_number):
    output = _run(
        pdftotext,
        [
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-layout",
            "-enc",
            "UTF-8",
            str(pdf_path),
            "-",
        ],
    )
    return output.decode("utf-8", errors="replace")


def _compact(value):
    return re.sub(r"\s+", "", str(value))


def _vertical_tokens(value):
    return re.findall(r"[A-Za-z0-9.+-]+|[\u4e00-\u9fff]|[^\s]", str(value))


def validate(report, layout, output_pdf, scratch_dir=None):
    issues = []
    pdfinfo = _resolve_tool("PDFINFO_BIN", ("pdfinfo.exe", "pdfinfo"))
    pdftotext = _resolve_tool("PDFTOTEXT_BIN", ("pdftotext.exe", "pdftotext"))
    pdffonts = _resolve_tool("PDFFONTS_BIN", ("pdffonts.exe", "pdffonts"))

    output_pdf = Path(output_pdf)
    poppler_pdf = output_pdf
    temporary_copy = None
    if os.name == "nt" and any(ord(character) > 127 for character in str(output_pdf)):
        scratch = Path(scratch_dir) if scratch_dir else Path.cwd() / ".template-fidelity"
        scratch.mkdir(parents=True, exist_ok=True)
        temporary_copy = scratch / f"output-{uuid.uuid4().hex}.pdf"
        shutil.copyfile(output_pdf, temporary_copy)
        poppler_pdf = temporary_copy

    try:
        issues.extend(_validate_pdf(report, layout, poppler_pdf, pdfinfo, pdftotext, pdffonts))
    finally:
        if temporary_copy and temporary_copy.exists():
            temporary_copy.unlink()
    return issues


def _validate_pdf(report, layout, output_pdf, pdfinfo, pdftotext, pdffonts):
    issues = []
    pages, size = _pdf_info(pdfinfo, output_pdf)
    expected_pages = layout["reference"]["page_count"]
    expected_size = tuple(float(value) for value in layout["reference"]["page_size_pts"])
    if pages != expected_pages:
        issues.append(f"成品页数 {pages}，应为 {expected_pages}")
    if any(abs(actual - expected) > 0.5 for actual, expected in zip(size, expected_size)):
        issues.append(f"成品页面尺寸 {size}，应为 {expected_size}")

    font_text = _run(pdffonts, [str(output_pdf)]).decode("utf-8", errors="replace").lower()
    for font in ("kaiti", "simsun", "calibri"):
        if font not in font_text:
            issues.append(f"成品 PDF 缺少字体：{font}")
    for substituted in ("noto sans", "dejavu"):
        if substituted in font_text:
            issues.append(f"成品 PDF 出现替代字体：{substituted}")

    items = {
        item["slot_id"]: item
        for section in report.get("sections") or []
        for item in section.get("items") or []
    }
    page_cache = {}
    for page_spec in layout["pages"]:
        page_number = page_spec["page"]
        text = _page_text(pdftotext, output_pdf, page_number)
        page_cache[page_number] = text
        compact = _compact(text)
        if _compact(page_spec["header"]) not in compact:
            issues.append(f"第 {page_number} 页缺少栏目标题：{page_spec['header']}")
        for slot_id in page_spec["slots"]:
            item = items.get(slot_id)
            if not item:
                issues.append(f"报告缺少槽位：{slot_id}")
                continue
            if not all(_compact(token) in compact for token in _vertical_tokens(item["short_title"])):
                issues.append(f"第 {page_number} 页缺少短标题：{item['short_title']}")
            marker = _compact(item["bullets"][0])[:12]
            if marker and marker not in compact:
                issues.append(f"第 {page_number} 页缺少 {slot_id} 的首条内容标记")

    all_text = "\n".join(page_cache.values())
    for marker in FORBIDDEN:
        if marker in all_text:
            issues.append(f"公开页面出现模板外措辞：{marker}")
    return issues


def main():
    parser = argparse.ArgumentParser(description="校验固定同事版教育双周报 PDF")
    parser.add_argument("report_json", type=Path)
    parser.add_argument("output_pdf", type=Path)
    parser.add_argument(
        "--layout",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "assets"
        / "colleague-template"
        / "layout.json",
    )
    parser.add_argument("--scratch-dir", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    layout = json.loads(args.layout.read_text(encoding="utf-8"))
    issues = validate(report, layout, args.output_pdf, args.scratch_dir)
    if issues:
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("template_fidelity: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
