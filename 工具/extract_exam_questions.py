#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从真题 PDF 按版面顺序抽取 33 道客观题（题干 + 四个选项）。

不依赖题号（原 PDF 题号常有 OCR 乱码），按 A-D 选项组顺序编号 1-33。
输出：工具/zhenti_new/parsed_<year>.json
"""
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "政治刷题App" / "工具" / "zhenti_new"
YEARS = {
    "2009": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2009年考研政治真题.pdf",
    "2010": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2010年考研政治真题.pdf",
    "2011": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2011年考研政治真题.pdf",
    "2012": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2012年考研政治真题.pdf",
    "2013": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2013年考研政治真题.pdf",
    "2014": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2014年考研政治真题.pdf",
    "2015": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2015年考研政治真题.pdf",
    "2016": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2016年考研政治真题.pdf",
    "2017": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2017年考研政治真题.pdf",
    "2018": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2018年考研政治真题.pdf",
    "2019": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2019年考研政治真题.pdf",
    "2020": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2020年考研政治真题.pdf",
    "2021": "2009-2021考研政治真题及解析/2009-2021年考研政治真题/2021年考研政治真题.pdf",
    "2024": "2022-2024年政治真题及解析/2024年政治真题及解析/2024考研政治真题.pdf",
}

HEAD = re.compile(r"研究生入学考研思想政治理论试题|^第?\s*\d+\s*页$")
SEC = re.compile(r"一、单项选择题.*?涂黑。|二、多项选择题.*?不得分。")


def page_lines(doc):
    lines = []
    for p in doc:
        rows = []
        for b in p.get_text("blocks"):
            x0, y0, x1, y1, t = b[0], b[1], b[2], b[3], b[4].strip()
            if not t:
                continue
            for r in rows:
                if abs(r["y0"] - y0) < 6:
                    r["parts"].append((x0, t))
                    break
            else:
                rows.append({"y0": y0, "parts": [(x0, t)]})
        for r in sorted(rows, key=lambda r: r["y0"]):
            t = " ".join(x[1] for x in sorted(r["parts"]))
            t = re.sub(r"\s+", " ", t).strip()
            if not t or HEAD.search(t):
                continue
            lines.append(t)
    return lines


def parse(path):
    doc = fitz.open(path)
    lines = page_lines(doc)
    segs = []
    for t in lines:
        pos = [m.start() for m in re.finditer(r"(?<![A-Za-z])([ABCD])\s*[.．、]", t)]
        if not pos:
            segs.append(("", t))
            continue
        if pos[0] > 0:
            segs.append(("", t[: pos[0]]))
        for i, p in enumerate(pos):
            end = pos[i + 1] if i + 1 < len(pos) else len(t)
            segs.append((t[p], t[p:end]))

    pre = []
    for letter, body in segs:
        if letter == "A":
            break
        pre.append(body)
    pending = re.sub(r"\s+", " ", " ".join(pre))
    pending = SEC.sub("", pending).strip()

    raw, cur = [], None
    for letter, body in segs:
        if letter:
            if letter == "A":
                if cur:
                    raw.append(cur)
                cur = {"stem": "", "options": {"A": body[1:].strip(" .．、")}}
            elif cur is not None:
                cur["options"][letter] = body[1:].strip(" .．、")
        else:
            if cur and set(cur["options"]) == {"A", "B", "C", "D"}:
                raw.append(cur)
                cur = {"stem": body, "options": {}}
            elif cur is not None:
                cur["stem"] += " " + body
    if cur:
        raw.append(cur)

    qs, pending = [], pending
    for g in raw:
        stem = g["stem"].strip()
        opts = {k: v.strip() for k, v in g["options"].items() if v.strip()}
        if stem and not opts:
            pending += " " + stem
            continue
        if opts:
            full = re.sub(r"\s+", " ", (pending + " " + stem)).strip()
            pending = ""
            if full:
                qs.append({"stem": full, "options": opts})

    cleaned = []
    for i, q in enumerate(qs, 1):
        stem = SEC.sub("", q["stem"]).strip()
        cleaned.append(
            {
                "n": i,
                "type": "single" if i <= 16 else "multi",
                "stem": stem,
                "options": [f"{k}. {q['options'].get(k, '')}" for k in "ABCD"],
            }
        )
    return cleaned


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for year, rel in YEARS.items():
        qs = parse(ROOT / rel)
        (OUT / f"parsed_{year}.json").write_text(
            json.dumps(qs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        ok = sum(1 for q in qs if all(re.sub(r"^[A-D]\. ", "", o).strip() for o in q["options"]))
        print(f"{year}: {len(qs)} 题，选项齐全 {ok}")


if __name__ == "__main__":
    main()
