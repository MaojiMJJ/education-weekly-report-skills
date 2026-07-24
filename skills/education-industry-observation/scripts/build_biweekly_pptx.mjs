#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { Presentation, PresentationFile } from "@oai/artifact-tool";


function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new Error(`未知参数：${token}`);
    }
    const key = token.slice(2);
    if (key === "template-only") {
      result.templateOnly = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`参数 --${key} 缺少值`);
    }
    result[key.replaceAll("-", "_")] = value;
    index += 1;
  }
  return result;
}


async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}


function addRect(slide, name, frame, fill, lineFill = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: {
      left: frame.left,
      top: frame.top,
      width: frame.width,
      height: frame.height,
    },
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
  });
}


function addText(slide, name, frame, text, style) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: {
      left: frame.left,
      top: frame.top,
      width: frame.width,
      height: frame.height,
    },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    autoFit: "none",
    wrap: "square",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
    ...style,
  };
  return shape;
}


function verticalLabel(value) {
  const tokens = String(value).match(/[A-Za-z0-9.+-]+|\p{Script=Han}|[^\s]/gu) ?? [];
  return tokens.join("\n");
}


function displayPeriod(value) {
  return String(value).replace(/\.0(\d)/g, ".$1");
}


function flattenItems(report) {
  const map = new Map();
  for (const section of report.sections ?? []) {
    for (const item of section.items ?? []) {
      map.set(item.slot_id, item);
    }
  }
  return map;
}


function estimatedLineCount(text, charactersPerLine = 31.5) {
  let width = 0;
  for (const character of Array.from(String(text))) {
    width += /[\u0000-\u00ff]/.test(character) ? 0.55 : 1;
  }
  return Math.max(1, Math.ceil(width / charactersPerLine));
}


function addBulletRows(slide, slotId, bullets, bodyFrame, slot, layout) {
  const fontSize = layout.fonts.body.font_size_pt * (4 / 3);
  const lineHeight = fontSize * 1.2;
  const gap = slot.body.height < 210 ? 5 : 10;
  const bulletLeft = bodyFrame.left + 11;
  const textLeft = bodyFrame.left + 39;
  const textWidth = bodyFrame.width - 51;
  let y = bodyFrame.top + 8;

  for (const [index, bullet] of bullets.entries()) {
    const lines = estimatedLineCount(bullet);
    const rowHeight = lines * lineHeight + 2;
    addText(
      slide,
      `${slotId}-bullet-${index + 1}`,
      { left: bulletLeft, top: y, width: 18, height: lineHeight + 2 },
      "•",
      {
        fontSize,
        typeface: "Arial",
        color: layout.colors.black,
        alignment: "left",
        verticalAlignment: "top",
        lineSpacing: 1.2,
      },
    );
    addText(
      slide,
      `${slotId}-bullet-text-${index + 1}`,
      { left: textLeft, top: y, width: textWidth, height: rowHeight },
      String(bullet),
      {
        fontSize,
        typeface: layout.fonts.body.typeface,
        color: layout.colors.black,
        alignment: "justify",
        verticalAlignment: "top",
        lineSpacing: 1.2,
      },
    );
    y += rowHeight + gap;
  }
  const contentBottom = bodyFrame.top + bodyFrame.height - 8;
  if (y - gap > contentBottom + 1) {
    throw new Error(
      `${slotId} 文本按固定16号字号排版后超出槽位：${Math.round(y - gap)} > ${Math.round(contentBottom)}`,
    );
  }
}


function placeholderReport(layout) {
  const labels = {
    listed_1: "上市公司一",
    listed_2: "上市公司二",
    listed_3: "上市公司三",
    other_1: "行业动态一",
    other_2: "行业动态二",
    other_3: "行业动态三",
    policy_1: "政策动态一",
    policy_2: "政策动态二",
    policy_3: "政策动态三",
    policy_4: "政策动态四",
    policy_5: "政策动态五",
  };
  const sections = [];
  for (const [name, slotIds] of [
    ["行业速览-上市公司", ["listed_1", "listed_2", "listed_3"]],
    ["行业速览-其他", ["other_1", "other_2", "other_3"]],
    ["行业速览-政策", ["policy_1", "policy_2", "policy_3", "policy_4", "policy_5"]],
  ]) {
    sections.push({
      name,
      items: slotIds.map((slotId) => {
        const slot = layout.slots[slotId];
        const bullets = [];
        for (let index = 0; index < slot.min_bullets; index += 1) {
          bullets.push(`【本期事项要点 ${index + 1}：写明时间、主体、动作和关键事实。】`);
        }
        return { slot_id: slotId, short_title: labels[slotId], bullets };
      }),
    });
  }
  return {
    title: "教育行业观察",
    period: "20XX.XX.XX-20XX.XX.XX",
    template_id: layout.template_id,
    sections,
  };
}


