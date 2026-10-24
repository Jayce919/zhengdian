# -*- coding: utf-8 -*-
r"""把历年真题（选择题）解析成题库。

输入：考研政治 目录下的真题 PDF / 原始OCR 中的同名 md
输出：知识点\questions_zhenti.json

答案来自「解析」文件：优先匹配 【答案】X；解析正文截取作 explain。
题号→学科：1-4/17-21 马原，5-8/22-26 毛中特或习思想（按关键词判定），
9-12/27-29 史纲，13-14/30-31 思修，15-16/32-33 时政。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

BASE = Path(__file__).resolve().parents[2]
OCR = BASE / "原始OCR"
OUT = BASE / "政治刷题App" / "知识点" / "questions_zhenti.json"

# (年份, 真题文件, 解析文件)
PAIRS = [
    (2009, "2009年考研政治真题.pdf", "2009年考研政治答案解析.pdf"),
    (2010, "2010年考研政治真题.pdf", "2010年考研政治答案解析.pdf"),
    (2011, "2011年考研政治真题.pdf", "2011年考研政治答案解析.pdf"),
    (2012, "2012年考研政治真题.pdf", "2012年考研政治答案解析.pdf"),
    (2013, "2013年考研政治真题.pdf", "2013年考研政治答案解析.pdf"),
    (2014, "2014年考研政治真题.pdf", "2014年考研政治答案解析.pdf"),
    (2015, "2015年考研政治真题.pdf", "2015年考研政治答案解析.pdf"),
    (2016, "2016年考研政治真题.pdf", "2016年考研政治答案解析.pdf"),
    (2017, "2017年考研政治真题.pdf", "2017年考研政治答案解析.pdf"),
    (2018, "2018年考研政治真题.pdf", "2018年考研政治答案解析.pdf"),
    (2019, "2019年考研政治真题.pdf", "2019年考研政治答案解析.pdf"),
    (2020, "2020年考研政治真题.pdf", "2020年考研政治答案解析.pdf"),
    (2021, "2021年考研政治真题.pdf", "2021年考研政治答案解析.pdf"),
    (2022, "2022年考研政治真题.pdf", "2022年考研政治真题解析.pdf"),
    (2023, "2023年政治真题及解析.pdf", None),
    (2024, "2024考研政治真题.pdf", "24考研政治选择题解析.pdf"),
    (2025, "2025考研政治真题及解析【完整版】.pdf", None),
    (2026, "2026考研政治真题试卷.pdf", "2026考研政治真题试卷完整解析.pdf"),
]


# 网上机构版答案（官方不公布）：用于解析文件缺答案的年份
ANSWER_OVERRIDE = {
    2024: {
        **{i + 1: a for i, a in enumerate("ACDD AABCB BACBCDD".replace(" ", ""))},
        **{n: a for n, a in [
            (17, "ABD"), (18, "ACD"), (19, "AC"), (20, "BC"), (21, "ABD"),
            (22, "BCD"), (23, "ABCD"), (24, "ABCD"), (25, "ABC"), (26, "ABD"),
            (27, "ABD"), (28, "ACD"), (29, "ABD"), (30, "ABC"), (31, "ABCD"),
            (32, "ABCD"), (33, "ACD")]},
    },
}

XI_WORDS = ("习近平", "新时代", "中国式现代化", "中国梦", "全面深化改革", "新发展", "共同富裕",
            "人类命运共同体", "四个全面", "五位一体", "党的自我革命", "新发展理念", "一带一路")


def read_pdf(name: str) -> str:
    path = next((p for p in BASE.rglob(name)), None)
    if path is None:
        return ""
    try:
        d = fitz.open(path)
        t = "\n".join(d[i].get_text() for i in range(d.page_count))
    except Exception:
        t = ""
    if len(t.strip()) < 200:
        md = OCR / (Path(name).stem + ".md")
        if md.exists():
            t = md.read_text("utf-8")
    return t


def norm(t: str) -> str:
    t = re.sub(r"-\s*\d+\s*-", "", t)
    t = re.sub(r"第\s*\d+\s*页", "", t)
    return t


def parse_questions(text: str) -> dict[int, dict]:
    """按题号定位：每题取第一处「题号后紧跟 A–D 选项」的片段。"""
    text = norm(text)
    text = re.sub(r"\n\s*\n", "\n", text)
    marks = [(m.start(), m.end(), int(m.group(1)))
             for m in re.finditer(r"(?<!\d)(\d{1,2})\s*[.．、]\s*", text)]
    out: dict[int, dict] = {}
    for n in range(1, 39):
        for st, en, num in marks:
            if num != n:
                continue
            nxt = len(text)
            for st2, _, num2 in marks:
                if st2 > en and num2 > n:
                    nxt = st2
                    break
            block = text[en: min(nxt, en + 1600)]
            idx = {}
            for L in "ABCD":
                mm = re.search(rf"{L}\s*[.．、]\s*", block)
                if mm:
                    idx[L] = mm.start()
            if len(idx) != 4:
                continue
            letters = sorted(idx, key=lambda x: idx[x])
            stem = block[: idx[letters[0]]].strip()
            if len(stem) < 8:
                continue
            opts = {}
            for j, L in enumerate(letters):
                s0 = idx[L]
                s1 = idx[letters[j + 1]] if j + 1 < len(letters) else len(block)
                opts[L] = re.sub(rf"^{L}\s*[.．．、]\s*", "", block[s0:s1]).strip()
            out[n] = {"stem": re.sub(r"\s+", " ", stem).strip(), "options": opts}
            break
    return out


def parse_answers(text: str) -> dict[int, tuple[str, str]]:
    """按题号切块，在块内寻找答案标记，兼容【答案】【标准答案】“答案为X”等写法。"""
    text = norm(text)
    text = re.sub(r"(?m)^\s*([A-D])\s*[。、]\s*", r". ", text)
    marks = [(m.start(), m.end(), int(m.group(1)))
             for m in re.finditer(r"(?<!\d)(\d{1,2})\s*[.．、]\s*", text)]
    picked = []
    last = 0
    for st, en, n in marks:
        if n > last and n <= 38 and n - last <= 6:
            picked.append((st, en, n))
            last = n
    res: dict[int, tuple[str, str]] = {}
    for k, (st, en, n) in enumerate(picked):
        end = picked[k + 1][0] if k + 1 < len(picked) else min(len(text), en + 2500)
        block = text[st:end]
        m = (re.search(r"[（(【]?\s*(?:标准)?答案\s*[）)】]?\s*[:：]?\s*([A-D]{1,4})", block)
             or re.search(r"答案[为是应]\s*[:：]?\s*([A-D]{1,4})", block)
             or re.search(r"故(?:正确)?选\s*[:：]?\s*([A-D]{1,4})", block))
        if not m:
            continue
        body = re.sub(r"\s+", " ", block[:1400]).strip()
        bleed = re.search(r"(?<!\d)\d{1,2}\s*[.．、]?\s*[（(【]?\s*(?:标准)?答案", body[10:])
        if bleed:
            body = body[: 10 + bleed.start()]
        res[n] = (m.group(1), body[:400])
    # 全局兜底：处理块切分失败的写法（如 2023 年的「1．（答案）A」）
    for m in re.finditer(r"(?<!\d)(\d{1,2})\s*[.．、]?\s*[（(【]?\s*(?:标准)?答案\s*[）)】]?\s*[:：]?\s*([A-D]{1,4})", text):
        n = int(m.group(1))
        if n in res or n > 38:
            continue
        body = re.sub(r"\s+", " ", text[m.end(): m.end() + 400]).strip()
        res[n] = (m.group(2), body)
    return res


def subject_of(n: int, stem: str) -> str:
    if n in (1, 2, 3, 4) or 17 <= n <= 21:
        return "mayuan"
    if 5 <= n <= 8 or 22 <= n <= 26:
        return "xisixiang" if any(w in stem for w in XI_WORDS) else "maozhongte"
    if 9 <= n <= 12 or 27 <= n <= 29:
        return "shigang"
    if n in (13, 14) or n in (30, 31):
        return "sifa"
    return "shizheng"


def main() -> None:
    items = []
    for year, qfile, afile in PAIRS:
        qtext = read_pdf(qfile)
        if not qtext:
            print(f"{year}: 真题缺失")
            continue
        atext = read_pdf(afile) if afile else qtext
        qs = parse_questions(qtext)
        ans = parse_answers(atext)
        for n, letters in ANSWER_OVERRIDE.get(year, {}).items():
            ans.setdefault(n, (letters, "参考答案（网络机构版整理）。"))
        if len(qs) < 12 and atext != qtext:
            qs2 = parse_questions(atext)
            for n, v in qs2.items():
                qs.setdefault(n, v)
        added = 0
        for n in range(1, 34):
            q = qs.get(n)
            a = ans.get(n)
            if not q or not a or len(q["options"]) != 4:
                continue
            letters, explain = a
            qtype = "single" if n <= 16 else "multi"
            if qtype == "single" and len(letters) != 1:
                continue
            if qtype == "multi" and len(letters) < 2:
                continue
            subj = subject_of(n, q["stem"])
            items.append({
                "id": f"q-zt-{year}-{n:02d}",
                "type": qtype,
                "subject": subj,
                "partId": f"{subj}-01",
                "stem": q["stem"][:400],
                "options": [f"{L}. {q['options'][L]}" for L in "ABCD"],
                "answer": letters if qtype == "single" else list(letters),
                "explain": explain or "详见真题解析。",
                "refs": [f"{year}年考研政治真题 第{n}题"],
                "source": "zhenti",
                "year": year,
            })
            added += 1
        print(f"{year}: {added} 题（答案 {len(ans)} 条）")
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print("合计", len(items))


if __name__ == "__main__":
    main()
