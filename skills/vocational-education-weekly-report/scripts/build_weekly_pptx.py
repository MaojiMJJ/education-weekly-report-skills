#!/usr/bin/env python3
"""Build a simple weekly-report PPTX from a structured JSON spec."""

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
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = FONT
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    return box


def add_bullets(slide, x, y, w, h, bullets):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.12)
    tf.margin_right = Inches(0.12)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    for idx, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = str(bullet)
        p.level = 0
        p.space_after = Pt(7)
        p.font.name = FONT
        p.font.size = Pt(15)
        p.font.color.rgb = TEXT
    return box


def add_footer(slide, source: str | None, source_url: str | None):
    if not source and not source_url:
        return
    txt = "来源：" + (source or "")
    if source_url:
        txt += f" | {source_url}"
    add_textbox(slide, 0.55, 7.05, 12.2, 0.25, txt, font_size=8, color=MUTED)


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
    p = title_panel.text_frame.paragraphs[0]
    p.text = str(item.get("headline", ""))
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = TITLE_COLOR

    bullets = item.get("bullets") or []
    add_bullets(slide, 3.25, 1.08, 9.25, 5.72, bullets)
    add_footer(slide, item.get("source"), item.get("source_url"))


def validate(spec: dict[str, Any]) -> None:
    if not spec.get("title"):
        raise ValueError("JSON must include title")
    if not spec.get("period"):
        raise ValueError("JSON must include period")
    sections = spec.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("JSON must include non-empty sections")
    for section in sections:
        if not section.get("name"):
            raise ValueError("Each section must include name")
        items = section.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"Section {section.get('name')} must include items")
        for item in items:
            if not item.get("headline"):
                raise ValueError("Each item must include headline")
            if not item.get("bullets"):
                raise ValueError(f"Item {item.get('headline')} must include bullets")


def build(spec: dict[str, Any], output: Path) -> None:
    validate(spec)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    add_cover(prs, spec)
    num = 1
    for section in spec["sections"]:
        for item in section["items"]:
            add_item_slide(prs, section["name"], item, num)
            num += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output)


def self_test_spec() -> dict[str, Any]:
    return {
        "title": "职教行业周报",
        "period": "2026.06.15-2026.06.28",
        "sections": [
            {
                "name": "职业教育-政策",
                "items": [
                    {
                        "headline": "教育发展十五五规划提出加快职业教育新双高建设",
                        "bullets": [
                            "国务院相关规划提出加快建设现代职业教育体系。",
                            "文件提出布局市域产教联合体和行业产教融合共同体。",
                            "关注后续国家和地方项目清单、预算落地和院校申报节奏。",
                        ],
                        "source": "示例来源",
                        "source_url": "https://example.com",
                    }
                ],
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", nargs="?", help="Path to report JSON")
    parser.add_argument("--output", required=True, help="Output PPTX path")
    parser.add_argument("--self-test", action="store_true", help="Use built-in sample data")
    args = parser.parse_args()

    if args.self_test:
        spec = self_test_spec()
    else:
        if not args.input_json:
            raise SystemExit("input_json is required unless --self-test is used")
        spec = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    build(spec, Path(args.output))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