async function addCover(presentation, report, layout, coverPath) {
  const slide = presentation.slides.add();
  slide.background.fill = layout.colors.white;
  const bytes = await fs.readFile(coverPath);
  const source = layout.cover.image;
  slide.images.add({
    blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    contentType: "image/jpeg",
    alt: "双周报封面握手照片",
    fit: "cover",
    position: source,
  });
  addRect(
    slide,
    "cover-green-block",
    layout.cover.green_block,
    layout.colors.cover_green,
  );
  addText(
    slide,
    "cover-title",
    layout.cover.title,
    report.title,
    {
      fontSize: layout.fonts.cover_title.font_size_pt * (4 / 3),
      typeface: layout.fonts.cover_title.typeface,
      color: layout.colors.white,
      alignment: "left",
      verticalAlignment: "middle",
    },
  );
  addText(
    slide,
    "cover-period",
    layout.cover.period,
    displayPeriod(report.period),
    {
      fontSize: layout.fonts.cover_period.font_size_pt * (4 / 3),
      typeface: layout.fonts.cover_period.typeface,
      color: layout.colors.white,
      alignment: "left",
      verticalAlignment: "middle",
    },
  );
}


function addContentSlide(presentation, pageSpec, items, layout) {
  const slide = presentation.slides.add();
  slide.background.fill = layout.colors.white;
  const chrome = layout.content_chrome;
  addRect(
    slide,
    `page-${pageSpec.page}-header`,
    chrome.header,
    layout.colors.header_green,
  );
  addText(
    slide,
    `page-${pageSpec.page}-header-text`,
    chrome.header_text,
    pageSpec.header,
    {
      fontSize: layout.fonts.header.font_size_pt * (4 / 3),
      typeface: layout.fonts.header.typeface,
      color: layout.colors.black,
      alignment: "left",
      verticalAlignment: "middle",
    },
  );

  for (const slotId of pageSpec.slots) {
    const slot = layout.slots[slotId];
    const item = items.get(slotId);
    if (!item) {
      throw new Error(`报告缺少槽位：${slotId}`);
    }
    const labelFrame = {
      left: chrome.label_left,
      top: slot.label.top,
      width: chrome.label_width,
      height: slot.label.height,
    };
    const bodyFrame = {
      left: chrome.body_left,
      top: slot.body.top,
      width: chrome.body_width,
      height: slot.body.height,
    };
    addRect(
      slide,
      `${slotId}-label-background`,
      labelFrame,
      layout.colors.label_green,
      layout.colors.line_green,
      chrome.line_width,
    );
    addText(
      slide,
      `${slotId}-label`,
      {
        left: labelFrame.left + 7,
        top: labelFrame.top + 7,
        width: labelFrame.width - 14,
        height: labelFrame.height - 14,
      },
      verticalLabel(item.short_title),
      {
        fontSize: layout.fonts.label.font_size_pt * (4 / 3),
        typeface: layout.fonts.label.typeface,
        color: layout.colors.black,
        alignment: "center",
        verticalAlignment: "middle",
        lineSpacing: 1.2,
      },
    );
    addRect(
      slide,
      `${slotId}-body-frame`,
      bodyFrame,
      layout.colors.white,
      layout.colors.line_green,
      chrome.line_width,
    );
    addBulletRows(slide, slotId, item.bullets, bodyFrame, slot, layout);
  }
}


async function build(args) {
  for (const required of ["layout", "cover", "output"]) {
    if (!args[required]) {
      throw new Error(`必须提供 --${required}`);
    }
  }
  const layout = JSON.parse(await fs.readFile(args.layout, "utf8"));
  const report = args.templateOnly
    ? placeholderReport(layout)
    : JSON.parse(await fs.readFile(args.input, "utf8"));
  if (report.template_id !== layout.template_id) {
    throw new Error(`template_id 必须是 ${layout.template_id}`);
  }
  const presentation = Presentation.create({
    slideSize: { width: layout.canvas_px[0], height: layout.canvas_px[1] },
  });
  await addCover(presentation, report, layout, args.cover);
  const items = flattenItems(report);
  for (const pageSpec of layout.pages) {
    addContentSlide(presentation, pageSpec, items, layout);
  }
  const output = path.resolve(args.output);
  await fs.mkdir(path.dirname(output), { recursive: true });
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(output);

  if (args.qa_dir) {
    const qaDir = path.resolve(args.qa_dir);
    await fs.mkdir(qaDir, { recursive: true });
    for (const [index, slide] of presentation.slides.items.entries()) {
      const stem = `slide-${String(index + 1).padStart(2, "0")}`;
      await writeBlob(
        path.join(qaDir, `${stem}.png`),
        await presentation.export({ slide, format: "png", scale: 1 }),
      );
      const layoutBlob = await slide.export({ format: "layout" });
      await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layoutBlob.text());
    }
    await writeBlob(
      path.join(qaDir, "montage.webp"),
      await presentation.export({ format: "webp", montage: true, scale: 1 }),
    );
  }
  console.log(output);
}


const args = parseArgs(process.argv.slice(2));
build(args).catch((error) => {
  console.error(error?.stack ?? String(error));
  process.exitCode = 1;
});
