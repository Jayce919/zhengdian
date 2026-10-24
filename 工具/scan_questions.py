#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""题库机械性问题扫描：只看格式与 OCR 残留，不做语义判断。

输出每类问题的条目、文件与样例，供人工/代理继续复核。
用法：python 工具/scan_questions.py [--file questions_zhenti.json]
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "政治刷题App" / "知识点"

CJK = re.compile(r"[一-龥]")
SPACE_BETWEEN_CJK = re.compile(r"[一-龥][ \t]+[一-龥]")
HALF_PUNCT = re.compile(r"[一-龥][,;:?!]")
QUOTE = re.compile(r"[“”]")
PAREN = re.compile(r"[（）()]")
GARBAGE = [
    (re.compile(r"【\s*标准答案"), "标准答案残片"),
    (re.compile(r"光速考研|新东方|文都|肖秀荣"), "机构水印"),
    (re.compile(r"第\s*\d+\s*页|##\s*P\d|P\d{1,2}\b"), "页码标记"),
    (re.compile(r"[�□■]"), "乱码字符"),
    (re.compile(r"2{2,}0\d{2}|20\d{3}年"), "年份异常"),
    (re.compile(r"①②③④⑤⑥⑦⑧⑨⑩"), "序号标记"),
    (re.compile(r"判断[：:]"), "判断前缀"),
]
FIELDS = ("stem", "explain")


def scan(file: Path):
    qs = json.loads(file.read_text(encoding="utf-8"))
    issues = defaultdict(list)
    ids_by_stem = defaultdict(list)
    for q in qs:
        qid = q.get("id", "?")
        for f in FIELDS:
            text = str(q.get(f, "") or "")
            if not text.strip():
                issues["空字段"].append((qid, f, ""))
                continue
            if SPACE_BETWEEN_CJK.search(text):
                issues["汉字间空格"].append((qid, f, text[:60]))
            if HALF_PUNCT.search(text):
                issues["半角标点"].append((qid, f, text[:60]))
            if len(QUOTE.findall(text)) % 2:
                issues["引号不成对"].append((qid, f, text[:60]))
            if len(PAREN.findall(text)) % 2:
                issues["括号不成对"].append((qid, f, text[:60]))
            for pat, name in GARBAGE:
                if pat.search(text):
                    issues[name].append((qid, f, text[:60]))
            if f == "explain" and len(text) < 20:
                issues["解析过短"].append((qid, f, text[:60]))
        if q.get("type") in ("single", "multi"):
            opts = q.get("options") or []
            if len(opts) != 4:
                issues["选项数异常"].append((qid, "options", str(len(opts))))
            for i, o in enumerate(opts):
                if not re.match(r"^[A-D][.．、]\s*", o):
                    issues["选项无字母前缀"].append((qid, f"options[{i}]", o[:40]))
        if q.get("type") == "judge":
            stem = str(q.get("stem", ""))
            if not stem.rstrip().endswith(("。", "？", "！", "”")):
                issues["判断未以句号收尾"].append((qid, "stem", stem[:60]))
        ids_by_stem[re.sub(r"\s+", "", str(q.get("stem", "")))].append(qid)
    for stem, ids in ids_by_stem.items():
        if len(ids) > 1:
            issues["重复题干"].append((ids[0], "stem", f"{len(ids)} 条：{','.join(ids)}"))
    return qs, issues


def main():
    only = None
    if "--file" in sys.argv:
        only = sys.argv[sys.argv.index("--file") + 1]
    files = sorted(SRC.glob("questions*.json"))
    if only:
        files = [f for f in files if f.name == only]
    total = 0
    grand = Counter()
    for f in files:
        if f.name in ("questions_cardjudge.json",):
            continue
        qs, issues = scan(f)
        total += len(qs)
        print(f"== {f.name}（{len(qs)} 题）")
        for name, items in sorted(issues.items(), key=lambda x: -len(x[1])):
            grand[name] += len(items)
            print(f"  {name}: {len(items)}")
            for it in items[:3]:
                print(f"    - {it[0]} {it[1]}: {it[2]}")
    print(f"\n合计扫描 {total} 题")
    print("问题总计：", dict(grand))


if __name__ == "__main__":
    main()
