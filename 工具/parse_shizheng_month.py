# -*- coding: utf-8 -*-
r"""把 1—9 月时政 PDF 解析成「时政」学科的专题与考点。

- 有文字层的直接抽取；纯扫描件读取 原始OCR\<同名>.md
- 输出 知识点\parts\shizheng-XX.json（XX 为月份）
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "政治刷题App" / "知识点" / "parts"
OCR = BASE / "原始OCR"

FILES = [
    ("01", "【时政】2027考研政治1-2月时政.pdf", "时政 1—2 月"),
    ("02", "【时政】2027考研政治3月时政.pdf", "时政 3 月"),
    ("03", "【时政】2027考研政治4月时政.pdf", "时政 4 月"),
    ("04", "【时政】2027考研政治5月时政.pdf", "时政 5 月"),
    ("05", "【时政】2027考研政治6月时政.pdf", "时政 6 月"),
    ("06", "【时政】2027考研政治7月时政.pdf", "时政 7 月"),
    ("07", "【时政】2027考研政治8月时政.pdf", "时政 8 月"),
    ("08", "【时政】2027考研政治9月时政.pdf", "时政 9 月"),
]

NOISE = re.compile(r"@考研政治徐涛|^\s*\d+\s*$|公众号|微信号")


def read_text(pdf: Path) -> str:
    d = fitz.open(pdf)
    t = "\n".join(d[i].get_text() for i in range(d.page_count))
    if len(t.strip()) < 200:
        md = OCR / (pdf.stem + ".md")
        if md.exists():
            t = md.read_text("utf-8")
    return t


def clean(s: str) -> str:
    s = NOISE.sub("", s)
    s = re.sub(r"[ \t]+", "", s)
    return re.sub(r"\n{2,}", "\n", s).strip()


def split_points(text: str):
    """按「考点N」切分，返回 [(专题, 考点标题, 正文)]"""
    text = clean(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    topic = ""
    points = []
    cur = None
    for ln in lines:
        m_topic = re.match(r"^专题[一二三四五六七八九十百]+[:：]\s*(.+)$", ln)
        if m_topic:
            if cur:
                points.append(cur)
                cur = None
            topic = m_topic.group(1).strip()
            continue
        m = re.match(r"^考点\s*(\d+)[:：]?\s*(.*)$", ln)
        if m:
            if cur:
                points.append(cur)
            cur = {"topic": topic, "title": re.sub(r"^考点\s*\d+", "", m.group(2)).strip(), "body": []}
            continue
        if cur is not None:
            cur["body"].append(ln)
    if cur:
        points.append(cur)
    return points


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for no, fname, part_title in FILES:
        pdf = BASE / fname
        if not pdf.exists():
            print("缺失", fname)
            continue
        text = read_text(pdf)
        raw = split_points(text)
        pts = []
        for k, p in enumerate(raw, 1):
            body = "".join(p["body"]).strip()
            if len(body) < 20:
                continue
            t = p["title"]
            if len(t) < 3 or t.startswith("考点"):
                t = p["topic"] or f"{part_title}要点{k}"
            elif p["topic"] and not t.startswith(p["topic"]):
                t = f"{p['topic']}·{t}"
            # 正文首句作核心，其余作展开
            sentences = [x.strip() for x in re.split(r"(?<=[。！？])", body) if x.strip()]
            # 取第一条有实质内容的句子作核心；小标题（如“（一）……”）跳过
            core = ""
            for sen in sentences:
                if len(sen) >= 18 and not re.match(r"^[（(][一二三四五六七八九十\d]+[)）]", sen):
                    core = sen
                    break
            if not core:
                core = "".join(sentences[:3])[:120]
            detail = [x for x in sentences if x != core and len(x) > 8][:4]
            pts.append({
                "id": f"shizheng-{no}-{k:02d}",
                "title": t[:44],
                "quote": body[:220],
                "core": core[:160],
                "detail": detail,
                "keywords": ["时政"],
                "confusions": [],
                "refs": [f"{part_title} {p['topic']}"],
            })
        if not pts:
            print("解析为空", fname)
            continue
        data = {
            "id": f"shizheng-{no}",
            "no": part_title,
            "title": "时政要点",
            "summary": f"{len(pts)} 个考点",
            "points": pts,
        }
        (OUT / f"shizheng-{no}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", "utf-8")
        print(f"{fname}: {len(pts)} 个考点")


if __name__ == "__main__":
    main()
