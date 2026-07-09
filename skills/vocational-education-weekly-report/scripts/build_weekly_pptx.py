#!/usr/bin/env python3
"""根据结构化 JSON 生成周报 PPTX。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


FONT = "Microsoft YaHei"
TITLE_COLOR = RGBColor(28, 59, 92)
ACCENT = RGBColor(29, 102, 145)
LIGHT_BG = RGBColor(239, 244, 248)
TEXT = RGBColor(36, 40, 45)
MUTED = RGBColor(110, 118, 128)


def add_textbox(slide, x, y, w, h, text="", font_size=18, bold=False, color=TEXT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.08)
    frame.margin_right = Inches(0.08)
    frame.margin_top = Inches(0.04)
    frame.margin_bottom = Inches(0.04)
    paragraph = frame.paragraphs[0]
    paragraph.text = str(text)
    paragraph.font.name = FONT
    paragraph.font.size = Pt(font_size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = color
    return box


def add_bullets(slide, x, y, w, h, bullets):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.12)
    frame.margin_right = Inches(0.12)
    frame.margin_top = Inches(0.05)
    frame.margin_bottom = Inches(0.05)
    for index, bullet in enumerate(bullets):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = str(bullet)
        paragraph.level = 0
        paragraph.space_after = Pt(7)
        paragraph.font.name = FONT
        paragraph.font.size = Pt(15)
        paragraph.font.color.rgb = TEXT
    return box


def add_footer(slide, source: str | None, source_url: str | None):
    if not source and not source_url:
        return
    text = "来源：" + (source or "")
    if source_url:
        text += f" | {source_url}"
    add_textbox(slide, 0.55, 7.05, 12.2, 0.25, text, font_size=8, color=MUTED)


def add_cover(prs: Presentation, spec: dict[str, Any]):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(255, 255, 255)

    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    band.fill.solid()
    band.fill.fore_color.rgb = LIGHT_BG
    band.line.fill.background()

    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.18), Inches(7.5))
    accent.fill.solid()
    accent.fill.fore_color.rgb = ACCENT
    accent.line.fill.background()

    add_textbox(slide, 0.85, 2.35, 11.6, 0.8, spec.get("title", "职教行业周报"), 34, True, TITLE_COLOR)
    add_textbox(slide, 0.9, 3.25, 10.0, 0.35, spec.get("period", ""), 18, False, MUTED)
    subtitle = spec.get("subtitle") or "每两周一次 | 每页一个事项 | 标题 + 正文内容"
    add_textbox(slide, 0.9, 4.0, 10.5, 0.35, subtitle, 14, False, TEXT)


def add_item_slide(prs: Presentation, section_name: str, item: dict[str, Any], number: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(255, 255, 255)

    top = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.52))
    top.fill.solid()
    top.fill.fore_color.rgb = LIGHT_BG
    top.line.fill.background()

    add_textbox(slide, 0.5, 0.12, 5.2, 0.28, f"{number} {section_name}", 11, True, ACCENT)

    title_panel = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.55), Inches(1.08), Inches(2.35), Inches(5.78))
    title_panel.fill.solid()
    title_panel.fill.fore_color.rgb = LIGHT_BG
    title_panel.line.color.rgb = RGBColor(218, 228, 236)
    title_panel.text_frame.clear()
    title_panel.text_frame.word_wrap = True
    title_panel.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = title_panel.text_frame.paragraphs[0]
    paragraph.text = str(item.get("headline", ""))
    paragraph.alignment = PP_ALIGN.CENTER
    paragraph.font.name = FONT
    paragraph.font.size = Pt(21)
    paragraph.font.bold = True
    paragraph.font.color.rgb = TITLE_COLOR

    add_bullets(slide, 3.25, 1.08, 9.25, 5.72, item.get("bullets") or [])
    add_footer(slide, item.get("source"), item.get("source_url"))


def validate(spec: dict[str, Any]) -> None:
    if not spec.get("title"):
        raise ValueError("JSON 必须包含 title")
    if not spec.get("period"):
        raise ValueError("JSON 必须包含 period")
    sections = spec.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("JSON 必须包含非空 sections")
    for section in sections:
        if not section.get("name"):
            raise ValueError("每个 section 必须包含 name")
        items = section.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"栏目 {section.get('name')} 必须包含 items")
        for item in items:
            if not item.get("headline"):
                raise ValueError("每个 item 必须包含 headline")
            if not item.get("bullets"):
                raise ValueError(f"事项 {item.get('headline')} 必须包含 bullets")


def build(spec: dict[str, Any], output: Path) -> None:
    validate(spec)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    add_cover(prs, spec)
    number = 1
    for section in spec["sections"]:
        for item in section["items"]:
            add_item_slide(prs, section["name"], item, number)
            number += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output)


def self_test_spec() -> dict[str, Any]:
    return {
        "title": "职教行业周报",
        "period": "2026.06.26-2026.07.09",
        "sections": [
            {
                "name": "职业教育-政策",
                "items": [
                    {
                        "headline": "教育发展规划提出加快职业教育新双高建设",
                        "bullets": [
                            "国务院印发教育发展相关规划，提出加快建设现代职业教育体系。",
                            "政策强调中职、高职、职业本科衔接培养和产教融合质量提升。",
                            "后续应跟踪地方项目清单、院校申报和企业参与办学进展。"
                        ],
                        "source": "示例来源",
                        "source_url": "https://example.com"
                    }
                ]
            }
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="根据 JSON 生成周报 PPTX")
    parser.add_argument("input_json", nargs="?", help="报告 JSON 文件路径")
    parser.add_argument("--output", required=True, help="输出 PPTX 路径")
    parser.add_argument("--self-test", action="store_true", help="使用内置示例数据")
    args = parser.parse_args()

    if args.self_test:
        spec = self_test_spec()
    else:
        if not args.input_json:
            raise SystemExit("未使用 --self-test 时必须提供 input_json")
        spec = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    build(spec, Path(args.output))
    print(f"已写入 {args.output}")


if __name__ == "__main__":
    main()
