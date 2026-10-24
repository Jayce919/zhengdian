#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""真题覆盖度与结构校验：每年 33 道客观题、答案/干扰项完整。"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "政治刷题App" / "知识点" / "questions_zhenti.json"
TRAPS = {"偷换概念", "扩大缩小", "张冠李戴", "绝对化", "因果倒置", "无关正确项"}


def main():
    qs = json.loads(BANK.read_text(encoding="utf-8"))
    by_year = defaultdict(set)
    errors = []
    for q in qs:
        m = re.match(r"q-zt-(\d{4})-(\d{2})$", q["id"])
        if not m:
            errors.append(f"{q['id']}: id 格式异常")
            continue
        year, n = m.group(1), int(m.group(2))
        by_year[year].add(n)
        if q["type"] not in ("single", "multi"):
            continue
        right = [q["answer"]] if isinstance(q["answer"], str) else list(q["answer"])
        letters = [o.strip()[0] for o in q["options"]]
        if len(q["options"]) != 4:
            errors.append(f"{q['id']}: 选项数 {len(q['options'])}")
        if any(r not in letters for r in right):
            errors.append(f"{q['id']}: 答案不在选项内")
        wrong = [l for l in letters if l not in right]
        d = q.get("distractors") or {}
        if set(d) != set(wrong):
            errors.append(f"{q['id']}: 干扰项 {sorted(d)} != 错误项 {sorted(wrong)}")
        for k, v in d.items():
            if not v.get("why", "").strip() or v.get("trap") not in TRAPS:
                errors.append(f"{q['id']}.{k}: why/trap 异常")
        if not q.get("explain", "").strip():
            errors.append(f"{q['id']}: 解析为空")

    print("年份  题数  缺失题号")
    total_missing = 0
    for y in range(2009, 2027):
        have = by_year.get(str(y), set())
        miss = [i for i in range(1, 34) if i not in have]
        total_missing += len(miss)
        print(f"{y}  {len(have):2d}   {miss if miss else '—'}")
    print(f"\n总计 {len(qs)} 题，缺 {total_missing} 题")
    if errors:
        print(f"结构错误 {len(errors)} 处：")
        for e in errors[:30]:
            print("  ✗", e)
    else:
        print("结构校验：0 错误")


if __name__ == "__main__":
    main()
