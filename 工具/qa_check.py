# -*- coding: utf-8 -*-
"""质量检查：OCR 残留、答案与选项不符、重复题、可疑日期、空/截断文本。"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "政治刷题App" / "src" / "data"
subjects = json.loads((DATA / "subjects.json").read_text("utf-8"))
questions = json.loads((DATA / "questions.json").read_text("utf-8"))

# 已知 OCR 误识字符（下册扫描件里成对出现的）
SUSPECT = ["垒断", "华断", "董断", "芍断", "八断", "更蔡", "翟秋白", "士地", "收关",
           "换救", "禹于", "金触", "资未", "资杰", "剩金", "商晶", "资木", "揭不", "资支",
           "�", "□", "〇", "口口", "??", "（）（）"]
DATE = re.compile(r"(1[6-9]\d{2}|20\d{2})年")

problems = defaultdict(list)

def scan_text(tag, text):
    for w in SUSPECT:
        if w in text:
            problems["OCR残留"].append((tag, w, text[:60]))

# ---------- 考点检查 ----------
for s in subjects:
    for part in s["parts"]:
        for p in part["points"]:
            scan_text(p["id"], p["quote"] + p["core"] + "".join(p["detail"]))
            if len(p["core"]) < 6:
                problems["核心过短"].append((p["id"], p["core"]))
            if not p["title"].strip() or len(p["title"]) > 44:
                problems["标题异常"].append((p["id"], p["title"]))
            # 日期合理性
            for y in DATE.findall(p["quote"] + p["core"]):
                yi = int(y)
                if yi < 1600 or yi > 2050:
                    problems["日期异常"].append((p["id"], y))
            # 核心与原文完全脱节（粗略：core 前 8 字不在 quote 中）
            # 核心里的数字（年份、比例、数量）必须能在原文中找到，防杜撰
            if not p.get("quoteExempt"):
                qn = set(re.findall(r"\d+(?:\.\d+)?", p["quote"]))
                for num in re.findall(r"\d+(?:\.\d+)?", p["core"]):
                    if num not in qn and num not in p["quote"]:
                        problems["核心数字无原文依据"].append((p["id"], num, p["core"][:50]))

# ---------- 题目检查 ----------
stems = Counter()
for q in questions:
    scan_text(q["id"], q["stem"] + "".join(q.get("options") or []) + q.get("explain", ""))
    stems[(q["type"], re.sub(r"\s|[，。、；：？！]", "", q["stem"]))] += 1
    if q["type"] in ("single", "multi"):
        opts = [o.strip()[0] for o in q.get("options") or [] if o.strip()]
        if len(opts) != 4:
            problems["选项数异常"].append((q["id"], len(opts)))
        ans = q["answer"] if isinstance(q["answer"], list) else [q["answer"]]
        if any(a not in opts for a in ans):
            problems["答案不在选项内"].append((q["id"], q["answer"]))
        if q["type"] == "multi" and len(ans) < 2:
            problems["多选少于两项"].append((q["id"], q["answer"]))
        if q["type"] == "multi" and len(set(ans)) != len(ans):
            problems["多选答案重复"].append((q["id"], q["answer"]))
    if q["type"] == "judge" and not isinstance(q["answer"], bool):
        problems["判断题答案非布尔"].append((q["id"], q["answer"]))
    if len(q["stem"]) < 6 and q["type"] != "card":
        problems["题干过短"].append((q["id"], q["stem"]))

# 重复题干（同类型）
dup = [(k, v) for k, v in stems.items() if v > 1]
problems["重复题干"].extend(dup[:20])

print("=" * 60)
print(f"考点 {sum(len(p['points']) for s in subjects for p in s['parts'])}  题目 {len(questions)}")
for k, v in problems.items():
    if not v:
        continue
    print(f"\n【{k}】{len(v)} 处")
    for item in v[:8]:
        print("   ", item)
