# -*- coding: utf-8 -*-
"""全面复查：结构、编码、答案一致性、跨引用、时间轴、导图。"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "政治刷题App" / "src" / "data"
subs = json.loads((DATA / "subjects.json").read_text("utf-8"))
qs = json.loads((DATA / "questions.json").read_text("utf-8"))
tl = json.loads((DATA / "timeline.json").read_text("utf-8"))
maps = json.loads((DATA / "mindmaps.json").read_text("utf-8"))

issues = defaultdict(list)

# ---------- 常见模板垃圾 ----------
JUNK = ["公众号", "微信", "配套课程", "云印", "线上5分", "扫码", "## P", "第页",
        "考研政治真题 共", "淘宝", "网盘", "qq群", "加群"]
MOJI = ["�", "□□", "。。", "，，", "、、", "（）"]

def scan(tag, text):
    for w in JUNK:
        if w in text:
            issues["模板垃圾"].append((tag, w, text[:50]))
    for w in MOJI:
        if w in text:
            issues["异常标点"].append((tag, w, text[:50]))

points = {}
for s in subs:
    for part in s["parts"]:
        for p in part["points"]:
            points[p["id"]] = (s["id"], part["id"], p)

# ---------- 考点 ----------
for pid, (sid, partid, p) in points.items():
    scan(pid, p["title"] + p["quote"] + p["core"] + "".join(p["detail"]))
    if not p["quote"].strip():
        issues["考点缺原句"].append(pid)
    if not p["refs"]:
        issues["考点缺出处"].append(pid)
    for c in p["confusions"]:
        if not c.get("a") or not c.get("b") or not c.get("diff"):
            issues["易混字段不全"].append((pid, c))
        if c.get("a") and c.get("a") == c.get("b"):
            issues["易混两端相同"].append((pid, c))

# ---------- 题目 ----------
for q in qs:
    scan(q["id"], q["stem"] + "".join(q.get("options") or []) + q.get("explain", ""))
    if q["partId"] not in {p["id"] for s in subs for p in s["parts"]}:
        issues["专题不存在"].append(q["id"])
    if not q.get("refs"):
        issues["题目缺出处"].append(q["id"])
    if q["type"] in ("single", "multi"):
        opts = q.get("options") or []
        letters = [o.strip()[:1] for o in opts]
        if letters != ["A", "B", "C", "D"]:
            issues["选项字母不规整"].append((q["id"], letters))
        # 同一题内选项完全重复
        texts = [re.sub(r"^[A-D][.．、]\s*", "", o) for o in opts]
        if len(set(texts)) < len(texts):
            issues["选项重复"].append((q["id"], texts))
        ans = q["answer"] if isinstance(q["answer"], list) else [q["answer"]]
        if any(a not in "ABCD" for a in ans):
            issues["答案非法"].append((q["id"], ans))
        # 单选答案解释里出现别的字母
        if q["type"] == "single" and len(ans) != 1:
            issues["单选多答案"].append((q["id"], ans))
    if q["type"] == "card" and not isinstance(q["answer"], str):
        issues["卡片答案非文本"].append(q["id"])
    if q["type"] == "card" and len(q["answer"]) < 2:
        issues["卡片答案过短"].append((q["id"], q["answer"]))

# ---------- 真题：正确答案文本是否出现在解析里 ----------
for q in qs:
    if q.get("source") != "zhenti" or q["type"] != "single":
        continue
    ans = q["answer"]
    opt = next((o for o in q["options"] if o.strip().startswith(ans)), "")
    body = re.sub(r"^[A-D][.．、]\s*", "", opt)
    key = re.sub(r"\s|[，。、；“”]", "", body)[:10]
    ex = re.sub(r"\s", "", q["explain"])
    if key and key not in ex and f"故{ans}" not in ex and f"{ans}正确" not in ex and f"答案为{ans}" not in ex and f"正确答案为{ans}" not in ex and f"正确答案是{ans}" not in ex and len(ex) > 80:
        issues["真题答案与解析脱节"].append((q["id"], ans, q["stem"][:30]))

# ---------- 时间轴 ----------
titles = Counter((e["year"], e["title"]) for e in tl)
for k, v in titles.items():
    if v > 1:
        issues["时间轴重复"].append(k)
for e in tl:
    for f in ("id", "year", "date", "title", "kind", "subject", "content", "meaning", "refs"):
        if not e.get(f):
            issues["时间轴字段缺失"].append((e.get("id"), f))
    if e["kind"] not in ("会议", "文件", "著作", "战争", "运动", "事件"):
        issues["时间轴类型非法"].append((e["id"], e["kind"]))

# ---------- 导图 ----------
for m in maps:
    for node in m["root"].get("children", []):
        pid = node.get("pointId")
        if pid and pid not in points:
            issues["导图指向不存在考点"].append((m["partId"], pid))

print("=" * 60)
print(f"考点 {len(points)}  题目 {len(qs)}  时间轴 {len(tl)}  导图 {len(maps)}")
total = 0
for k, v in sorted(issues.items(), key=lambda x: -len(x[1])):
    total += len(v)
    print(f"\n【{k}】{len(v)}")
    for it in v[:6]:
        print("   ", it)
print("\n合计问题", total)
