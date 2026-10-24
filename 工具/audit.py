# -*- coding: utf-8 -*-
"""对账：源文档 → 知识点 → 题库 → 导图 → 时间轴，列出缺口。"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "政治刷题App" / "src" / "data"

subjects = json.loads((DATA / "subjects.json").read_text("utf-8"))
questions = json.loads((DATA / "questions.json").read_text("utf-8"))
timeline = json.loads((DATA / "timeline.json").read_text("utf-8"))
maps = json.loads((DATA / "mindmaps.json").read_text("utf-8"))

EXPECT_PARTS = {
    "mayuan": 29, "maozhongte": 7, "xisixiang": 20, "shigang": 14, "sifa": 7, "shizheng": 8,
}

print("=" * 60)
print("1. 知识点覆盖（专题数 vs 教材目录）")
for s in subjects:
    n = len(s["parts"])
    exp = EXPECT_PARTS.get(s["id"])
    flag = "" if exp is None or n == exp else f"  ← 应为 {exp}"
    pts = sum(len(p["points"]) for p in s["parts"])
    print(f"  {s['short']:<6} 专题 {n:>2}  考点 {pts:>4}{flag}")

print("\n2. 题库覆盖")
by_point = defaultdict(int)
for q in questions:
    if q["type"] == "card":
        by_point[q["stem"]] += 1
point_ids = {p["id"] for s in subjects for part in s["parts"] for p in part["points"]}
part_ids = {p["id"] for s in subjects for p in s["parts"]}
missing_card = [p["id"] for s in subjects for part in s["parts"] for p in part["points"]
                if not any(q["type"] == "card" and q["partId"] == part["id"] and q["stem"] == p["title"]
                           for q in questions)]
print(f"  考点总数 {len(point_ids)}，无背诵卡的 {len(missing_card)}")
bad_part = Counter(q["partId"] for q in questions if q["partId"] not in part_ids)
print(f"  题目引用不存在的专题：{sum(bad_part.values())}")
types = Counter(q["type"] for q in questions)
print("  题型分布：", dict(types))
srcs = Counter(q.get("source", "handmade") for q in questions)
print("  来源分布：", dict(srcs))

print("\n3. 各学科题型是否齐全（单选/多选/判断/卡）")
by_subj = defaultdict(Counter)
for q in questions:
    by_subj[q["subject"]][q["type"]] += 1
for sid in EXPECT_PARTS:
    c = by_subj.get(sid, Counter())
    lack = [t for t in ("card", "single", "multi", "judge") if c.get(t, 0) == 0]
    print(f"  {sid:<12} 卡{c.get('card',0):>4} 单{c.get('single',0):>4} 多{c.get('multi',0):>4} 判{c.get('judge',0):>3}"
          + (f"  ← 缺 {','.join(lack)}" if lack else ""))

print("\n4. 思维导图覆盖")
map_parts = {m["partId"] for m in maps}
missing_maps = [p["id"] for s in subjects for p in s["parts"] if p["id"] not in map_parts]
print(f"  导图 {len(maps)} 张，未覆盖专题 {len(missing_maps)}")
if missing_maps:
    print("    ", missing_maps[:12], "…" if len(missing_maps) > 12 else "")

print("\n5. 时间轴")
kinds = Counter(e["kind"] for e in timeline)
print("  条目", len(timeline), dict(kinds))
years = [e["year"] for e in timeline]
print(f"  年份范围 {min(years)}—{max(years)}")
# 教材重要会议清单
book = (BASE / "原始OCR" / "2027考研政治-背诵手册【下册】-全新改版--肖秀荣.fixed.md").read_text("utf-8")
i = book.rfind("中国共产党的重要会议")
seg = book[i: i + 12000]
meetings = re.findall(r"(中共[一二三四五六七八九十]+大|八七会议|遵义会议|瓦窑堡会议|洛川会议|古田会议|"
                      r"七届二中全会|十一届三中全会|十八届三中全会|十九届六中全会|二十大|二十届三中全会)", seg)
uniq = sorted(set(meetings))
def norm(t):
    return t.replace("中国共产党", "中共").replace("党的", "中共").replace(" ", "")
tl_titles = norm(" ".join(e["title"] for e in timeline))
missing_m = [m for m in uniq if norm(m) not in tl_titles]
print(f"  教材会议 {len(uniq)} 个，时间轴缺少：{missing_m if missing_m else '无'}")

print("\n6. 提法速查关键词覆盖")
kw = Counter()
for s in subjects:
    for part in s["parts"]:
        for p in part["points"]:
            for k in p["keywords"]:
                kw[k] += 1
for k in ("根本", "本质", "前提", "决定", "源泉", "根源", "第一", "标志", "里程碑"):
    print(f"  {k}: {kw.get(k,0)}", end="   ")
print()
