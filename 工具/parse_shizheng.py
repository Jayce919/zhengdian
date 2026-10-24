# -*- coding: utf-8 -*-
r"""从《背诵手册》下册抽出「习题190」为独立时政题库。

输入：原始OCR\...下册...clean.md
输出：知识点\questions_shizheng.json

题目与答案都是双栏排版，OCR 会把选项顺序打乱，但每个选项的字母标记
仍与文本对应，故按 “字母. 文本” 解析即可；答案区单选/多选各自从 1 编号。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SRC = next((BASE / "原始OCR").glob("*下册*.clean.md"))
OUT = BASE / "政治刷题App" / "知识点" / "questions_shizheng.json"

s = SRC.read_text("utf-8")

# ---------- 切分四个区域 ----------
q_single_start = s.find("单项选择题")
q_multi_start = s.find("多项选择题")
a_all = s.find("参考答案", q_multi_start)
a_single_start = s.find("单项选择题", a_all)
a_multi_start = s.find("多项选择题", a_all)
if a_multi_start < 0:
    a_multi_start = s.find("（二）", a_all)
q_end = a_all

q_single = s[q_single_start:q_multi_start]
q_multi = s[q_multi_start:q_end]
a_single = s[a_single_start:a_multi_start]
a_multi = s[a_multi_start:]


def parse_answers(seg: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for n, a in re.findall(r"(\d{1,3})\s*[.．、]\s*([A-D]{1,4})(?![A-Za-z])", seg):
        out.setdefault(int(n), a)
    return out


def split_questions(seg: str, total: int) -> dict[int, str]:
    """按题号递增切分；题号偶有 OCR 丢失时允许小幅跳号续接。"""
    marks = [(m.start(), m.end(), int(m.group(1))) for m in re.finditer(r"(?<!\d)(\d{1,3})[.．、]\s*", seg)]
    picked: list[tuple[int, int, int]] = []
    last = 0
    for st, en, num in marks:
        if num <= last:
            continue
        if num - last <= 6 and num <= total:
            picked.append((st, en, num))
            last = num
    blocks: dict[int, str] = {}
    for k, (st, en, num) in enumerate(picked):
        nxt = picked[k + 1][0] if k + 1 < len(picked) else len(seg)
        blocks[num] = seg[en:nxt]
    return blocks


def parse_options(block: str) -> tuple[str, list[str]]:
    """返回 (题干, [A文本, B文本, C文本, D文本])"""
    idx = {}
    for L in "ABCD":
        m = re.search(rf"{L}\s*[.．、]\s*", block)
        if m:
            idx[L] = m.start()
    if len(idx) < 4:
        return block.strip(), []
    letters = sorted(idx, key=lambda x: idx[x])
    stem = block[: idx[letters[0]]].strip()
    opts = {}
    for k, L in enumerate(letters):
        start = idx[L]
        end = idx[letters[k + 1]] if k + 1 < len(letters) else len(block)
        raw = block[start:end]
        raw = re.sub(rf"^{L}\s*[.．、]\s*", "", raw).strip()
        opts[L] = raw
    return stem, [opts[L] for L in "ABCD"]


def clean(t: str) -> str:
    t = re.sub(r"配套课程.*$|热联系微信.*$|线上5分.*$", "", t)
    return re.sub(r"\s+", " ", t).strip()


a_s = parse_answers(a_single)
a_m = parse_answers(a_multi)
q_s = split_questions(q_single, max(a_s) if a_s else 46)
q_m = split_questions(q_multi, max(a_m) if a_m else 144)

items = []
bad = 0
for qtype, blocks, answers in (("single", q_s, a_s), ("multi", q_m, a_m)):
    for n, ans in sorted(answers.items()):
        block = blocks.get(n, "")
        stem, opts = parse_options(block)
        if not stem or len(opts) != 4 or len(stem) < 6:
            bad += 1
            continue
        if qtype == "single" and len(ans) != 1:
            bad += 1
            continue
        if qtype == "multi" and len(ans) < 2:
            bad += 1
            continue
        items.append(
            {
                "id": f"q-shizheng-{qtype}-{n:03d}",
                "type": qtype,
                "subject": "shizheng",
                "partId": "shizheng-01",
                "stem": clean(stem),
                "options": [f"{L}. {clean(o)}" for L, o in zip("ABCD", opts)],
                "answer": ans if qtype == "single" else list(ans),
                "explain": "出自肖秀荣《背诵手册》下册习题190。",
                "refs": ["背诵手册下 习题190"],
                "source": "textbook",
            }
        )

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", "utf-8")
singles = sum(1 for i in items if i["type"] == "single")
print(f"✓ {OUT.name}: {len(items)} 题（单选 {singles} / 多选 {len(items) - singles}），跳过 {bad} 条")
